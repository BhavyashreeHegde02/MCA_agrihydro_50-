# Prediction model compatibility record

## Root cause

The active `reduced_input/v1` pipeline was serialized with scikit-learn 1.7.1.
The backend runtime had scikit-learn 1.9.1. Loading the joblib file emitted
scikit-learn's `InconsistentVersionWarning`; the failure occurred later during
inference when `SimpleImputer` tried to access `_fill_dtype`, which is not
present on the deserialized estimator.

The v1 metadata did not record its Python, XGBoost, or joblib versions. The
serialized XGBoost estimator also warned that it came from an older release,
but the exact version is not recorded and is not inferred here.

## Compatibility retraining

The original v1 artifact is retained for audit. `reduced_input/v2` was retrained
and promoted from the same `datasets/processed/cwr_baseline_panel.parquet`
panel. Its feature-data fingerprint is unchanged:
`e45116067efed3c5`.

| Item | v1 artifact | v2 active artifact |
|---|---|---|
| Python | Not recorded | 3.14.6 |
| scikit-learn | 1.7.1 (embedded in serialized estimator) | 1.9.1 |
| XGBoost | Not recorded; old-version warning only | 3.4.1 |
| joblib | Not recorded | 1.6.0 |
| Task and target | `reduced_input`; reference-derived `etc_mm_day = ET0 x Kc` | Unchanged |
| Feature set/order | 16 features in v1 metadata | Unchanged |
| Data split | Chronological train/calibration/test | Same unchanged split implementation and panel |

Retraining was selected because the recorded scikit-learn version cannot be
installed into the existing Python 3.14 runtime, while the project did not
record a complete environment for the v1 artifact. No serialized private
attributes were modified. Model definitions, target, feature semantics,
leakage controls, growth-stage logic, FAO-56 baseline, chronological split, and
conformal interval method were not changed.

The backend pins `scikit-learn==1.9.1`, `xgboost==3.4.1`, and `joblib==1.6.0`.
Newly trained artifacts record their Python and ML-library versions in
`training_environment` metadata.

## Validation

On the unchanged chronological held-out test set, the reselected model remained
XGBoost:

| Metric | v1 | v2 |
|---|---:|---:|
| MAE (mm/day) | 0.3687 | 0.3623 |
| RMSE (mm/day) | 0.5105 | 0.5001 |
| R² | 0.9527 | 0.9546 |
| Nominal 90% interval coverage | 90% | 90% |
| Empirical interval coverage | 90.14% | 90.88% |
| Mean interval width (mm/day) | 1.6986 | 1.7487 |

These scores evaluate the reference-derived target, not field-observed water
use. The serving regression test loads the promoted artifact and performs both
direct model inference and a complete authenticated prediction API request.
