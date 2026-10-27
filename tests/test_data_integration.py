import ast
from pathlib import Path

import pandas as pd
import pytest

from ml import config, data_loader, water_productivity
from ml.data_integration import (
    _active_model_support,
    _support_status,
    build_curated_layer,
)


PROJECT_ROOT = config.PROJECT_ROOT


@pytest.fixture(scope="module")
def integration_result():
    before = data_loader.raw_fingerprint()
    tables = build_curated_layer(export=False)
    after = data_loader.raw_fingerprint()
    pd.testing.assert_frame_equal(before, after)
    return {"before": before, "after": after, "tables": tables}


class TestRawIntegrity:
    def test_raw_data_unchanged(self, integration_result):
        pd.testing.assert_frame_equal(integration_result["before"], integration_result["after"])
        assert len(integration_result["before"]) > 0


class TestCanonicalMappings:
    def test_documented_crop_aliases(self, integration_result):
        mapping = integration_result["tables"]["canonical_crop_mapping"]
        by_name = mapping.set_index("original_crop_name")["canonical_crop_name"].to_dict()
        assert by_name["Paddy (Rice)"] == "rice"
        assert by_name["Finger Millet (Ragi)"] == "finger_millet"
        assert by_name["SOYABEAN"] == "soybean"

    def test_original_crop_labels_are_retained(self, integration_result):
        tables = integration_result["tables"]
        evidence = tables["crop_location_evidence"]
        mapping = tables["canonical_crop_mapping"]
        assert set(evidence["crop"]).issubset(set(mapping["original_crop_name"]))
        assert mapping["original_crop_name"].is_unique
        assert mapping["mapping_reason"].notna().all()
        assert mapping["mapping_source"].notna().all()

    def test_location_mapping_is_format_only(self, integration_result):
        mapping = integration_result["tables"]["canonical_location_mapping"]
        expected_state = mapping["original_state"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
        expected_district = mapping["original_district"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
        assert mapping["canonical_state"].tolist() == expected_state.tolist()
        assert mapping["canonical_district"].tolist() == expected_district.tolist()
        assert set(mapping["mapping_status"]).issubset({"FORMAT_ONLY", "IDENTITY_PRESERVED"})
        assert mapping["district_code"].notna().all()
        assert mapping["mapping_source"].str.contains("no district-boundary crosswalk").all()


class TestCropEvidence:
    def test_evidence_matches_positive_area_source_records(self, integration_result):
        evidence = integration_result["tables"]["crop_location_evidence"]
        raw = data_loader.load_dataset("district_yield", stage="raw")
        expected = water_productivity.build_district_yield(raw)
        expected = expected[~expected["is_aggregate"]]
        expected = expected[pd.to_numeric(expected["area_1000_ha"], errors="coerce").gt(0)]
        assert len(evidence) == len(expected)
        assert len(evidence) < len(raw) * 30
        assert evidence["source_row_id"].notna().all()
        assert evidence["source_dataset"].eq("Crops_data.csv").all()
        assert evidence["transformation_type"].eq("WIDE_CROP_TRIPLET_UNPIVOT").all()

    def test_no_duplicate_evidence_or_application_keys(self, integration_result):
        tables = integration_result["tables"]
        evidence_keys = ["state_code", "district_code", "year", "canonical_crop", "season"]
        assert not tables["crop_location_evidence"].duplicated(evidence_keys).any()
        view_keys = [
            "state", "district", "district_code", "season", "canonical_crop", "crop_category"
        ]
        assert not tables["application_location_view"].duplicated(view_keys).any()
        assert tables["application_location_view"]["evidence_type"].eq(
            "REGIONAL_CROP_EVIDENCE_NOT_SUITABILITY"
        ).all()
        assert "suitability_score" not in tables["application_location_view"]

    def test_no_index_based_joins(self):
        source = (PROJECT_ROOT / "ml" / "data_integration.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        merge_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "merge"
        ]
        assert merge_calls
        for call in merge_calls:
            keywords = {keyword.arg: keyword.value for keyword in call.keywords}
            assert "on" in keywords or ("left_on" in keywords and "right_on" in keywords)
            assert not any(
                key in keywords and isinstance(value, ast.Constant) and value.value is True
                for key, value in keywords.items()
                if key in {"left_index", "right_index"}
            )


class TestReferenceAndSupport:
    def test_kc_and_stage_values_come_from_processed_reference(self, integration_result):
        catalog = integration_result["tables"]["crop_reference_catalog"]
        source = pd.read_csv(PROJECT_ROOT / "datasets" / "processed" / "crop_stage_reference.csv")
        allowed_kc = set(pd.to_numeric(source["kc_anchor"], errors="coerce").dropna())
        allowed_duration = set(pd.to_numeric(source["duration_days"], errors="coerce").dropna())
        actual_kc = set(pd.to_numeric(catalog["kc"], errors="coerce").dropna())
        actual_duration = set(pd.to_numeric(catalog["duration_days"], errors="coerce").dropna())
        assert actual_kc.issubset(allowed_kc)
        assert actual_duration.issubset(allowed_duration)

    def test_status_logic_and_active_model_evidence(self, integration_result):
        supported, basis = _active_model_support(PROJECT_ROOT)
        assert "rice" in supported
        assert "validated held-out rows=" in basis
        assert _support_status("rice", supported, {"rice"}) == "SUPPORTED"
        assert _support_status("reference_crop", supported, {"reference_crop"}) == "REFERENCE_ONLY"
        assert _support_status("new_crop", supported, set()) == "UNDER_DEVELOPMENT"
        status = set(integration_result["tables"]["crop_reference_catalog"]["cwr_support_status"])
        assert status.issubset({"SUPPORTED", "UNDER_DEVELOPMENT", "REFERENCE_ONLY"})


class TestContextLayers:
    def test_soil_is_provisional_without_verified_state(self, integration_result):
        soil = integration_result["tables"]["soil_context_reference"]
        assert soil["data_status"].eq("PROVISIONAL").all()
        assert soil["state_if_verified"].isna().all()
        assert "latitude" not in soil and "longitude" not in soil

    def test_rainfall_products_remain_separate(self, integration_result):
        tables = integration_result["tables"]
        daily = tables["rainfall_context"]
        normals = tables["rainfall_normals_context"]
        assert daily["period_type"].eq("DAILY_OBSERVATION").all()
        assert normals["period_type"].eq("ANNUAL_NORMAL").all()
        assert normals["date"].isna().all()
        assert daily["source_dataset"].nunique() == 1
        assert normals["source_dataset"].nunique() == 1
        assert "WEEKLY" not in set(daily["period_type"])

    def test_weather_has_no_invented_location_or_units(self, integration_result):
        weather = integration_result["tables"]["weather_context"]
        assert weather["site_id"].eq("UNKNOWN").all()
        assert weather["location_status"].eq("UNKNOWN").all()
        assert weather["units_status"].eq("UNVERIFIED").all()
        assert weather["provenance_status"].eq("UNVERIFIED").all()
        assert "latitude" not in weather and "longitude" not in weather

    def test_all_curated_data_carries_lineage(self, integration_result):
        for name, frame in integration_result["tables"].items():
            if name == "join_validation_report":
                continue
            assert "source_dataset" in frame, name
            assert "source_row_id" in frame or "source_row_ids" in frame, name
            assert "transformation_type" in frame, name
            assert "mapping_status" in frame, name
            lineage_column = "source_row_id" if "source_row_id" in frame else "source_row_ids"
            assert frame[lineage_column].notna().all(), name

    def test_join_report_records_safe_and_rejected_joins(self, integration_result):
        report = integration_result["tables"]["join_validation_report"]
        assert {"join_key", "cardinality", "matched_rows", "unmatched_rows", "duplicate_expansion",
                "temporal_compatibility", "spatial_compatibility", "unit_compatibility"}.issubset(report.columns)
        assert (report.loc[report["status"] == "SAFE", "duplicate_expansion"] == 0).all()
        assert (report["status"] == "REJECTED_UNSAFE").any()
        assert not report["status"].eq("SAFE").all()

    def test_export_writes_only_curated_outputs(self, tmp_path):
        before = data_loader.raw_fingerprint()
        tables = build_curated_layer(output_dir=tmp_path, export=True)
        after = data_loader.raw_fingerprint()
        pd.testing.assert_frame_equal(before, after)
        assert all((tmp_path / f"{name}.csv").exists() for name in tables)
        assert (tmp_path / "integration_summary.json").exists()
        assert not (tmp_path / "cleaned").exists()
        assert not (tmp_path / "raw").exists()
