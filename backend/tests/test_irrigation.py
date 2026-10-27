"""Irrigation recalculation, logged applications and recorded water use."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient


class TestIrrigationCalculation:
    def test_recalculates_from_a_stored_prediction(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prediction_id"] == prediction["id"]
        assert body["gross_irrigation_mm"] >= body["net_irrigation_mm"]

    def test_a_less_efficient_system_must_deliver_more(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        efficient = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], "irrigation_efficiency": 0.9},
        ).json()
        leaky = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], "irrigation_efficiency": 0.45},
        ).json()

        # The crop's demand has not changed; what must be pumped to satisfy it
        # has. Halving the efficiency roughly doubles the delivery.
        assert leaky["cwr_mm_day"] == pytest.approx(efficient["cwr_mm_day"])
        assert leaky["gross_irrigation_mm"] > efficient["gross_irrigation_mm"]

    def test_expected_rain_reduces_what_must_be_applied(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        without = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"]},
        ).json()
        with_rain = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], "forecast_rainfall_mm": 30.0},
        ).json()
        assert with_rain["net_irrigation_mm"] < without["net_irrigation_mm"]

    def test_the_requirement_never_goes_negative(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        # More rain than the crop can use does not mean the farmer is owed
        # water back.
        body = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], "forecast_rainfall_mm": 500.0},
        ).json()
        assert body["net_irrigation_mm"] >= 0
        assert body["gross_irrigation_mm"] >= 0

    def test_an_area_produces_a_volume(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        body = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], "area_ha": 2.0},
        ).json()
        # One millimetre over one hectare is ten thousand litres.
        expected = body["gross_irrigation_mm"] * 2.0 * 10_000
        assert body["gross_irrigation_litres"] == pytest.approx(expected, rel=0.01)

    def test_the_assumptions_are_returned(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        body = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"]},
        ).json()
        assert body["assumptions"], "a figure without its assumptions is not auditable"

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("irrigation_efficiency", 0),
            ("irrigation_efficiency", 1.5),
            ("irrigation_efficiency", -0.2),
            ("forecast_rainfall_mm", -1),
            ("area_ha", 0),
            ("area_ha", -3),
        ],
    )
    def test_impossible_assumptions_are_refused(
        self, client: TestClient, headers: dict, prediction: dict, key: str, value: float
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/calculate",
            headers=headers,
            json={"prediction_id": prediction["id"], key: value},
        )
        assert response.status_code == 422, response.text

    def test_an_unknown_prediction_is_not_found(
        self, client: TestClient, headers: dict
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/calculate", headers=headers, json={"prediction_id": 999999}
        )
        assert response.status_code == 404

    def test_cannot_recalculate_another_farmers_prediction(
        self, client: TestClient, prediction: dict, other_account: dict
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/calculate",
            headers=other_account["headers"],
            json={"prediction_id": prediction["id"]},
        )
        assert response.status_code == 404

    def test_requires_authentication(self, client: TestClient, prediction: dict) -> None:
        response = client.post(
            "/api/v1/irrigation/calculate", json={"prediction_id": prediction["id"]}
        )
        assert response.status_code == 401


class TestIrrigationRecords:
    def test_logs_an_application(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/records",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "irrigation_date": dt.date.today().isoformat(),
                "water_applied_mm": 6.0,
                "method": "drip",
                "duration_hours": 2.0,
            },
        )
        assert response.status_code == 201
        assert response.json()["water_applied_mm"] == 6.0

    def test_lists_records_back(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        client.post(
            "/api/v1/irrigation/records",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "irrigation_date": dt.date.today().isoformat(),
                "water_applied_mm": 4.0,
            },
        )
        response = client.get("/api/v1/irrigation/records", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("water_applied_mm", -1),
            ("water_applied_mm", 5000),   # beyond any single application
            ("duration_hours", -2),
            ("duration_hours", 100),      # beyond the documented 48-hour cap
            ("application_efficiency", 0),
            ("application_efficiency", 2),
            ("irrigation_date", "not-a-date"),
        ],
    )
    def test_impossible_records_are_refused(
        self, client: TestClient, headers: dict, planting: dict, key: str, value: object
    ) -> None:
        payload = {
            "field_crop_id": planting["id"],
            "irrigation_date": dt.date.today().isoformat(),
            "water_applied_mm": 5.0,
            key: value,
        }
        response = client.post("/api/v1/irrigation/records", headers=headers, json=payload)
        assert response.status_code == 422, response.text

    def test_cannot_log_against_another_farmers_planting(
        self, client: TestClient, planting: dict, other_account: dict
    ) -> None:
        response = client.post(
            "/api/v1/irrigation/records",
            headers=other_account["headers"],
            json={
                "field_crop_id": planting["id"],
                "irrigation_date": dt.date.today().isoformat(),
                "water_applied_mm": 5.0,
            },
        )
        assert response.status_code == 404

    def test_records_are_scoped_to_the_farmer(
        self, client: TestClient, headers: dict, planting: dict, other_account: dict
    ) -> None:
        client.post(
            "/api/v1/irrigation/records",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "irrigation_date": dt.date.today().isoformat(),
                "water_applied_mm": 5.0,
            },
        )
        theirs = client.get("/api/v1/irrigation/records", headers=other_account["headers"])
        assert theirs.json() == []


class TestWaterUse:
    def test_records_water_use(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        response = client.post(
            "/api/v1/water-use",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "record_date": dt.date.today().isoformat(),
                "water_used_mm": 7.5,
            },
        )
        assert response.status_code == 201, response.text

    def test_lists_water_use(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        client.post(
            "/api/v1/water-use",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "record_date": dt.date.today().isoformat(),
                "water_used_mm": 7.5,
            },
        )
        response = client.get("/api/v1/water-use", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/water-use").status_code == 401


class TestAnalytics:
    def test_summarises_stored_predictions(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        response = client.get("/api/v1/analytics/cwr", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["predictions"] >= 1
        assert body["total_predicted_demand_mm"] > 0
        assert body["daily_series"]

    def test_the_balance_compares_applied_against_required(
        self, client: TestClient, headers: dict, planting: dict, prediction: dict
    ) -> None:
        client.post(
            "/api/v1/water-use",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "record_date": dt.date.today().isoformat(),
                "water_used_mm": 100.0,
            },
        )
        body = client.get("/api/v1/analytics/cwr", headers=headers).json()
        expected = body["total_water_applied_mm"] - body["total_gross_irrigation_mm"]
        assert body["balance_mm"] == pytest.approx(expected, abs=0.01)

    def test_states_what_the_balance_actually_compares(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        # A modelled demand against a self-reported application. The response
        # says so rather than letting it read as a measured water balance.
        body = client.get("/api/v1/analytics/cwr", headers=headers).json()
        assert body["note"]

    def test_empty_analytics_are_zeros_not_an_error(
        self, client: TestClient, other_account: dict
    ) -> None:
        response = client.get("/api/v1/analytics/cwr", headers=other_account["headers"])
        assert response.status_code == 200
        assert response.json()["predictions"] == 0

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/analytics/cwr").status_code == 401


class TestAdvisory:
    def test_lists_advisories_from_stored_predictions(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        response = client.get("/api/v1/advisory", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["count"] >= 1
        first = body["advisories"][0]
        for key in ("headline", "detail", "priority", "crop"):
            assert key in first

    def test_advisories_are_scoped_to_the_farmer(
        self, client: TestClient, prediction: dict, other_account: dict
    ) -> None:
        theirs = client.get("/api/v1/advisory", headers=other_account["headers"])
        assert theirs.json()["advisories"] == []

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/advisory").status_code == 401
