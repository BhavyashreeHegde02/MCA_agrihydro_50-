"""Loading the trained model and running inference.

Three commitments shape this module.

**The API never re-implements preprocessing.** The saved artefact is a single
scikit-learn pipeline containing the imputer, the scaler, the encoder and the
estimator, all fitted on the training partition. Inference calls ``predict`` on
that object, so the preprocessing at inference is the preprocessing from
training by construction rather than by careful duplication.

**Features are assembled in the trained order.** The metadata records the exact
ordered feature list, and :meth:`ModelService.build_feature_frame` builds a frame
to match. A silently reordered column would produce plausible, wrong numbers.

**A missing model is reported, never faked.** If nothing has been promoted, the
service says so and the prediction endpoint falls back to the physics baseline
with the ML fields explicitly absent. It does not invent a confidence value.
"""

from __future__ import annotations

import dataclasses
import threading
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings
from ml import registry
from ml.logging_utils import get_logger

log = get_logger("api.ml_service")


class ModelUnavailableError(RuntimeError):
    """The promoted model cannot serve a prediction."""


MODEL_COMPATIBILITY_MESSAGE = (
    "Prediction model environment is incompatible. Check the pinned "
    "scikit-learn/model training version."
)


@dataclasses.dataclass
class Prediction:
    """One inference result, with its interval and its provenance."""

    value_mm_day: float
    lower_mm_day: float | None
    upper_mm_day: float | None
    nominal_coverage: float | None
    model_name: str
    model_version: str
    algorithm: str
    source: str  # "ml_model" or "physics_baseline"

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class ModelService:
    """Loads the promoted model once and serves predictions from it.

    Loading is lazy and guarded by a lock, so the first request pays the cost
    and concurrent requests do not race to load the same artefact twice.
    """

    def __init__(self, registry_dir: Path | None = None) -> None:
        self._registry_dir = registry_dir or settings.model_registry_dir
        self._lock = threading.Lock()
        self._pipeline: Any | None = None
        self._version: registry.ModelVersion | None = None
        self._load_error: str | None = None
        self._load_failed = False

    # -- loading ---------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self._pipeline is not None or self._load_error is not None:
            return
        with self._lock:
            if self._pipeline is not None or self._load_error is not None:
                return
            try:
                version = registry.get_active(self._registry_dir)
                if version is None:
                    self._load_error = (
                        "No model has been promoted. Train one with "
                        "'python scripts/train_models.py'. Until then the "
                        "prediction endpoint returns the physics baseline and "
                        "reports the machine-learning fields as unavailable."
                    )
                    log.warning(self._load_error)
                    return
                self._pipeline = version.load_pipeline()
                self._version = version
                log.info("loaded model %s/%s (%s)", version.name, version.version,
                         version.metadata.get("algorithm"))
            except Exception:  # noqa: BLE001 - logged and surfaced without internals
                self._load_failed = True
                self._load_error = (
                    "The active prediction model could not be loaded. Check the "
                    "pinned scikit-learn/model training version and server logs."
                )
                log.exception("failed to load the promoted prediction model")

    def reload(self) -> None:
        """Drop the cached model so the next call picks up a new promotion."""
        with self._lock:
            self._pipeline = None
            self._version = None
            self._load_error = None
            self._load_failed = False
        self._ensure_loaded()

    # -- status ----------------------------------------------------------
    @property
    def is_available(self) -> bool:
        self._ensure_loaded()
        return self._pipeline is not None

    @property
    def unavailable_reason(self) -> str | None:
        self._ensure_loaded()
        return self._load_error

    @property
    def load_failed(self) -> bool:
        self._ensure_loaded()
        return self._load_failed

    @property
    def metadata(self) -> dict[str, Any]:
        self._ensure_loaded()
        return dict(self._version.metadata) if self._version else {}

    @property
    def feature_order(self) -> list[str]:
        return list(self.metadata.get("feature_order") or [])

    @property
    def interval_settings(self) -> dict[str, Any]:
        return dict(self.metadata.get("interval") or {})

    def status(self) -> dict[str, Any]:
        """What the admin dashboard and the health check report."""
        self._ensure_loaded()
        if not self.is_available:
            return {"available": False, "reason": self._load_error}
        metadata = self.metadata
        return {
            "available": True,
            "model_name": metadata.get("model_name"),
            "version": metadata.get("version"),
            "algorithm": metadata.get("algorithm"),
            "task": (metadata.get("task") or {}).get("task"),
            "trained_at": metadata.get("saved_at"),
            "dataset_fingerprint": metadata.get("dataset_fingerprint"),
            "n_features": len(self.feature_order),
            "test_metrics": (metadata.get("metrics") or {}).get("test"),
            "interval": self.interval_settings,
            "target": {
                key: (metadata.get("target_definition") or {}).get(key)
                for key in ("name", "unit", "definition", "provenance_class",
                            "is_field_observed", "statement")
            },
        }

    # -- inference -------------------------------------------------------
    def build_feature_frame(self, features: dict[str, Any]) -> pd.DataFrame:
        """Assemble a single-row frame in exactly the trained column order.

        A feature the caller did not supply becomes NaN rather than an error:
        the pipeline's imputer was fitted for precisely this case, and refusing
        to predict because one optional input is absent would be worse advice
        than an imputed one, provided the caller is told. The endpoint reports
        which inputs were missing.
        """
        order = self.feature_order
        if not order:
            raise ModelUnavailableError("the loaded model records no feature order")
        row = {name: features.get(name, np.nan) for name in order}
        return pd.DataFrame([row], columns=order)

    def missing_features(self, features: dict[str, Any]) -> list[str]:
        return [name for name in self.feature_order
                if name not in features or features[name] is None]

    def predict(self, features: dict[str, Any]) -> Prediction:
        """Predict crop water demand for one day, with a calibrated interval."""
        self._ensure_loaded()
        if self._pipeline is None:
            raise ModelUnavailableError(self._load_error or "model unavailable")

        frame = self.build_feature_frame(features)
        try:
            value = float(self._pipeline.predict(frame)[0])
        except AttributeError as error:
            log.exception("prediction model inference failed")
            message = (
                MODEL_COMPATIBILITY_MESSAGE
                if "_fill_dtype" in str(error)
                else "The prediction model could not complete inference. Check server logs."
            )
            raise ModelUnavailableError(message) from error
        except Exception as error:  # noqa: BLE001 - log details, return a safe API error
            log.exception("prediction model inference failed")
            raise ModelUnavailableError(
                "The prediction model could not complete inference. Check server logs."
            ) from error
        # Demand cannot be negative; a model may extrapolate slightly below zero
        # on an unusual input.
        value = max(value, 0.0)

        interval = self.interval_settings
        half_width = interval.get("half_width_mm_day")
        lower = upper = None
        if half_width is not None:
            lower = max(value - float(half_width), 0.0)
            upper = value + float(half_width)

        metadata = self.metadata
        return Prediction(
            value_mm_day=value,
            lower_mm_day=lower,
            upper_mm_day=upper,
            nominal_coverage=interval.get("nominal_coverage"),
            model_name=str(metadata.get("model_name", "unknown")),
            model_version=str(metadata.get("version", "unknown")),
            algorithm=str(metadata.get("algorithm", "unknown")),
            source="ml_model",
        )

    # -- explanation -----------------------------------------------------
    def feature_importance(self) -> pd.DataFrame:
        """Permutation importance recorded at training time, on held-out data."""
        self._ensure_loaded()
        if self._version is None:
            return pd.DataFrame(columns=["feature", "importance_mae_increase"])
        path = self._version.directory / "feature_importance.csv"
        if not path.exists():
            return pd.DataFrame(columns=["feature", "importance_mae_increase"])
        return pd.read_csv(path)

    def explain(self, features: dict[str, Any], prediction: Prediction) -> dict[str, Any]:
        """Explain one prediction using the trained model's own importances.

        Global permutation importance is combined with the actual input values,
        so the explanation names the drivers the model genuinely relies on and
        reports what each was on this particular day. It is deliberately not a
        per-feature attribution: producing one honestly needs SHAP over the
        fitted pipeline, which is reported separately in the research notebook
        rather than computed inside a request.
        """
        importance = self.feature_importance()
        if importance.empty:
            return {
                "available": False,
                "reason": "no feature importance was recorded for the active model",
            }

        total = float(importance["importance_mae_increase"].clip(lower=0).sum()) or 1.0
        contributors = []
        for _, row in importance.head(6).iterrows():
            name = str(row["feature"])
            weight = max(float(row["importance_mae_increase"]), 0.0)
            contributors.append(
                {
                    "feature": name,
                    "relative_importance": round(weight / total, 4),
                    "value_today": _plain(features.get(name)),
                    "meaning": FEATURE_MEANINGS.get(name, name.replace("_", " ")),
                }
            )

        return {
            "available": True,
            "method": "permutation importance, measured on held-out test data",
            "note": (
                "These are the inputs the model relies on most across the whole "
                "test set, shown with this day's values. They are not per-day "
                "attributions for this single prediction."
            ),
            "prediction_mm_day": round(prediction.value_mm_day, 3),
            "contributors": contributors,
        }


