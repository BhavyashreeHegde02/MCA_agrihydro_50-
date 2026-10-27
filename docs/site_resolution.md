# Decision record: what to do about the unresolved weather site

**Status:** accepted, Phase 1
**Applies to:** every ET₀ calculation in the study
**Implemented by:** `config/site.yaml`, `ml/config.py`, `ml/site_inference.py`
**Evidence:** `reports/data_quality/site_resolution.json`,
`reports/data_quality/site_et0_sensitivity.csv`,
`reports/data_quality/site_latitude_profile.csv`

---

## The problem

FAO-56 Penman–Monteith requires two pieces of site information:

- **latitude**, which determines extraterrestrial radiation Ra, which in turn
  sets the clear-sky ceiling Rso and therefore the cloudiness correction inside
  net longwave radiation;
- **elevation**, which determines barometric pressure and hence the
  psychrometric constant, and also enters Rso.

The project's weather file contains neither. It contains no location column of
any kind.

Three responses were available. Two of them are unacceptable:

- *Assume a coordinate.* Fabricating provenance is exactly what the project's
  integrity rules forbid, and it would silently propagate into every result.
- *Stop entirely.* Defensible, but it abandons a complete seven-year daily series
  over a quantity whose influence had not yet been measured.

The third is what was done.

---

## What was decided

**Estimate what the data can support, bound what it cannot, and make the residual
uncertainty visible in every artefact.**

Concretely:

1. Latitude is estimated from the radiation series by a documented, reproducible
   method, and reported with its resampling spread and its known bias.
2. The consequence of the residual uncertainty is measured by recomputing ET₀
   across the full plausible envelope of sites.
3. The site lives in one configuration file, never in code, carrying its
   provenance and its caveats as text.
4. Every ET₀ output carries the site's resolution status.
5. A gate in `ml/config.py` can refuse to compute ET₀ at all.

---

## Step 1 — estimating latitude from the data

### The idea

On a cloud-free day, incoming shortwave radiation Rs approaches the clear-sky
ceiling. Define the clearness index

```
Kt = Rs / Ra(latitude, day-of-year)
```

If the assumed latitude is correct, the clearest day of each month should reach
about the same Kt all year round, because atmospheric transparency on a clear day
does not depend on the calendar.

If the assumed latitude is wrong, it will not. Latitude controls how strongly Ra
swings through the year — nearly flat at the equator, strongly seasonal further
north — so an incorrect latitude leaves a residual seasonal pattern in the
high-percentile Kt.

So: scan latitude, and pick the value that flattens the month-to-month profile of
the 95th-percentile Kt. Because the criterion measures *flatness* rather than
*level*, it is insensitive to the absolute transparency of the atmosphere, which
is the quantity we do not know.

### Restrictions applied

Only November-to-May days with zero recorded rainfall are used — 1351 days of the
2557. Monsoon months never produce a clear sky, so including them would drag the
high percentile down for reasons having nothing to do with latitude.

### Result

| quantity | value |
|---|---|
| best-fit latitude | **23.75 °N** |
| leave-one-year-out mean over 2018–2024 | 23.71 °N |
| leave-one-year-out standard deviation | 0.25 ° |
| implied clear-sky clearness index | 0.726 |
| days used | 1351 |
| objective within 1.5× of its minimum over | 21.25 – 26.00 °N |

A southern-hemisphere search was run as a control and fits substantially worse,
confirming the series is northern-hemisphere.

### The bias this estimate carries

The method assumes atmospheric transparency is constant through the year. In
India it is not. Winter haze depresses radiation in December and January, and
pre-monsoon dust depresses it in April and May. Both effects flatten the observed
radiation cycle relative to the astronomical one, and both are absorbed by the
fit as *higher latitude*.

**The estimate is therefore upper-leaning, and 23.75 °N must not be reported as
the site's location.** It is a weak constraint that narrows the possibilities; it
does not establish provenance. The implied clear-sky Kt of 0.726 sitting slightly
below the FAO-56 nominal 0.75 is consistent with exactly this kind of
atmospheric loading.

### A second, independent line of evidence

The monthly rainfall climatology says something about the region on its own:

| month | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mm | 0.8 | 0.0 | 4.1 | 3.3 | 8.4 | 111.6 | 267.2 | 266.0 | 179.4 | 23.8 | 5.8 | 0.7 |

