"""Registration, sign-in, token handling and the protected-route boundary.

Auth is where a mistake is quietest. A broken prediction endpoint is obvious;
a token that outlives its type, or an ownership check that leaks whether a
record exists, fails silently and correctly-looking. These tests are written
against the behaviour that matters rather than the happy path.
"""

from __future__ import annotations

import datetime as dt

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from tests.conftest import DEFAULT_PASSWORD, auth_header, login, register_account


class TestRegister:
    def test_creates_an_account_and_returns_it(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new-farmer@jalachakra.example.com",
                "password": DEFAULT_PASSWORD,
                "full_name": "New Farmer",
                "phone": "9876543210",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "new-farmer@jalachakra.example.com"
        assert body["role"] == "farmer"
        assert body["is_active"] is True

    def test_never_returns_the_password_in_any_form(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "secret@jalachakra.example.com",
                "password": "a-very-distinctive-password",
                "full_name": "Secret",
                "phone": "9876543210",
            },
        )
        # Neither the password nor its hash may appear anywhere in the body.
        assert "a-very-distinctive-password" not in response.text
        assert "password" not in response.json()
        assert "password_hash" not in response.json()

    def test_a_farmer_profile_is_created_alongside_the_user(
        self, client: TestClient
    ) -> None:
        # Registration creates both, because a user without a farmer profile
        # cannot own a farm and would be stuck.
        credentials = register_account(client, full_name="Profiled Farmer")
        token = login(client, credentials["email"])
        profile = client.get("/api/v1/farmers/profile", headers=auth_header(token))
        assert profile.status_code == 200
        assert profile.json()["full_name"] == "Profiled Farmer"

    def test_a_duplicate_email_is_a_conflict(self, client: TestClient) -> None:
        payload = {
            "email": "taken@jalachakra.example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "First",
            "phone": "9876543210",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201

        second = client.post("/api/v1/auth/register", json=payload)
        assert second.status_code == 409
        assert second.json()["error"] == "EMAIL_ALREADY_REGISTERED"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("email", "not-an-email"),
            ("email", ""),
            ("password", "short"),
            ("password", "x" * 73),  # bcrypt truncates past 72 bytes
            ("password", "test-password-123"),
            ("full_name", "A"),
            ("full_name", ""),
            ("phone", "1234567890"),
            ("phone", "987654321"),
            ("phone", "98765 43210"),
        ],
    )
    def test_invalid_values_are_rejected_and_named(
        self, client: TestClient, field: str, value: str
    ) -> None:
        payload = {
            "email": "valid@jalachakra.example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "Valid Name",
            "phone": "9876543210",
            field: value,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "VALIDATION_ERROR"
        # The response names the field, so a form can attach the message to it.
        assert any(f["field"] == field for f in body["details"]["fields"])

    @pytest.mark.parametrize("missing", ["email", "password", "full_name", "phone"])
    def test_a_missing_required_field_is_reported_by_name(
        self, client: TestClient, missing: str
    ) -> None:
        payload = {
            "email": "someone@jalachakra.example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "Someone",
            "phone": "9876543210",
        }
        del payload[missing]
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        assert any(
            f["field"] == missing for f in response.json()["details"]["fields"]
        )

    def test_every_invalid_field_is_reported_at_once(self, client: TestClient) -> None:
        # Not just the first: a farmer should fix one form, not three in turn.
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "bad",
                "password": "x",
                "full_name": "",
                "phone": "123",
            },
        )
        assert response.status_code == 422
        assert len(response.json()["details"]["fields"]) >= 3

    def test_a_wrong_json_type_is_rejected_rather_than_coerced(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": ["list", "not", "string"],
                "password": DEFAULT_PASSWORD,
                "full_name": "Typed",
                "phone": "9876543210",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_returns_a_usable_token_pair(self, client: TestClient) -> None:
        credentials = register_account(client)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": credentials["email"], "password": DEFAULT_PASSWORD},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"] and body["refresh_token"]
        assert body["token_type"].lower() == "bearer"

    def test_a_wrong_password_is_rejected(self, client: TestClient) -> None:
        credentials = register_account(client)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": credentials["email"], "password": "wrong-password"},
        )
        assert response.status_code == 401

    def test_an_unknown_email_fails_the_same_way_as_a_wrong_password(
        self, client: TestClient
    ) -> None:
        credentials = register_account(client)
        unknown = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@jalachakra.example.com", "password": DEFAULT_PASSWORD},
        )
        wrong = client.post(
            "/api/v1/auth/login",
            json={"email": credentials["email"], "password": "wrong-password"},
        )
        # Identical responses. Distinguishing them would let an attacker
        # enumerate which email addresses have accounts.
        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json()["error"] == wrong.json()["error"]

    def test_the_password_is_case_sensitive(self, client: TestClient) -> None:
        credentials = register_account(client)
        response = client.post(
            "/api/v1/auth/login",
            json={"email": credentials["email"], "password": DEFAULT_PASSWORD.upper()},
        )
        assert response.status_code == 401

    def test_missing_credentials_are_a_validation_failure(
        self, client: TestClient
    ) -> None:
        assert client.post("/api/v1/auth/login", json={}).status_code == 422


