"""Weather, crop reference, data quality, admin authorisation, error shape.

The weather tests matter because that endpoint depends on something outside
this process. An external service is slow, occasionally wrong and sometimes
absent, and the brief asks specifically that each of those degrade rather than
surface as a 500.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestWeatherStatus:
    def test_reports_the_provider_honestly(self, client: TestClient, headers: dict) -> None:
        response = client.get("/api/v1/weather/status", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert "provider" in body and "configured" in body
        # The suite runs with WEATHER_PROVIDER=none.
        assert body["configured"] is False


class TestWeatherUnavailable:
    """With no provider configured, every weather route must decline clearly."""

    def test_current_weather_declines(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        response = client.get(
            "/api/v1/weather/current", headers=headers, params={"farm_id": farm["id"]}
        )
        assert response.status_code == 503
        assert response.json()["error"] == "WEATHER_UNAVAILABLE"
        # It explains how to fix it rather than just failing.
        assert "WEATHER_PROVIDER" in response.json()["message"]

    def test_forecast_declines(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        response = client.get(
            "/api/v1/weather/forecast", headers=headers, params={"farm_id": farm["id"]}
        )
        assert response.status_code == 503


class TestWeatherLocation:
    def test_a_location_is_required(self, client: TestClient, headers: dict) -> None:
        # No farm and no coordinates. The service must ask rather than pick a
        # default location, which would silently produce weather for a place
        # the farmer has never been.
        response = client.get("/api/v1/weather/current", headers=headers)
        assert response.status_code == 422
        assert response.json()["error"] == "LOCATION_REQUIRED"

    def test_a_farm_without_coordinates_is_reported_not_guessed(
        self, client: TestClient, headers: dict
    ) -> None:
        farm = client.post(
            "/api/v1/farms", headers=headers, json={"name": "No GPS", "total_area_ha": 1.0}
        ).json()
        response = client.get(
            "/api/v1/weather/current", headers=headers, params={"farm_id": farm["id"]}
        )
        assert response.status_code == 422
        assert response.json()["error"] == "FARM_HAS_NO_COORDINATES"

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [(120, 77), (-120, 77), (13, 400), (13, -400)],
    )
    def test_impossible_coordinates_are_refused(
        self, client: TestClient, headers: dict, latitude: float, longitude: float
    ) -> None:
        response = client.get(
            "/api/v1/weather/current",
            headers=headers,
            params={"latitude": latitude, "longitude": longitude},
        )
        assert response.status_code == 422

    def test_cannot_use_another_farmers_farm_for_a_location(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        response = client.get(
            "/api/v1/weather/current",
            headers=other_account["headers"],
            params={"farm_id": farm["id"]},
        )
        assert response.status_code == 404

    def test_requires_authentication(self, client: TestClient) -> None:
        assert client.get("/api/v1/weather/current").status_code == 401


class TestWeatherProviderFailures:
    """A provider that is configured but misbehaving."""

    def test_a_timeout_becomes_a_service_unavailable_not_a_crash(
        self, client: TestClient, headers: dict, farm: dict, monkeypatch
    ) -> None:
        from app.services import weather_service as weather_module

        def timed_out(*_args, **_kwargs):
            raise weather_module.WeatherUnavailableError(
                "the provider did not respond within 8 seconds"
            )

        monkeypatch.setattr(weather_module.weather_service, "current", timed_out)

        response = client.get(
            "/api/v1/weather/current", headers=headers, params={"farm_id": farm["id"]}
        )
        assert response.status_code == 503
        assert response.status_code != 500

    def test_an_unexpected_provider_error_is_still_not_a_leak(
        self, client_observing_500s: TestClient, headers: dict, farm: dict, monkeypatch
    ) -> None:
        from app.services import weather_service as weather_module

        def explode(*_args, **_kwargs):
            raise RuntimeError("connection pool exhausted at 0x7fff")

        monkeypatch.setattr(weather_module.weather_service, "current", explode)

        response = client_observing_500s.get(
            "/api/v1/weather/current", headers=headers, params={"farm_id": farm["id"]}
        )
        # A genuinely unexpected failure is a 500, but it must still arrive in
        # the standard shape rather than as an HTML stack trace.
        assert response.status_code == 500
        body = response.json()
        assert body["error"] == "INTERNAL_ERROR"
        assert "message" in body


class TestCropReference:
    def test_lists_the_seeded_crops(self, client: TestClient, crops: list) -> None:
        assert len(crops) >= 8
        assert {"id", "slug", "name"} <= set(crops[0])

    def test_reads_one_crop(self, client: TestClient, crops: list) -> None:
        response = client.get(f"/api/v1/crops/{crops[0]['id']}")
        assert response.status_code == 200
        assert response.json()["slug"] == crops[0]["slug"]

    def test_an_unknown_crop_is_not_found(self, client: TestClient, crops: list) -> None:
        assert client.get("/api/v1/crops/999999").status_code == 404

    def test_growth_stages_are_ordered_and_contiguous(
        self, client: TestClient, crops: list
    ) -> None:
        maize = next(c for c in crops if c["slug"] == "maize")
        stages = client.get(f"/api/v1/crops/{maize['id']}/growth-stages").json()
        assert stages

        orders = [s["stage_order"] for s in stages]
        assert orders == sorted(orders)
        # Each stage must begin where the previous one ended; a gap would mean
        # a day with no defined crop coefficient.
        for earlier, later in zip(stages, stages[1:]):
            assert later["start_day"] == earlier["end_day"]

    def test_the_kc_curve_is_continuous_and_positive(
        self, client: TestClient, crops: list
    ) -> None:
        maize = next(c for c in crops if c["slug"] == "maize")
        curve = client.get(f"/api/v1/crops/{maize['id']}/kc-curve").json()
        assert len(curve) >= 4
        assert all(point["kc"] > 0 for point in curve)
        days = [point["days_after_sowing"] for point in curve]
        assert days == sorted(days)

    def test_the_curve_peaks_in_mid_season(
        self, client: TestClient, crops: list
    ) -> None:
        # The agronomic shape: low at sowing, highest at full canopy, falling
        # as the crop matures. If this inverted, every prediction would be
        # wrong in a way no unit test of the arithmetic would catch.
        maize = next(c for c in crops if c["slug"] == "maize")
        curve = client.get(f"/api/v1/crops/{maize['id']}/kc-curve").json()
        peak = max(curve, key=lambda point: point["kc"])
        assert peak["kc"] > curve[0]["kc"]
        assert peak["kc"] >= curve[-1]["kc"]

    def test_the_crop_reference_is_public(self, client: TestClient, crops: list) -> None:
        # Agronomic reference data is not anybody's private record, and the
        # crop selector needs it before a farmer has signed in anywhere.
        assert client.get("/api/v1/crops").status_code == 200


class TestDataQuality:
    def test_the_summary_states_the_targets_provenance(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/data-quality/summary")
        assert response.status_code == 200
        # The single most important disclosure this API makes: the training
        # target is reference-derived, not an observed field measurement.
        assert "observed" in response.text.lower()

    def test_alerts_are_listable(self, client: TestClient, headers: dict) -> None:
        response = client.get("/api/v1/data-quality/alerts", headers=headers)
        assert response.status_code == 200


class TestAdminAuthorisation:
    """Research endpoints aggregate across farmers and must be gated."""

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/admin/model-performance",
            "/api/v1/admin/dataset-statistics",
            "/api/v1/admin/prediction-statistics",
        ],
    )
    def test_a_farmer_is_forbidden(
        self, client: TestClient, headers: dict, path: str
    ) -> None:
        response = client.get(path, headers=headers)
        # 403, not 404: the farmer is authenticated and the route exists. This
        # is a permission answer, unlike the ownership checks elsewhere.
        assert response.status_code == 403
        assert response.json()["error"] == "FORBIDDEN"

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/admin/model-performance",
            "/api/v1/admin/dataset-statistics",
            "/api/v1/admin/prediction-statistics",
        ],
    )
    def test_anonymous_access_is_unauthenticated(
        self, client: TestClient, path: str
    ) -> None:
        assert client.get(path).status_code == 401

    def test_a_researcher_is_allowed(
        self, client: TestClient, account: dict, db
    ) -> None:
        from app.db.models import User

        user = db.get(User, account["user"]["id"])
        user.role = "researcher"
        db.commit()

        response = client.get(
            "/api/v1/admin/model-performance", headers=account["headers"]
        )
        assert response.status_code == 200


class TestErrorShape:
    """Every failure uses one shape, so a client can handle them uniformly."""

    def test_a_not_found_carries_error_and_message(
        self, client: TestClient, headers: dict
    ) -> None:
        body = client.get("/api/v1/farms/999999", headers=headers).json()
        assert set(body) >= {"error", "message"}
        assert isinstance(body["error"], str)

    def test_a_validation_failure_names_every_field(
        self, client: TestClient, headers: dict
    ) -> None:
        body = client.post(
            "/api/v1/farms", headers=headers, json={"name": "", "total_area_ha": -1}
        ).json()
        assert body["error"] == "VALIDATION_ERROR"
        for problem in body["details"]["fields"]:
            assert "field" in problem and "problem" in problem

    def test_an_unauthenticated_failure_uses_the_same_shape(
        self, client: TestClient
    ) -> None:
        body = client.get("/api/v1/farms").json()
        assert set(body) >= {"error", "message"}

    def test_an_unroutable_path_is_a_clean_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/no-such-endpoint")
        assert response.status_code == 404
        assert "error" in response.json()

    def test_malformed_json_is_rejected_cleanly(
        self, client: TestClient, headers: dict
    ) -> None:
        response = client.post(
            "/api/v1/farms",
            headers={**headers, "Content-Type": "application/json"},
            content=b"{not json at all",
        )
        assert response.status_code in (400, 422)
        assert response.status_code != 500


class TestMeta:
    def test_health_reports_what_actually_works(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "model_available" in body
        assert "weather_provider" in body

    def test_health_names_its_own_limitations(self, client: TestClient) -> None:
        # With no weather provider configured, health says so rather than
        # reporting a clean bill.
        body = client.get("/health").json()
        assert body["notes"], "health must disclose what is unavailable"

    def test_the_openapi_document_is_served(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert len(response.json()["paths"]) > 20
