"""Water productivity, budget allocation and rainfall context, for the API.

This service is the application-side face of ``ml.water_productivity``. It owns
the loading and caching of three source files that are expensive to parse and
never change while the process runs, and it degrades honestly: a source that
cannot be read makes its features report themselves unavailable, rather than
taking the whole service down or quietly returning empty results that look
like "no crops are productive".

The heavy frame here is the district yield record - 57 132 rows after
reshaping. It is parsed once on first use and held, because re-reading and
re-reshaping an 80-column CSV on every request would dominate the response
time of an endpoint whose actual arithmetic is a division.
"""

from __future__ import annotations

import dataclasses
from functools import lru_cache
from typing import Any

import pandas as pd

from ml import config as ml_config
from ml import data_loader, districts
from ml import water_productivity as wp
from ml.logging_utils import get_logger

log = get_logger("api.water_intelligence")


class SourceUnavailable(RuntimeError):
    """A source file this feature needs could not be read."""


# --------------------------------------------------------------------------
# Cached sources
# --------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _season_totals() -> pd.DataFrame:
    """Seasonal water requirement per crop, from the research pipeline."""
    path = ml_config.PROCESSED_DIR / "baseline_season_totals.csv"
    if not path.exists():
        raise SourceUnavailable(
            "baseline_season_totals.csv is missing. Run the baseline: "
            "python scripts/train_models.py"
        )
    return pd.read_csv(path)


@lru_cache(maxsize=1)
def _district_yield() -> pd.DataFrame:
    """District-year yields, reshaped long. The expensive one."""
    raw = data_loader.load_dataset("district_yield", stage="raw")
    frame = wp.build_district_yield(raw)
    log.info("district yield cached: %d rows", len(frame))
    return frame


@lru_cache(maxsize=1)
def _district_rainfall() -> pd.DataFrame:
    raw = data_loader.load_dataset("district_rainfall_daily", stage="raw")
    return wp.build_district_rainfall(raw)


@lru_cache(maxsize=1)
def _market() -> pd.DataFrame:
    # Read through the dedicated loader: the workbook's headings sit on the
    # third row under a title banner, which load_dataset cannot express.
    return wp.build_market_prices(wp.load_market_sheet())


# --------------------------------------------------------------------------
# Coverage, stated up front
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class SourceCoverage:
    """What each source actually covers, so the interface can say so."""

    available: bool
    detail: str
    rows: int = 0