class TestProtectedRoutes:
    def test_no_token_is_rejected(self, client: TestClient) -> None:
        response = client.get("/api/v1/farms")
        assert response.status_code == 401
        assert response.json()["error"] == "NOT_AUTHENTICATED"

    @pytest.mark.parametrize(
        "header",
        [
            {"Authorization": "Bearer not-a-real-token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic dXNlcjpwYXNz"},
            {"Authorization": "totally-malformed"},
        ],
    )
    def test_a_malformed_token_is_rejected_without_crashing(
        self, client: TestClient, header: dict[str, str]
    ) -> None:
        response = client.get("/api/v1/farms", headers=header)
        assert response.status_code == 401
        # A rejection, not a 500: a bad header must never reach a handler.
        assert "error" in response.json()

    def test_a_token_signed_with_another_key_is_rejected(
        self, client: TestClient, account: dict
    ) -> None:
        forged = jwt.encode(
            {
                "sub": str(account["user"]["id"]),
                "type": "access",
                "exp": int(
                    (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).timestamp()
                ),
            },
            "an-attackers-key",
            algorithm="HS256",
        )
        response = client.get("/api/v1/farms", headers=auth_header(forged))
        assert response.status_code == 401

    def test_an_expired_token_is_rejected(self, client: TestClient, account: dict) -> None:
        expired = jwt.encode(
            {
                "sub": str(account["user"]["id"]),
                "type": "access",
                "exp": int(
                    (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).timestamp()
                ),
            },
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
        response = client.get("/api/v1/farms", headers=auth_header(expired))
        assert response.status_code == 401

    def test_a_refresh_token_cannot_be_used_as_an_access_token(
        self, client: TestClient, account: dict
    ) -> None:
        # The type claim exists for this. A refresh token lives fourteen days;
        # accepting one as an access token would extend that lifetime to every
        # endpoint in the API.
        refresh = create_refresh_token(account["user"]["id"])
        response = client.get("/api/v1/farms", headers=auth_header(refresh))
        assert response.status_code == 401

    def test_a_token_for_a_deleted_user_is_rejected(
        self, client: TestClient, account: dict, db
    ) -> None:
        from app.db.models import User

        user = db.get(User, account["user"]["id"])
        db.delete(user)
        db.commit()

        response = client.get("/api/v1/farms", headers=account["headers"])
        assert response.status_code == 401

    def test_a_deactivated_user_is_rejected(
        self, client: TestClient, account: dict, db
    ) -> None:
        from app.db.models import User

        user = db.get(User, account["user"]["id"])
        user.is_active = False
        db.commit()

        response = client.get("/api/v1/farms", headers=account["headers"])
        assert response.status_code == 401
        assert response.json()["error"] == "USER_INACTIVE"


class TestRefresh:
    def test_refresh_token_uses_configured_lifetime(self, account: dict) -> None:
        token = create_refresh_token(account["user"]["id"])
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )

        assert settings.refresh_token_expire_minutes == 7 * 24 * 60
        assert claims["exp"] - claims["iat"] == settings.refresh_token_expire_minutes * 60

    def test_exchanges_a_refresh_token_for_a_new_pair(
        self, client: TestClient, account: dict
    ) -> None:
        pair = client.post(
            "/api/v1/auth/login",
            json={"email": account["email"], "password": DEFAULT_PASSWORD},
        ).json()

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    def test_the_new_access_token_works(self, client: TestClient, account: dict) -> None:
        pair = client.post(
            "/api/v1/auth/login",
            json={"email": account["email"], "password": DEFAULT_PASSWORD},
        ).json()
        renewed = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
        ).json()

        response = client.get("/api/v1/farms", headers=auth_header(renewed["access_token"]))
        assert response.status_code == 200

    def test_an_access_token_cannot_be_used_to_refresh(
        self, client: TestClient, account: dict
    ) -> None:
        access = create_access_token(account["user"]["id"])
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
        assert response.status_code == 401

    def test_a_garbage_refresh_token_is_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-token"}
        )
        assert response.status_code == 401


class TestMeAndLogout:
    def test_me_returns_the_signed_in_user(
        self, client: TestClient, account: dict
    ) -> None:
        response = client.get("/api/v1/auth/me", headers=account["headers"])
        assert response.status_code == 200
        assert response.json()["email"] == account["email"]

    def test_me_requires_a_token(self, client: TestClient) -> None:
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_logout_succeeds(self, client: TestClient, account: dict) -> None:
        response = client.post("/api/v1/auth/logout", headers=account["headers"])
        assert response.status_code == 200

    def test_logout_requires_a_token(self, client: TestClient) -> None:
        assert client.post("/api/v1/auth/logout").status_code == 401
