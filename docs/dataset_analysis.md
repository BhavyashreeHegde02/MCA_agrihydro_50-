# Dataset analysis

*Phase 1 deliverable. Every number below was produced by
`notebooks/02_data_preprocessing.ipynb` running on the files in `datasets/`.
Nothing here is quoted from a reference document or estimated by hand.*

Reproduce with:

```bash
python scripts/run_notebooks.py 02_data_preprocessing.ipynb
```

---

## 1. What the repository contains

Nine source files were found. Each is assigned a tier in `ml/data_loader.py`
that fixes what it is allowed to do in the study.

| file | rows × cols | tier | what it contributes |
|---|---|---|---|
| `Climate_Data.csv` | 2557 × 11 | primary | the daily weather series that drives ET₀ |
| `Crop_recommendation.csv` | 2200 × 8 | primary | agronomic suitability samples for crop recommendation |
| `Crop_Calender.csv` | 25 × 9 | reference | stage lengths, rooting depth and Kc for five crops |
| `Karnataka_Crop_Growth_Stage_Reference.xlsx` | 13 × 7 | reference | growth-stage Kc for paddy, finger millet and maize |
| `Soil data.csv` | 875 × 5 | supporting | district soil nutrients and pH |
| `Rainfall_2016_districtwise.csv` | 30 × 7 | supporting | Karnataka district rainfall normals |
| `data_season.csv` | 3158 × 12 | supporting | Karnataka cropping, area, price and season context |
| `crop_water_data.csv` | 10000 × 14 | **excluded** | candidate target, rejected in section 5 |
| `crop_dataset.csv` | 5000 × 4 | **excluded** | no crop, date, location or stated units |

Assigning the tier before any analysis is deliberate. It prevents a file
drifting into the modelling path later simply because it happens to contain a
column with a familiar name.

---

## 2. What the inherited cleaning had already done

The repository arrived with a `datasets/cleaned/` directory produced by earlier
work. Rather than assume it was correct, each cleaned file was diffed against
its untouched original. Exactly two differences were found, both in the same
column of the same file:

| dataset | aspect | raw | cleaned |
|---|---|---|---|
| climate | `missing[allsky_sfc_sw_dwn]` | 0 | 1 |
| climate | `min[allsky_sfc_sw_dwn]` | −999.0 | 1.58 |

One solar-radiation value of −999 became a missing value. −999 is the
provider's no-observation sentinel, so that conversion was correct — but it
means the value is now a genuine gap this study has to fill, which section 6
does. Row counts and column counts were untouched in every file, so no records
were dropped anywhere.

The originals are hashed at the start and end of every notebook run, and the run
asserts that the hashes match. `datasets/raw/` is not in the pipeline's list of
writable directories, so no code path can modify it.

---

## 3. The weather series

2557 daily records covering 2018-01-01 to 2024-12-31 with no gaps, no duplicate
dates and no remaining sentinel values.

| variable | unit | min | mean | max |
|---|---|---:|---:|---:|
| mean air temperature | °C | 13.49 | 26.62 | 36.70 |
| minimum air temperature | °C | 5.95 | 20.90 | 29.47 |
| maximum air temperature | °C | 21.44 | 33.73 | 45.18 |
| relative humidity | % | 14.79 | 58.89 | 94.51 |
| wind speed at 2 m | m/s | 0.52 | 3.09 | 12.25 |
| precipitation | mm/day | 0.00 | 2.39 | 174.26 |
| shortwave radiation | MJ/m²/day | 1.58 | 18.99 | 28.92 |

### 3.1 What the column names establish

The headings `T2M`, `T2M_MIN`, `T2M_MAX`, `RH2M`, `WS2M`, `PRECTOTCORR` and
`ALLSKY_SFC_SW_DWN` are the parameter names of a NASA POWER daily point export.
This matters more than it might appear, because it fixes the **units** exactly:
degrees Celsius, percent, metres per second *referenced to two metres*,
millimetres per day and MJ m⁻² day⁻¹.

