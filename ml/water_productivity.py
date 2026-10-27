"""Water productivity: what a crop returns per unit of water it consumes.

This module is the point at which the two halves of the project meet.

The water engine (``ml.baseline``) answers *how much water does this crop
need*. It knows nothing about what the crop produces. The district yield
record knows what crops produced, over eight years and 311 districts, but
nothing about the water that went into them. Neither file alone can answer the
question a farmer in a water-scarce district actually faces:

    given the water I can actually get, which crop returns the most per drop?

Water productivity is the standard way that question is posed in the
literature - "more crop per drop" - and it is simply yield divided by water
consumed. Two variants are computed here, because they answer different
questions and are routinely confused:

``wp_etc_kg_per_m3``
    Yield over crop evapotranspiration. What the plant achieves per unit of
    water it actually transpires. A biological efficiency, independent of how
    the water was delivered.

``wp_applied_kg_per_m3``
    Yield over *gross irrigation*, which includes what the irrigation system
    loses on the way. What the farmer achieves per unit of water pumped. Always
    the smaller of the two, and the one that matters when the constraint is a
    borewell rather than the plant.

Economic productivity uses the minimum support price rather than the market
snapshot. That is a deliberate choice: MSP is an annual published figure for
the whole season, while the market file in this project covers three days. A
rupees-per-cubic-metre figure built on a three-day spot price would be a
number about one week, dressed up as a number about a season.

WHAT THIS IS NOT
----------------
These are **comparative planning indicators, not measured field efficiencies**,
and three limits are load-bearing:

1. The water term comes from a FAO-56 reference computed on a weather series
   whose location this project could not verify (see ``docs/site_resolution.md``).
   It is therefore a consistent yardstick applied to every crop equally, not a
   district-specific water measurement.
2. The yield term is a district median over 2010-2017. It reflects the
   management, rainfall and varieties of that period, not this season.
3. The two terms come from different places and are not observations of the
   same fields.

The consequence is that the *ranking* these numbers produce is far more
defensible than their absolute values, and every caller is expected to present
them that way.
"""

from __future__ import annotations

import dataclasses
from typing import Final

import pandas as pd

from ml import config, data_loader, districts
from ml.logging_utils import get_logger

log = get_logger("water_productivity")

# --------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------
#: One millimetre of depth spread over one hectare is ten cubic metres.
#: 1 mm = 0.001 m, 1 ha = 10 000 m^2, so 0.001 x 10 000 = 10 m^3.
M3_PER_MM_PER_HA: Final[float] = 10.0

#: One quintal is 100 kg. Indian prices are quoted per quintal throughout.
KG_PER_QUINTAL: Final[float] = 100.0


def mm_to_m3_per_ha(depth_mm: float) -> float:
    """Convert a water depth in millimetres to a volume per hectare."""
    return depth_mm * M3_PER_MM_PER_HA


def m3_per_ha_to_mm(volume_m3: float) -> float:
    """Inverse of :func:`mm_to_m3_per_ha`."""
    return volume_m3 / M3_PER_MM_PER_HA


# --------------------------------------------------------------------------
# Name bridges between the two source projects
# --------------------------------------------------------------------------
#: The water engine's crop slugs mapped to the yield record's crop labels.
#:
#: Only names that denote the same plant are bridged. ``cumin`` is deliberately
#: absent: the yield file has no cumin column, and mapping it to a neighbouring
#: spice to fill the gap would be fabrication.
YIELD_CROP_NAMES: Final[dict[str, str]] = {
    "paddy": "rice",
    "finger_millet": "finger millet",
    "maize": "maize",
    "wheat": "wheat",
    "chickpea": "chickpea",
    "groundnut": "groundnut",
    "cotton": "cotton",
}

#: The water engine's crop slugs mapped to commodity names in the price file.
#:
#: ``chickpea`` maps to Bengal gram, which is the same pulse under its Indian
#: market name. ``cumin`` is again absent rather than approximated.
COMMODITY_NAMES: Final[dict[str, str]] = {
    "paddy": "Paddy(Common)",
    "finger_millet": "Ragi(Finger Millet)",
    "maize": "Maize",
    "wheat": "Wheat",
    "chickpea": "Bengal Gram(Gram)(Whole)",
    "groundnut": "Groundnut",
    "cotton": "Cotton",
}

