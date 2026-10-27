"""Project paths, run metadata and the weather-site configuration.

Everything another module might otherwise hard-code lives here: where the
repository is, which directory holds which stage of data, the random seed, and
the site coordinates that FAO-56 requires.

Paths resolve relative to this file, so notebooks behave identically whether
they are launched from the repository root or from ``notebooks/``.
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import os
from pathlib import Path
from typing import Any, Final

import yaml

# --------------------------------------------------------------------------
# Directory layout
# --------------------------------------------------------------------------
# ml/config.py -> ml/ -> repository root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

DATASETS_DIR: Final[Path] = PROJECT_ROOT / "datasets"
RAW_DIR: Final[Path] = DATASETS_DIR / "raw"
CLEANED_DIR: Final[Path] = DATASETS_DIR / "cleaned"
PROCESSED_DIR: Final[Path] = DATASETS_DIR / "processed"
ARCHIVE_DIR: Final[Path] = DATASETS_DIR / "archive"

CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "reports"
QUALITY_DIR: Final[Path] = REPORTS_DIR / "data_quality"
FIGURES_DIR: Final[Path] = REPORTS_DIR / "figures"
ARTIFACTS_DIR: Final[Path] = PROJECT_ROOT / "artifacts"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"

SITE_CONFIG_PATH: Final[Path] = CONFIG_DIR / "site.yaml"

# Reproducibility: one seed for the whole study.
RANDOM_SEED: Final[int] = 20260918

# Directories the pipeline is allowed to write into. ``raw`` and ``cleaned``
# are deliberately absent -- the pipeline must never create or modify them.
_WRITABLE_DIRS: Final[tuple[Path, ...]] = (
    PROCESSED_DIR,
    ARCHIVE_DIR,
    REPORTS_DIR,
    QUALITY_DIR,
    FIGURES_DIR,
    ARTIFACTS_DIR,
)


def ensure_directories() -> None:
    """Create the output directories the pipeline writes into."""
    for directory in _WRITABLE_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def run_timestamp() -> str:
    """UTC timestamp stamped into every generated artefact."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Weather-site configuration
# --------------------------------------------------------------------------
class SiteNotResolvedError(RuntimeError):
    """Raised when ET0 is requested but no defensible site is configured.

    This is the guard that stops the pipeline from silently inventing a
    coordinate.
    """


@dataclasses.dataclass(frozen=True)
class SiteConfig:
    """Latitude/elevation for the weather series, plus how they were obtained."""

    latitude_deg: float | None
    longitude_deg: float | None
    elevation_m: float | None
    resolution_status: str
    provenance: str
    caveats: str
    allow_provisional: bool
    latitude_envelope: tuple[float, float]
    elevation_envelope: tuple[float, float]
    fao56: dict[str, Any]

    @property
    def is_provisional(self) -> bool:
        """True when the coordinate is not backed by verified provenance."""
        return self.resolution_status != "measured_provenance"

    def require_usable(self) -> SiteConfig:
        """Return self, or explain precisely why ET0 must not be computed."""
        if self.latitude_deg is None or self.elevation_m is None:
            raise SiteNotResolvedError(
                "FAO-56 Penman-Monteith needs both a latitude and an elevation, "
                f"and {SITE_CONFIG_PATH} does not supply both.\n"
                "Fix: open config/site.yaml, enter the coordinates that were used "
                "when the weather series was downloaded, and set "
                "resolution_status: measured_provenance."
            )
        if self.is_provisional and not self.allow_provisional:
            raise SiteNotResolvedError(
                f"The configured site is {self.resolution_status!r}, which is not "
                "verified provenance, and site.allow_provisional is false.\n"
                "Fix: either supply a coordinate with real provenance, or set "
                "site.allow_provisional: true in config/site.yaml to proceed with "
                "results that are explicitly labelled provisional."
            )
        return self

    def as_metadata(self) -> dict[str, Any]:
        """Site description embedded in every artefact this configuration touches."""
        return {
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "elevation_m": self.elevation_m,
            "resolution_status": self.resolution_status,
            "is_provisional": self.is_provisional,
            "provenance": " ".join(self.provenance.split()),
            "caveats": " ".join(self.caveats.split()),
            "latitude_envelope_deg": list(self.latitude_envelope),
            "elevation_envelope_m": list(self.elevation_envelope),
        }


_VALID_STATUSES: Final[frozenset[str]] = frozenset(
    {"measured_provenance", "inferred_from_data", "unresolved"}
)


def load_site_config(path: Path | None = None) -> SiteConfig:
    """Read ``config/site.yaml``.

    The environment variable ``JALACHAKRA_SITE_CONFIG`` overrides the default
    location. That is how the test-suite exercises the unresolved-site branch
    without editing the checked-in configuration.
    """
    if path is None:
        env_override = os.environ.get("JALACHAKRA_SITE_CONFIG")
        path = Path(env_override) if env_override else SITE_CONFIG_PATH

    if not path.exists():
        raise SiteNotResolvedError(
            f"Site configuration not found at {path}. "
            "Copy config/site.yaml from the repository and fill it in."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    site = raw.get("site") or {}
    envelope = raw.get("sensitivity_envelope") or {}

    status = str(site.get("resolution_status", "unresolved"))
    if status not in _VALID_STATUSES:
        raise ValueError(
            f"site.resolution_status must be one of {sorted(_VALID_STATUSES)}, "
            f"got {status!r}"
        )

    lat_env = envelope.get("latitude_deg", [11.5, 25.0])
    elev_env = envelope.get("elevation_m", [0.0, 1000.0])

    def _opt_float(value: Any) -> float | None:
        return None if value is None else float(value)

    return SiteConfig(
        latitude_deg=_opt_float(site.get("latitude_deg")),
        longitude_deg=_opt_float(site.get("longitude_deg")),
        elevation_m=_opt_float(site.get("elevation_m")),
        resolution_status=status,
        provenance=str(site.get("provenance", "")).strip(),
        caveats=str(site.get("caveats", "")).strip(),
        allow_provisional=bool(site.get("allow_provisional", False)),
        latitude_envelope=(float(lat_env[0]), float(lat_env[1])),
        elevation_envelope=(float(elev_env[0]), float(elev_env[1])),
        fao56=dict(raw.get("fao56") or {}),
    )
