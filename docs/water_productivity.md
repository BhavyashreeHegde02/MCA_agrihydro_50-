# Water productivity: what the merged project contributes

**Status of this document.** Every figure in it was produced by running the
code in this repository against the data in `datasets/`. Where something is an
estimate, an assumption or a limitation, it is labelled as one. The claim table
at the end marks each statement.

---

## The gap this closes

Two systems were merged to build this project, and each answered half a
question.

**Jalachakra AgriHydro** estimates crop water requirement. Given a crop, a
growth stage and a day's weather, it produces reference evapotranspiration,
the crop coefficient, crop water demand, effective rainfall and the irrigation
that follows. It is careful about the physics and it knows nothing whatever
about what the crop produces.

**Jalachakra Crop Intelligence Platform** classifies crops by soil and
climate suitability, and explores historical yields, prices and rainfall. It
knows what crops produced across 311 districts over eight years, and nothing
about the water that went into them.

Neither can answer the question a farmer in a water-scarce district actually
faces:

> Given the water I can actually get, which crop returns the most per drop?

Answering it requires the water term from one system and the production term
from the other. That join is this project's contribution.

---

## The metric

Water productivity is yield divided by the water consumed to produce it. It is
the standard framing in the irrigation literature — "more crop per drop" — and
it is computed here in two forms, because they answer different questions and
are routinely confused.

**Physical water productivity**, kg/m³

    WP_ETc = yield (kg/ha) / (seasonal ETc (mm) × 10)

What the plant achieves per unit of water it transpires. A biological
efficiency, independent of how the water was delivered.

**Applied water productivity**, kg/m³

    WP_applied = yield (kg/ha) / (seasonal gross irrigation (mm) × 10)

What the *farmer* achieves per unit of water pumped, after the irrigation
system's losses. Always the lower of the two, and the one that matters when
the constraint is a borewell rather than the plant.

**Economic water productivity**, ₹/m³

    EWP = (yield (kg/ha) / 100 × MSP (₹/quintal)) / (water (mm) × 10)

The unit conversion that everything rests on is that **one millimetre of depth
over one hectare is ten cubic metres**: 0.001 m × 10 000 m² = 10 m³. Getting
that factor wrong by an order of magnitude produces numbers that still look
plausible, which is why `tests/test_water_productivity.py` asserts it directly.

### Why minimum support price, not the market price

The market file in this project covers three days — 4 to 6 September 2026 —
with 46 numeric prices across 19 commodities. A rupees-per-cubic-metre figure
built on that would be a number about one week presented as a number about a
season.

Minimum support price is an annual figure published for the whole crop year.
It is also the price that matters to the decision being supported: it is the
floor a farmer can rely on when choosing what to sow. The market snapshot is
retained and shown as context, but it is not the basis of any ranking.

---

## Results

Karnataka, median district yields 2010–2017 against the project's own FAO-56
seasonal water requirements.

| crop | yield kg/ha | season ETc | kg/m³ | kg/m³ pumped | ₹/m³ | obs. |
|---|---:|---:|---:|---:|---:|---:|
| maize | 3,106 | 568 mm | **0.546** | 0.385 | 13.17 | 151 |
| finger millet | 1,515 | 364 mm | 0.416 | 0.295 | **21.67** | 105 |
| paddy | 2,670 | 721 mm | 0.371 | 0.259 | 9.05 | 152 |
| wheat | 1,115 | 456 mm | 0.245 | 0.172 | 6.32 | 67 |
| groundnut | 805 | 559 mm | 0.144 | 0.102 | 10.46 | 150 |
| chickpea | 636 | 493 mm | 0.129 | 0.091 | 7.58 | 129 |
| cotton | 412 | 971 mm | 0.042 | 0.030 | 3.27 | 120 |

### The finding worth stating

**The physical and economic rankings disagree, and the disagreement is the
useful part.**

Maize converts water into the most food: 0.546 kg per cubic metre transpired.
Finger millet converts it into the most income: ₹21.67 per cubic metre, which
is **2.4 times what paddy returns**.

Finger millet achieves that on roughly half paddy's water — 364 mm against
721 mm — while carrying a considerably higher support price (₹5,205 against
₹2,441 per quintal), which reflects national policy encouraging millet
cultivation. A farmer choosing between them on yield alone would pick paddy,
which produces 76 % more grain per hectare. A farmer choosing on water would
not.

