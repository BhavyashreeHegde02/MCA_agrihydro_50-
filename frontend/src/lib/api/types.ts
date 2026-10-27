/**
 * Readable names for the generated backend types.
 *
 * `schema.d.ts` is generated from the FastAPI service's own OpenAPI document by
 * `npm run api:types`, so these aliases cannot drift from the backend: if a
 * field is renamed there, the build breaks here. Nothing in this file is
 * hand-written structure — it is only naming.
 */

import type { components } from "./schema";

type S = components["schemas"];

// -- authentication ---------------------------------------------------------
export type RegisterRequest = S["RegisterRequest"];
export type LoginRequest = S["LoginRequest"];
export type TokenPair = S["TokenPair"];
export type UserOut = S["UserOut"];

// -- farmer, farm, field ----------------------------------------------------
export type FarmerOut = S["FarmerOut"];
export type FarmerUpdate = S["FarmerUpdate"];
export type FarmOut = S["FarmOut"];
export type FarmDetail = S["FarmDetail"];
export type FarmCreate = S["FarmCreate"];
export type FarmUpdate = S["FarmUpdate"];
export type FieldOut = S["FieldOut"];
export type FieldCreate = S["FieldCreate"];
export type FieldUpdate = S["FieldUpdate"];

// -- crops and plantings ----------------------------------------------------
export type CropOut = S["CropOut"];
export type CropDetail = S["CropDetail"];
export type GrowthStageOut = S["GrowthStageOut"];
export type KcCurvePoint = S["KcCurvePoint"];
export type FieldCropCreate = S["FieldCropCreate"];
export type FieldCropDetail = S["FieldCropDetail"];

// -- soil and weather -------------------------------------------------------
export type SoilDataCreate = S["SoilDataCreate"];
export type SoilDataOut = S["SoilDataOut"];
export type WeatherOut = S["WeatherOut"];
export type WeatherInput = S["WeatherInputSchema"];

// -- prediction -------------------------------------------------------------
export type PredictionRequest = S["PredictionRequest"];
export type PredictionOut = S["PredictionOut"];
export type PredictionSummary = S["PredictionSummary"];
export type ExplanationOut = S["ExplanationOut"];
export type IntervalOut = S["IntervalOut"];
export type ModelInfoOut = S["ModelInfoOut"];

// -- irrigation -------------------------------------------------------------
export type IrrigationCalculationRequest = S["IrrigationCalculationRequest"];
export type IrrigationCalculationOut = S["IrrigationCalculationOut"];
export type IrrigationRecordCreate = S["IrrigationRecordCreate"];
export type IrrigationRecordOut = S["IrrigationRecordOut"];
export type WaterUseCreate = S["WaterUseCreate"];
export type WaterUseOut = S["WaterUseOut"];

// -- advisory and analytics -------------------------------------------------
export type AdvisoryOut = S["AdvisoryOut"];
export type AnalyticsOut = S["AnalyticsOut"];
export type CropRecommendationRequest = S["CropRecommendationRequest"];
export type CropRecommendationOut = S["CropRecommendationOut"];
export type CropRecommendationItem = S["CropRecommendationItem"];

// -- water intelligence -----------------------------------------------------
// The merged project's own layer: what a crop returns per unit of water, and
// what a finite water budget will actually grow.
export type WaterProductivityItem = S["WaterProductivityItem"];
export type WaterProductivityResponse = S["WaterProductivityResponse"];
export type WaterBudgetRequest = S["WaterBudgetRequest"];
export type WaterBudgetOption = S["WaterBudgetOptionOut"];
export type WaterBudgetResponse = S["WaterBudgetResponse"];

// -- meta -------------------------------------------------------------------
export type HealthResponse = S["HealthResponse"];
export type Message = S["Message"];

/**
 * How a prediction was produced.
 *
 * The backend serves the physics baseline when no model is promoted, and says
 * which one it used. The interface must show this rather than let a farmer
 * assume a model spoke when it did not.
 */
export type PredictionSource = PredictionOut["prediction_source"];