Those are precisely the units FAO-56 Penman–Monteith expects. Two consequences
follow, and both are implemented rather than assumed:

- no unit conversion is applied anywhere in `ml/et0.py`;
- the FAO-56 logarithmic wind-height correction is deliberately **not** applied,
  because the wind is already at the reference height. `wind_speed_at_2m()`
  exists as a named, tested function precisely so that this decision is visible
  instead of implicit.

What the column names do **not** establish is where the data came from. A POWER
export does not carry its own coordinates, and no latitude, longitude or
elevation column is present.

### 3.2 Internal consistency

All of the following were checked and hold on every record:

- minimum ≤ mean ≤ maximum temperature, on all 2557 days;
- relative humidity within 0–100 %;
- no negative wind speed or rainfall;
- every value inside physically possible terrestrial bounds;
- one record per calendar day with no repeats.

35 automated checks run in `ml/preprocessing.py`. All 35 pass with no blocking
errors and no warnings.

---

## 4. Where was the weather recorded?

FAO-56 needs latitude and elevation. The file supplies neither, and inventing a
coordinate is not acceptable. The study therefore separates what can be
estimated from what can only be bounded.

### 4.1 Latitude estimated from the radiation itself

On a cloud-free day the incoming shortwave radiation approaches the clear-sky
ceiling, so the clearness index Rs / Ra(latitude, day-of-year) should reach
roughly the same value on the clearest day of every month. Latitude controls how
strongly Ra swings through the year, so the latitude that flattens the
month-to-month profile of the high-percentile clearness index is the one most
consistent with the observations. Only rain-free November-to-May days are used,
because monsoon months never produce a clear sky.

**Result: 23.75 °N**, with a leave-one-year-out standard deviation of 0.25° over
the seven years, and an implied clear-sky clearness index of 0.73.

That interval is a statistical one only. The estimator assumes atmospheric
transparency is constant through the year, and it is not: Indian winter haze and
pre-monsoon dust both depress radiation in specific months and both bias the fit
towards higher latitude. **The estimate is upper-leaning and is not evidence of
the site's location.** Geographic provenance remains unresolved.

### 4.2 Rainfall regime, as independent evidence

| J | F | M | A | M | J | J | A | S | O | N | D |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.8 | 0.0 | 4.1 | 3.3 | 8.4 | 111.6 | 267.2 | 266.0 | 179.4 | 23.8 | 5.8 | 0.7 |

*mean mm per month, 2018–2024; annual total 871 mm*

95 % of the annual rainfall arrives between June and September and October is
nearly dry. South-interior Karnataka has a different signature — a pronounced
secondary September–October peak from the retreating monsoon. Together with the
latitude estimate, the evidence **does not support** treating this series as a
Karnataka record.

### 4.3 The consequence, measured rather than argued

This is the result that lets the study proceed honestly.

Latitude and elevation enter ET₀ through a narrow channel. Latitude appears only
in extraterrestrial radiation Ra, which sets the clear-sky ceiling Rso and hence
the cloudiness correction inside net longwave radiation. Elevation appears only
in barometric pressure and in Rso. The dominant energy term comes from *measured*
shortwave radiation, which does not depend on where the site is.

ET₀ was therefore recomputed across the entire plausible envelope — latitudes
11.5 to 25.0 °N crossed with elevations 0 to 1000 m, 21 combinations in total.

| mean ET₀ (mm/day) | 0 m | 500 m | 1000 m |
|---|---:|---:|---:|
| 11.5 °N | 5.594 | 5.577 | 5.561 |
| 15.0 °N | 5.567 | 5.550 | 5.534 |
| 18.5 °N | 5.531 | 5.514 | 5.498 |
| 22.0 °N | 5.487 | 5.469 | 5.452 |
| 25.0 °N | 5.441 | 5.422 | 5.404 |

