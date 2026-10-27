"""Schemas for the water-intelligence endpoints.

Every quantity here carries its unit in the field name, because the same
endpoint reports millimetres, cubic metres, kilograms, kilograms per cubic
metre and rupees per cubic metre at once, and an unlabelled number in that
company is an invitation to misread it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class WaterProductivityItem(BaseModel):
    """What one crop returns per unit of water, with the terms behind it."""

    crop: str
    yield_kg_ha: float = Field(description="Median district yield.")
    yield_p25_kg_ha: float
    yield_p75_kg_ha: float
    observations: int = Field(
        description="District-year observations behind the median."
    )
    etc_mm: float = Field(description="Seasonal crop evapotranspiration.")
    gross_irrigation_mm: float = Field(
        description="Seasonal water that must be delivered, losses included."
    )
    wp_etc_kg_per_m3: float = Field(
        description="Yield per cubic metre transpired. A biological efficiency."
    )
    wp_applied_kg_per_m3: float = Field(
        description="Yield per cubic metre delivered. What the farmer achieves."
    )
    revenue_msp_rs_ha: float | None = Field(
        default=None, description="Median yield valued at minimum support price."
    )
    ewp_etc_rs_per_m3: float | None = None
    ewp_applied_rs_per_m3: float | None = None
    msp_rs_quintal: float | None = None
    region: str


class WaterProductivityResponse(BaseModel):
    crops: list[WaterProductivityItem]
    region: str | None
    requested_district: str | None
    fell_back_to_state: bool = Field(
        description=(
            "True when the requested district had too little yield history and "
            "the state figure is being shown instead. The interface must say so."
        )
    )
    economic_basis: str | None
    interpretation: str
    limitations: list[str]


class WaterBudgetRequest(BaseModel):
    """A finite seasonal water budget and the plot it has to cover."""

    available_water_m3: float = Field(
        gt=0,
        le=10_000_000,
        description=(
            "Water available for the whole season, in cubic metres. "
            "One cubic metre is a thousand litres."
        ),
    )
    plot_area_ha: float = Field(gt=0, le=100_000, description="Area to grow on.")
    farm_id: int | None = Field(
        default=None,
        description="Take the location from one of your farms instead of typing it.",
    )
    state: str | None = None
    district: str | None = None


class WaterBudgetOptionOut(BaseModel):
    crop: str
    water_needed_m3: float = Field(
        description="Gross irrigation for the whole plot, losses included."
    )
    feasible: bool
    irrigable_area_ha: float = Field(
        description="Area the budget can finish, which may be under the plot."
    )
    coverage: float = Field(ge=0, le=1, description="Fraction of the plot covered.")
    expected_yield_kg: float
    expected_value_rs: float | None
    wp_applied_kg_per_m3: float
    ewp_applied_rs_per_m3: float | None


class WaterBudgetResponse(BaseModel):
    options: list[WaterBudgetOptionOut]
    available_water_m3: float
    available_water_litres: float | None = None
    plot_area_ha: float
    feasible_count: int = 0
    region: str | None = None
    note: str
    limitations: list[str] = Field(default_factory=list)