class WaterIntelligenceService:
    """Water productivity and allocation over the joined sources."""

    # -- availability ----------------------------------------------------
    def coverage(self) -> dict[str, Any]:
        """What this service can currently answer, and on what evidence.

        Called by the interface before it offers a feature, so a farmer is
        told "this deployment has no price data" rather than shown an empty
        rupees column.
        """
        report: dict[str, Any] = {}

        try:
            totals = _season_totals()
            report["water"] = dataclasses.asdict(
                SourceCoverage(
                    available=True,
                    rows=len(totals),
                    detail=(
                        f"Seasonal FAO-56 water requirement for {len(totals)} crops, "
                        "from this project's own baseline."
                    ),
                )
            )
        except Exception as error:  # noqa: BLE001 - reported, not raised
            report["water"] = dataclasses.asdict(
                SourceCoverage(available=False, detail=str(error))
            )

        try:
            yields = _district_yield()
            usable = yields[(~yields["is_aggregate"]) & (~yields["not_recorded"])]
            report["yield"] = dataclasses.asdict(
                SourceCoverage(
                    available=True,
                    rows=len(usable),
                    detail=(
                        f"{len(usable):,} district-year observations, "
                        f"{int(yields['year'].min())}-{int(yields['year'].max())}, "
                        f"{yields['district'].nunique()} districts, "
                        f"{yields['state'].nunique()} states."
                    ),
                )
            )
        except Exception as error:  # noqa: BLE001
            report["yield"] = dataclasses.asdict(
                SourceCoverage(available=False, detail=str(error))
            )

        try:
            rain = _district_rainfall()
            report["rainfall"] = dataclasses.asdict(
                SourceCoverage(
                    available=True,
                    rows=len(rain),
                    detail=(
                        f"IMD daily district rainfall, "
                        f"{rain['date'].min().date()} to {rain['date'].max().date()} "
                        f"({rain['date'].nunique()} days), "
                        f"{rain['district'].nunique()} districts. "
                        "Current-season context only; too short to be a climatology."
                    ),
                )
            )
        except Exception as error:  # noqa: BLE001
            report["rainfall"] = dataclasses.asdict(
                SourceCoverage(available=False, detail=str(error))
            )

        try:
            market = _market()
            priced = int(market["price_rs_quintal"].notna().sum())
            report["market"] = dataclasses.asdict(
                SourceCoverage(
                    available=True,
                    rows=len(market),
                    detail=(
                        f"{market['commodity'].nunique()} commodities over "
                        f"{market['date'].nunique()} days; {priced} of {len(market)} "
                        "slots carry a numeric price. Value figures use the annual "
                        "minimum support price, not this three-day snapshot."
                    ),
                )
            )
        except Exception as error:  # noqa: BLE001
            report["market"] = dataclasses.asdict(
                SourceCoverage(available=False, detail=str(error))
            )

        return report

    # -- productivity ----------------------------------------------------
    def productivity(
        self,
        *,
        state: str | None = None,
        district: str | None = None,
        min_observations: int = 5,
    ) -> dict[str, Any]:
        """Rank crops by what they return per unit of water."""
        totals = _season_totals()
        yields = _district_yield()

        market: pd.DataFrame | None
        try:
            market = _market()
        except Exception as error:  # noqa: BLE001
            # Prices are optional. Without them the physical ranking still
            # stands; the economic columns report themselves absent.
            log.warning("market prices unavailable: %s", error)
            market = None

        results = wp.compute_water_productivity(
            totals,
            yields,
            market=market,
            state=state,
            district=district,
            min_observations=min_observations,
        )

        # A district with too little history yields nothing. Falling back to
        # the state silently would answer a question the farmer did not ask.
        fell_back = False
        if not results and district:
            log.info("no district-level results for %s; offering state level", district)
            results = wp.compute_water_productivity(
                totals, yields, market=market, state=state,
                min_observations=min_observations,
            )
            fell_back = bool(results)

        return {
            "crops": [r.as_dict() for r in results],
            "region": results[0].region if results else None,
            "requested_district": district,
            "fell_back_to_state": fell_back,
            "economic_basis": (
                "Minimum support price for 2026-27, an annual published figure."
                if market is not None
                else None
            ),
            "interpretation": (
                "Two productivities are reported and they answer different "
                "questions. Kilograms per cubic metre of crop evapotranspiration "
                "is what the plant achieves per unit of water it transpires. "
                "Kilograms per cubic metre of gross irrigation is what you "
                "achieve per unit pumped, and is always lower because no "
                "irrigation system delivers everything it lifts."
            ),
            "limitations": [
                "The water term is a FAO-56 reference computed on a weather "
                "series whose location this project could not verify. It is a "
                "consistent yardstick applied equally to every crop, not a "
                "district-specific measurement.",
                "The yield term is a district median for 2010-2017 and reflects "
                "the management and varieties of that period, not this season.",
                "The two terms are not observations of the same fields, so the "
                "ranking is far more defensible than the absolute values.",
            ],
        }

    # -- allocation ------------------------------------------------------
    def budget(
        self,
        *,
        available_water_m3: float,
        plot_area_ha: float,
        state: str | None = None,
        district: str | None = None,
    ) -> dict[str, Any]:
        """Assess crops against a finite seasonal water budget."""
        productivity = self.productivity(state=state, district=district)
        records = [
            wp.WaterProductivity(**crop) for crop in productivity["crops"]
        ]
        if not records:
            return {
                "options": [],
                "available_water_m3": available_water_m3,
                "plot_area_ha": plot_area_ha,
                "note": "No crop has enough yield history in this region to rank.",
            }

        options = wp.allocate_water_budget(
            records,
            available_water_m3=available_water_m3,
            plot_area_ha=plot_area_ha,
        )
        feasible = [o for o in options if o.feasible]

        return {
            "options": [dataclasses.asdict(o) for o in options],
            "available_water_m3": available_water_m3,
            "available_water_litres": available_water_m3 * 1000.0,
            "plot_area_ha": plot_area_ha,
            "feasible_count": len(feasible),
            "region": productivity["region"],
            "note": (
                "Ranked by what the budget actually delivers, not by efficiency "
                "alone: a thrifty crop you can only water on a tenth of the plot "
                "may return less than a thirstier one that fits. Water needed "
                "is gross irrigation, so it already includes what your system "
                "loses on the way to the root zone."
            ),
            "limitations": productivity["limitations"],
        }

    # -- rainfall --------------------------------------------------------
    def rainfall(self, *, state: str, district: str) -> dict[str, Any] | None:
        """Recent rainfall for one district, against its normal."""
        frame = _district_rainfall()
        context = wp.rainfall_context(frame, state=state, district=district)
        if context is None:
            return None

        payload = dataclasses.asdict(context)
        payload["unresolved_reason"] = districts.unresolved_reason(district)
        return payload

    def districts_with_rainfall(self, *, state: str | None = None) -> list[str]:
        """Which districts the rainfall file actually covers."""
        frame = _district_rainfall()
        if state:
            frame = frame[frame["state"].str.casefold() == state.casefold()]
        return sorted(frame["district_key"].unique())


#: One shared instance. FastAPI dependencies resolve to this.
water_intelligence = WaterIntelligenceService()
