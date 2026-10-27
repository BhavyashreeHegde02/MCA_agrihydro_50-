"""Fixtures for the API test suite.

Three decisions shape everything here.

**Each test gets its own database.** A file-backed SQLite database per test,
created and dropped around it. Not the development database, which carries a
demo account and whatever the last manual session left behind, and not a
shared one, because ownership tests need two farmers who cannot see each other
and a leaked row between tests would make that pass for the wrong reason.

A file rather than ``:memory:``: SQLite gives every connection its own memory
database, and the application's engine pools connections, so an in-memory
database would let the schema be created on one connection and the query run
against another, empty one.

**The application is exercised, not imitated.** Only two things are replaced -
the database session and, where a test is about failure handling, the weather
provider or the model. Authentication, validation, serialisation, ownership
checks and error shaping are the real implementations, because those are what
the tests are for.

**Fixtures build state through the API, not through the ORM.** A farm created
by ``INSERT`` proves nothing about ``POST /farms``. Building through the public
surface means a broken create endpoint fails the tests that depend on it
instead of silently passing them.
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

# Import the application the same way uvicorn does, so the test suite exercises
# the real package layout rather than a copy assembled for testing.
_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent
for candidate in (str(_ROOT), str(_BACKEND)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

# Settings are read once at import and cached, so anything the suite needs to
# differ must be set before the application package is imported.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-only-secret-not-used-anywhere-else")
os.environ.setdefault("WEATHER_PROVIDER", "none")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.db.models import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

DEFAULT_PASSWORD = "Test-password-123!"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def engine(db_path: Path):
    """A fresh engine and schema for one test."""
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):  # type: ignore[no-untyped-def]
        # SQLite ignores foreign keys unless asked per connection. Without
        # this, the referential-integrity tests would pass against a database
        # that is not enforcing anything.
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


@pytest.fixture
def db(session_factory) -> Iterator[Session]:
    """A session for tests that need to inspect or corrupt state directly."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
@pytest.fixture
def client(session_factory) -> Iterator[TestClient]:
    """The real application, pointed at this test's database.

    Constructed without the ``with`` block on purpose. Entering a TestClient as
    a context manager runs the application's lifespan, and this lifespan calls
    ``create_all`` and seeds a demo account against the module-level engine -
    the *development* database, not the override. Running it would write shared
    state into the wrong file and leave each test's database still empty.

    Requests work perfectly well without the lifespan; only startup and
    shutdown hooks are skipped, and the `crops` fixture seeds exactly what a
    test asks for instead.
    """

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client_observing_500s(session_factory) -> Iterator[TestClient]:
    """A client that returns the 500 response instead of re-raising.

    TestClient re-raises an unhandled server exception by default, which is
    usually what you want - a crash in a test should surface as a crash. But it
    makes the application's own 500 handler untestable, and that handler has a
    job: return the standard error shape and, outside development, withhold the
    exception text so a stack trace or a connection string is not handed to the
    caller. Observing that requires seeing the response the client would.
    """

    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
@pytest.fixture
def crops(client: TestClient, session_factory) -> list[dict[str, Any]]:
    """The crop reference, seeded from the project's real agronomic sources.

    Not invented rows: this is the same seeding path the application runs at
    startup, so the Kc values and stage boundaries the prediction tests rely on
    are the ones the study actually uses.
    """
    from app.db.seed import seed_crops

    with session_factory() as session:
        seed_crops(session)
    response = client.get("/api/v1/crops")
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
def register_account(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
    full_name: str = "Test Farmer",
    **extra: Any,
) -> dict[str, Any]:
    """Register through the public endpoint and return the credentials."""
    email = email or f"farmer-{uuid.uuid4().hex[:10]}@jalachakra.example.com"
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "phone": "9876543210",
        **extra,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return {"email": email, "password": password, "user": response.json()}


def login(client: TestClient, email: str, password: str = DEFAULT_PASSWORD) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def account(client: TestClient) -> dict[str, Any]:
    """A registered, signed-in farmer."""
    credentials = register_account(client)
    token = login(client, credentials["email"], credentials["password"])
    return {**credentials, "token": token, "headers": auth_header(token)}


@pytest.fixture
def other_account(client: TestClient) -> dict[str, Any]:
    """A second farmer, for proving one cannot reach the other's records."""
    credentials = register_account(client, full_name="Other Farmer")
    token = login(client, credentials["email"], credentials["password"])
    return {**credentials, "token": token, "headers": auth_header(token)}


@pytest.fixture
def headers(account: dict[str, Any]) -> dict[str, str]:
    return account["headers"]


# ---------------------------------------------------------------------------
# Farm structure, built through the API
# ---------------------------------------------------------------------------
@pytest.fixture
def farm(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post(
        "/api/v1/farms",
        headers=headers,
        json={
            "name": "Test Farm",
            "total_area_ha": 5.0,
            "state": "Karnataka",
            "district": "Tumakuru",
            # Real coordinates for Tumakuru, so weather tests ask a provider
            # for a place that exists rather than a made-up point.
            "latitude": 13.34,
            "longitude": 77.10,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def field(client: TestClient, headers: dict[str, str], farm: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/farms/{farm['id']}/fields",
        headers=headers,
        json={
            "name": "Test Plot",
            "area_ha": 2.0,
            "soil_type": "clay_loam",
            "irrigation_method": "drip",
            "irrigation_efficiency": 0.9,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def planting(
    client: TestClient,
    headers: dict[str, str],
    field: dict[str, Any],
    crops: list[dict[str, Any]],
) -> dict[str, Any]:
    """A maize planting, sown far enough back to be mid-season.

    Mid-season is chosen deliberately: it is where Kc is at its peak and
    furthest from 1.0, so a prediction that ignored the growth stage would
    produce a visibly different number.
    """
    import datetime as dt

    maize = next(c for c in crops if c["slug"] == "maize")
    sowing = dt.date.today() - dt.timedelta(days=60)
    response = client.post(
        f"/api/v1/fields/{field['id']}/crops",
        headers=headers,
        json={
            "crop_id": maize["id"],
            "sowing_date": sowing.isoformat(),
            "planting_area_ha": 1.5,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Weather payloads
# ---------------------------------------------------------------------------
@pytest.fixture
def weather_payload() -> dict[str, float]:
    """A coherent day's weather: a warm, humid day with a little rain."""
    return {
        "temperature_mean_c": 27.0,
        "temperature_min_c": 21.0,
        "temperature_max_c": 33.0,
        "humidity_pct": 64.0,
        "rainfall_mm": 3.0,
    }


@pytest.fixture
def prediction(
    client: TestClient,
    headers: dict[str, str],
    planting: dict[str, Any],
    weather_payload: dict[str, float],
) -> dict[str, Any]:
    """One stored prediction, for the endpoints that read one back."""
    response = client.post(
        "/api/v1/predictions/cwr",
        headers=headers,
        json={
            "field_crop_id": planting["id"],
            "weather": weather_payload,
            "persist": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()