#: Yield columns that total other columns in the same file. Summing these
#: alongside their parts would double-count the same production.
AGGREGATE_CROPS: Final[frozenset[str]] = frozenset({"sorghum", "oilseeds"})


# --------------------------------------------------------------------------
# Source reshaping
# --------------------------------------------------------------------------
def build_district_yield(raw: pd.DataFrame) -> pd.DataFrame:
    """Reshape the wide district-year yield file into one row per crop.

    The source carries an AREA / PRODUCTION / YIELD triplet per crop across 80
    columns. Reshaping is a change of layout only - no row is created, dropped
    or interpolated, and the returned frame has exactly ``rows x crops`` rows.

    Two flags are carried rather than acted on here, so the caller decides:

    ``is_aggregate``
        The crop column totals others in the same file (see
        :data:`AGGREGATE_CROPS`).
    ``not_recorded``
        Yield or area is zero or missing. In this source that means the
        district did not report the crop, which is not the same as the crop
        having failed, and averaging the zero in would drag the median down
        with an absence.
    """
    # Work in the slug space ml.data_loader normalises every source into, so
    # this accepts a frame from load_dataset() as readily as a bare read_csv.
    frame = data_loader.normalise_columns(raw)

    yield_columns = [c for c in frame.columns if c.endswith("_yield_kg_per_ha")]
    if not yield_columns:
        raise ValueError(
            "No YIELD columns found; the district yield file's schema has changed."
        )

    identity = ["dist_code", "year", "state_name", "dist_name"]
    missing = [c for c in identity if c not in frame.columns]
    if missing:
        raise ValueError(f"District yield file is missing {missing}.")

    pieces: list[pd.DataFrame] = []
    for column in yield_columns:
        crop = column.removesuffix("_yield_kg_per_ha")
        area_column = f"{crop}_area_1000_ha"
        production_column = f"{crop}_production_1000_tons"
        if area_column not in frame.columns:
            log.warning("skipping %s: no matching AREA column", crop)
            continue

        piece = frame[identity].copy()
        piece.columns = ["district_code", "year", "state", "district"]
        # Canonical district name, so this frame can be joined to rainfall.
        # See ml/districts.py: the sources do not agree on these names.
        piece["district_key"] = piece["district"].map(districts.normalise)
        # "kharif_sorghum" -> "kharif sorghum", matching the crop labels used
        # everywhere else in the project.
        crop_label = crop.replace("_", " ")
        piece["crop"] = crop_label
        piece["yield_kg_ha"] = pd.to_numeric(frame[column], errors="coerce")
        piece["area_1000_ha"] = pd.to_numeric(frame[area_column], errors="coerce")
        piece["production_1000_t"] = (
            pd.to_numeric(frame[production_column], errors="coerce")
            if production_column in frame.columns
            else pd.NA
        )
        piece["is_aggregate"] = crop_label in AGGREGATE_CROPS
        piece["not_recorded"] = (
            piece["yield_kg_ha"].isna()
            | (piece["yield_kg_ha"] <= 0)
            | piece["area_1000_ha"].isna()
            | (piece["area_1000_ha"] <= 0)
        )
        pieces.append(piece)

    long = pd.concat(pieces, ignore_index=True)
    log.info(
        "district yield reshaped: %d rows, %d crops, %d districts, %d-%d",
        len(long), long["crop"].nunique(), long["district"].nunique(),
        int(long["year"].min()), int(long["year"].max()),
    )
    return long


