"""Turning a number into advice a farmer can act on.

Three rules govern everything here.

**Say the uncertainty out loud.** Where a calibrated interval exists, the advice
quotes a range rather than a single decimal. "About 5 mm, likely between 4 and 6"
is honest; "5.27 mm" implies a precision the model does not have.

**Never present an estimate as a measurement.** Root-zone status has no sensor
behind it. Every message that mentions it says so.

**Advise on gross, report both.** The farmer has to deliver the gross depth,
because their system loses some of it. The demand and the net requirement are
still reported, because a farmer who is told only one number cannot tell whether
a dry spell or a leaky channel is the problem.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Literal

Priority = Literal["low", "medium", "high"]

#: Water-need bands, in mm/day of crop demand. Thresholds are a presentation
#: choice for the status chip in the app, not a physical boundary, and they are
#: stated in the response so the app and the write-up cannot disagree.
DEMAND_BANDS: tuple[tuple[float, str, str], ...] = (
    (2.0, "low", "The crop is using little water at the moment."),
    (5.0, "moderate", "The crop is using a moderate amount of water."),
    (8.0, "high", "The crop is using a lot of water."),
    (float("inf"), "very high", "The crop is under heavy water demand."),
)


@dataclasses.dataclass
class AdvisoryMessage:
    """One piece of advice."""

    advisory_type: str
    headline: str
    detail: str
    priority: Priority
    action_required: bool

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def demand_band(etc_mm_day: float) -> tuple[str, str]:
    """Map crop demand onto a farmer-facing band and sentence."""
    for threshold, label, sentence in DEMAND_BANDS:
        if etc_mm_day < threshold:
            return label, sentence
    return DEMAND_BANDS[-1][1], DEMAND_BANDS[-1][2]


def _about(value: float) -> str:
    """Round to a precision the estimate can actually support."""
    if value < 1:
        return f"{value:.1f}"
    return f"{value:.0f}" if value >= 10 else f"{value:.1f}"


def _range_phrase(lower: float | None, upper: float | None, coverage: float | None) -> str:
    if lower is None or upper is None:
        return ""
    confidence = f" ({int(round(coverage * 100))}% of the time)" if coverage else ""
    return f", likely between {_about(lower)} and {_about(upper)} mm{confidence}"


def build_advisories(
    *,
    crop_name: str,
    growth_stage: str,
    days_after_sowing: int,
    etc_mm_day: float,
    etc_lower: float | None,
    etc_upper: float | None,
    coverage: float | None,
    rainfall_mm: float,
    effective_rainfall_mm: float,
    net_irrigation_mm: float,
    gross_irrigation_mm: float,
    gross_irrigation_litres: float | None,
    application_efficiency: float,
    area_ha: float | None,
    forecast_rainfall_mm: float | None = None,
    previous_etc_mm_day: float | None = None,
    estimated_inputs: list[str] | None = None,
    prediction_source: str = "ml_model",
) -> list[AdvisoryMessage]:
    """Assemble the advice for one prediction."""
    messages: list[AdvisoryMessage] = []
    band, band_sentence = demand_band(etc_mm_day)

    # -- what the crop needs ---------------------------------------------
    messages.append(
        AdvisoryMessage(
            advisory_type="water_demand",
            headline=(
                f"{crop_name} needs about {_about(etc_mm_day)} mm of water today"
                f"{_range_phrase(etc_lower, etc_upper, coverage)}"
            ),
            detail=(
                f"{band_sentence} It is at the {growth_stage.replace('_', ' ')} stage, "
                f"{days_after_sowing} days after sowing. This is the water the crop "
                f"will lose through its leaves and the soil surface, not the amount "
                f"you need to apply."
            ),
            priority="low",
            action_required=False,
        )
    )

    # -- what the rain contributed ---------------------------------------
    if rainfall_mm > 0:
        share = 100.0 * effective_rainfall_mm / rainfall_mm if rainfall_mm else 0.0
        messages.append(
            AdvisoryMessage(
                advisory_type="rainfall",
                headline=(
                    f"{_about(rainfall_mm)} mm of rain fell, of which about "
                    f"{_about(effective_rainfall_mm)} mm reaches the roots"
                ),
                detail=(
                    f"Roughly {share:.0f}% of the rain is usable by the crop. The rest "
                    f"is caught on the leaves and evaporates, runs off, or drains below "
                    f"the roots."
                ),
                priority="low",
                action_required=False,
            )
        )

    # -- the actual instruction ------------------------------------------
    if gross_irrigation_mm <= 0.05:
        messages.append(
            AdvisoryMessage(
                advisory_type="irrigation",
                headline="No irrigation needed today",
                detail=(
                    "Rainfall has covered the crop's water needs for today. Check again "
                    "tomorrow, especially if no more rain falls."
                ),
                priority="low",
                action_required=False,
            )
        )
    else:
        volume = ""
        if gross_irrigation_litres is not None and area_ha:
            volume = (
                f" That is roughly {gross_irrigation_litres:,.0f} litres "
                f"across {area_ha:g} hectare{'s' if area_ha != 1 else ''}."
            )
        loss = 100.0 * (1.0 - application_efficiency)
        messages.append(
            AdvisoryMessage(
                advisory_type="irrigation",
                headline=f"Apply about {_about(gross_irrigation_mm)} mm of water",
                detail=(
                    f"The crop needs {_about(net_irrigation_mm)} mm to reach its roots. "
                    f"Because your irrigation method loses about {loss:.0f}% of what you "
                    f"deliver, you need to apply {_about(gross_irrigation_mm)} mm for that "
                    f"much to arrive.{volume}"
                ),
                priority="high" if gross_irrigation_mm > 8 else "medium",
                action_required=True,
            )
        )

    # -- forecast ---------------------------------------------------------
    if forecast_rainfall_mm is not None and forecast_rainfall_mm > 2.0:
        could_cover = forecast_rainfall_mm >= net_irrigation_mm > 0
        messages.append(
            AdvisoryMessage(
                advisory_type="forecast",
                headline=(
                    f"About {_about(forecast_rainfall_mm)} mm of rain is forecast"
                    + (" — you may be able to wait" if could_cover else "")
                ),
                detail=(
                    "Forecast rain could cover today's requirement, so consider delaying "
                    "irrigation and checking again tomorrow."
                    if could_cover else
                    "Forecast rain will help but is unlikely to cover the full requirement "
                    "on its own."
                ),
                priority="medium",
                action_required=False,
            )
        )

    # -- trend ------------------------------------------------------------
    if previous_etc_mm_day is not None and previous_etc_mm_day > 0:
        change = (etc_mm_day - previous_etc_mm_day) / previous_etc_mm_day
        if abs(change) >= 0.15:
            rising = change > 0
            messages.append(
                AdvisoryMessage(
                    advisory_type="trend",
                    headline=(
                        f"Water demand is {'higher' if rising else 'lower'} than last time "
                        f"by about {abs(change) * 100:.0f}%"
                    ),
                    detail=(
                        "Demand rises as the crop grows and as the weather gets hotter, "
                        "drier or windier."
                        if rising else
                        "Demand falls as the weather cools or becomes more humid, and as "
                        "the crop approaches maturity."
                    ),
                    priority="low",
                    action_required=False,
                )
            )

    # -- honesty about the inputs ----------------------------------------
    if estimated_inputs:
        readable = {
            "solar_radiation_estimated_from_temperature_range_fao56_eq50":
                "sunlight was estimated from the day's temperature range",
            "wind_speed_substituted_with_fao56_default_2_m_per_s":
                "an average wind speed was assumed",
        }
        described = [readable.get(item, item) for item in estimated_inputs]
        messages.append(
            AdvisoryMessage(
                advisory_type="data_quality",
                headline="Some weather inputs were estimated, not measured",
                detail=(
                    "This advice used estimated values where measurements were not "
                    f"available: {'; '.join(described)}. Supplying measured values would "
                    "make the estimate more reliable."
                ),
                priority="low",
                action_required=False,
            )
        )

    if prediction_source == "physics_baseline":
        messages.append(
            AdvisoryMessage(
                advisory_type="method",
                headline="This figure comes from the scientific calculation, not the model",
                detail=(
                    "No trained model is currently active on the server, so the value "
                    "shown is the FAO-56 reference calculation. It is a valid estimate, "
                    "but it carries no prediction range."
                ),
                priority="low",
                action_required=False,
            )
        )

    return messages


def water_need_status(etc_mm_day: float) -> dict[str, Any]:
    """The status chip shown on the dashboard, with its thresholds disclosed."""
    band, sentence = demand_band(etc_mm_day)
    return {
        "band": band,
        "description": sentence,
        "value_mm_day": round(etc_mm_day, 2),
        "thresholds_mm_day": {
            "low": "< 2", "moderate": "2 to 5", "high": "5 to 8", "very high": ">= 8",
        },
        "note": "Bands are a presentation choice for the interface, not a physical boundary.",
    }
