"""Water-aware crop recommendation.

Two stages, kept separate so the trade-off stays visible.

**Agronomic suitability.** A classifier trained on the project's suitability
samples answers "which crops grow well in these soil and climate conditions?"
from nitrogen, phosphorus, potassium, pH, temperature, humidity and rainfall.

**Water feasibility.** Suitability alone can recommend a crop the farmer has no
water for. Each candidate's seasonal demand is estimated from its own
growth-stage coefficient curve against the reference evapotranspiration for the
site, and compared with what the farmer says they can supply.

The output ranks on both and *states the trade-off* rather than collapsing it
into one opaque score. A crop that scores well agronomically but needs more water
than is available is shown, marked infeasible, with the shortfall quantified.

Honest limits, reported with every response: the suitability samples are a
curated teaching dataset with exactly 100 rows per crop, so the model's
confidence does not reflect real-world prevalence; and seasonal demand can only
be estimated for the eight crops that have a coefficient curve.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from ml.config import RANDOM_SEED
from ml.logging_utils import get_logger

log = get_logger("api.recommendation")

FEATURES = ("n", "p", "k", "ph", "temperature", "humidity", "rainfall")

#: Maps suitability-dataset crop labels onto the slugs that have a Kc curve.
LABEL_TO_SLUG: dict[str, str] = {
    "rice": "paddy",
    "maize": "maize",
    "cotton": "cotton",
    "chickpea": "chickpea",
}

_lock = threading.Lock()


@lru_cache(maxsize=1)
def _load_samples() -> pd.DataFrame:
    path = settings.processed_data_dir / "crop_suitability_samples.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the preprocessing notebook first:\n"
            "  python scripts/run_notebooks.py 02_data_preprocessing.ipynb"
        )
    return pd.read_parquet(path)


@lru_cache(maxsize=1)
def _suitability_model() -> Pipeline:
    """Fit the suitability classifier once, on first use.

    Fitting at startup would slow every boot for a feature many requests never
    touch; the dataset is small enough that first-call latency is negligible.
    """
    with _lock:
        samples = _load_samples()
        pipeline = Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", RandomForestClassifier(
                    n_estimators=300, min_samples_leaf=1,
                    random_state=RANDOM_SEED, n_jobs=-1)),
            ]
        )
        pipeline.fit(samples[list(FEATURES)], samples["label"])
        log.info("suitability classifier fitted on %d samples across %d crops",
                 len(samples), samples["label"].nunique())
        return pipeline


@lru_cache(maxsize=1)
def _seasonal_demand_by_slug() -> dict[str, float]:
    """Mean seasonal ETc per crop, from the stored baseline panel.

    Using the computed panel rather than a textbook figure keeps the
    recommendation consistent with everything else the system reports.
    """
    path = settings.processed_data_dir / "cwr_baseline_panel.parquet"
    if not path.exists():
        log.warning("baseline panel not found; water feasibility will be unavailable")
        return {}
    panel = pd.read_parquet(path, columns=["crop", "sowing_date", "etc_mm_day"])
    per_cohort = panel.groupby(["crop", "sowing_date"])["etc_mm_day"].sum()
    return {str(crop): float(value)
            for crop, value in per_cohort.groupby("crop").mean().items()}


def recommend(
    *,
    nitrogen: float, phosphorus: float, potassium: float, ph: float,
    temperature_c: float, humidity_pct: float, rainfall_mm: float,
    available_water_mm: float | None = None, top_n: int = 5,
) -> dict[str, Any]:
    """Rank crops on agronomic suitability and water feasibility together."""
    model = _suitability_model()
    demands = _seasonal_demand_by_slug()

    query = pd.DataFrame(
        [[nitrogen, phosphorus, potassium, ph, temperature_c, humidity_pct, rainfall_mm]],
        columns=list(FEATURES),
    )
    probabilities = model.predict_proba(query)[0]
    classes = list(model.named_steps["model"].classes_)
    ranked = sorted(zip(classes, probabilities), key=lambda pair: -pair[1])

    recommendations: list[dict[str, Any]] = []
    for rank, (label, probability) in enumerate(ranked[: max(top_n * 3, top_n)], start=1):
        if probability <= 0:
            continue

        slug = LABEL_TO_SLUG.get(label)
        demand = demands.get(slug) if slug else None
        reasons: list[str] = []
        caveats: list[str] = []

        reasons.append(
            f"Matches {probability:.0%} of the reference conditions recorded for this crop"
        )
        if 5.5 <= ph <= 7.5:
            reasons.append("Soil pH is in a broadly favourable range")
        elif ph < 5.5:
            caveats.append(f"Soil is acidic at pH {ph:.1f}, which limits many crops")
        else:
            caveats.append(f"Soil is alkaline at pH {ph:.1f}, which limits many crops")

        feasible = None
        balance = None
        if demand is not None:
            # Rainfall is credited at the effective fraction the baseline uses,
            # not at face value, so this matches the irrigation arithmetic.
            supply = (available_water_mm or 0.0) + 0.65 * rainfall_mm
            balance = supply - demand
            feasible = balance >= 0
            if available_water_mm is None:
                caveats.append(
                    "No irrigation capacity was given, so feasibility assumes "
                    "rainfall alone"
                )
            if feasible:
                reasons.append(
                    f"Estimated seasonal demand of {demand:,.0f} mm is within the "
                    f"{supply:,.0f} mm available"
                )
            else:
                caveats.append(
                    f"Estimated seasonal demand of {demand:,.0f} mm exceeds the "
                    f"{supply:,.0f} mm available, a shortfall of {abs(balance):,.0f} mm"
                )
        else:
            caveats.append(
                "No growth-stage coefficient curve exists for this crop, so its "
                "water demand could not be estimated"
            )

        # Infeasible crops are penalised but still shown: the farmer should see
        # that a good agronomic match was ruled out by water, and by how much.
        combined = float(probability)
        if feasible is False:
            combined *= 0.35

        recommendations.append(
            {
                "crop": label,
                "suitability_score": round(float(probability), 4),
                "suitability_rank": rank,
                "estimated_season_demand_mm": round(demand, 1) if demand else None,
                "water_feasible": feasible,
                "water_balance_mm": round(balance, 1) if balance is not None else None,
                "combined_score": round(combined, 4),
                "reasons": reasons,
                "caveats": caveats,
            }
        )

    recommendations.sort(key=lambda item: -item["combined_score"])

    return {
        "recommendations": recommendations[:top_n],
        "method": {
            "suitability": (
                "Random forest classifier over nitrogen, phosphorus, potassium, "
                "pH, temperature, humidity and rainfall, fitted on the project's "
                "suitability samples."
            ),
            "water_demand": (
                "Mean seasonal crop evapotranspiration per crop, taken from this "
                "project's own FAO-56 baseline panel rather than a textbook figure."
            ),
            "combination": (
                "Crops whose estimated demand exceeds the available supply are "
                "down-weighted but still shown, with the shortfall stated, so the "
                "trade-off stays visible."
            ),
            "rainfall_credited_at": 0.65,
        },
        "limitations": [
            "The suitability samples contain exactly 100 rows per crop, so the "
            "classifier's confidence reflects that balanced design rather than "
            "real-world prevalence.",
            "Seasonal demand could only be estimated for crops with a "
            "growth-stage coefficient curve; the rest are ranked on suitability "
            "alone and marked accordingly.",
            "Demand is computed against this project's weather series, whose "
            "geographic provenance is unresolved.",
            "This is decision support, not an agronomic prescription. Local "
            "extension advice should take precedence.",
        ],
    }