**Across the whole envelope, mean ET₀ moves by ±1.72 % about the envelope mean.**

That is substantially smaller than the uncertainty in the crop coefficients that
multiply it — the project's own reference file offers Kc values for maize
end-of-season that differ by a factor of two. The unresolved site is a documented
limitation, not a threat to the conclusions, and the study proceeds with the
coordinate held in `config/site.yaml` alongside its provenance and its caveats.

Three consequences are enforced in code:

1. `ml/config.py` refuses to compute ET₀ at all when the site is unresolved and
   `allow_provisional` is false, with an error that explains how to fix it.
2. Every ET₀ output carries the site's `resolution_status`.
3. The district rainfall file and the Karnataka growth-stage reference are
   **never joined to the weather series by location**. They are used only for
   what they are: a regional context lookup, and a source of agronomic constants.

See `docs/site_resolution.md` for the full decision record.

---

## 5. The candidate target is rejected

`crop_water_data.csv` is the only file offering something resembling a crop water
requirement, so it had to be tested before being trusted. Four independent tests
were applied.

Crucially, the audit is validated in **both** directions. `tests/test_target_audit.py`
constructs a synthetic dataset that is physically coherent by design — real
seasonal weather, evapotranspiration that genuinely responds to radiation and
humidity, and volume computed as depth × area × 10 000 — and confirms the audit
**accepts** it. An audit that rejected everything would prove nothing; the
positive control is what gives the rejection below its force.

### Test 1 — does the volume correspond to a real water depth?

One millimetre over one hectare is 10 000 litres, so
`depth (mm) = litres / (hectares × 10 000)`.

- median implied depth: **0.004458 mm**
- largest implied depth across all 10 000 rows: 0.0296 mm
- rows implying a depth in the realistic 0.5–150 mm range: **0.00 %**

The median record implies a depth roughly **112 times smaller** than the
lightest realistic irrigation application. Nothing in irrigation practice
produces that. This test alone is decisive.

### Test 2 — does the evapotranspiration column respond to its own drivers?

| driver | correlation with stated ET |
|---|---:|
| temperature | −0.0107 |
| humidity | +0.0131 |
| solar radiation | −0.0069 |
| wind speed | +0.0063 |

Evapotranspiration is *caused* by radiation, temperature, humidity and wind.
Here it is uncorrelated with all four at once. A measured series cannot look like
this, and neither can a physically modelled one.

### Test 3 — are the marginals just uniform draws?

**All nine** numeric columns are statistically indistinguishable from a uniform
distribution over a round interval (Kolmogorov–Smirnov, p > 0.07 in every case):
temperature 10–45, humidity 20–95, rainfall 0–50, wind 0–40, radiation 5–30,
field area 0.51–49.99, crop age 1–179, soil moisture 10–60, ET 1–15. Measured
agronomic variables are not uniform.

### Test 4 — can the generating formula be recovered?

A log-linear model of the target on the other columns explains **R² = 0.896** of
its variance, with an exponent of 1.22 on evapotranspiration and 1.05 on field
area. 474 rows sit exactly on the minimum of 1 and 427 exactly on the maximum of
5000. The implied per-category multipliers are clean and regular:

- crop: sugarcane ×1.52, rice ×1.19, maize ×0.85, soybean ×0.67, wheat ×0.66, potato ×0.51
- stage: fruiting ×1.11, vegetative ×0.61, maturity ×0.53, germination ×0.35
- soil: silty ×0.89, loamy ×0.79, peaty ×0.70, sandy ×0.60
- irrigation: flood ×1.66, furrow ×1.40, sprinkler ×1.19

The column behaves exactly like a generated quantity: multiplicative in
evapotranspiration and area, scaled by a fixed factor per category, with
lognormal noise, clipped to a round interval at both ends.

### Verdict

**`water_requirement_liters` is rejected as supervised ground truth.**