This is exactly the substitution that water-scarcity policy in southern India
argues for, and the project arrives at it from two independent data sources
rather than from the policy literature.

### Under a real constraint

Twelve million litres (12,000 m³) over two hectares, the demo farm's district:

| crop | reaches | expected return |
|---|---|---:|
| finger millet | **the whole 2 ha** | ₹164,582 |
| maize | 74 % of the plot | ₹85,424 |
| paddy | 58 % | ₹79,895 |
| cotton | 43 % | ₹29,363 |

Only finger millet finishes the plot, and it returns roughly double the next
best option. A crop the budget cannot complete is reported with the area it
*can* complete rather than dropped, because growing a smaller area properly is
a real decision and it is the one this is meant to inform.

---

## Reconciling the sources

The two projects do not agree on district names. IMD writes `TUMKUR` and
`BIJAAPUR`; the yield file writes `BIJAPUR / VIJAYAPURA` and `SHIMOGE`; farms
recorded in the application write `Tumakuru`.

`ml/districts.py` resolves these with an **explicit alias table, not fuzzy
matching**. The reason is in the test suite: `BIJAPUR` and `VIJAYANAGARA` are
close enough on common string metrics to be matched by a similarity threshold,
and they are different districts. A wrong join here would attribute one
district's water to another district's harvest with nothing visibly failing.

Matching improved from **10 to 18 of 19** Karnataka districts. The nineteenth
is Bangalore, and it is **refused rather than guessed**: the yield record
predates the 1986 split into Bangalore Urban and Rural, Ramanagara was carved
out of the rural district in 2007, and the rainfall file reports all three
separately. Apportioning one district's yields across three would be inventing
data. The refusal is reported to the caller with its reason.

---

## What these numbers are not

Three limits are load-bearing and are repeated in the module docstring, the API
response and the user interface.

**1. The water term is not a district measurement.** It comes from a FAO-56
reference computed on a weather series whose location this project could not
verify — see [`site_resolution.md`](site_resolution.md). It is a consistent
yardstick applied equally to every crop, which is what makes the comparison
valid, but it is not specific to any district.

**2. The yield term is historical.** A district median for 2010–2017 reflects
the management, varieties and rainfall of that period, not this season.

**3. The two terms are not observations of the same fields.** They come from
different sources describing different places at different times.

The consequence is stated plainly wherever the figures appear: **the ranking is
far more defensible than the absolute values.** The values also sit below
published FAO ranges for these crops, which is consistent with Karnataka's
median yields being low — largely rainfed smallholder production — and with
ETc being used as the denominator rather than a smaller effective-use term.

One figure deserves particular caution. **Cotton at 0.042 kg/m³** is low even
allowing for the above, and the likely cause is a unit question in the source:
cotton yield may be reported as lint rather than seed cotton, which would be
roughly a third of the harvested weight. This has not been resolved against the
source documentation and the figure should not be quoted without doing so.

---

## Coverage of the added sources

| source | what it covers | limit |
|---|---|---|
| district yield | 57,132 crop-district-year rows, 2010–2017, 311 districts, 20 states | 31,729 usable after excluding aggregate and unreported rows |
| IMD daily rainfall | 14,545 rows, 728 districts | **20 days only**, 19 Aug – 7 Sep 2026. Current-season context, not a climatology |
| market prices | 19 commodities, MSP for 2026-27 | **3 days** of spot prices, 46 numeric values of 57 slots |

The rainfall window is too short to establish a trend and the interface says so
in every response that uses it. What it does support is departure from the
long-period normal and dry-spell length, which is current-season irrigation
context. Tumakuru, the demo farm's district, is at **−68.3 % departure with a
seven-day dry spell** over that window.

---

## Claim status

| claim | status |
|---|---|
| Productivity table figures | **measured** — computed from the committed data |
| Budget allocation figures | **measured** — via the running API |
| District matching 10 → 18 of 19 | **measured** — `tests/test_districts.py` |
| Tumakuru at −68.3 % departure | **measured** — IMD file, 20-day window |
| 1 mm/ha = 10 m³ | **definitional** — asserted in tests |
| MSP is the appropriate basis | **judgement**, argued above |
| Finger millet substitution is policy-relevant | **judgement**, consistent with published policy |
| Cotton figure reflects a lint/seed-cotton unit issue | **hypothesis, unresolved** |
| Absolute values comparable to FAO field measurements | **explicitly not claimed** |
