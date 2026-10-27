"""The Jalachakra API.

    uvicorn app.main:app --reload --app-dir backend

Interactive documentation is at ``/docs``.

Startup creates the schema if it is absent and seeds the crop reference, so the
service is usable immediately after a clone with no migration step. Alembic is
still present and is what a real deployment should use; ``create_all`` is a
development convenience, and the log says so when it runs.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Make the repository root importable so `ml` resolves whether the app is
# started from the repository root or from backend/.
_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent
for candidate in (str(_ROOT), str(_BACKEND)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from fastapi import FastAPI, Request, status  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

from app.api.v1.router import api_router  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.db.seed import seed_crops, seed_demo_account  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.schemas.common import HealthResponse  # noqa: E402
from app.services.ml_service import model_service  # noqa: E402
from app.services.weather_service import weather_service  # noqa: E402
from ml import config as ml_config  # noqa: E402
from ml.logging_utils import get_logger, setup_logging  # noqa: E402

setup_logging("INFO")
log = get_logger("api")


def _prepare_schema() -> None:
    """Make sure a schema exists, without ever competing with Alembic.

    Three cases, and the distinction matters.

    A database that already carries ``alembic_version`` is managed by
    migrations. ``create_all`` is skipped entirely: it would add any table the
    migration history has not yet created, which is precisely the drift
    migrations exist to prevent, and it would do so invisibly.

    An empty SQLite database is a developer who has just cloned the repository.
    ``create_all`` gets them running without an extra step, and the log says
    that is what happened.

    An empty PostgreSQL database is a deployment that has not been migrated.
    The schema is created so the service starts, but this is logged as a
    warning naming the command that should have been run, because a production
    database built by ``create_all`` has no migration history and the first
    real migration will not know where to begin.
    """
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "alembic_version" in tables:
        with engine.connect() as connection:
            row = connection.exec_driver_sql(
                "select version_num from alembic_version"
            ).first()
        log.info(
            "schema is managed by Alembic at revision %s; create_all skipped",
            row[0] if row else "(none stamped)",
        )
        return

    Base.metadata.create_all(bind=engine)

    if settings.is_sqlite:
        log.info(
            "created the schema with create_all in SQLite at %s. Fine for "
            "development; run 'alembic -c backend/alembic.ini upgrade head' to "
            "manage it with migrations, and set DATABASE_URL for PostgreSQL.",
            settings.database_url,
        )
    else:
        log.warning(
            "created the schema with create_all on a non-SQLite database. This "
            "database has no migration history, so future migrations cannot be "
            "applied to it. Run 'alembic -c backend/alembic.ini upgrade head' "
            "against an empty database instead."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare the database and report what the service can actually do."""
    log.info("starting %s in %s mode", settings.app_name, settings.environment)

    _prepare_schema()

    with SessionLocal() as db:
        try:
            summary = seed_crops(db)
            log.info("crop reference: %s", summary)
        except Exception as error:  # noqa: BLE001 - startup must not be fatal here
            log.error("could not seed the crop reference: %s", error)

        if settings.environment.lower() == "development":
            try:
                demo = seed_demo_account(db)
                if demo.get("created"):
                    log.info("demo account created: %s / %s (field_crop_id=%s)",
                             demo["email"], demo["password"], demo.get("field_crop_id"))
            except Exception as error:  # noqa: BLE001
                log.error("could not create the demo account: %s", error)

    # Report model availability loudly. A service silently serving the fallback
    # is worse than one that says it is doing so.
    if model_service.is_available:
        status_payload = model_service.status()
        log.info("model %s/%s loaded (%s), test MAE %s mm/day",
                 status_payload["model_name"], status_payload["version"],
                 status_payload["algorithm"],
                 (status_payload.get("test_metrics") or {}).get("mae_mm_day"))
    else:
        log.warning("NO TRAINED MODEL: %s", model_service.unavailable_reason)
        if settings.require_active_model:
            raise RuntimeError(
                "REQUIRE_ACTIVE_MODEL is set but no model is promoted. "
                "Run: python scripts/train_models.py"
            )

    log.info("weather provider: %s (configured=%s)",
             weather_service.provider_name, weather_service.is_configured)

    yield
    log.info("shutting down")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Crop water requirement prediction and irrigation decision support.\n\n"
        "**What the numbers mean.** `cwr_mm_day` is crop water *demand*: what the "
        "crop will transpire. `net_irrigation_mm` is what must reach the root zone "
        "after rainfall. `gross_irrigation_mm` is what must be *delivered*, and is "
        "always the larger figure because no irrigation system is fully efficient. "
        "These are three different quantities and the API never conflates them.\n\n"
        "**What the model was trained on.** A FAO-56 reference-derived crop "
        "evapotranspiration, not observed field water use. No independently "
        "observed water requirement exists in this project's data, and "
        "`/api/v1/data-quality/summary` says so in the response."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# A wildcard origin and credentialed requests are mutually exclusive per the
# CORS specification, and a browser silently drops any response that claims
# both. Rather than ship a combination that cannot work, credentials are
# enabled only when the origins are actually enumerated.
_cors_wildcard = settings.cors_allows_wildcard
if _cors_wildcard:
    log.warning(
        "CORS_ORIGINS contains '*', so credentialed cross-origin requests are "
        "disabled. Set CORS_ORIGINS to the frontend's actual origins to allow "
        "cookie-bearing requests from a browser."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not _cors_wildcard,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)


# --------------------------------------------------------------------------
# One error shape for every failure
# --------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        payload = detail
    else:
        payload = {"error": _code_for(exc.status_code), "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request,
                                       exc: RequestValidationError) -> JSONResponse:
    """Report every invalid field at once, named, rather than only the first."""
    fields = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or str(error["loc"][0]),
            "problem": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": f"{len(fields)} field(s) failed validation.",
            "details": {"fields": fields},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            # The message is echoed only outside production; a stack trace or an
            # exception string can disclose internals.
            "message": (str(exc) if settings.debug and not settings.is_production
                        else "An unexpected error occurred."),
        },
    )


def _code_for(status_code: int) -> str:
    return {
        400: "BAD_REQUEST", 401: "NOT_AUTHENTICATED", 403: "FORBIDDEN",
        404: "NOT_FOUND", 409: "CONFLICT", 422: "VALIDATION_ERROR",
        429: "RATE_LIMITED", 503: "SERVICE_UNAVAILABLE",
    }.get(status_code, "ERROR")


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root() -> dict[str, Any]:
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_v1_prefix,
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """What is actually working, stated plainly."""
    site = ml_config.load_site_config()
    notes: list[str] = []

    if not model_service.is_available:
        notes.append(
            "No trained model is promoted, so predictions fall back to the FAO-56 "
            "physics baseline and report no interval. Run "
            "'python scripts/train_models.py' to train one."
        )
    if not weather_service.is_configured:
        notes.append(
            "No weather provider is configured; weather must be supplied in the "
            "prediction request."
        )
    if site.is_provisional:
        notes.append(
            f"The weather site is '{site.resolution_status}', not verified "
            "provenance. Reference evapotranspiration varies by under two percent "
            "across the plausible envelope."
        )

    metadata = model_service.metadata
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        database="postgresql" if not settings.is_sqlite else "sqlite",
        model_available=model_service.is_available,
        model_version=(f"{metadata.get('model_name')}/{metadata.get('version')}"
                       if model_service.is_available else None),
        weather_provider=weather_service.provider_name,
        site_resolution_status=site.resolution_status,
        notes=notes,
    )