The file stays in the repository as a documented negative control — it is
genuinely useful for demonstrating what a model trained on an invalid target
looks like — but it does not enter the research path.

This leaves the study without independently observed crop water requirement.
That is a real limitation and is recorded as one, not hidden. The supervised
target is instead defined explicitly as a FAO-56 reference-derived crop
evapotranspiration computed from the real weather series and the growth-stage
crop coefficients. The model learns and refines a reference-derived quantity; it
does not predict field-observed water use, and the write-up says so in those
words.

---

## 6. The one real gap, and how it was filled

A single day — 2024-12-04 — has no shortwave radiation observation.

It was filled from that day's own temperature range using the FAO-56 radiation
estimator, `Rs = k·√(Tmax − Tmin)·Ra` with k = 0.16 for an interior site. This is
the substitution FAO-56 itself prescribes when measured radiation is
unavailable, and it uses same-day observations rather than borrowing from
neighbouring days.

Two alternatives were computed for comparison:

| method | value (MJ/m²/day) |
|---|---:|
| FAO-56 temperature range (**used**) | 15.515 |
| linear interpolation | 15.495 |
| seasonal normal | 14.587 |

The physics estimate and simple interpolation agree to 0.13 %. Two unrelated
methods landing together is reasonable evidence the fill is sound. The column
`allsky_sfc_sw_dwn_was_imputed` travels with the data so any downstream result
can be recomputed with that day excluded.

---

## 7. Crop coefficients

Two files contribute, shaped very differently.

`Crop_Calender_cleaned.csv` is already numeric: stage durations and Kc are
columns, covering groundnut, cotton, wheat, cumin and chickpea. Its `ETo` and
`ETc` columns are the compiler's own worked example rather than measurements and
are **not** used as data.

The Karnataka reference states coefficients and timings as English sentences with
ranges and citations — "Wet paddy Kc_ini = 1.05–1.10; local Hemavathy study uses
1.10". `extract_kc_candidates()` pulls the numbers out mechanically, but it
returns *candidates*, not a choice. Choosing between competing values, and
reconciling stage windows that overlap and leave gaps, are judgement calls; they
live in `config/crop_stages.yaml` with the reasoning written beside each
decision.

The stage windows genuinely required reconciliation. For paddy, the file gives
development at roughly 14–34 days after transplanting and mid-season at roughly
27–65 — overlapping — then jumps to maturity at 97–101 and harvest at 112–113,
leaving a gap. The reconciliation adopted, and its justification, is recorded in
the configuration file.

**Result: eight crops with a continuous, growth-stage-aware Kc curve** built to
the FAO-56 four-stage shape — flat at Kc_ini, linear ramp to Kc_mid across
development, flat through mid-season, linear ramp to Kc_end across the late
stage.

| crop | cycle (days) | Kc_ini | Kc_mid | Kc_end | source |
|---|---:|---:|---:|---:|---|
| paddy | 112 | 1.10 | 1.20 | 1.05 | Karnataka reference |
| finger millet | 98 | 0.30 | 1.00 | 0.30 | Karnataka reference |
| maize | 125 | 0.30 | 1.20 | 0.35 | Karnataka reference |
| groundnut | 130 | 0.45 | 0.97 | 0.80 | crop calendar |
| cotton | 195 | 0.45 | 1.15 | 0.85 | crop calendar |
| wheat | 100 | 0.30 | 1.20 | 0.42 | crop calendar |
| cumin | 100 | 0.30 | 0.70 | 0.40 | crop calendar |
| chickpea | 115 | 0.40 | 1.05 | 0.55 | crop calendar |

Because development and late-season values are interpolated rather than
tabulated, a crop with a 40-day development stage produces 40 distinct
coefficients. That is what makes the resulting water requirement genuinely
stage-aware rather than a four-level step function.

Where the reference file offers a competing value, the alternative is retained
in configuration so the sensitivity experiment can run the study both ways. The
largest such disagreement is maize end-of-season: 0.35 locally against an FAO
tabulated 0.70.