95 % of the 871 mm annual total falls between June and September, and October is
nearly dry. South-interior Karnataka has a distinctly different pattern, with a
pronounced September–October secondary peak from the retreating monsoon.

Two unrelated signals — radiation geometry and rainfall seasonality — point the
same way. **The evidence does not support treating this series as a Karnataka
record.**

---

## Step 2 — measuring what the uncertainty actually costs

This is the step that determines whether the study can proceed.

Latitude and elevation enter ET₀ through a narrow channel. The dominant energy
term is net shortwave radiation, computed from *measured* Rs, which is
independent of location. Latitude affects only the clear-sky ceiling used in the
longwave correction; elevation affects only pressure and that same ceiling.

So ET₀ was recomputed over the whole 2018–2024 series at 21 site combinations
spanning latitudes 11.5–25.0 °N and elevations 0–1000 m.

| mean ET₀ (mm/day) | 0 m | 500 m | 1000 m |
|---|---:|---:|---:|
| 11.5 °N | 5.594 | 5.577 | 5.561 |
| 13.0 °N | 5.583 | 5.566 | 5.550 |
| 15.0 °N | 5.567 | 5.550 | 5.534 |
| 16.5 °N | 5.553 | 5.536 | 5.519 |
| 18.5 °N | 5.531 | 5.514 | 5.498 |
| 22.0 °N | 5.487 | 5.469 | 5.452 |
| 25.0 °N | 5.441 | 5.422 | 5.404 |

| | value |
|---|---|
| envelope mean | 5.518 mm/day |
| envelope minimum | 5.404 mm/day |
| envelope maximum | 5.594 mm/day |
| **half-spread** | **±1.72 %** |

### Why that settles it

±1.72 % is small compared with uncertainties the study cannot avoid and does not
hide. The project's own growth-stage reference offers maize end-of-season Kc as
either 0.35 or 0.70 — a factor of two, applied multiplicatively to ET₀. The
crop-coefficient uncertainty dominates the site uncertainty by more than an order
of magnitude.

Refusing to proceed over a 1.7 % term while accepting a 100 % term elsewhere
would not be rigour. Quantifying both and stating both is.

---

## Step 3 — how this is enforced in code

**One configuration file.** `config/site.yaml` holds the coordinate, its
`resolution_status`, a prose `provenance` field describing exactly how it was
obtained, and a `caveats` field stating what it does not establish. No
coordinate appears anywhere else in the repository.

**Three possible statuses.**

| status | meaning |
|---|---|
| `measured_provenance` | someone supplied the coordinates actually used for the download |
| `inferred_from_data` | estimated by the method above — the current state |
| `unresolved` | nothing known |

**A gate that can stop the pipeline.** `SiteConfig.require_usable()` raises
`SiteNotResolvedError` when latitude or elevation is absent, or when the status is
not `measured_provenance` and `allow_provisional` is false. The error text names
the file to edit and the field to set. `allow_provisional` is currently true
*because* the sensitivity study above justifies it; setting it to false turns the
hard stop back on, and the test suite exercises that path.

**Status travels with the data.** Every frame `et0_for_weather_frame()` returns
carries `et0_latitude_deg`, `et0_elevation_m` and `et0_site_status`, so a result
can never be separated from the assumption that produced it.

**No location joins.** The district rainfall file and the Karnataka growth-stage
reference are never joined to the weather series by place. They supply a regional
context lookup and agronomic constants respectively, and nothing else. Section
4.2 above is the reason.

---

## What would close this out

A single piece of information: **the latitude, longitude and elevation used when
the weather series was downloaded.** Whoever performed the download has it.

With that in hand:

1. enter the values in `config/site.yaml`;
2. set `resolution_status: measured_provenance`;
3. re-run `python scripts/run_notebooks.py`.

Every downstream artefact regenerates with verified provenance, and the
sensitivity table above becomes a robustness check rather than a limitation. The
study is built so that this is a configuration change, not a rewrite.

---

## Status of each claim in this record

| claim | status |
|---|---|
| the file carries no location column | **validated** |
| units are fixed by the NASA POWER parameter naming | **validated** |
| latitude ≈ 23.75 °N, LOYO sd 0.25° | **estimated from data** |
| the estimator is biased upward by seasonal haze | **reasoned limitation**, not quantified |
| rainfall regime is inconsistent with south-interior Karnataka | **observed** |
| ET₀ varies ±1.72 % across the envelope | **measured** |
| site provenance | **unresolved** |
| elevation of 300 m | **assumption**, not a measurement |
