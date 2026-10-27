import json

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from ml import random_forest_baseline as rf
from ml import target_builder


def approved_target_metadata():
    return {
        "name": "etc_mm_day",
        "unit": "mm/day",
        "definition": "ETc = ET0 x Kc",
        "provenance_class": "reference_derived",
        "is_field_observed": False,
        "statement": "This is NOT an observed field measurement of water use.",
    }


def small_panel():
    return pd.DataFrame(
        {
            "etc_mm_day": [1.0, 2.0, 3.0],
            "et0_mm_day": [2.0, 4.0, 6.0],
            "kc": [0.5, 0.5, 0.5],
        }
    )


ASSESSMENT = (
    "Use `etc_mm_day` as a reference-derived quantity, not measured field CWR."
)


def test_target_readiness_accepts_only_documented_reference_etc():
    ready, reasons = rf.assess_target_readiness(
        approved_target_metadata(), small_panel(), ASSESSMENT
    )

    assert ready
    assert reasons == []


def test_target_readiness_blocks_unvalidated_or_field_claimed_target():
    metadata = approved_target_metadata()
    metadata["provenance_class"] = "observed"
    metadata["is_field_observed"] = True

    ready, reasons = rf.assess_target_readiness(
        metadata, small_panel(), "No validated field CWR target."
    )

    assert not ready
    assert len(reasons) >= 3


def test_feature_selection_excludes_target_and_all_leakage_columns():
    panel = pd.DataFrame(columns=[*rf.RESEARCH_FEATURES, "etc_mm_day"])
    features = rf.select_features(panel)

    assert features == list(target_builder.TASKS["reduced_input"].features)
    assert "etc_mm_day" not in features
    assert not set(features) & target_builder.LEAKAGE_SENSITIVE
    with pytest.raises(ValueError, match="target-derived"):
        rf.make_pipeline([*features, "et0_mm_day"])


def test_training_loader_uses_only_the_approved_panel_not_quarantined_targets(
    tmp_path, monkeypatch
):
    seen_paths = []
    approved_path = rf.approved_panel_path(tmp_path)
    approved_path.parent.mkdir(parents=True)
    approved_path.touch()
    monkeypatch.setattr(
        rf.pd,
        "read_parquet",
        lambda path: seen_paths.append(path) or pd.DataFrame({"approved": [1]}),
    )

    panel = rf.load_approved_panel(tmp_path)

    assert panel["approved"].tolist() == [1]
    assert seen_paths == [approved_path]
    assert rf.approved_panel_path(tmp_path).name == "cwr_baseline_panel.parquet"
    assert rf.QUARANTINED_TARGET_DATASETS == {
        "crop_dataset.csv",
        "crop_water_data.csv",
        "data_season.csv",
    }


def test_chronological_split_has_ordered_non_overlapping_periods():
    dates = pd.Series(pd.date_range("2020-01-01", periods=100).repeat(2))
    split = target_builder.chronological_split(dates)
    train_dates = dates[split["train"]]
    validation_dates = dates[split["validation"]]
    test_dates = dates[split["test"]]

    assert len(train_dates) + len(validation_dates) + len(test_dates) == len(dates)
    assert train_dates.max() < validation_dates.min()
    assert validation_dates.max() < test_dates.min()


def test_one_day_ahead_features_never_use_current_or_other_cohort_events():
    panel = pd.DataFrame(
        {
            "crop": ["rice", "rice", "rice", "maize", "maize"],
            "sowing_date": pd.to_datetime(
                ["2020-01-01", "2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"]
            ),
            "date": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-02", "2020-01-03"]
            ),
            "etc_mm_day": [1.0, 2.0, 3.0, 4.0, 5.0],
            "rainfall_mm": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )

    aligned = rf.build_one_day_ahead_panel(panel, ["rainfall_mm"])

    assert len(aligned) == 3
    assert (aligned["feature_date"] < aligned["date"]).all()
    assert ((aligned["date"] - aligned["feature_date"]).dt.days == 1).all()
    rice = aligned[aligned["crop"] == "rice"]
    maize = aligned[aligned["crop"] == "maize"]
    assert rice[["date", "rainfall_mm"]].values.tolist() == [
        [pd.Timestamp("2020-01-02"), 10.0],
        [pd.Timestamp("2020-01-03"), 20.0],
    ]
    assert maize[["date", "rainfall_mm"]].values.tolist() == [
        [pd.Timestamp("2020-01-03"), 40.0]
    ]


def test_random_forest_pipeline_imputes_and_encodes_with_train_fit():
    features = ["t2m", "crop"]
    pipeline = rf.make_pipeline(features)
    assert isinstance(pipeline, Pipeline)
    assert isinstance(pipeline.named_steps["model"], RandomForestRegressor)

    train = pd.DataFrame({"t2m": [10.0, np.nan, 20.0, 30.0], "crop": ["rice", "maize", "rice", "maize"]})
    pipeline.fit(train, [1.0, 1.5, 2.0, 2.5])
    predictions = pipeline.predict(pd.DataFrame({"t2m": [np.nan], "crop": ["unknown"]}))

    assert predictions.shape == (1,)
    assert np.isfinite(predictions).all()


def test_research_artifacts_are_marked_nonproduction_and_leave_active_model_unchanged(
    tmp_path,
):
    project_root = tmp_path
    active_pointer = project_root / "artifacts" / "models" / "ACTIVE"
    active_pointer.parent.mkdir(parents=True)
    active_pointer.write_text("reduced_input/v2\n", encoding="utf-8")
    before = active_pointer.read_bytes()
    metadata = {
        "model_name": "Random Forest",
        "model_role": "research_baseline",
        "production": False,
        "active_model": False,
        "production_ready": False,
        "active": False,
    }
    pipeline = rf.make_pipeline(["t2m"])
    pipeline.fit(pd.DataFrame({"t2m": [10.0, 20.0]}), [1.0, 2.0])

    output_dir = rf.save_research_outputs(
        project_root=project_root,
        pipeline=pipeline,
        metrics={"test": {"mae_mm_day": 0.1, "rmse_mm_day": 0.2, "r2": 0.9}},
        feature_importance=pd.DataFrame({"feature": ["t2m"], "importance": [1.0]}),
        predictions_test=pd.DataFrame({"actual": [1.0], "predicted": [1.1]}),
        residuals=pd.DataFrame({"residual": [-0.1]}),
        metadata=metadata,
    )

    assert output_dir == project_root / rf.RESEARCH_OUTPUT_RELATIVE_PATH
    assert {path.name for path in output_dir.iterdir()} == {
        "rf_metrics.json",
        "rf_feature_importance.csv",
        "rf_predictions_test.csv",
        "rf_residuals.csv",
        "rf_model.joblib",
        "rf_metadata.json",
    }
    saved_metadata = json.loads((output_dir / "rf_metadata.json").read_text(encoding="utf-8"))
    assert saved_metadata["model_role"] == "research_baseline"
    assert saved_metadata["production"] is False
    assert saved_metadata["active_model"] is False
    assert saved_metadata["production_ready"] is False
    assert saved_metadata["active"] is False
    assert active_pointer.read_bytes() == before


def test_research_writer_rejects_production_shaped_metadata(tmp_path):
    with pytest.raises(ValueError, match="research-only"):
        rf.save_research_outputs(
            project_root=tmp_path,
            pipeline=rf.make_pipeline(["t2m"]),
            metrics={},
            feature_importance=pd.DataFrame(),
            predictions_test=pd.DataFrame(),
            residuals=pd.DataFrame(),
            metadata={
                "model_role": "production",
                "production_ready": True,
                "active": True,
            },
        )