---

## 8. Supporting files, and the limits placed on them

**Soil** — 875 samples across 101 districts spanning Karnataka, Tamil Nadu and
Gujarat. Nitrogen is heavily piled at its 20.0 minimum (median 20.27), which
suggests a reporting floor rather than a measurement distribution; pH is tightly
clustered near 7.0. There is no sample date and no field-level identifier, so
this is a district reference lookup, not a per-field soil record.

**District rainfall** — 29 Karnataka districts after removing a state-aggregate
row that would otherwise have been counted as a district. These are annual
normals, not a daily series; they cannot join to a daily weather record and are
not used as a modelling input.

**Season context** — 3158 rows, 11 Karnataka locations, 2004–2019, with area,
price, soil type, irrigation method and season. The raw file's temperature column
reaches physically impossible values and was dropped upstream; it stays dropped.
Retained as market and cropping context only.

**Crop recommendation** — 2200 samples across 22 crops, exactly 100 each. The
perfect class balance is itself a signal that this is a curated teaching dataset
rather than a field survey, which is noted but does not disqualify it: it feeds
the suitability component of the recommendation module only, never the CWR
regression.

**`crop_dataset.csv`** — 5000 rows of temperature, humidity, rainfall and a water
volume, with no crop, no date, no location and no stated units for the target.
Nothing can be established about it, so it is archived and excluded.

---

## 9. Feature lineage

Every one of the 28 columns the pipeline produces is registered with its source
file, its source columns, the transformation applied and its unit. Each carries a
provenance class:

| class | count | meaning |
|---|---:|---|
| `raw` | 8 | straight from a source file, renamed and range-checked |
| `derived` | 20 | computed from raw inputs, never involving the target |
| `reference` | 0 | agronomic constants — introduced in the next phase |
| `reference_derived` | 0 | physics-baseline quantities — introduced in the next phase |

The absence of the last two classes is deliberate and is a stronger leakage
guarantee than any after-the-fact check: ET₀, Kc and the target belong to the
next phase, so **every feature produced here is independent of the eventual
target by construction**.

Rolling statistics are strictly backward-looking. A test asserts this directly:
placing a 500 mm rainfall spike on the final day of a synthetic series must leave
every earlier row's rolling features bit-identical.

---

## 10. Limitations carried forward

1. **Geographic provenance is unresolved.** Quantified as ±1.72 % on ET₀, but not
   eliminated. Resolved the moment someone supplies the coordinates used for the
   POWER download.
2. **No independently observed crop water requirement exists in this data.** The
   supervised target is reference-derived and must always be described that way.
3. **The weather series is a single point.** No spatial generalisation is
   supported, and none is claimed.
4. **Soil and rainfall files cannot be joined to the weather series by location.**
   Section 4 is the reason.
5. **Stage-boundary reconciliations are modelling assumptions**, written out in
   `config/crop_stages.yaml` rather than embedded in code, and changeable.
6. **The soil nitrogen floor at 20.0 is unexplained** and is carried as a caveat
   on anything that uses soil nitrogen.

---

## 11. Status of each claim on this page

| claim | status |
|---|---|
| weather series complete, daily, internally consistent | **validated** — 35 automated checks |
| units fixed by the NASA POWER parameter naming | **validated** — no conversion needed |
| one radiation day imputed by FAO-56 eq. 50 | **implemented** |
| latitude ≈ 23.75 °N | **estimated from data**, upper-leaning, not provenance |
| site geography | **unresolved** — recorded limitation |
| ET₀ varies ±1.72 % across the site envelope | **measured** in this run |
| `water_requirement_liters` is not ground truth | **validated** — four tests, both controls |
| Kc curves for eight crops | **implemented** from project reference files |
| stage-boundary reconciliations | **assumptions**, externalised to configuration |
| model accuracy | **not established** — no model has been trained yet |
