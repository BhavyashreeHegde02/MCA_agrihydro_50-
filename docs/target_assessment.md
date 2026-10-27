# Target Assessment

## Decision

Use `etc_mm_day` as the target for the current reference-estimation task. It is **reference-derived crop evapotranspiration**, not measured field CWR or observed irrigation use.

The definition is:

`ETc = ET0 x Kc`

- `ET0`: FAO-56 Penman-Monteith reference evapotranspiration, computed from the daily weather series.
- `Kc`: the project's growth-stage curve assembled from the agronomic references and assumptions in `config/crop_stages.yaml`.
- `etc_mm_day`: the resulting reference-derived ETc in mm/day.

The saved `reduced_input/v1` artifact explicitly records provenance class `reference_derived` and `is_field_observed: false`. The model can therefore be evaluated as an estimator of the FAO-56/Kc reference, but its scores must not be presented as accuracy against measured field water use.

## Rejected Candidate

`crop_water_data.csv -> water_requirement_liters` is not used as a supervised label. The project audit rejects it based on four independent checks: physical-scale inconsistency with its stated ET and field-area variables, lack of expected relationships to physical drivers, implausible numeric distributions, and strong recovery of a clipped multiplicative generating formula. It remains in the repository as a negative control. See `docs/dataset_analysis.md` section 5 and `ml/target_audit.py`.

No labels are fabricated or inferred from that rejected column.

## Modeling Task

The current primary task is `reduced_input`: estimate `etc_mm_day` from inputs a smallholder can plausibly supply, without measured solar radiation or wind. Its 16 predictors are defined in `ml/target_builder.py` and recorded in the model artifact. ET0, Kc, ETc, effective rainfall, irrigation amounts and other ET0-derived quantities are excluded from this estimator to prevent target leakage.

Evaluation is chronological: training through 2022-02-25, calibration through 2023-06-27, and held-out testing through 2024-12-29. The test metrics describe agreement with the reference-derived target on this held-out period only. Split-conformal uncertainty is calibrated on the distinct calibration segment.

## Limitations

- There is no independent field-observed crop water requirement in the current data.
- The weather record is a single point with unresolved geographic provenance; spatial generalization is not established.
- Growth-stage windows and Kc values include documented agronomic choices.
- The model does not establish causal effects or actual farm water consumption.

## Recommendation

Keep `etc_mm_day` for the explicitly scoped reference-estimation experiment. Any later claim about field CWR requires independently collected, unit-checked field measurements and a separate validation design. Never relabel this target as measured CWR.
