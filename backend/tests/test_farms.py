"""Farms, fields, plantings and soil — CRUD, validation and ownership.

The ownership tests are the point of this file. Everything else here is
ordinary CRUD; the isolation between two farmers is the part that, if it
broke, would be invisible until someone else's field appeared in a farmer's
list.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient


class TestFarmCrud:
    def test_creates_a_farm(self, client: TestClient, headers: dict) -> None:
        response = client.post(
            "/api/v1/farms",
            headers=headers,
            json={"name": "Green Acres", "total_area_ha": 3.5, "district": "Tumakuru"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Green Acres"
        assert body["total_area_ha"] == 3.5
        assert body["id"] > 0

    def test_lists_only_this_farmers_farms(
        self, client: TestClient, headers: dict, other_account: dict
    ) -> None:
        client.post(
            "/api/v1/farms", headers=headers, json={"name": "Mine", "total_area_ha": 1}
        )
        client.post(
            "/api/v1/farms",
            headers=other_account["headers"],
            json={"name": "Theirs", "total_area_ha": 1},
        )

        names = [f["name"] for f in client.get("/api/v1/farms", headers=headers).json()]
        assert names == ["Mine"]

    def test_reads_a_farm_back(self, client: TestClient, headers: dict, farm: dict) -> None:
        response = client.get(f"/api/v1/farms/{farm['id']}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == farm["name"]

    def test_updates_a_farm(self, client: TestClient, headers: dict, farm: dict) -> None:
        response = client.put(
            f"/api/v1/farms/{farm['id']}",
            headers=headers,
            json={"name": "Renamed", "total_area_ha": 9.0},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed"

        again = client.get(f"/api/v1/farms/{farm['id']}", headers=headers)
        assert again.json()["name"] == "Renamed"

    def test_deletes_a_farm(self, client: TestClient, headers: dict, farm: dict) -> None:
        assert client.delete(f"/api/v1/farms/{farm['id']}", headers=headers).status_code == 200
        assert client.get(f"/api/v1/farms/{farm['id']}", headers=headers).status_code == 404

    def test_a_missing_farm_is_not_found(self, client: TestClient, headers: dict) -> None:
        assert client.get("/api/v1/farms/999999", headers=headers).status_code == 404

    def test_every_farm_route_requires_a_token(
        self, client: TestClient, farm: dict
    ) -> None:
        assert client.get("/api/v1/farms").status_code == 401
        assert client.post("/api/v1/farms", json={"name": "X", "total_area_ha": 1}).status_code == 401
        assert client.get(f"/api/v1/farms/{farm['id']}").status_code == 401
        assert client.delete(f"/api/v1/farms/{farm['id']}").status_code == 401


class TestFarmValidation:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("total_area_ha", 0),        # the boundary the backend excludes
            ("total_area_ha", -5),
            ("total_area_ha", 200_000),  # above the documented maximum
            ("total_area_ha", "lots"),
            ("name", ""),
            ("latitude", 120),           # off the planet
            ("latitude", -120),
            ("longitude", 400),
        ],
    )
    def test_out_of_range_and_wrong_type_values_are_rejected(
        self, client: TestClient, headers: dict, field: str, value: object
    ) -> None:
        payload = {"name": "Valid", "total_area_ha": 2.0, field: value}
        response = client.post("/api/v1/farms", headers=headers, json=payload)
        assert response.status_code == 422, response.text

    @pytest.mark.parametrize("missing", ["name", "total_area_ha"])
    def test_a_missing_required_field_is_named(
        self, client: TestClient, headers: dict, missing: str
    ) -> None:
        payload = {"name": "Valid", "total_area_ha": 2.0}
        del payload[missing]
        response = client.post("/api/v1/farms", headers=headers, json=payload)
        assert response.status_code == 422
        assert any(f["field"] == missing for f in response.json()["details"]["fields"])

    def test_coordinates_are_optional(self, client: TestClient, headers: dict) -> None:
        # A farmer who does not know their coordinates must still be able to
        # record a farm; it only costs them live weather.
        response = client.post(
            "/api/v1/farms", headers=headers, json={"name": "No GPS", "total_area_ha": 1.0}
        )
        assert response.status_code == 201
        assert response.json()["latitude"] is None


class TestFarmOwnership:
    """One farmer must never see, change or delete another's records."""

    def test_cannot_read_another_farmers_farm(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        response = client.get(f"/api/v1/farms/{farm['id']}", headers=other_account["headers"])
        # 404, not 403. Telling an attacker that a record exists but belongs to
        # someone else is itself a disclosure.
        assert response.status_code == 404
        assert response.json()["error"] == "NOT_FOUND"

    def test_cannot_update_another_farmers_farm(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        response = client.put(
            f"/api/v1/farms/{farm['id']}",
            headers=other_account["headers"],
            json={"name": "Hijacked"},
        )
        assert response.status_code == 404

    def test_cannot_delete_another_farmers_farm(
        self, client: TestClient, headers: dict, farm: dict, other_account: dict
    ) -> None:
        assert (
            client.delete(
                f"/api/v1/farms/{farm['id']}", headers=other_account["headers"]
            ).status_code
            == 404
        )
        # And it is still there afterwards.
        assert client.get(f"/api/v1/farms/{farm['id']}", headers=headers).status_code == 200

    def test_a_missing_farm_and_someone_elses_farm_are_indistinguishable(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        theirs = client.get(f"/api/v1/farms/{farm['id']}", headers=other_account["headers"])
        absent = client.get("/api/v1/farms/999999", headers=other_account["headers"])
        assert theirs.status_code == absent.status_code == 404
        assert theirs.json()["error"] == absent.json()["error"]


class TestFields:
    def test_creates_a_field(self, client: TestClient, headers: dict, farm: dict) -> None:
        response = client.post(
            f"/api/v1/farms/{farm['id']}/fields",
            headers=headers,
            json={"name": "North Plot", "area_ha": 1.5, "irrigation_method": "drip"},
        )
        assert response.status_code == 201
        assert response.json()["irrigation_method"] == "drip"

    def test_a_field_larger_than_its_farm_is_refused(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        # The farm fixture is 5 ha.
        response = client.post(
            f"/api/v1/farms/{farm['id']}/fields",
            headers=headers,
            json={"name": "Too Big", "area_ha": 99.0},
        )
        # 422 rather than 400: the request is well formed, it just breaks a
        # rule about the farm it refers to.
        assert response.status_code == 422
        assert response.json()["error"] == "AREA_EXCEEDS_FARM"
        # The message names both quantities so a farmer can see the problem.
        assert "99" in response.json()["message"]

    def test_fields_may_not_collectively_exceed_the_farm(
        self, client: TestClient, headers: dict, farm: dict
    ) -> None:
        # Individually fine, together over the 5 ha farm.
        for area in (3.0, 2.0):
            created = client.post(
                f"/api/v1/farms/{farm['id']}/fields",
                headers=headers,
                json={"name": f"Plot {area}", "area_ha": area},
            )
            assert created.status_code == 201

        response = client.post(
            f"/api/v1/farms/{farm['id']}/fields",
            headers=headers,
            json={"name": "One Too Many", "area_ha": 1.0},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "AREA_EXCEEDS_FARM"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("area_ha", 0),
            ("area_ha", -1),
            ("name", ""),
            ("irrigation_efficiency", 0),
            ("irrigation_efficiency", 1.5),   # cannot exceed unity
            ("irrigation_method", "telepathy"),
        ],
    )
    def test_invalid_field_values_are_rejected(
        self, client: TestClient, headers: dict, farm: dict, field: str, value: object
    ) -> None:
        payload = {"name": "Valid", "area_ha": 1.0, field: value}
        response = client.post(
            f"/api/v1/farms/{farm['id']}/fields", headers=headers, json=payload
        )
        assert response.status_code == 422, response.text

    def test_cannot_add_a_field_to_another_farmers_farm(
        self, client: TestClient, farm: dict, other_account: dict
    ) -> None:
        response = client.post(
            f"/api/v1/farms/{farm['id']}/fields",
            headers=other_account["headers"],
            json={"name": "Intruder", "area_ha": 1.0},
        )
        assert response.status_code == 404

    def test_cannot_list_another_farmers_fields(
        self, client: TestClient, farm: dict, field: dict, other_account: dict
    ) -> None:
        response = client.get(
            f"/api/v1/farms/{farm['id']}/fields", headers=other_account["headers"]
        )
        assert response.status_code == 404

    def test_deleting_a_farm_removes_its_fields(
        self, client: TestClient, headers: dict, farm: dict, field: dict
    ) -> None:
        assert client.delete(f"/api/v1/farms/{farm['id']}", headers=headers).status_code == 200
        # The field goes with it; a field cannot outlive the farm it sits in.
        assert (
            client.get(f"/api/v1/farms/{farm['id']}/fields", headers=headers).status_code
            == 404
        )


class TestPlantings:
    def test_plants_a_crop_and_derives_its_stage(
        self, client: TestClient, headers: dict, field: dict, crops: list
    ) -> None:
        maize = next(c for c in crops if c["slug"] == "maize")
        sowing = dt.date.today() - dt.timedelta(days=60)
        response = client.post(
            f"/api/v1/fields/{field['id']}/crops",
            headers=headers,
            json={"crop_id": maize["id"], "sowing_date": sowing.isoformat()},
        )
        assert response.status_code == 201
        body = response.json()
        # The stage is computed from the sowing date, not supplied.
        assert body["days_after_sowing"] == 60
        assert body["current_stage"]
        assert body["current_kc"] is not None and body["current_kc"] > 0

    def test_an_unknown_crop_is_rejected(
        self, client: TestClient, headers: dict, field: dict
    ) -> None:
        response = client.post(
            f"/api/v1/fields/{field['id']}/crops",
            headers=headers,
            json={"crop_id": 999999, "sowing_date": "2026-01-01"},
        )
        assert response.status_code in (400, 404, 422)

    @pytest.mark.parametrize("bad_date", ["not-a-date", "2026-13-45", ""])
    def test_an_invalid_sowing_date_is_rejected(
        self, client: TestClient, headers: dict, field: dict, crops: list, bad_date: str
    ) -> None:
        maize = next(c for c in crops if c["slug"] == "maize")
        response = client.post(
            f"/api/v1/fields/{field['id']}/crops",
            headers=headers,
            json={"crop_id": maize["id"], "sowing_date": bad_date},
        )
        assert response.status_code == 422

    def test_cannot_plant_in_another_farmers_field(
        self, client: TestClient, field: dict, crops: list, other_account: dict
    ) -> None:
        maize = next(c for c in crops if c["slug"] == "maize")
        response = client.post(
            f"/api/v1/fields/{field['id']}/crops",
            headers=other_account["headers"],
            json={"crop_id": maize["id"], "sowing_date": "2026-07-01"},
        )
        assert response.status_code == 404

    def test_cannot_read_another_farmers_planting(
        self, client: TestClient, planting: dict, other_account: dict
    ) -> None:
        response = client.get(
            f"/api/v1/field-crops/{planting['id']}", headers=other_account["headers"]
        )
        assert response.status_code == 404

    def test_listing_all_plantings_is_scoped_to_the_farmer(
        self, client: TestClient, planting: dict, other_account: dict
    ) -> None:
        theirs = client.get("/api/v1/field-crops", headers=other_account["headers"])
        assert theirs.status_code == 200
        assert theirs.json() == []


class TestSoil:
    def test_records_a_soil_reading(
        self, client: TestClient, headers: dict, field: dict
    ) -> None:
        response = client.post(
            f"/api/v1/fields/{field['id']}/soil-data",
            headers=headers,
            json={"ph_level": 6.4, "nitrogen": 120, "texture": "clay loam"},
        )
        assert response.status_code == 201
        assert response.json()["ph_level"] == 6.4

    def test_a_partial_reading_is_accepted(
        self, client: TestClient, headers: dict, field: dict
    ) -> None:
        # A farmer may know only pH. Requiring the full set would mean
        # recording nothing.
        response = client.post(
            f"/api/v1/fields/{field['id']}/soil-data", headers=headers, json={"ph_level": 7.0}
        )
        assert response.status_code == 201
        assert response.json()["nitrogen"] is None

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("ph_level", -1),     # pH runs 0 to 14
            ("ph_level", 15),
            ("nitrogen", -5),     # a negative nutrient is impossible
            ("organic_matter", 150),  # a percentage cannot exceed 100
            ("ph_level", "acidic"),
        ],
    )
    def test_impossible_soil_values_are_rejected(
        self, client: TestClient, headers: dict, field: dict, field_name: str, value: object
    ) -> None:
        response = client.post(
            f"/api/v1/fields/{field['id']}/soil-data",
            headers=headers,
            json={field_name: value},
        )
        assert response.status_code == 422, response.text

    def test_reads_soil_readings_back(
        self, client: TestClient, headers: dict, field: dict
    ) -> None:
        client.post(
            f"/api/v1/fields/{field['id']}/soil-data", headers=headers, json={"ph_level": 6.0}
        )
        response = client.get(f"/api/v1/fields/{field['id']}/soil-data", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_cannot_read_another_farmers_soil(
        self, client: TestClient, field: dict, other_account: dict
    ) -> None:
        response = client.get(
            f"/api/v1/fields/{field['id']}/soil-data", headers=other_account["headers"]
        )
        assert response.status_code == 404


class TestProfile:
    def test_reads_the_profile(self, client: TestClient, headers: dict) -> None:
        response = client.get("/api/v1/farmers/profile", headers=headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Test Farmer"

    def test_updates_the_profile(self, client: TestClient, headers: dict) -> None:
        response = client.put(
            "/api/v1/farmers/profile",
            headers=headers,
            json={"full_name": "Renamed Farmer", "district": "Mysuru"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Renamed Farmer"

    def test_a_too_short_name_is_rejected(self, client: TestClient, headers: dict) -> None:
        response = client.put(
            "/api/v1/farmers/profile", headers=headers, json={"full_name": "A"}
        )
        assert response.status_code == 422

    def test_the_profile_requires_a_token(self, client: TestClient) -> None:
        assert client.get("/api/v1/farmers/profile").status_code == 401
