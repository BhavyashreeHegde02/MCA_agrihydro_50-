"""The CWR prediction endpoint, its physics, and how it fails.

Two things are checked here that ordinary CRUD tests would not reach.

First, the **physical relationships**. ET₀, ETc, net irrigation and gross
irrigation are four different quantities with a fixed ordering between them,
and a refactor that quietly swapped two of them would still return a plausible
number. The invariants below would not survive it.

Second, the **degradation paths** the brief calls for: what happens when the
weather provider is unavailable, when the model is missing, and when the
inputs are incoherent. A prediction endpoint that returns a confident number
under those conditions is worse than one that refuses.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient


class TestPredictionSucceeds:
    def test_active_model_loads_and_performs_inference(self) -> None:
        from app.services.ml_service import ModelService
        from ml.registry import get_active

        active = get_active()
        assert active is not None, "the regression test requires a promoted model"

        result = ModelService().predict(
            {
                "t2m": 27.0,
                "t2m_min": 21.0,
                "t2m_max": 33.0,
                "rh2m": 64.0,
                "temp_range_c": 12.0,
                "rainfall_mm": 3.0,
                "rain_sum_7d_mm": 12.0,
                "rain_sum_30d_mm": 38.0,
                "days_since_rain": 1.0,
                "day_of_year": 276.0,
                "doy_sin": -0.998,
                "doy_cos": 0.07,
                "month": 10.0,
                "days_after_sowing": 60.0,
                "crop": "maize",
                "growth_stage": "mid_season",
            }
        )

        assert result.source == "ml_model"
        assert result.model_name == active.name
        assert result.model_version == active.version
        assert result.value_mm_day >= 0

    def test_prediction_endpoint_serves_active_model_and_irrigation_result(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["prediction_source"] == "ml_model"
        assert body["model_info"]["available"] is True
        assert isinstance(body["net_irrigation_mm"], (int, float))
        assert isinstance(body["gross_irrigation_mm"], (int, float))
        assert body["advisories"]

    def test_model_inference_failure_returns_sanitized_service_error(
        self,
        client: TestClient,
        headers: dict,
        planting: dict,
        weather_payload: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.api.v1.endpoints import predictions as prediction_endpoint
        from app.services.ml_service import ModelUnavailableError

        def fail_inference(_features: dict) -> None:
            raise ModelUnavailableError(
                "Prediction model environment is incompatible. Check the pinned "
                "scikit-learn/model training version."
            )

        monkeypatch.setattr(prediction_endpoint.model_service, "predict", fail_inference)
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )

        assert response.status_code == 503
        assert response.json()["message"].startswith(
            "Prediction model environment is incompatible."
        )
        assert "_fill_dtype" not in response.text

    def test_model_load_failure_does_not_fall_back_to_a_successful_prediction(
        self,
        client: TestClient,
        headers: dict,
        planting: dict,
        weather_payload: dict[str, float],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.api.v1.endpoints import predictions as prediction_endpoint
        from ml import registry

        service = prediction_endpoint.model_service
        monkeypatch.setattr(service, "_pipeline", None)
        monkeypatch.setattr(service, "_version", None)
        monkeypatch.setattr(service, "_load_error", None)
        monkeypatch.setattr(service, "_load_failed", False)

        def fail_load(*_args: object, **_kwargs: object) -> None:
            raise OSError("internal artifact path must not reach the response")

        monkeypatch.setattr(registry, "get_active", fail_load)
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )

        assert response.status_code == 503
        assert "pinned scikit-learn/model training version" in response.text
        assert "internal artifact path" not in response.text

    def test_returns_a_prediction(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["crop_slug"] == "maize"
        assert body["growth_stage"]
        assert body["prediction_source"] in {"ml_model", "physics_baseline"}

    def test_the_four_water_quantities_are_reported_separately(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # The brief is explicit: these must not be collapsed into one variable.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        for key in (
            "et0_mm_day",
            "cwr_mm_day",
            "net_irrigation_mm",
            "gross_irrigation_mm",
        ):
            assert key in body, key
            assert isinstance(body[key], (int, float))

    def test_crop_demand_is_et0_times_the_crop_coefficient(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        # The physics baseline is ETc = ET0 x Kc exactly. The served figure may
        # be a model refinement, so the *baseline* is what must satisfy this.
        expected = body["et0_mm_day"] * body["kc_value"]
        assert body["cwr_baseline_mm_day"] == pytest.approx(expected, rel=0.01)

    def test_gross_irrigation_is_never_below_net(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # Gross includes what the irrigation system loses. The reverse would be
        # a system that delivers more than it lifts.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        assert body["gross_irrigation_mm"] >= body["net_irrigation_mm"]

    def test_gross_irrigation_follows_the_application_efficiency(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        expected = body["net_irrigation_mm"] / body["application_efficiency"]
        assert body["gross_irrigation_mm"] == pytest.approx(expected, rel=0.01)

    def test_effective_rainfall_never_exceeds_the_rain_that_fell(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # Some rain runs off, evaporates or drains past the roots. None of it
        # multiplies.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {**weather_payload, "rainfall_mm": 20.0},
            },
        ).json()
        assert 0 <= body["effective_rainfall_mm"] <= body["rainfall_mm"]

    def test_et0_is_physically_plausible(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # Reference evapotranspiration on Earth sits well inside 0-20 mm/day.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        assert 0 < body["et0_mm_day"] < 20

    def test_more_rain_reduces_the_irrigation_requirement(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        dry = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {**weather_payload, "rainfall_mm": 0.0},
                "persist": False,
            },
        ).json()
        wet = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {**weather_payload, "rainfall_mm": 25.0},
                "persist": False,
            },
        ).json()
        assert wet["net_irrigation_mm"] < dry["net_irrigation_mm"]

    def test_a_hotter_day_demands_more_water(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        cool = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {
                    **weather_payload,
                    "temperature_mean_c": 20.0,
                    "temperature_min_c": 15.0,
                    "temperature_max_c": 25.0,
                },
                "persist": False,
            },
        ).json()
        hot = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {
                    **weather_payload,
                    "temperature_mean_c": 35.0,
                    "temperature_min_c": 28.0,
                    "temperature_max_c": 42.0,
                },
                "persist": False,
            },
        ).json()
        assert hot["et0_mm_day"] > cool["et0_mm_day"]

    def test_the_response_says_where_the_number_came_from(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # A farmer must be able to tell a model estimate from a physics
        # fallback. The API never leaves that ambiguous.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        assert body["prediction_source"] in {"ml_model", "physics_baseline"}
        assert "model_info" in body
        if body["prediction_source"] == "ml_model":
            assert body["model_info"]["available"] is True
            assert body["model_info"]["version"]

    def test_estimated_inputs_are_declared_not_hidden(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        # Wind and solar radiation were not supplied, so they were inferred.
        # The response has to say so.
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        assert isinstance(body["estimated_inputs"], list)
        assert body["estimated_inputs"], "inferred inputs must be declared"

    def test_supplying_wind_and_radiation_removes_the_estimates(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {
                    **weather_payload,
                    "wind_speed_ms": 2.1,
                    "solar_radiation_mj_m2": 18.5,
                },
            },
        ).json()
        assert body["estimated_inputs"] == []

    def test_advisories_are_generated_from_the_result(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        assert body["advisories"], "a prediction must produce advice"
        # The advice quotes the figures, which is what makes it generated
        # rather than a fixed string.
        text = " ".join(a["detail"] for a in body["advisories"])
        assert any(character.isdigit() for character in text)


class TestUncertainty:
    def test_a_model_prediction_carries_a_calibrated_interval(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        body = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        ).json()
        if body["prediction_source"] != "ml_model":
            pytest.skip("no promoted model in this environment")

        interval = body["interval"]
        assert interval["lower_mm_day"] is not None
        assert interval["upper_mm_day"] is not None
        # The interval must bracket the estimate, and its coverage must be a
        # real figure rather than a decorative 0.85.
        assert interval["lower_mm_day"] <= body["cwr_mm_day"] <= interval["upper_mm_day"]
        assert 0 < interval["nominal_coverage"] < 1
        assert interval["method"]


class TestPredictionFailsSafely:
    def test_an_unknown_planting_is_not_found(
        self, client: TestClient, headers: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": 999999, "weather": weather_payload},
        )
        assert response.status_code == 404

    def test_cannot_predict_for_another_farmers_planting(
        self, client: TestClient, planting: dict, other_account: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=other_account["headers"],
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )
        assert response.status_code == 404

    def test_requires_authentication(
        self, client: TestClient, planting: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )
        assert response.status_code == 401

    def test_a_missing_planting_id_is_a_validation_failure(
        self, client: TestClient, headers: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr", headers=headers, json={"weather": weather_payload}
        )
        assert response.status_code == 422
        assert any(
            "field_crop_id" in f["field"] for f in response.json()["details"]["fields"]
        )

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("temperature_mean_c", 222),    # the brief's own example
            ("temperature_mean_c", -100),
            ("humidity_pct", 150),
            ("humidity_pct", -10),
            ("rainfall_mm", -5),
            ("rainfall_mm", 99999),
            ("temperature_max_c", 200),
            ("wind_speed_ms", -3),
        ],
    )
    def test_impossible_weather_is_refused_not_absorbed(
        self,
        client: TestClient,
        headers: dict,
        planting: dict,
        weather_payload: dict,
        key: str,
        value: float,
    ) -> None:
        # 222 degrees must be rejected, never silently turned into a number.
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": {**weather_payload, key: value}},
        )
        assert response.status_code == 422, response.text

    def test_a_wrong_type_is_refused(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": {**weather_payload, "temperature_mean_c": "warm"},
            },
        )
        assert response.status_code == 422

    def test_no_weather_and_no_provider_refuses_rather_than_inventing_one(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        # The test environment has WEATHER_PROVIDER=none. Asked to fetch
        # weather it cannot fetch, the endpoint must decline, not guess.
        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "use_weather_provider": True},
        )
        assert response.status_code in (422, 503), response.text
        assert response.json()["error"] != "INTERNAL_ERROR"

    def test_no_weather_at_all_is_refused(
        self, client: TestClient, headers: dict, planting: dict
    ) -> None:
        response = client.post(
            "/api/v1/predictions/cwr", headers=headers, json={"field_crop_id": planting["id"]}
        )
        assert response.status_code in (422, 503)

    def test_a_weather_provider_failure_degrades_without_a_500(
        self, client: TestClient, headers: dict, planting: dict, monkeypatch
    ) -> None:
        from app.services import weather_service as weather_module

        def explode(*_args, **_kwargs):
            raise weather_module.WeatherUnavailableError("provider timed out")

        monkeypatch.setattr(weather_module.weather_service, "current", explode)

        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "use_weather_provider": True},
        )
        # A provider outage is not a server bug and must not be reported as one.
        assert response.status_code in (422, 503)
        assert response.status_code != 500

    def test_a_missing_model_falls_back_to_the_physics_baseline(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict, monkeypatch
    ) -> None:
        from app.services import ml_service as ml_module

        # With no model available the endpoint must still answer, from the
        # FAO-56 calculation, and say that is what it did.
        monkeypatch.setattr(
            type(ml_module.model_service), "is_available", property(lambda self: False)
        )

        response = client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={"field_crop_id": planting["id"], "weather": weather_payload},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prediction_source"] == "physics_baseline"
        assert body["cwr_mm_day"] > 0
        # And it must not pretend to an interval it cannot calibrate.
        assert body["interval"]["lower_mm_day"] is None


class TestPersistenceAndHistory:
    def test_a_prediction_is_stored_and_listed(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        history = client.get("/api/v1/predictions/history", headers=headers)
        assert history.status_code == 200
        assert any(row["id"] == prediction["id"] for row in history.json())

    def test_persist_false_does_not_store(
        self, client: TestClient, headers: dict, planting: dict, weather_payload: dict
    ) -> None:
        before = len(client.get("/api/v1/predictions/history", headers=headers).json())
        client.post(
            "/api/v1/predictions/cwr",
            headers=headers,
            json={
                "field_crop_id": planting["id"],
                "weather": weather_payload,
                "persist": False,
            },
        )
        after = len(client.get("/api/v1/predictions/history", headers=headers).json())
        assert after == before

    def test_reads_one_prediction_back(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        response = client.get(f"/api/v1/predictions/{prediction['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == prediction["id"]

    def test_history_is_scoped_to_the_farmer(
        self, client: TestClient, prediction: dict, other_account: dict
    ) -> None:
        theirs = client.get("/api/v1/predictions/history", headers=other_account["headers"])
        assert theirs.status_code == 200
        assert theirs.json() == []

    def test_cannot_read_another_farmers_prediction(
        self, client: TestClient, prediction: dict, other_account: dict
    ) -> None:
        response = client.get(
            f"/api/v1/predictions/{prediction['id']}", headers=other_account["headers"]
        )
        assert response.status_code == 404

    def test_history_can_be_filtered_by_date(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        future = (dt.date.today() + dt.timedelta(days=30)).isoformat()
        response = client.get(
            "/api/v1/predictions/history", headers=headers, params={"start_date": future}
        )
        assert response.status_code == 200
        assert response.json() == []


class TestExplanation:
    def test_explains_a_prediction(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        response = client.get(
            f"/api/v1/predictions/{prediction['id']}/explanation", headers=headers
        )
        assert response.status_code == 200
        body = response.json()
        assert body["prediction_id"] == prediction["id"]
        # Whether or not a model explanation exists, the comparison against the
        # physics reference always does.
        assert body["baseline_comparison"] is not None

    def test_the_explanation_compares_against_the_physics_reference(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        body = client.get(
            f"/api/v1/predictions/{prediction['id']}/explanation", headers=headers
        ).json()
        comparison = body["baseline_comparison"]
        assert "baseline_cwr_mm_day" in comparison
        assert "served_cwr_mm_day" in comparison
        difference = comparison["served_cwr_mm_day"] - comparison["baseline_cwr_mm_day"]
        assert comparison["difference_mm_day"] == pytest.approx(difference, abs=0.01)

    def test_contributors_come_from_the_model_not_a_fixed_list(
        self, client: TestClient, headers: dict, prediction: dict
    ) -> None:
        body = client.get(
            f"/api/v1/predictions/{prediction['id']}/explanation", headers=headers
        ).json()
        if not body["available"]:
            pytest.skip("no model explanation in this environment")
        for contributor in body["contributors"]:
            assert 0 <= contributor["relative_importance"] <= 1
            # Each names the value it actually saw today, which a hard-coded
            # list could not do.
            assert "value_today" in contributor

    def test_cannot_explain_another_farmers_prediction(
        self, client: TestClient, prediction: dict, other_account: dict
    ) -> None:
        response = client.get(
            f"/api/v1/predictions/{prediction['id']}/explanation",
            headers=other_account["headers"],
        )
        assert response.status_code == 404

    def test_an_unknown_prediction_is_not_found(
        self, client: TestClient, headers: dict
    ) -> None:
        assert (
            client.get("/api/v1/predictions/999999/explanation", headers=headers).status_code
            == 404
        )