def _plain(value: Any) -> Any:
    """Convert numpy scalars to plain Python so the response serialises."""
    if isinstance(value, (np.floating, np.integer)):
        return round(float(value), 4)
    if isinstance(value, float):
        return round(value, 4)
    return value


#: Farmer-readable descriptions of the model inputs, used in explanations.
FEATURE_MEANINGS: dict[str, str] = {
    "t2m": "average air temperature today",
    "t2m_min": "coldest temperature today",
    "t2m_max": "hottest temperature today",
    "rh2m": "air humidity today",
    "temp_range_c": "gap between the day's hottest and coldest temperature, which indicates cloud cover",
    "rainfall_mm": "rain that fell today",
    "rain_sum_7d_mm": "rain over the past week",
    "rain_sum_30d_mm": "rain over the past month",
    "days_since_rain": "days since the last rain",
    "day_of_year": "position in the year",
    "doy_sin": "position in the seasonal cycle",
    "doy_cos": "position in the seasonal cycle",
    "month": "month of the year",
    "days_after_sowing": "how long the crop has been growing",
    "crop": "which crop is planted",
    "growth_stage": "the crop's current growth stage",
    "ws2m": "wind speed today",
    "allsky_sfc_sw_dwn": "sunlight energy reaching the ground today",
}


#: One shared instance. FastAPI dependencies resolve to this.
model_service = ModelService()
