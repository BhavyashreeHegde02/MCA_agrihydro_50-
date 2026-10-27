# Research problem statement

*Written at the end of Phase 1, after the data had been examined. Several
positions here are narrower than they would have been before that examination,
which is the point of doing it first.*

---

## 1. The decision a farmer actually has to make

Not "how much water does this crop need in total", but a narrower and harder
question asked repeatedly through a season:

> *Given this crop, at this point in its growth, in this weather, with this much
> rain having already fallen — should I irrigate, and roughly how much?*

Two quantities sit behind that question and are routinely conflated:

- **Crop water demand (ETc)** — the depth of water the crop is expected to lose
  through evapotranspiration under stated conditions, in mm/day.
- **Irrigation requirement** — what should actually be supplied, after rainfall,
  soil-water contribution and application efficiency have been accounted for.

They are related but they are not the same number, and a system that reports one
while calling it the other gives bad advice. Keeping them distinct is a design
constraint throughout this project, including in the API response and the
farmer-facing screens.

---

## 2. What this study can and cannot claim

Phase 1 established the boundary, and stating it up front is what keeps the rest
of the work honest.

**No independently observed crop water requirement exists in this project's
data.** The one file offering such a column, `crop_water_data.csv`, was tested
against four criteria and failed all four: the stated volumes imply irrigation
depths roughly a hundred times smaller than the lightest real application; its
evapotranspiration column is uncorrelated with radiation, temperature, humidity
and wind simultaneously; all nine of its numeric columns are indistinguishable
from uniform draws over round intervals; and a log-linear model recovers 90 % of
its variance as a clipped multiplicative formula over the other columns. The
evidence is in `docs/dataset_analysis.md` §5.

So this study **cannot** claim to predict observed field water use, and it does
not. Instead:

> The supervised target is a **FAO-56 reference-derived crop evapotranspiration**,
> computed from a real seven-year daily weather series and growth-stage crop
> coefficients drawn from the project's agronomic reference files.

Every statement about model performance in this project refers to that target.
The phrase "reference-derived" is not a hedge to be dropped later; it is part of
what the number means.

---

## 3. Why that is still worth doing

An obvious objection: if the target is computed by a formula, and the model is
given the formula's inputs, the model simply relearns the formula. R² approaches
one and the result is empty.

That objection is correct, and the study is designed around it rather than
against it. Three research tasks are separated, and only two of them are
presented as findings.

### Task A — surrogate recovery *(diagnostic, not a headline)*

Full weather inputs → ETc. The model is expected to reproduce FAO-56 almost
exactly. This is run as a **wiring check**: near-perfect recovery confirms the
feature pipeline, the target construction and the training loop are consistent.
It is reported as a formula-surrogate result and is explicitly **not** offered as
predictive accuracy. Any write-up that quotes this number as "model accuracy" is
misreporting it.

### Task B — estimation from what a farmer actually has *(primary contribution)*

> **How accurately can growth-stage-aware crop water demand be estimated when
> radiation and wind measurements are unavailable?**

FAO-56 needs solar radiation and wind speed. A smallholder has neither. What is
plausibly available is temperature, a humidity estimate, recent rainfall, the
crop, and how long ago it was sown.

This is a genuine estimation problem with irreducible error, because the
withheld variables carry real information. It is directly useful: it quantifies
what advice is worth under realistic instrumentation, against a physics reference
computed on the same days. And it is exactly the reduced-input comparison the
project brief asks for.

### Task C — short-horizon forecasting *(secondary contribution)*

> **How far ahead can crop water demand be usefully anticipated using only
> information available today?**

Irrigation is a decision made in advance. Predicting demand *h* days ahead from
information available at time *t* is a real forecasting problem — future weather
is genuinely unknown — evaluated chronologically, with uncertainty intervals
whose coverage is measured rather than assumed.

---

## 4. Research questions

1. How closely does a compact machine-learning model reproduce FAO-56
   Penman–Monteith when given its full inputs? *(Task A — expected: very
   closely; reported as a surrogate result.)*
2. How much accuracy is lost when radiation and wind are withheld, and does the
   loss vary by season and by growth stage? *(Task B.)*