// ---------------------------------------------------------------------------
// Endpoints the backend declares as `dict[str, Any]`
// ---------------------------------------------------------------------------
//
// A handful of handlers return a plain dict, so FastAPI emits no schema for
// them and `schema.d.ts` has nothing to alias. These shapes are written by hand
// from the handler source, and are the only types in this app that a backend
// change would not break automatically. Each names the handler it mirrors so
// the pairing can be checked.

/** `analytics.latest_advisories` — GET /api/v1/advisory */
export interface AdvisoryListItem {
  id: number;
  prediction_id: number;
  prediction_date: string;
  crop: string;
  advisory_type: string;
  headline: string;
  detail: string;
  priority: string;
  action_required: boolean;
}

export interface AdvisoryListResponse {
  advisories: AdvisoryListItem[];
  count: number;
}

/** `analytics.cwr_analytics` — the `daily_series` entries of AnalyticsOut. */
export interface AnalyticsDailyPoint {
  date: string;
  cwr_mm_day: number;
  baseline_mm_day: number;
  lower: number | null;
  upper: number | null;
  gross_irrigation_mm: number;
  effective_rainfall_mm: number;
  growth_stage: string;
  kc: number;
}

/** `analytics.cwr_analytics` — the `by_growth_stage` entries of AnalyticsOut. */
export interface AnalyticsStageTotal {
  growth_stage: string;
  days: number;
  total_demand_mm: number;
  mean_demand_mm_day: number;
  total_gross_irrigation_mm: number;
}

/** `ml_service.explain` — the `contributors` entries of ExplanationOut. */
export interface ExplanationContributor {
  feature: string;
  relative_importance: number;
  value_today: string | number | boolean | null;
  meaning: string;
}

/** `predictions.prediction_explanation` — the `baseline_comparison` object. */
export interface BaselineComparison {
  baseline_cwr_mm_day: number;
  served_cwr_mm_day: number;
  difference_mm_day: number;
  note: string;
}

/** `analytics.weather_status` — GET /api/v1/weather/status. */
export interface WeatherStatusOut {
  provider: string;
  configured: boolean;
  note?: string;
  cache_ttl_seconds?: number;
  [key: string]: unknown;
}

/** `analytics.data_quality_summary` — GET /api/v1/data-quality/summary. */
export interface DataQualitySummary {
  [key: string]: unknown;
}

/** `predictions.prediction_detail` — GET /api/v1/predictions/{id}. */
export interface PredictionDetail {
  id: number;
  field_crop_id: number;
  prediction_date: string;
  crop_name: string | null;
  growth_stage: string;
  days_after_sowing: number;
  kc_value: number;
  et0_mm_day: number;
  cwr_mm_day: number;
  cwr_baseline_mm_day: number;
  cwr_lower_mm_day: number | null;
  cwr_upper_mm_day: number | null;
  interval_coverage: number | null;
  effective_rainfall_mm: number;
  net_irrigation_mm: number;
  gross_irrigation_mm: number;
  gross_irrigation_litres: number | null;
  application_efficiency: number;
  prediction_source: string;
  weather_snapshot: Record<string, unknown> | null;
  soil_snapshot: Record<string, unknown> | null;
  feature_snapshot: Record<string, unknown> | null;
  assumptions: Record<string, unknown> | null;
  advisories: {
    advisory_type: string;
    headline: string;
    detail: string;
    priority: string;
    action_required: boolean;
  }[];
  created_at: string;
}


/** `water_intelligence.coverage` — GET /api/v1/water-intelligence/coverage. */
export interface SourceCoverage {
  available: boolean;
  detail: string;
  rows: number;
}

export interface CoverageResponse {
  water: SourceCoverage;
  yield: SourceCoverage;
  rainfall: SourceCoverage;
  market: SourceCoverage;
}

/** `water_intelligence.district_rainfall` — the rainfall context payload. */
export interface RainfallContextOut {
  state: string;
  district: string;
  start_date: string;
  end_date: string;
  days: number;
  total_actual_mm: number;
  total_normal_mm: number;
  departure_pct: number | null;
  longest_dry_spell_days: number;
  days_since_rain: number;
  category: string;
  coverage_note: string;
  unresolved_reason: string | null;
}
