"""Water productivity, budget allocation and district rainfall.

These endpoints read three large source files rather than the database, so the
tests here are as much about honest degradation as about arithmetic: a missing
source must report itself, not take the service down or return an empty list
that reads as "no crop is productive".
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestCoverage:
    def test_reports_each_source(self, client: TestClient, headers: dict) -> None:
        response = client.get("/api/v1/water-intelligence/coverage", headers=headers)
        assert response.status_code == 200
        body = response.json()
        for source in ("water", "yield", "rainfall", "market"):
            assert source in body
            assert "available" in body[source]
            # Available or not, every source explains itself. That sentence is
            # what lets the interface say "this deployment has no price data"
            # rather than render an empty column.
            assert body[source]["detail"]

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/water-intelligence/coverage").status_code == 401


class TestProductivity:
    @pytest.fixture
    def productivity(self, client: TestClient, headers: dict) -> dict:
        response = client.get(
            "/api/v1/water-intelligence/productivity",
            headers=headers,
            params={"state": "Karnataka"},
        )
        assert response.status_code == 200, response.text
        return response.json()

    def test_ranks_crops(self, productivity: dict) -> None:
        crops = productivity["crops"]
        assert crops, "the join should produce a ranking"
        values = [c["wp_etc_kg_per_m3"] for c in crops]
        assert values == sorted(values, reverse=True)

    def test_productivity_is_yield_over_water(self, productivity: dict) -> None:
        # One millimetre over one hectare is ten cubic metres. Getting that
        # factor wrong by an order of magnitude still looks plausible, which is
        # exactly why it is asserted.
        for crop in productivity["crops"]:
            expected = crop["yield_kg_ha"] / (crop["etc_mm"] * 10.0)
            assert crop["wp_etc_kg_per_m3"] == pytest.approx(expected, rel=0.01)

    def test_applied_productivity_never_exceeds_transpired(
        self, productivity: dict
    ) -> None:
        # Gross irrigation includes the delivery losses, so its denominator is
        # larger. The reverse would be impossible.
        for crop in productivity["crops"]:
            assert crop["wp_applied_kg_per_m3"] <= crop["wp_etc_kg_per_m3"]

    def test_every_figure_is_physically_plausible(self, productivity: dict) -> None:
        for crop in productivity["crops"]:
            assert 0 < crop["wp_etc_kg_per_m3"] < 5, crop["crop"]
            assert crop["etc_mm"] > 0
            assert crop["gross_irrigation_mm"] >= crop["etc_mm"]
            assert crop["observations"] >= 5

    def test_the_yield_spread_brackets_the_median(self, productivity: dict) -> None:
        for crop in productivity["crops"]:
            assert crop["yield_p25_kg_ha"] <= crop["yield_kg_ha"] <= crop["yield_p75_kg_ha"]

    def test_the_limits_are_returned_with_the_numbers(self, productivity: dict) -> None:
        # The ranking is defensible; the absolute values are not authoritative.
        # That has to travel with the response, not sit only in a document.
        assert productivity["limitations"]
        assert productivity["interpretation"]

    def test_a_crop_with_no_yield_record_is_absent_rather_than_estimated(
        self, productivity: dict
    ) -> None:
        # Cumin has a water requirement in this project but no column in the
        # yield file. Substituting a neighbouring spice would be fabrication.
        assert "cumin" not in {crop["crop"] for crop in productivity["crops"]}

    def test_a_region_with_no_history_is_reported_not_silently_widened(
        self, client: TestClient, headers: dict
    ) -> None:
        response = client.get(
            "/api/v1/water-intelligence/productivity",
            headers=headers,
            params={"state": "Karnataka", "district": "Nowhere At All"},
        )
        assert response.status_code == 200
        body = response.json()
        if body["crops"]:
            # A fallback is allowed, but it must be declared, because the
            # farmer asked about a district and got a state.
            assert body["fell_back_to_state"] is True

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/water-intelligence/productivity").status_code == 401


class TestWaterBudget:
    def test_assesses_crops_against_a_budget(
        self, client: TestClient, headers: dict
    ) -> None:
        response = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 25_000, "plot_area_ha": 2.0, "state": "Karnataka"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["options"]
        assert body["available_water_m3"] == 25_000

    def test_a_crop_that_does_not_fit_reports_the_area_it_reaches(
        self, client: TestClient, headers: dict
    ) -> None:
        # Deliberately small. Growing a smaller area properly is a real option
        # and the decision this endpoint exists to inform, so a crop that will
        # not finish the plot must not simply vanish from the list.
        body = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 3_000, "plot_area_ha": 5.0, "state": "Karnataka"},
        ).json()

        infeasible = [o for o in body["options"] if not o["feasible"]]
        assert infeasible, "this budget should not finish every crop"
        for option in infeasible:
            assert 0 <= option["irrigable_area_ha"] < 5.0
            assert 0 <= option["coverage"] < 1

    def test_a_generous_budget_finishes_the_plot(
        self, client: TestClient, headers: dict
    ) -> None:
        body = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 5_000_000, "plot_area_ha": 1.0, "state": "Karnataka"},
        ).json()
        assert all(option["feasible"] for option in body["options"])
        assert all(option["coverage"] == pytest.approx(1.0) for option in body["options"])

    def test_water_needed_scales_with_the_plot(
        self, client: TestClient, headers: dict
    ) -> None:
        small = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 100_000, "plot_area_ha": 1.0, "state": "Karnataka"},
        ).json()
        large = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 100_000, "plot_area_ha": 2.0, "state": "Karnataka"},
        ).json()

        small_by_crop = {o["crop"]: o["water_needed_m3"] for o in small["options"]}
        for option in large["options"]:
            assert option["water_needed_m3"] == pytest.approx(
                small_by_crop[option["crop"]] * 2, rel=0.01
            )

    def test_can_take_its_location_from_an_owned_farm(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        response = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": 25_000, "plot_area_ha": 2.0, "farm_id": farm["id"]},
        )
        assert response.status_code == 200

    def test_cannot_use_another_farmers_farm(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        response = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=other_account["headers"],
            json={"available_water_m3": 25_000, "plot_area_ha": 2.0, "farm_id": farm["id"]},
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(
        ("water", "area"),
        [(0, 1.0), (-100, 1.0), (1000, 0), (1000, -2), (1e12, 1.0)],
    )
    def test_impossible_budgets_are_refused(
        self, client: TestClient, headers: dict, water: float, area: float
    ) -> None:
        response = client.post(
            "/api/v1/water-intelligence/water-budget",
            headers=headers,
            json={"available_water_m3": water, "plot_area_ha": area},
        )
        assert response.status_code == 422, response.text

    def test_requires_authentication(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/water-intelligence/water-budget",
            json={"available_water_m3": 1000, "plot_area_ha": 1.0},
        )
        assert response.status_code == 401


class TestDistrictRainfall:
    def test_reports_departure_and_dry_spell(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        response = client.get(
            "/api/v1/water-intelligence/rainfall",
            headers=headers,
            params={"farm_id": farm["id"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["district"] == "TUMAKURU"
        assert body["days"] > 0
        assert body["longest_dry_spell_days"] >= 0
        # The window is twenty days. The response says so rather than letting
        # it be read as a climatology.
        assert "not a climatology" in body["coverage_note"]

    def test_resolves_a_district_under_its_other_name(
        self, client: TestClient, headers: dict
    ) -> None:
        # The IMD file writes TUMKUR; farms write Tumakuru. If the alias table
        # broke, that farm would silently lose its rainfall.
        modern = client.get(
            "/api/v1/water-intelligence/rainfall",
            headers=headers,
            params={"state": "Karnataka", "district": "Tumakuru"},
        )
        historical = client.get(
            "/api/v1/water-intelligence/rainfall",
            headers=headers,
            params={"state": "Karnataka", "district": "TUMKUR"},
        )
        assert modern.status_code == historical.status_code == 200
        assert modern.json()["total_actual_mm"] == historical.json()["total_actual_mm"]

    def test_an_uncovered_district_is_a_clear_not_found(
        self, client: TestClient, headers: dict
    ) -> None:
        response = client.get(
            "/api/v1/water-intelligence/rainfall",
            headers=headers,
            params={"state": "Karnataka", "district": "Nowhere At All"},
        )
        assert response.status_code == 404
        assert response.json()["error"] == "DISTRICT_NOT_COVERED"
        # And it says which districts it does have, so the caller can recover.
        assert response.json()["details"]["covered_districts"]

    def test_a_location_is_required(self, client: TestClient, headers: dict) -> None:
        response = client.get("/api/v1/water-intelligence/rainfall", headers=headers)
        assert response.status_code == 422
        assert response.json()["error"] == "LOCATION_REQUIRED"

    def test_lists_covered_districts(self, client: TestClient, headers: dict) -> None:
        response = client.get(
            "/api/v1/water-intelligence/rainfall/districts",
            headers=headers,
            params={"state": "Karnataka"},
        )
        assert response.status_code == 200
        assert response.json()["count"] > 0

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/water-intelligence/rainfall").status_code == 401


class TestSourceUnavailable:
    def test_a_missing_source_reports_itself_rather_than_crashing(
        self, client_observing_500s: TestClient, headers: dict, monkeypatch
    ) -> None:
        from app.services import water_intelligence_service as module

        def missing():
            raise module.SourceUnavailable("baseline_season_totals.csv is missing")

        monkeypatch.setattr(module, "_season_totals", missing)

        response = client_observing_500s.get(
            "/api/v1/water-intelligence/productivity", headers=headers
        )
        # A 503 that explains itself, not a 500.
        assert response.status_code == 503
        assert response.json()["error"] == "SOURCE_UNAVAILABLE"

    def test_coverage_still_answers_when_a_source_is_broken(
        self, client: TestClient, headers: dict, monkeypatch
    ) -> None:
        from app.services import water_intelligence_service as module

        def missing():
            raise module.SourceUnavailable("yield file unreadable")

        monkeypatch.setattr(module, "_district_yield", missing)

        response = client.get("/api/v1/water-intelligence/coverage", headers=headers)
        # Reporting availability is the one thing that must keep working when
        # something is unavailable.
        assert response.status_code == 200
        assert response.json()["yield"]["available"] is False
