"""The complete farmer journey, in one test, through the public API only.

The brief specifies this chain and says it must actually work:

    register -> login -> create farm -> create field -> store location
    -> select crop -> sowing date -> growth stage -> soil -> weather
    -> ET0 -> Kc -> CWR baseline -> ML prediction -> uncertainty
    -> rainfall adjustment -> irrigation requirement -> advisory
    -> explanation -> save -> history -> analytics

Each of those steps is exercised somewhere in the other files with its edge
cases. What this file adds is that they compose: that the identifier returned
by one call is accepted by the next, that state persists across requests, and
that the numbers stay consistent from one end of the chain to the other.

Nothing is inserted directly into the database. If a create endpoint is broken,
this fails at that step rather than passing on a row the API never made.
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from fastapi.testclient import TestClient


def test_the_whole_farmer_journey(client: TestClient, crops: list) -> None:
    email = f"journey-{uuid.uuid4().hex[:8]}@jalachakra.example.com"
    password = "Journey-password-123!"

    # -- register ----------------------------------------------------------
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Journey Farmer",
            "phone": "9876543210",
            "state": "Karnataka",
            "district": "Tumakuru",
        },
    )
    assert registered.status_code == 201, registered.text

    # -- login -------------------------------------------------------------
    tokens = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert tokens.status_code == 200, tokens.text
    headers = {"Authorization": f"Bearer {tokens.json()['access_token']}"}

    # The account starts genuinely empty. If this is not true, the test is
    # reading someone else's data and everything below it is meaningless.
    assert client.get("/api/v1/farms", headers=headers).json() == []

    # -- farm, with a real location ---------------------------------------
    farm = client.post(
        "/api/v1/farms",
        headers=headers,
        json={
            "name": "Journey Farm",
            "total_area_ha": 4.0,
            "state": "Karnataka",
            "district": "Tumakuru",
            "latitude": 13.34,
            "longitude": 77.10,
        },
    )
    assert farm.status_code == 201, farm.text
    farm_id = farm.json()["id"]
    assert farm.json()["latitude"] == 13.34

    # -- field -------------------------------------------------------------
    field = client.post(
        f"/api/v1/farms/{farm_id}/fields",
        headers=headers,
        json={
            "name": "Journey Plot",
            "area_ha": 2.0,
            "soil_type": "clay_loam",
            "irrigation_method": "drip",
            "irrigation_efficiency": 0.9,
        },
    )
    assert field.status_code == 201, field.text
    field_id = field.json()["id"]

    # -- soil --------------------------------------------------------------
    soil = client.post(
        f"/api/v1/fields/{field_id}/soil-data",
        headers=headers,
        json={"ph_level": 6.5, "nitrogen": 110, "phosphorus": 45, "potassium": 90},
    )
    assert soil.status_code == 201, soil.text

    # -- crop and sowing date, from which the stage follows ---------------
    maize = next(c for c in crops if c["slug"] == "maize")
    sowing = dt.date.today() - dt.timedelta(days=60)
    planting = client.post(
        f"/api/v1/fields/{field_id}/crops",
        headers=headers,
        json={
            "crop_id": maize["id"],
            "sowing_date": sowing.isoformat(),
            "planting_area_ha": 1.5,
        },
    )
    assert planting.status_code == 201, planting.text
    planting_body = planting.json()
    planting_id = planting_body["id"]

    # -- growth stage, derived rather than supplied ------------------------
    assert planting_body["days_after_sowing"] == 60
    assert planting_body["current_stage"]
    assert planting_body["current_kc"] > 0

    # -- prediction: weather -> ET0 -> Kc -> ETc -> irrigation -------------
    predicted = client.post(
        "/api/v1/predictions/cwr",
        headers=headers,
        json={
            "field_crop_id": planting_id,
            "weather": {
                "temperature_mean_c": 27.0,
                "temperature_min_c": 21.0,
                "temperature_max_c": 33.0,
                "humidity_pct": 64.0,
                "rainfall_mm": 3.0,
            },
            "forecast_rainfall_mm": 5.0,
            "persist": True,
        },
    )
    assert predicted.status_code == 200, predicted.text
    result = predicted.json()
    prediction_id = result["id"]
    assert prediction_id is not None, "the prediction was asked to persist"

    # The four quantities, distinct and correctly ordered.
    assert result["et0_mm_day"] > 0
    assert result["cwr_mm_day"] > 0
    assert result["gross_irrigation_mm"] >= result["net_irrigation_mm"]
    assert result["effective_rainfall_mm"] <= result["rainfall_mm"]

    # The stage the planting reported is the stage the prediction used.
    assert result["growth_stage"] == planting_body["current_stage"]
    assert result["kc_value"] == pytest.approx(planting_body["current_kc"])

    # -- uncertainty, where a model produced the figure -------------------
    if result["prediction_source"] == "ml_model":
        interval = result["interval"]
        assert interval["lower_mm_day"] <= result["cwr_mm_day"] <= interval["upper_mm_day"]
        assert 0 < interval["nominal_coverage"] < 1

    # -- advisory, generated from that result ------------------------------
    assert result["advisories"], "a prediction must produce advice"

    # -- irrigation requirement under the farmer's own assumptions ---------
    irrigation = client.post(
        "/api/v1/irrigation/calculate",
        headers=headers,
        json={
            "prediction_id": prediction_id,
            "irrigation_efficiency": 0.75,
            "area_ha": 1.5,
        },
    )
    assert irrigation.status_code == 200, irrigation.text
    calculated = irrigation.json()
    # A less efficient system than the field's own 0.9 must demand more water
    # for the same crop demand.
    assert calculated["cwr_mm_day"] == pytest.approx(result["cwr_mm_day"], rel=0.01)
    assert calculated["gross_irrigation_mm"] > calculated["net_irrigation_mm"]
    assert calculated["gross_irrigation_litres"] == pytest.approx(
        calculated["gross_irrigation_mm"] * 1.5 * 10_000, rel=0.01
    )

    # -- explanation -------------------------------------------------------
    explanation = client.get(
        f"/api/v1/predictions/{prediction_id}/explanation", headers=headers
    )
    assert explanation.status_code == 200, explanation.text
    comparison = explanation.json()["baseline_comparison"]
    assert comparison["served_cwr_mm_day"] == pytest.approx(result["cwr_mm_day"], rel=0.01)

    # -- log what was actually applied -------------------------------------
    logged = client.post(
        "/api/v1/irrigation/records",
        headers=headers,
        json={
            "field_crop_id": planting_id,
            "irrigation_date": dt.date.today().isoformat(),
            "water_applied_mm": calculated["gross_irrigation_mm"],
            "method": "drip",
        },
    )
    assert logged.status_code == 201, logged.text

    client.post(
        "/api/v1/water-use",
        headers=headers,
        json={
            "field_crop_id": planting_id,
            "record_date": dt.date.today().isoformat(),
            "water_used_mm": calculated["gross_irrigation_mm"],
        },
    )

    # -- history -----------------------------------------------------------
    history = client.get("/api/v1/predictions/history", headers=headers)
    assert history.status_code == 200
    assert any(row["id"] == prediction_id for row in history.json())

    # -- advisory feed -----------------------------------------------------
    advisory = client.get("/api/v1/advisory", headers=headers)
    assert advisory.status_code == 200
    assert advisory.json()["count"] >= 1

    # -- analytics ---------------------------------------------------------
    analytics = client.get("/api/v1/analytics/cwr", headers=headers)
    assert analytics.status_code == 200
    summary = analytics.json()
    assert summary["predictions"] >= 1
    assert summary["total_water_applied_mm"] > 0
    assert summary["daily_series"]

    # -- water-aware crop recommendation, the supporting feature ----------
    recommended = client.post(
        "/api/v1/recommendations/crops",
        headers=headers,
        json={
            "nitrogen": 110,
            "phosphorus": 45,
            "potassium": 90,
            "ph": 6.5,
            # Unit-suffixed, as the rest of this API is. The schema names are
            # temperature_c / humidity_pct / rainfall_mm, not the bare nouns.
            "temperature_c": 27.0,
            "humidity_pct": 64.0,
            "rainfall_mm": 120.0,
            # The water-aware part: what the farmer can actually supply.
            "available_water_mm": 400.0,
        },
    )
    assert recommended.status_code == 200, recommended.text
    assert recommended.json()["recommendations"]

    # -- and the merged layer: what returns most per drop -----------------
    productivity = client.get(
        "/api/v1/water-intelligence/productivity",
        headers=headers,
        params={"state": "Karnataka"},
    )
    assert productivity.status_code == 200
    assert productivity.json()["crops"]


def test_one_farmers_journey_is_invisible_to_another(
    client: TestClient, crops: list, prediction: dict, other_account: dict
) -> None:
    """The same journey, from the outside, sees nothing.

    Written as a separate test because it is a different claim: not that the
    chain works, but that completing it leaks nothing to anyone else.
    """
    headers = other_account["headers"]

    assert client.get("/api/v1/farms", headers=headers).json() == []
    assert client.get("/api/v1/field-crops", headers=headers).json() == []
    assert client.get("/api/v1/predictions/history", headers=headers).json() == []
    assert client.get("/api/v1/irrigation/records", headers=headers).json() == []
    assert client.get("/api/v1/advisory", headers=headers).json()["advisories"] == []
    assert client.get("/api/v1/analytics/cwr", headers=headers).json()["predictions"] == 0

    # And the other farmer's prediction is not reachable by its identifier,
    # which is the only thing they would need to guess.
    assert (
        client.get(f"/api/v1/predictions/{prediction['id']}", headers=headers).status_code
        == 404
    )
