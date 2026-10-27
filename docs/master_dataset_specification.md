# Master Dataset Specification

## Purpose and Unit of Analysis

The modeling table is `datasets/processed/cwr_baseline_panel.parquet`: 158,118 crop-day rows, 35 columns, eight crops, covering 2018-01-01 through 2024-12-29. Each row represents one crop cohort on one observation date. It is derived from the project's daily weather series combined with crop, sowing-date, growth-stage and reference calculations; it is not a farm-level survey.

The foundational primary weather source is `datasets/raw/Climate_Data.csv` (2,557 daily rows, 2018-01-01 through 2024-12-31). Its NASA POWER parameter names establish units but not geographic coordinates. Processed weather and transformations are documented in `datasets/processed/feature_lineage.csv`, `preprocessing_metadata.json`, and `docs/dataset_analysis.md`.

## Sources and Roles

| Source | Role | Modeling use |
|---|---|---|
| `Climate_Data.csv` | Primary daily weather | Drives ET0 and supplies weather predictors |
| `Crop_Calender.csv` and `Karnataka_Crop_Growth_Stage_Reference.xlsx` | Agronomic references | Stage duration and Kc inputs; not observations of ETc |
| `Soil data.csv` | Supporting district soil context | Not joined to the daily panel; no field-level/date key |
| `Rainfall_2016_districtwise.csv` | Supporting annual district normals | Not joined to daily weather; not a daily series |
| `Crop_recommendation.csv` | Supporting crop recommendation samples | Excluded from CWR regression |
| `data_season.csv` | Supporting season/market context | Excluded from CWR regression; invalid temperature field dropped |
| `crop_water_data.csv` | Rejected candidate target | Negative control only; `water_requirement_liters` is not ground truth |
| `crop_dataset.csv` | Unusable for this task | Excluded: no crop, date, location or target units |

## Target

`etc_mm_day` (mm/day), defined as `ET0 x Kc`, where ET0 is calculated by FAO-56 Penman-Monteith and Kc comes from the growth-stage reference curves. Its lineage class is `reference_derived`; it is not field-observed. Read `docs/target_assessment.md` before quoting any model result.

## Primary Estimation Features

The current `reduced_input` task uses these 16 predictors, in the saved model's feature order:

| Feature | Meaning / unit | Type |
|---|---|---|
| `t2m` | Daily mean air temperature, °C | Numeric |
| `t2m_min` | Daily minimum air temperature, °C | Numeric |
| `t2m_max` | Daily maximum air temperature, °C | Numeric |
| `rh2m` | Relative humidity at 2 m, % | Numeric |
| `temp_range_c` | `t2m_max - t2m_min`, °C | Numeric |
| `rainfall_mm` | Observation-day precipitation, mm/day | Numeric |
| `rain_sum_7d_mm` | Trailing 7-day precipitation total, mm | Numeric |
| `rain_sum_30d_mm` | Trailing 30-day precipitation total, mm | Numeric |
| `days_since_rain` | Consecutive days without measurable rain, capped at 120 days | Numeric |
| `day_of_year` | Observation ordinal day, 1-366 | Numeric |
| `doy_sin` | Cyclical encoding of day-of-year | Numeric |
| `doy_cos` | Cyclical encoding of day-of-year | Numeric |
| `month` | Calendar month, 1-12 | Numeric |
| `days_after_sowing` | Crop age in days | Numeric |
| `crop` | Crop identity | Categorical |
| `growth_stage` | Calendar-based stage from crop age | Categorical |

This reduced-input task intentionally withholds solar radiation and wind speed, which are used by the full FAO-56 reference calculation but are not assumed available to a smallholder. The separate `surrogate` task uses full FAO inputs and is diagnostic only; its near-perfect scores must not be reported as predictive skill.

## Preprocessing and Leakage Controls

- Preserve `datasets/raw/`; cleaning writes to cleaned/processed destinations.
- Normalize provider sentinels and physical ranges, sort daily weather chronologically, and retain the radiation-imputation flag. The single missing radiation value was filled using the FAO-56 temperature-range estimator.
- Derive rainfall totals with trailing 7- and 30-day windows and derive date/crop-stage fields without future observations.
- Split by observation date before fitting preprocessing. Numeric missing values use a training-fitted median imputer. Categorical values use a training-fitted most-frequent imputer and one-hot encoding with unseen categories ignored. XGBoost does not use numeric scaling.
- `ml/target_builder.py` blocks target-derived columns for non-surrogate tasks. Excluded examples include `et0_mm_day`, `etc_mm_day`, `kc`, radiation/ET0 terms, `effective_rainfall_mm`, and net/gross irrigation quantities.
- District soil and rainfall-normal sources are not aligned to the daily point record and must not be joined by guesswork.

## Evaluation Partitions and Existing Result

The saved `reduced_input/v1` model uses a chronological three-way split:

| Partition | Rows | Through |
|---|---:|---|
| Train | 94,889 | 2022-02-25 |
| Calibration | 31,669 | 2023-06-27 |
| Test | 31,560 | 2024-12-29 |

The existing selected estimator is XGBoost, compared against a mean dummy, Ridge, random forest and gradient boosting on the same split. Its saved held-out metrics are MAE 0.3687 mm/day, RMSE 0.5105 mm/day and R² 0.9527. Split conformal calibration reports 0.9014 empirical coverage at nominal 0.90. These are agreement metrics against a reference-derived target, not field-measured accuracy.

The reproducible evaluation notebook is `notebooks/04_baseline_model.ipynb`. It loads the saved artifact, recreates the chronological partition and asserts that independently recomputed metrics agree with the artifact; it does not retrain the model.