def build_district_rainfall(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalise the IMD daily rainfall file.

    The source column names carry embedded newlines and one misspelling
    ('Departue'). They are normalised on read rather than corrected in the
    file, so ``datasets/raw`` stays byte-identical to what was supplied.
    """
    frame = data_loader.normalise_columns(raw)

    wanted = {
        "state": "state",
        "district": "district",
        "date": "date",
        "daily_actual": "actual_mm",
        "daily_normal": "normal_mm",
    }
    missing = [c for c in wanted if c not in frame.columns]
    if missing:
        raise ValueError(f"IMD rainfall file is missing {missing}.")

    out = frame[list(wanted)].rename(columns=wanted)
    out["state"] = out["state"].astype(str).str.strip().str.upper()
    out["district"] = out["district"].astype(str).str.strip().str.upper()
    out["district_key"] = out["district"].map(districts.normalise)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["actual_mm"] = pd.to_numeric(out["actual_mm"], errors="coerce")
    out["normal_mm"] = pd.to_numeric(out["normal_mm"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values(["state", "district", "date"])

    log.info(
        "district rainfall: %d rows, %d states, %d districts, %s to %s",
        len(out), out["state"].nunique(), out["district"].nunique(),
        out["date"].min().date(), out["date"].max().date(),
    )
    return out.reset_index(drop=True)


def load_market_sheet() -> pd.DataFrame:
    """Read the price workbook with its real header row.

    The sheet opens with a title row ("Marketwise Price & Arrival Report
    (06-09-2026)") and a merged band naming the Price and Arrival groups, so
    the actual column headings are on the third row. ``data_loader`` reads a
    source with default options and cannot express that, so this file is read
    here instead of through the registry - the registry still declares it, and
    the path still comes from the spec, so the file is not read from a
    hard-coded location.

    The header row is located rather than assumed: if the workbook is
    re-exported with an extra banner row, this finds the headings anyway
    instead of silently returning a frame of 'unnamed_*' columns.
    """
    spec = data_loader.DATASETS["market_prices"]
    path = spec.raw_path()
    if not path.exists():
        raise FileNotFoundError(f"Market price workbook not found at {path}")

    for header_row in range(0, 6):
        frame = pd.read_excel(path, header=header_row)
        if any(str(c).startswith("Price on ") for c in frame.columns):
            log.info("market sheet header found on row %d", header_row)
            return frame

    raise ValueError(
        "No 'Price on ...' columns found in the first six rows of the market "
        "workbook; its layout has changed."
    )


def build_market_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Reshape the price sheet into one row per commodity and observation date.

    The observation dates live in the column headers ("Price on 06 Sep, 2026"),
    so they are parsed out of the header rather than assumed. A dash in the
    source means no trade was recorded that day; it stays null, because zero
    would be a price and this is an absence.
    """
    price_columns = [c for c in raw.columns if str(c).startswith("Price on ")]
    if not price_columns:
        raise ValueError("No 'Price on ...' columns; the price sheet has changed.")

    msp_column = next(
        (c for c in raw.columns if "MSP" in str(c).upper()), None
    )

    rows: list[dict[str, object]] = []
    for _, record in raw.iterrows():
        commodity = str(record.get("Commodity", "")).strip()
        if not commodity or commodity.lower() == "nan":
            continue
        for column in price_columns:
            label = str(column).replace("Price on ", "").strip()
            arrival_column = f"Arrival on {label}"
            rows.append(
                {
                    "commodity": commodity,
                    "group": str(record.get("Commodity Group", "")).strip(),
                    "date": pd.to_datetime(label, format="%d %b, %Y", errors="coerce"),
                    "price_rs_quintal": pd.to_numeric(record[column], errors="coerce"),
                    "arrival_tonnes": (
                        pd.to_numeric(record[arrival_column], errors="coerce")
                        if arrival_column in raw.columns
                        else pd.NA
                    ),
                    "msp_rs_quintal": (
                        pd.to_numeric(record[msp_column], errors="coerce")
                        if msp_column
                        else pd.NA
                    ),
                }
            )

    out = pd.DataFrame(rows)
    log.info(
        "market prices: %d commodity-date slots, %d with a numeric price, %d commodities",
        len(out), int(out["price_rs_quintal"].notna().sum()), out["commodity"].nunique(),
    )
    return out


# --------------------------------------------------------------------------
# The metric
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class WaterProductivity:
    """What one crop returns per unit of water, with the terms it was built from."""

    crop: str
    #: Median district yield, kg/ha.
    yield_kg_ha: float
    #: Interquartile range of that yield, which is the honest spread.
    yield_p25_kg_ha: float
    yield_p75_kg_ha: float
    #: Number of district-year observations behind the median.
    observations: int
    #: Seasonal crop evapotranspiration, mm.
    etc_mm: float
    #: Seasonal gross irrigation, mm - what must be delivered.
    gross_irrigation_mm: float
    #: Yield over water transpired. A biological efficiency.
    wp_etc_kg_per_m3: float
    #: Yield over water delivered. What the farmer gets per unit pumped.
    wp_applied_kg_per_m3: float
    #: Value of the median yield at minimum support price, rupees per hectare.
    revenue_msp_rs_ha: float | None
    #: Rupees returned per cubic metre transpired.
    ewp_etc_rs_per_m3: float | None
    #: Rupees returned per cubic metre delivered.
    ewp_applied_rs_per_m3: float | None
    msp_rs_quintal: float | None
    #: Region the yield median was taken over, e.g. "Karnataka" or "all states".
    region: str

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


def compute_water_productivity(
    season_totals: pd.DataFrame,
    district_yield: pd.DataFrame,
    *,
    market: pd.DataFrame | None = None,
    state: str | None = None,
    district: str | None = None,
    min_observations: int = 5,
) -> list[WaterProductivity]:
    """Rank crops by what they return per unit of water.

    Parameters
    ----------
    season_totals
        One row per crop from the water engine, carrying ``etc_total_mm`` and
        ``gross_irrigation_total_mm``. Produced by ``ml.baseline``.
    district_yield
        Long-format yield from :func:`build_district_yield`.
    market
        Optional prices from :func:`build_market_prices`. Without it the
        economic fields are ``None`` rather than guessed.
    state, district
        Narrow the yield median. A district median is more relevant and rests
        on fewer observations; the count is returned so the caller can say so.
    min_observations
        Crops with fewer district-year observations than this are dropped. A
        median over two rows is not a median.

    Returns
    -------
    Sorted by water productivity, most productive first.
    """
    usable = district_yield[
        (~district_yield["is_aggregate"]) & (~district_yield["not_recorded"])
    ]

    region = "all states"
    if state:
        usable = usable[usable["state"].str.strip().str.casefold() == state.casefold()]
        region = state.title()
    if district:
        key = districts.normalise(district)
        usable = usable[usable["district_key"] == key]
        region = f"{district.title()}, {region}"

    msp_by_crop: dict[str, float] = {}
    if market is not None and not market.empty:
        for crop_slug, commodity in COMMODITY_NAMES.items():
            match = market[market["commodity"] == commodity]
            if match.empty:
                continue
            msp = pd.to_numeric(match["msp_rs_quintal"], errors="coerce").dropna()
            if not msp.empty:
                msp_by_crop[crop_slug] = float(msp.iloc[0])

    results: list[WaterProductivity] = []
    for _, water in season_totals.iterrows():
        crop = str(water["crop"])
        yield_name = YIELD_CROP_NAMES.get(crop)
        if yield_name is None:
            # No yield record exists for this crop. Say nothing rather than
            # substitute a neighbour; see YIELD_CROP_NAMES.
            log.info("%s: no yield counterpart, omitted from productivity", crop)
            continue

        subset = usable[usable["crop"] == yield_name]
        if len(subset) < min_observations:
            log.info(
                "%s: %d observations in %s, below the minimum of %d",
                crop, len(subset), region, min_observations,
            )
            continue

        etc_mm = float(water["etc_total_mm"])
        gross_mm = float(water["gross_irrigation_total_mm"])
        if etc_mm <= 0 or gross_mm <= 0:
            log.warning("%s: non-positive seasonal water, skipped", crop)
            continue

        median_yield = float(subset["yield_kg_ha"].median())
        etc_m3 = mm_to_m3_per_ha(etc_mm)
        gross_m3 = mm_to_m3_per_ha(gross_mm)

        msp = msp_by_crop.get(crop)
        revenue = (median_yield / KG_PER_QUINTAL) * msp if msp else None

        results.append(
            WaterProductivity(
                crop=crop,
                yield_kg_ha=round(median_yield, 1),
                yield_p25_kg_ha=round(float(subset["yield_kg_ha"].quantile(0.25)), 1),
                yield_p75_kg_ha=round(float(subset["yield_kg_ha"].quantile(0.75)), 1),
                observations=len(subset),
                etc_mm=round(etc_mm, 1),
                gross_irrigation_mm=round(gross_mm, 1),
                wp_etc_kg_per_m3=round(median_yield / etc_m3, 4),
                wp_applied_kg_per_m3=round(median_yield / gross_m3, 4),
                revenue_msp_rs_ha=round(revenue, 0) if revenue else None,
                ewp_etc_rs_per_m3=round(revenue / etc_m3, 2) if revenue else None,
                ewp_applied_rs_per_m3=round(revenue / gross_m3, 2) if revenue else None,
                msp_rs_quintal=msp,
                region=region,
            )
        )

    results.sort(key=lambda r: r.wp_etc_kg_per_m3, reverse=True)
    return results


# --------------------------------------------------------------------------
# Allocation
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class WaterBudgetOption:
    """One crop assessed against a finite volume of water."""

    crop: str
    #: Water needed to grow the crop over the whole plot, cubic metres.
    water_needed_m3: float
    #: Whether the budget covers that.
    feasible: bool
    #: Hectares the budget can actually irrigate, which may be under the plot.
    irrigable_area_ha: float
    #: Fraction of the plot the budget covers, 0 to 1.
    coverage: float
    #: Expected production over the irrigable area, kg.
    expected_yield_kg: float
    #: Expected value of that production at MSP, rupees.
    expected_value_rs: float | None
    wp_applied_kg_per_m3: float
    ewp_applied_rs_per_m3: float | None


def allocate_water_budget(
    productivity: list[WaterProductivity],
    *,
    available_water_m3: float,
    plot_area_ha: float,
) -> list[WaterBudgetOption]:
    """Assess each crop against a finite seasonal water budget.

    This is the question the ranking exists to answer. A farmer with a borewell
    that will yield a known volume this season does not need to know which crop
    is most efficient in the abstract - they need to know which crops that
    volume will actually finish, and what each returns.

    Gross irrigation is used rather than ETc, because the budget is water the
    farmer must *deliver*, and the system's losses are real.

    A crop the budget cannot finish over the whole plot is not dropped: the
    irrigable area is reported instead, since growing a smaller area properly
    is a real option and abandoning it is the decision this is meant to inform.
    """
    if available_water_m3 <= 0:
        raise ValueError("available_water_m3 must be positive.")
    if plot_area_ha <= 0:
        raise ValueError("plot_area_ha must be positive.")

    options: list[WaterBudgetOption] = []
    for record in productivity:
        per_hectare_m3 = mm_to_m3_per_ha(record.gross_irrigation_mm)
        needed_m3 = per_hectare_m3 * plot_area_ha
        irrigable_ha = min(plot_area_ha, available_water_m3 / per_hectare_m3)
        expected_kg = record.yield_kg_ha * irrigable_ha
        value = (
            (expected_kg / KG_PER_QUINTAL) * record.msp_rs_quintal
            if record.msp_rs_quintal
            else None
        )

        options.append(
            WaterBudgetOption(
                crop=record.crop,
                water_needed_m3=round(needed_m3, 0),
                feasible=needed_m3 <= available_water_m3,
                irrigable_area_ha=round(irrigable_ha, 3),
                coverage=round(irrigable_ha / plot_area_ha, 4),
                expected_yield_kg=round(expected_kg, 0),
                expected_value_rs=round(value, 0) if value else None,
                wp_applied_kg_per_m3=record.wp_applied_kg_per_m3,
                ewp_applied_rs_per_m3=record.ewp_applied_rs_per_m3,
            )
        )

    # Ranked by what the budget actually delivers, not by efficiency alone: a
    # highly efficient crop the farmer can only water on a tenth of the plot
    # may return less than a thirstier one that fits.
    options.sort(
        key=lambda o: (o.expected_value_rs or 0, o.expected_yield_kg), reverse=True
    )
    return options


# --------------------------------------------------------------------------
# Rainfall context
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class RainfallContext:
    """What rain has actually done in one district over the covered window."""

    state: str
    district: str
    start_date: str
    end_date: str
    days: int
    total_actual_mm: float
    total_normal_mm: float
    #: Percentage departure from the long-period normal. Negative is a deficit.
    departure_pct: float | None
    #: Longest run of days with no measurable rain inside the window.
    longest_dry_spell_days: int
    #: Days since the last measurable rain at the end of the window.
    days_since_rain: int
    #: IMD-style label for the departure.
    category: str
    coverage_note: str


#: IMD's own departure bands, used so the label matches the source's vocabulary.
_DEPARTURE_BANDS: Final[tuple[tuple[float, str], ...]] = (
    (60.0, "large excess"),
    (20.0, "excess"),
    (-19.0, "normal"),
    (-59.0, "deficient"),
    (-99.0, "large deficient"),
)


def _departure_category(departure_pct: float | None) -> str:
    if departure_pct is None:
        return "unknown"
    for threshold, label in _DEPARTURE_BANDS:
        if departure_pct >= threshold:
            return label
    return "no rain"


def rainfall_context(
    rainfall: pd.DataFrame,
    *,
    state: str,
    district: str,
    dry_threshold_mm: float = 2.5,
) -> RainfallContext | None:
    """Summarise recent rainfall for one district.

    ``dry_threshold_mm`` defaults to 2.5 mm, the IMD convention for a 'rainy
    day'. A day below it is treated as dry for spell counting, because a
    trace of rain does not interrupt a dry spell agronomically.

    Returns ``None`` when the district is absent, rather than an empty summary
    that would read as 'no rain fell'.
    """
    key = districts.normalise(district)
    subset = rainfall[
        (rainfall["state"].str.casefold() == state.casefold())
        & (rainfall["district_key"] == key)
    ].sort_values("date")

    if subset.empty:
        return None

    actual = subset["actual_mm"].fillna(0.0)
    total_actual = float(actual.sum())
    total_normal = float(subset["normal_mm"].fillna(0.0).sum())
    departure = (
        round((total_actual - total_normal) / total_normal * 100.0, 1)
        if total_normal > 0
        else None
    )

    longest = current = 0
    for value in actual:
        if value < dry_threshold_mm:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    trailing_dry = current

    days = len(subset)
    return RainfallContext(
        state=state.upper(),
        district=key,
        start_date=str(subset["date"].min().date()),
        end_date=str(subset["date"].max().date()),
        days=days,
        total_actual_mm=round(total_actual, 1),
        total_normal_mm=round(total_normal, 1),
        departure_pct=departure,
        longest_dry_spell_days=longest,
        days_since_rain=trailing_dry,
        category=_departure_category(departure),
        coverage_note=(
            f"Based on {days} days of IMD district records "
            f"({subset['date'].min().date()} to {subset['date'].max().date()}). "
            "This is current-season context, not a climatology, and it is too "
            "short to establish a trend."
        ),
    )


__all__ = [
    "M3_PER_MM_PER_HA",
    "KG_PER_QUINTAL",
    "YIELD_CROP_NAMES",
    "COMMODITY_NAMES",
    "WaterProductivity",
    "WaterBudgetOption",
    "RainfallContext",
    "mm_to_m3_per_ha",
    "m3_per_ha_to_mm",
    "build_district_yield",
    "build_district_rainfall",
    "build_market_prices",
    "load_market_sheet",
    "compute_water_productivity",
    "allocate_water_budget",
    "rainfall_context",
]