3. Does supplying a growth-stage-aware crop coefficient, rather than a
   single per-crop constant, measurably improve estimates? *(Task B, ablation.)*
4. How far ahead can demand be forecast before the estimate stops beating a
   seasonal-climatology baseline? *(Task C.)*
5. Do prediction intervals achieve their nominal coverage on held-out
   chronological data? *(Tasks B and C.)*
6. How much does rainfall-aware accounting change the resulting irrigation
   advice, as distinct from the demand estimate? *(Decision layer.)*

Questions 2 to 6 have outcomes that are not knowable in advance. Question 1 does
not, which is why it is labelled a diagnostic.

---

## 5. Scope

**In scope**

- daily reference evapotranspiration by FAO-56 Penman–Monteith, unit-checked
  and verified against numerical integration;
- growth-stage crop coefficients with FAO-56 interpolation across development
  and late season;
- crop evapotranspiration as the reference-derived target;
- effective rainfall by a declared, swappable method;
- net and gross irrigation requirement, kept distinct from demand;
- machine-learning estimation under reduced inputs, and short-horizon forecasting;
- prediction intervals with measured coverage;
- model-based explanation of individual predictions;
- water-aware crop recommendation as a supporting module;
- a farmer-facing application, a versioned inference service, and a reproducible
  deployment path.

**Out of scope, and why**

- *Observed-water-use validation* — no such data exists here.
- *Spatial generalisation* — the weather series is a single point of unresolved
  provenance.
- *Soil-moisture sensing* — no sensors. The root-zone balance is an estimate and
  is labelled as one everywhere it appears, including in the UI.
- *Yield or crop-risk prediction* — a different problem; the brief explicitly
  excludes it.
- *Claims of novelty for the technology stack* — Flutter, FastAPI, SHAP, XGBoost,
  Docker and cloud hosting are engineering choices, not contributions.

---

## 6. What is actually claimed as a contribution

Not an algorithm. An integrated, auditable framework:

1. **A data-validation pass that changed the research design.** The candidate
   target was rejected on physical grounds, with a positive control proving the
   audit accepts a coherent dataset. That rejection, not a modelling choice,
   determined what this study could honestly ask.
2. **A method for proceeding with an unresolved site without fabricating one.**
   Latitude is estimated from the clear-sky radiation envelope of the project's
   own data, its bias is stated, and the residual uncertainty is *measured*
   (±1.7 % on ET₀) rather than argued about.
3. **Continuous growth-stage crop coefficients** assembled from free-text
   agronomic references, with every judgement call externalised to configuration
   alongside its reasoning.
4. **Reduced-input estimation benchmarked against a physics reference** on
   identical days — the question of what advice is worth without a weather
   station.
5. **Leakage prevention by construction**, through a provenance class attached to
   every feature, rather than by after-the-fact inspection.
6. **An end-to-end path from prediction to advisory** that keeps demand and
   irrigation requirement distinct, attaches uncertainty, and states its
   assumptions in the response itself.

---

## 7. Known limitations, carried from Phase 1

1. The supervised target is reference-derived, not observed.
2. Geographic provenance of the weather series is unresolved; quantified at
   ±1.7 % on ET₀, not eliminated.
3. A single point series, so no spatial claim is supported.
4. Crop-coefficient uncertainty dominates: the project's own reference offers
   maize end-of-season Kc as either 0.35 or 0.70, a factor of two applied
   multiplicatively. This is run as an explicit sensitivity experiment.
5. Stage-boundary reconciliations for paddy and finger millet are modelling
   assumptions, written out in `config/crop_stages.yaml`.
6. Soil and district-rainfall files cannot be spatially joined to the weather
   series and are context lookups only.
7. Effective rainfall has no locally validated method; the chosen one is
   declared, swappable, and its influence is reported.

---

## 8. Status of each claim on this page

| claim | status |
|---|---|
| candidate target fails four physical and statistical tests | **validated** |
| no observed CWR exists in this data | **validated** |
| site provenance unresolved; ET₀ sensitivity ±1.7 % | **measured** |
| growth-stage Kc curves for eight crops | **implemented** |
| Task A will show near-perfect recovery | **expected**, not yet run |
| Tasks B and C outcomes | **unknown** — that is why they are the research |
| any model accuracy figure | **none exists yet** |
