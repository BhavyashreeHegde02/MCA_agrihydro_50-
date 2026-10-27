# JALACHAKRA — Phase 0 dataset audit

Audit date: 29 September 2026. Status: **Phase 0 complete; Phase 1 not started.**

## Decision summary

The archive contains **12 datasets: 10 CSV files and 2 XLSX workbooks (4 sheets in total)**. All were read in full. They support conditional historical crop-location evidence, limited soil/rainfall context and reference growth-stage information. **No supplied dataset is currently approved as a scientifically defensible daily CWR training set.** The primary CWR dataset category is therefore empty. No model, API, application, database, authentication or production pipeline was built.

The best recovery path is to identify the site, units and export provenance for `Climate_Data.csv`, then validate crop-stage/Kc references and obtain planting-cycle information. Derive explicitly labelled reference ETc only after those gaps are resolved. Keep the two unverified litre-target datasets out of the main research evidence.

## Scope and audit method

Inputs: `AgriHydro_JALACHAKRA.zip` and `Pasted text(20260929-133214).txt` (master specification). Archive members are under `AgriHydro_JALACHAKRA/datasets/raw/`. The ZIP contains datasets only and no previous project source code. Extracted audit copies are under `audit_input/`; raw bytes were not edited. The specification is not counted as a dataset.

All counts are full-file counts, not estimates or sampled counts. CSVs were parsed with pandas; workbooks with pandas/openpyxl, including all sheets and metadata. `Crop_Calender.csv` required Windows-1252 decoding; other CSVs parsed as UTF-8. Spreadsheet data rows exclude titles and field headers. Duplicates mean full-row duplicates beyond the first unless a key is stated. Parser null counts and explicit placeholder counts are reported separately; an apparent zero may still mean unavailable data. Dates and key uniqueness were checked without merging or changing raw files. Field types below are inferred storage types, not proof of semantic correctness. No model was fitted and no performance metrics were calculated.

Source/licence assessment distinguishes supplied evidence, independently checked references and unresolved provenance. No dataset includes an explicit dataset-level reuse licence. This audit cannot certify legal permission from possession of a file; “unresolved” is not a finding that use is illegal. Rights must be established before public redistribution or operational deployment.

## Dataset inventory

The compact table is followed by per-dataset coverage, units, provenance, scientific/rights decisions and a complete field-level quality appendix.

| File / dataset | Rows × columns | Category | Date range | Geographic coverage | Possible target | Potential use |
| --- | --- | --- | --- | --- | --- | --- |
| Climate_Data.csv | CSV: 2557×11 | WEATHER DATA; RAINFALL DATA | 2018-01-01–2024-12-31, daily; 2,557 consecutive dates | Unknown: no coordinates, station, district, state or elevation | No CWR/ET0/ETc target. PRECTOTCORR could be a future rainfall target; ET0 could be derived only after metadata recovery. | Best candidate historical weather input for a future physical baseline; anonymous weather-series exploration now. |
| Crops_data.csv | CSV: 2484×80 | LOCATION/CROP DATA | 2010–2017, annual | 20 state labels; 311 district codes/names; Karnataka has 19 historical district labels | Existing yield/production columns for separate district-level research, not CWR. | Strongest structural support for historical district → represented crop, preferably positive area and a stated year. |
| Soil data.csv | CSV: 875×5 | SOIL DATA | Unknown; no collection date/year | 101 district strings; names suggest Karnataka, Tamil Nadu and Gujarat, but no state field; mapping is not verified | No CWR or crop label. Existing nutrients/pH are measurements or generated values of unknown provenance. | Provisional district-labelled nutrient/pH exploration; document within-label distributions. |
| Rainfall_2016_districtwise.csv | CSV: 30×7 | RAINFALL DATA; SUPPORTING DATA | 2016 appears only in filename; climatological normal reference period not provided | 29 Karnataka district labels plus one STATE/Total row; serial numbers 2–30, no serial 1 | None suitable for CWR; Normal Rainfall is a normal, not observed 2016 rainfall. | Conditional annual-normal context and rain-gauge inventory. |
| rainfall_districtwise_daily_imd.csv | CSV: 14545×22 | RAINFALL DATA | 2026-08-19–2026-09-07: 20 daily dates | 39 raw state/UT strings, 728 state-district pairs; Karnataka 31 district labels. Not 39 distinct administrative states: spelling variants occur. | Daily Actual could support rainfall analysis, not CWR training. | Short district rainfall history after quality screening; retain reporting categories and period metadata. |
| Crop_Calender.csv | CSV: 25×14 | CROP CALENDAR/GROWTH DATA; SUPPORTING DATA | No calendar dates, sowing month or reference year; durations only | Absent | ETc (mm/day) is a reference calculation; not observed daily CWR. | 20 stage-reference rows for dimensional/formula checks and provisional calendar content. |
| Karnataka_Crop_Growth_Stage_Reference.xlsx | Growth_Stage_Reference: 13×7; Sources: 5×3; How_to_Use: 4×2 | CROP CALENDAR/GROWTH DATA; SUPPORTING DATA | No observation dates. Citation years include 2009 and 2026; not dataset time coverage. | Karnataka/Hemavathy/Bangalore context stated in reference text; no location key per observation | None: Kc/stage literature references, not observations or daily labels. | Best provenance-bearing starting point for curated growth-stage/Kc reference content. |
| Crop_recommendation.csv | CSV: 2200×8 | CROP RECOMMENDATION/SUITABILITY DATA | Absent | Absent | label (22-class classification); no CWR target. | Conditional offline crop-label classification benchmark only. |
| crop_dataset.csv | CSV: 5000×4 | UNSUITABLE DATA for scientific CWR; unverified water-label candidate | Absent | Absent | water_required_liters (1.62–41.14), semantically unverified. | Quarantine; at most explicitly labelled offline software-test data after provenance review. |
| crop_water_data.csv | CSV: 10000×14 | UNSUITABLE DATA for scientific CWR; unverified water-label candidate | Absent | Absent | water_requirement_liters; evapotranspiration is an ambiguous possible related target/input. | Quarantine pending full provenance, units and physical-consistency resolution. |
| data_season.csv | CSV: 3158×12 | LOCATION/CROP DATA candidate; UNSUITABLE for numerical modelling as supplied | 2004–2019, year only | 11 Location labels, mixing city/district names; includes Kasaragodu, so not safely Karnataka-only | yeilds or price only after semantics/provenance correction; no CWR. | Provisional named location/crop/season associations for review; preserve spelling Cardamum and yeilds. |
| Market_Wise_Price_Arrival_08-09-2026_08-43-27_AM.xlsx | Data_Report: 19×9 | SUPPORTING DATA; excluded from CWR scope | Price/arrival dates 2026-09-04–2026-09-06; MSP 2026–27. Filename timestamp is not observation coverage. | No market name, district or state column despite report title | Price or arrival for separate market context only; three dates inadequate for robust forecasting. | Optional price/arrival reference after identifying market coverage; outside core water-demand architecture. |

### Category assignment

| Required category | Audit disposition |
| --- | --- |
| PRIMARY CWR DATA | None accepted. crop_dataset.csv and crop_water_data.csv have unverified litre targets and are quarantined. |
| LOCATION/CROP DATA | Crops_data.csv primary historical evidence; data_season.csv provisional only. |
| SOIL DATA | Soil data.csv provisional district-labelled nutrients/pH; no validated farm soil dataset. |
| WEATHER DATA | Climate_Data.csv conditional historical series; location/units missing. |
| RAINFALL DATA | Daily IMD-named file conditional short history; 2016-named file annual normals; PRECTOTCORR in climate file anonymous history. |
| CROP CALENDAR/GROWTH DATA | Karnataka reference workbook preferred for provenance; Crop_Calender.csv unverified reference. |
| CROP RECOMMENDATION/SUITABILITY DATA | Crop_recommendation.csv standalone label benchmark; no location-aware suitability proof. |
| SUPPORTING DATA | Growth workbook Sources/How_to_Use; annual gauge inventory; market snapshot optional and outside CWR. |
| UNSUITABLE DATA | Two litre-target datasets for scientific CWR; data_season numerical fields as supplied; market data for water-demand modelling. |

## 1. `Climate_Data.csv`

| Audit item | Finding |
| --- | --- |
| Category | WEATHER DATA; RAINFALL DATA |
| Source / provenance | No source URL or licence; parameter names resemble NASA POWER, not proof of origin. |
| Date range | 2018-01-01–2024-12-31, daily; 2,557 consecutive dates |
| Geographic coverage | Unknown: no coordinates, station, district, state or elevation |
| Crop coverage | None |
| Season | No agricultural season; calendar month/year present |
| Units | No units in file. NASA POWER-like field names suggest temperature °C, RH %, wind m/s, precipitation mm/day, radiation energy/area/day; all require original export metadata, especially radiation conversion. |
| Possible target | No CWR/ET0/ETc target. PRECTOTCORR could be a future rainfall target; ET0 could be derived only after metadata recovery. |
| Potential project use | Best candidate historical weather input for a future physical baseline; anonymous weather-series exploration now. |
| Excluded use | Location-specific weather, farm forecasts and immediate FAO-56 labels |
| Reason / limitations | Location, elevation, units, observation time basis and provenance absent. |
| Legal reuse status | Unresolved; establish provider/export and applicable reuse terms before redistribution/deployment. |
| Scientific support | Conditional weather input; not a complete validated FAO-56 input package. |

**Quality findings:** One ALLSKY_SFC_SW_DWN=-999 on 2024-12-04: semantic missingness despite zero parser nulls. Date components match datetime interpreted as month/day/year. No missing daily dates; no T2M_MIN ≤ T2M ≤ T2M_MAX violations. Do not fill radiation from another unidentified location.

**CSV** — 2,557 data rows; 11 columns; 0 exact duplicate rows; 0 parser-null cells; 1 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 2. `Crops_data.csv`

| Audit item | Finding |
| --- | --- |
| Category | LOCATION/CROP DATA |
| Source / provenance | No source URL, methodology or licence included. Do not assign a provider by resemblance. |
| Date range | 2010–2017, annual |
| Geographic coverage | 20 state labels; 311 district codes/names; Karnataka has 19 historical district labels |
| Crop coverage | 23 area/production/yield crop-series groups plus 6 area-only groups; includes overlapping sorghum and oilseed aggregates |
| Season | Kharif and Rabi only explicit in sorghum column names; other crop series annual |
| Units | Area: 1000 ha; production: 1000 tons; yield: Kg per ha, exactly as headers. Codes are identifiers. |
| Possible target | Existing yield/production columns for separate district-level research, not CWR. |
| Potential project use | Strongest structural support for historical district → represented crop, preferably positive area and a stated year. |
| Excluded use | Farm suitability ranking, current crop presence, daily CWR or irrigation labels |
| Reason / limitations | Historical aggregates; no farm observations, daily weather or water-demand outcome. |
| Legal reuse status | Unresolved; obtain original source/reuse licence. |
| Scientific support | Conditionally supports historical regional evidence; cannot establish agronomic suitability. |

**Quality findings:** Unique (State Code, Dist Code, Year); 310 districts have 8 years and one has 4, so panel is incomplete. No nulls or negative numeric values. 169 crop-row combinations have zero area but positive production: rounding or source inconsistency unresolved. Zero area is not automatically proof of absence. Do not sum aggregate oilseeds/sorghum alongside their components. Historical district boundaries need a versioned crosswalk.

**CSV** — 2,484 data rows; 80 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 3. `Soil data.csv`

| Audit item | Finding |
| --- | --- |
| Category | SOIL DATA |
| Source / provenance | No sampling provenance, source URL or licence. |
| Date range | Unknown; no collection date/year |
| Geographic coverage | 101 district strings; names suggest Karnataka, Tamil Nadu and Gujarat, but no state field; mapping is not verified |
| Crop coverage | None |
| Season | Absent |
| Units | pH is dimensionless by scientific convention; N/P/K units, laboratory method and sampling depth are absent. |
| Possible target | No CWR or crop label. Existing nutrients/pH are measurements or generated values of unknown provenance. |
| Potential project use | Provisional district-labelled nutrient/pH exploration; document within-label distributions. |
| Excluded use | Farm soil profile, soil moisture, field capacity, wilting point, hydraulic model, automatic suitability join |
| Reason / limitations | No sample ID, coordinates, date, state, units, soil texture or sampling method. |
| Legal reuse status | Unresolved; obtain collection provenance and reuse rights. |
| Scientific support | Only provisional descriptive context; no verified representativeness or physical soil-water parameters. |

**Quality findings:** 875 rows with repeated district labels and zero exact duplicate rows. The 101 names remain 101 after case/space normalization. Includes variants such as Ramangara, Tuticorn, Tiruchippalli and Bagalakote. District-only merge is one-to-many and cannot identify a farm sample.

**CSV** — 875 data rows; 5 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 4. `Rainfall_2016_districtwise.csv`

| Audit item | Finding |
| --- | --- |
| Category | RAINFALL DATA; SUPPORTING DATA |
| Source / provenance | No source URL, licence or normal-period documentation. |
| Date range | 2016 appears only in filename; climatological normal reference period not provided |
| Geographic coverage | 29 Karnataka district labels plus one STATE/Total row; serial numbers 2–30, no serial 1 |
| Crop coverage | None |
| Season | Annual normals; no seasonal/daily observations |
| Units | Station counts and rainy-day counts implied by headers. Normal Rainfall likely mm/year but unit and normal period unconfirmed. |
| Possible target | None suitable for CWR; Normal Rainfall is a normal, not observed 2016 rainfall. |
| Potential project use | Conditional annual-normal context and rain-gauge inventory. |
| Excluded use | Daily rainfall, observed 2016 totals, effective rainfall, forecast or irrigation labels |
| Reason / limitations | Normal climatology with unknown baseline; lacks dates and actual rain observations. |
| Legal reuse status | Unresolved; establish publisher and reuse terms. |
| Scientific support | Reference context only after confirming units/normal period; not daily weather. |

**Quality findings:** Station arithmetic passes for all 30 rows. The 29 detail rows sum to 1,136 working + 138 not working = 1,274 total, matching STATE/Total. Do not count Total as a district or infer statewide geographic completeness from this arithmetic.

**CSV** — 30 data rows; 7 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 5. `rainfall_districtwise_daily_imd.csv`

| Audit item | Finding |
| --- | --- |
| Category | RAINFALL DATA |
| Source / provenance | Filename claims IMD; no source URL, export metadata or licence included. Not independently authenticated against original bulletin. |
| Date range | 2026-08-19–2026-09-07: 20 daily dates |
| Geographic coverage | 39 raw state/UT strings, 728 state-district pairs; Karnataka 31 district labels. Not 39 distinct administrative states: spelling variants occur. |
| Crop coverage | None |
| Season | No crop season; cumulative anchor 2026-06-01; monthly/weekly strings retained separately |
| Units | Rainfall amounts likely mm, absent from headers; departures explicitly % strings. Confirm reporting and normal-period definitions. |
| Possible target | Daily Actual could support rainfall analysis, not CWR training. |
| Potential project use | Short district rainfall history after quality screening; retain reporting categories and period metadata. |
| Excluded use | Live/forecast weather, long-term climate training, same-day joins to 2010–2024 sources |
| Reason / limitations | 20-day extract, temporal mismatch, category/period anomalies, unverified provenance. |
| Legal reuse status | Unresolved; confirm IMD extraction source and licence before public reuse. |
| Scientific support | Conditional short historical district context. Quarantine inconsistent aggregate periods and verify category meaning. |

**Quality findings:** Unique (State, District, Date), zero exact duplicate rows. A 728×20 grid lacks 15 records: TAMIL NADU/NAGAPATTINAM appears on only 5 dates. 182 Daily Category=ND rows store Daily Actual=0: treat as unverified/no-data, not confirmed dry days. Departure null counts are daily 182, weekly 138, cumulative 100, monthly 105. Five Week Date values refer to January 2026; 80 Monthly Date values refer to May 2025 despite August/September 2026 Date values. Weekly/monthly/cumulative totals overlap; never sum these with daily values. State spelling variants include CHHATISGARH/CHHATTISGARH and TAMIL NADU/TAMILNADU; headers contain literal backslash-n and spelling errors.

**CSV** — 14,545 data rows; 22 columns; 0 exact duplicate rows; 525 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 6. `Crop_Calender.csv`

| Audit item | Finding |
| --- | --- |
| Category | CROP CALENDAR/GROWTH DATA; SUPPORTING DATA |
| Source / provenance | No references or licence. Windows-1252 encoding used for en-dash placeholders. |
| Date range | No calendar dates, sowing month or reference year; durations only |
| Geographic coverage | Absent |
| Crop coverage | Groundnut, Cotton, Wheat, Cumin, Chickpea |
| Season | Four stages plus Total season; no Kharif/Rabi mapping |
| Units | Duration days; root depth cm; Kc dimensionless; ETo/ETc mm/day; effective rainfall mm; WHC mm/m. |
| Possible target | ETc (mm/day) is a reference calculation; not observed daily CWR. |
| Potential project use | 20 stage-reference rows for dimensional/formula checks and provisional calendar content. |
| Excluded use | Training on 25 independent observations, zero-demand total-season labels, location-specific crop scheduling |
| Reason / limitations | Five summary rows mixed with stages; no dates, site or supporting reference for numeric values. |
| Legal reuse status | Unresolved; recover original source and permissions. |
| Scientific support | Reference-only pending agronomic validation; formula consistency does not establish field accuracy. |

**Quality findings:** 25×14 physical layout includes five wholly empty columns (Unnamed: 9–13); 9 meaningful columns. Four stages for each of five crops and five Total season rows. Kc has 1 null + 4 en-dashes; ETo has 5 en-dashes; effective rainfall has 20 en-dashes. All 20 stage ETc values match ETo×Kc within 0.01 mm/day. Five total-season ETc values are 0, not defensible seasonal sums. Stage durations sum to stated totals: 130, 195, 100, 100 and 115 days for Groundnut, Cotton, Wheat, Cumin and Chickpea. WHC=125 in every row is a reference assumption, not measured soil.

**CSV** — 25 data rows; 14 columns; 0 exact duplicate rows; 126 parser-null cells; 29 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 7. `Karnataka_Crop_Growth_Stage_Reference.xlsx`

| Audit item | Finding |
| --- | --- |
| Category | CROP CALENDAR/GROWTH DATA; SUPPORTING DATA |
| Source / provenance | Sources sheet contains 5 citations/URLs: FAO-56, FAO Crop Water Needs, Thirumalesha et al. 2026, Patil & Puttanna 2009, TNAU Ragi. Compiler licence absent. |
| Date range | No observation dates. Citation years include 2009 and 2026; not dataset time coverage. |
| Geographic coverage | Karnataka/Hemavathy/Bangalore context stated in reference text; no location key per observation |
| Crop coverage | Paddy (Rice), Finger Millet (Ragi), Maize |
| Season | Stage descriptions; no normalized season field or complete sowing calendar |
| Units | Durations in text: days, weeks, DAT (after transplanting), WAS (after sowing); Kc dimensionless, embedded in prose. |
| Possible target | None: Kc/stage literature references, not observations or daily labels. |
| Potential project use | Best provenance-bearing starting point for curated growth-stage/Kc reference content. |
| Excluded use | Automatic universal stage assignment; independent ML training samples; using harvest as numeric Kc |
| Reason / limitations | Mixed timing conventions, overlapping rice phenology and incomplete intervals; several Kc values need interpolation and contextual choice. |
| Legal reuse status | Reference-specific rights plus compiler rights unresolved. A citation or accessible article is not a blanket dataset licence. |
| Scientific support | Supports qualified reference explanations. Numeric operational curves need source-table validation and local/varietal applicability review. |

**Quality findings:** All 3 sheets inspected: Growth_Stage_Reference 13×7; Sources 5×3; How_to_Use 4×2. All fields are text; no nulls/duplicates, formulas or external links. Source URLs are cell text. Rice timings overlap (≈14–34 and ≈27–65 DAT); do not force mutually exclusive stage boundaries. Maize contains local vs FAO alternatives (mid 1.20 vs 1.15; end 0.35 vs 0.70). Source-specific selection required. Vague Indian rice study citations are not uniquely identified. The MAUSAM abstract confirms the cited ragi peak, but this does not validate every timing/value in the workbook.

**Growth_Stage_Reference** — 13 data rows; 7 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

**Sources** — 5 data rows; 3 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

**How_to_Use** — 4 data rows; 2 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 8. `Crop_recommendation.csv`

| Audit item | Finding |
| --- | --- |
| Category | CROP RECOMMENDATION/SUITABILITY DATA |
| Source / provenance | No source, collection method, licence or sampling frame. Do not infer provenance from a familiar filename. |
| Date range | Absent |
| Geographic coverage | Absent |
| Crop coverage | 22 labels; listed in schema appendix |
| Season | Absent |
| Units | N/P/K units absent; temperature, humidity and rainfall units/period absent. ph denotes dimensionless pH. |
| Possible target | label (22-class classification); no CWR target. |
| Potential project use | Conditional offline crop-label classification benchmark only. |
| Excluded use | Location → crop evidence, farm suitability guarantee, water demand and soil joins by row order |
| Reason / limitations | No geographic/time/sample linkage, water-demand outcome or agronomic validation. |
| Legal reuse status | Unresolved; establish original dataset licence and provenance. |
| Scientific support | Technically trainable classification data; scientific generalizability and operational suitability unverified. |

**Quality findings:** 2,200 rows, exactly 100 per crop label; no nulls or exact duplicates. Balanced classes do not establish representative farm prevalence. No grouping identifiers for field-independent validation.

**CSV** — 2,200 data rows; 8 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 9. `crop_dataset.csv`

| Audit item | Finding |
| --- | --- |
| Category | UNSUITABLE DATA for scientific CWR; unverified water-label candidate |
| Source / provenance | No source, generation method, target definition or licence. |
| Date range | Absent |
| Geographic coverage | Absent |
| Crop coverage | Absent: no crop column |
| Season | Absent |
| Units | Explicit °C, %, mm and litres by headers; rainfall and water time interval absent; no area. |
| Possible target | water_required_liters (1.62–41.14), semantically unverified. |
| Potential project use | Quarantine; at most explicitly labelled offline software-test data after provenance review. |
| Excluded use | Primary CWR ML, mm/day conversion, crop-specific advisory |
| Reason / limitations | Unknown crop, field area, water interval and target basis prevent physical interpretation. |
| Legal reuse status | Unresolved. |
| Scientific support | Not suitable for current research target or farmer advice. |

**Quality findings:** 5,000 complete numeric rows and zero exact duplicates do not make a valid scientific dataset. Bounded numeric ranges are not proof of synthetic generation; origin remains unknown.

**CSV** — 5,000 data rows; 4 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 10. `crop_water_data.csv`

| Audit item | Finding |
| --- | --- |
| Category | UNSUITABLE DATA for scientific CWR; unverified water-label candidate |
| Source / provenance | No source, observation/generation procedure, licence or target definition. |
| Date range | Absent |
| Geographic coverage | Absent |
| Crop coverage | Cotton, Maize, Potato, Rice, Soybean, Sugarcane, Wheat |
| Season | Absent; growth_stage uses Germination, Vegetative, Flowering, Fruiting, Maturity |
| Units | Explicit rainfall mm, wind km/h, area ha, age days, soil moisture %, target litres; temperature/humidity/radiation/evapotranspiration units or periods not explicit. |
| Possible target | water_requirement_liters; evapotranspiration is an ambiguous possible related target/input. |
| Potential project use | Quarantine pending full provenance, units and physical-consistency resolution. |
| Excluded use | Primary CWR/irrigation model, daily forecast, temporal validation, joining to reference Kc as if observed |
| Reason / limitations | No date/location/field ID; implausible water depth if interpreted as whole-field demand; stage/age incoherence and endpoint concentrations. |
| Legal reuse status | Unresolved. |
| Scientific support | Not defensible CWR evidence without target/provenance repair. |

**Quality findings:** 10,000 rows; zero nulls/exact duplicates. Dividing litres by 10,000×ha gives implied depth 0.0000020008–0.0296384 mm, median 0.00445758 mm; no daily basis can be assigned. Targets equal exactly 1 litre in 474 rows and 5,000 in 423 rows. Every stage spans ages 1–179 days. These are quality flags, not proof of fabrication. Evapotranspiration ranges 1–15 with no declared unit; cannot call it ET0 or ETc.

**CSV** — 10,000 data rows; 14 columns; 0 exact duplicate rows; 0 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 11. `data_season.csv`

| Audit item | Finding |
| --- | --- |
| Category | LOCATION/CROP DATA candidate; UNSUITABLE for numerical modelling as supplied |
| Source / provenance | No source, methodology or licence. |
| Date range | 2004–2019, year only |
| Geographic coverage | 11 Location labels, mixing city/district names; includes Kasaragodu, so not safely Karnataka-only |
| Crop coverage | Coconut, Cocoa, Coffee, Cardamum, Pepper, Arecanut, Ginger, Tea, Paddy, Groundnut, Blackgram, Cashew, Cotton |
| Season | Kharif, Rabi, Zaid |
| Units | Area, Rainfall, Temperature, yeilds, Humidity and price units not stated; aggregation periods unclear. |
| Possible target | yeilds or price only after semantics/provenance correction; no CWR. |
| Potential project use | Provisional named location/crop/season associations for review; preserve spelling Cardamum and yeilds. |
| Excluded use | Scientific weather, yield, suitability or water-demand training; quantitative joins |
| Reason / limitations | 767 temperatures >60 (maximum 222); missing soil values; repeated ambiguous entity keys and mixed spatial grain. |
| Legal reuse status | Unresolved. |
| Scientific support | Quarantine numeric modelling; associations remain provisional until original source confirms them. |

**Quality findings:** 58 Soil type nulls. No full-row duplicates, but 1,750 excess rows repeat (Year, Location, Crops, Season), leaving 1,408 unique combinations; largest group has 78 rows. No sample/variety ID explains multiplicity. Only 21 distinct Rainfall values across 3,158 rows. Soil labels have trailing-space variants. Rainfall variability within location prevents treating it as a unique location normal.

**CSV** — 3,158 data rows; 12 columns; 0 exact duplicate rows; 58 parser-null cells; 0 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## 12. `Market_Wise_Price_Arrival_08-09-2026_08-43-27_AM.xlsx`

| Audit item | Finding |
| --- | --- |
| Category | SUPPORTING DATA; excluded from CWR scope |
| Source / provenance | No publisher, URL, licence or market aggregation definition; creator metadata openpyxl is not provenance. |
| Date range | Price/arrival dates 2026-09-04–2026-09-06; MSP 2026–27. Filename timestamp is not observation coverage. |
| Geographic coverage | No market name, district or state column despite report title |
| Crop coverage | 19 commodity labels in 5 groups; commodity is not necessarily field crop (e.g. Copra) |
| Season | No crop season; MSP fiscal/marketing label 2026–27 |
| Units | Prices/MSP Rs./Quintal; arrivals Metric Tonnes, from report header. |
| Possible target | Price or arrival for separate market context only; three dates inadequate for robust forecasting. |
| Potential project use | Optional price/arrival reference after identifying market coverage; outside core water-demand architecture. |
| Excluded use | Regional crop occurrence, CWR/ET0/ETc/ML features, farm suitability |
| Reason / limitations | Commodity trading is not cultivation evidence; missing geography and no water information. |
| Legal reuse status | Unresolved; recover publisher and reuse terms. |
| Scientific support | Limited descriptive market snapshot, not agricultural water evidence. |

**Quality findings:** One sheet Data_Report, 22 physical rows×9 columns. Row 1 title, row 2 unit bands, row 3 field headers, rows 4–22 contain 19 records. Default first-row parsing incorrectly gives 21 rows. Actual table has 0 nulls/duplicates but 23 dash missing values: MSP 1; prices Sep 6:9, Sep 4:2; arrivals Sep 6:9, Sep 4:2. Do not replace dashes with zero.

**Data_Report** — 19 data rows; 9 columns; 0 exact duplicate rows; 0 parser-null cells; 23 detected placeholder/sentinel cells. Full field names, types and counts appear in Appendix A.

## Recommended dataset architecture — design only

Keep independent evidence layers with explicit source lineage. These are proposed logical datasets, not implemented tables or invented source fields.

| Proposed layer | Source and grain | Controls before promotion |
| --- | --- | --- |
| Immutable raw | Original 12 files, byte-for-byte | Record source URL, licence, retrieval date, file hash, encoding and original headers; keep raw placeholders. |
| Curated historical crop evidence | Crops_data: state code + district code + year + crop-series after a documented wide-to-long transformation | Versioned district boundaries, unit conversion, aggregate/component flags, ambiguous zeros and provenance. |
| Location/crop crosswalks | Separately reviewed alias dictionaries, not inferred measurements | Preserve raw labels; canonical IDs and validity periods are new metadata, not existing source columns. Distinguish city, district and farm. |
| Weather series | Climate_Data: currently date only at unknown site | Recover site/grid ID, coordinates, elevation, time zone, product/source, units and radiation missingness before ET0 derivation. |
| Rainfall evidence | IMD-named district/date history and separate annual-normal table | Do not combine normals with observations; keep period/category/source fields; isolate Total row and incompatible aggregate periods. |
| Soil evidence | District-labelled records without sample identity | Recover state/date/sample/depth/units; until then preserve distributions with unknown representativeness, not farm lookup values. |
| Crop-stage references | Karnataka workbook and calendar CSV kept separately | Source-specific crop/stage curves, duration conventions, variety, local applicability; exclude total rows/terminal harvest from daily labels. |
| Independent classifier benchmark | Crop_recommendation.csv | Rights and label provenance, units, independent external validation; no synthetic spatial linkage. |
| Quarantine | Both litre-target files; numerical data_season fields; inconsistent rainfall aggregates | No promotion merely because parsing succeeds. Resolve semantic defects with the owner/source. |
| Future reference targets | Site + crop cycle + date + versioned method | Derived ET0, Kc and ETc tracked separately from measured water use; this layer does not exist yet. |

## Join / merge feasibility

**No full multi-dataset training merge is defensible now.** Matching crop names or row counts does not establish common observations. There are viable reference/catalogue relationships and conditional district-context relationships; these must not manufacture farm-level paired labels.

| Datasets / relation | Actual candidate key | Cardinality / overlap evidence | Decision and alignment requirements |
| --- | --- | --- | --- |
| Crops_data internal panel | State Code + Dist Code + Year | 2,484 unique keys; 311 districts; 2010–2017 | Valid source-internal grain. Crop series may be unpivoted later without fabricating crop observations from missing values. |
| Growth_Stage_Reference → Sources | Evidence Source vs Source text | Composite citations and vague Indian rice study wording; not an exact foreign key | Manually curate citation relationships. Do not string-join multiple references as one source. |
| Crops_data → growth workbook | Crop name extracted from column header → Crop | rice ↔ Paddy (Rice); finger millet ↔ Finger Millet (Ragi); maize ↔ Maize | Reference enrichment only, using reviewed crop aliases. Historical presence does not validate local Kc or provide planting dates. |
| Crops_data → Crop_Calender | Crop-series label → Crop | Wheat, cotton, chickpea, groundnut overlap; cumin absent from crop-series headers | Conditional reference lookup; exclude Total season from stage dimension; four stages per crop create intended one-to-many reference expansion, not training observations. |
| Climate_Data → crop-stage references | No actual crop-cycle/site key | Calendar dates exist only in climate; crop and planting dates absent there | Blocked observational merge. Later simulation needs a recovered site and explicit planting/crop scenario, labelled reference-derived. Never arbitrary Cartesian training expansion. |
| Climate_Data → daily rainfall | Date would be a partial key only | 2018–2024 versus 2026: zero temporal overlap; climate location unknown | Blocked. No same-site or same-day pairing. |
| Crops_data → daily rainfall | State/district after crosswalk, plus date/year for observations | 2010–2017 versus 2026: zero temporal overlap; 10 of 19 Karnataka crop district labels exactly match rainfall names after case/space normalization | Separate historical context only. Need boundary-vintage crosswalk; do not append 2026 rain to 2010 yield as contemporaneous data. |
| data_season → Climate_Data | Year only | 2018–2019 overlap, but no common site key; climate daily vs season/year grain | Blocked. A common year alone is insufficient; numerical defects also block model use. |
| data_season → Crops_data | Location → Dist Name; Year; Crops → crop-series | 2010–2017 overlap, but data_season key has 1,750 excess rows and mixed city/district meanings | Not safe raw join. Resolve sources, geography, season vs annual grain, unit definitions and multiplicity first. Do not average away unknown record meaning. |
| Soil → district crop/rainfall | District label only | 875 records / 101 labels; 14 exact overlaps with Karnataka daily rainfall after case/space normalization | Potential descriptive spatial association after authoritative state+district mapping; no dates or sample identity for scientific temporal pairing. Aggregation would need a sampling rationale. |
| 2016 normals → district tables | Districts after trimming/alias crosswalk | 29 detail rows plus STATE/Total; no normal-period key | Conditional climatology context only. Exclude Total; verify baseline/units/boundaries. Cannot substitute annual normals for daily rain. |
| data_season → daily rainfall | Location label only | 5 exact Karnataka name matches; 2004–2019 versus 2026 | No observational time join; location aliases alone do not solve mismatched grain. |
| Crop_recommendation → Soil/Climate | N/P/K or weather values are not identifiers | No shared location/date/sample keys; units not established | Blocked. Do not nearest-neighbour match unrelated rows to create “ground truth”. |
| crop_dataset / crop_water_data → any observational file | No shared field/site/date/sample ID | Some crop names overlap only in crop_water_data | Blocked for paired training; crop-name equality alone cannot align weather, age or water demand. |
| Market → crop catalogue | Commodity alias → crop name | Possible reference alias mapping, e.g. Paddy(Common) → rice; no market geography | Optional commodity reference only; no CWR or crop-location evidence join. |

Future joins must declare one-to-one/many-to-one/reference one-to-many contracts and check unmatched keys, duplicate expansion, geographic boundary version, time grain and unit compatibility. Crop aliases such as rice/paddy, ragi/finger millet and soybean/soyabean require explicit reviewed mappings. Do not automatically equate copra with a coconut field record or city Bangalore with both urban and rural districts.

## Supported features and limits

| Requested feature | Available support | Current verdict |
| --- | --- | --- |
| 1. Location → crop | Crops_data district/year area-production evidence; data_season provisional crop-season names | Historical represented crops only; not best crop, current cultivation or farm suitability. |
| 2. Soil information | Soil data district-labelled N/P/K/pH; data_season unverified soil types | Provisional descriptive context; no trustworthy farm soil lookup. |
| 3. Weather/rainfall | Climate daily series; 20-day district rain extract; annual normals | Historical, conditional and mutually distinct products; no live or forecast service. |
| 4. Crop calendar/growth stages | Reference workbook (3 crops), calendar CSV (5 crops) | Reference explanations available; automated farmer-specific stages require planting/variety/location and validated boundaries. |
| 5. CWR/ET0/ETc | 20 calendar stage ETc values arithmetically consistent; candidate climate inputs and Kc references | Reference review supported; complete site-specific daily FAO-56 baseline not currently supported. |
| 6. ML training | Crop_recommendation technically supports label classification; no accepted CWR labels | Conditional offline classifier experiment; core CWR ML blocked. No training performed. |
| Crop support status | Dataset evidence and audit findings | All CWR crops remain Under Development / Model not available yet. Reference coverage is not trained-model support. |
| 7. Datasets not to use | Both litre-target files for CWR; data_season numerical fields; market data for CWR; malformed aggregate rain periods | Quarantine/exclude these uses. Keep immutable raw files; do not delete. |

## Unsupported features and required evidence

| Feature absent or not defensible now | What is missing |
| --- | --- |
| Farm/GPS → district or taluk/village evidence | No coordinates, polygons, gazetteer, validated geocoding or farm identifiers in the supplied datasets. |
| Current farm weather / forecasts | No live data connection, forecast vintages, farm/site spatial linkage or current observations beyond historical extracts. |
| Verified farm soil moisture and water storage | No soil sampling date/depth/coordinates, field capacity, wilting point, bulk density, reliable hydraulic parameters or sensor series. |
| Automatic current crop stage / GDD | No farm sowing/transplanting date and variety records; no complete validated local phenology curve or base-temperature dataset. |
| Reliable daily CWR ML and uncertainty | No accepted dated/site-specific daily target panel, independent validation set or trained model. |
| Physics-guided model superiority | No valid experimental targets/splits; reproducing a formula is not independent evidence of improved actual water estimation. |
| Effective rainfall and actual irrigation advice | Daily district rainfall is not effective rainfall; missing field water balance, storage, runoff/drainage, method assumptions and crop-specific requirements. |
| Net/gross irrigation and farm water volume | Need validated demand interval, effective rain, field area, application efficiency and relevant balance terms. Existing anonymous area values cannot be linked to a user farm. |
| Paddy total water requirement | ETc alone omits land preparation, ponding/seepage/percolation needs where applicable; these inputs are not supplied. |
| Location-aware Help Me Choose suitability scoring | No validated joined soil-weather-season-water-availability-crop outcome data; crop presence/class labels cannot establish suitability scores. |
| Perennial CWR (arecanut/coffee etc.) | Names exist in general datasets but validated perennial water-demand targets/Kc/phenology are absent. |
| Water savings, water use and prediction history | No actual irrigation logs, farm histories, prediction records or measured baselines. |
| Satellite crop maps, NDVI/NDWI, remote sensing | No imagery, georeferenced raster/vector data or sensor metadata. |
| Application accounts/authentication/database/API | Not dataset-derived features and expressly outside Phase 0; nothing implemented. |

## Recommended target variable

**Recommended future primary target: reference-derived daily crop evapotranspiration, `ETc_reference_mm_day`, at a verified site/crop-cycle/date. This is a proposed output name, not a column that exists in the supplied files.** Define it as FAO-56 ET0 × a documented, locally appropriate stage-dependent Kc. Preserve the target derivation version and distinguish it from measured crop water use, net irrigation and gross irrigation. [R1–R2]

There is no accepted ready-to-train primary target today. The calendar ETc column has only 20 stage lookup values, not a daily observational panel. The two litre targets lack trustworthy duration/physical definitions; the smaller file also lacks area and crop. Do not rename either as CWR mm/day. If independent measured ET/soil-water-balance data later becomes available, use it as a separate validation target, not silently interchange it with reference-derived ETc.

For a meaningful forecasting experiment, choose a fixed issue time and horizon (for example next-day reference ETc) and permit only information available at that issue time. Same-day ET0 and Kc supplied together to predict their product make the task formula reproduction. Lagged weather/ET0/ETc and growth-stage information can be explored after lawful, aligned inputs and planting histories exist.

## Recommended ML experiments — planned, none executed

| Experiment | Data and design | Gate / interpretation |
| --- | --- | --- |
| E0 Physical baseline | Validate FAO-56 ET0; curated Kc curve → daily reference ETc. Compare formula arithmetic and source/reference cases. | Recover climate site/elevation/units; correct radiation sentinel; validate stage sources and planting dates. A deterministic target-generator matches its own labels by construction and is not an independent accuracy competitor. |
| E1 Simple forecast benchmarks | Persistence and historical seasonal baselines for a fixed next-day horizon. | Only prior observations available at forecast issue time. Needed before complex ML claims. |
| E2 Conventional baselines | Random Forest Regressor and XGBoost Regressor, same dated target panel and same permitted weather/calendar features. | No training on quarantined litre labels; tune on earlier validation periods only. |
| E3 Proposed model and ablations | Growth-stage-aware XGBoost with temporally available physical features, then remove stage features and physical features separately. | Use same split/budget as E2. No same-day ET0+Kc shortcut; forecast physical features need archived forecast vintages, not realized future weather. |
| E4 Uncertainty | Temporally separated calibration for prediction intervals; report empirical coverage and interval width. | Evaluate drift and dependence; no guaranteed per-farm probability or claimed coverage before testing. |
| E5 Separate crop-label benchmark | Crop_recommendation label classification: majority/dummy baseline, then modest models; stratified partitions if no groups can be recovered. | Conditional on rights/provenance; report macro-F1, balanced accuracy and confusion matrix, not CWR metrics. External regional validation required for suitability. |

For the 2018–2024 candidate series, a provisional chronology is 2018–2021 training, 2022 tuning, 2023 calibration and 2024 untouched testing, subject to actual crop-cycle availability. Keep shared weather dates/cycles together across crop-derived rows and embargo overlapping forecast windows. Fit imputers/encoders only on training data. If multiple sites are recovered, add held-out-site testing. Current anonymous data cannot support a location-generalization claim. Evaluate regression with MAE/RMSE in mm/day, R² and bias by crop/stage/year; use MAPE only with justified nonzero targets. Report actual post-filter sample counts later, not the raw 2,557 dates as crop-labelled samples now.

## Data risks / limitations and priorities

| Priority | Risk | Required resolution |
| --- | --- | --- |
| Blocking | No verified primary CWR labels | Recover climate metadata and crop cycles; derive versioned reference labels or obtain independent observations. |
| Blocking | No documented dataset reuse licence | Obtain owner/source URLs, licence, attribution and usage conditions per dataset; do not assume public-file status grants rights. |
| Blocking | Missing spatial keys and incompatible years | Recover original station/site metadata; create reviewed district boundary/alias mapping; acquire contemporaneous records. |
| High | Unverified water-label semantics | Resolve litres interval, area basis, measured vs generated origin and endpoint clipping. Exclude until justified. |
| High | Temperature anomalies in data_season | Recover original records; do not cap 222 to a plausible temperature and present it as corrected truth. |
| High | Rainfall metadata and no-data zeros | Check original bulletins/category definitions; quarantine bad period rows; preserve missingness, avoid double-counting cumulative totals. |
| High | Reference transferability | Kc/stage ranges depend on local practice and variety; preserve uncertainty and contradictory alternatives. |
| High | Target leakage and pseudo-replication | Split by time/cycle/site; distinguish simulated labels from independent observations; no random crop-expansion splits. |
| Medium | Panel/coverage and rounding | Treat missing district-year combinations, aggregate overlap and zero-area positive-production cases explicitly. |
| Medium | Header/encoding/placeholder issues | Preserve originals; later curated schema may normalize escaped line markers and typos with an explicit mapping. |
| Medium | Historical or short coverage | 2010–2017 crop data and 20 days of 2026 rainfall do not establish current farm suitability or robust long-term rain models. |

## Source verification notes

External checks were limited to methodological requirements and the workbook’s five reference links. They do not authenticate the remaining dataset origins or add observations to the audit. References checked on 29 September 2026:

- **[R1] FAO-56 Chapter 2:** https://www.fao.org/4/x0490e/x0490e06.htm — weather variables and site latitude/elevation requirements.
- **[R2] FAO-56 Chapter 6:** https://www.fao.org/4/X0490E/x0490e0b.htm — ETc = Kc × ET0 and context-specific stages/coefficients.
- **[R3] FAO Crop Water Needs:** https://www.fao.org/4/S2022E/s2022e07.htm — general crop-water reference; not evidence that the supplied calendar values are locally measured.
- **[R4] Thirumalesha et al. (2026):** https://link.springer.com/article/10.1007/s44288-026-00607-1 — article existence, Hemavathy context and CROPWAT methodology confirmed. Exact Kc table values were not independently resolved in this audit; workbook transcriptions remain subject to table-level checking.
- **[R5] Patil & Puttanna (2009), MAUSAM:** https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/1105 — abstract confirms ragi peak Kc 1.02 on day 66 for a specific Bangalore rainfed study. Its page displays inconsistent licence wording (CC BY-NC and CC BY statements); confirm applicable terms rather than assuming commercial reuse.
- **[R6] TNAU Ragi:** https://agritech.tnau.ac.in/agriculture/millets_ragi.html — accessible variety reference; does not supply the missing farm planting record.

## Appendix A — complete field inventory and measured quality

`object` means text or mixed storage; numeric-looking placeholder columns remain object. Nulls are pandas-recognized missing values. Placeholder count scans `-`, en/em dash, empty strings, NA/N/A/null/None and -999; in these files detected tokens are dashes or -999. It is additional to parser nulls, not a replacement for domain validation. Ranges are raw numeric minima/maxima and include invalid sentinels. Text values are enumerated when fewer than 100 distinct values; high-cardinality names are described in coverage sections. Header spelling and literal escape sequences are preserved.

### `Climate_Data.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| datetime | object | 0 | 0 | 2557 | 1/1/2018, 1/2/2018, 1/3/2018 (examples only) |
| DATE | int64 | 0 | 0 | 31 | 1.0 … 31.0 |
| MONTH | int64 | 0 | 0 | 12 | 1.0 … 12.0 |
| YEAR | int64 | 0 | 0 | 7 | 2018.0 … 2024.0 |
| T2M | float64 | 0 | 0 | 1284 | 13.49 … 36.7 |
| T2M_MIN | float64 | 0 | 0 | 1390 | 5.95 … 29.47 |
| T2M_MAX | float64 | 0 | 0 | 1316 | 21.44 … 45.18 |
| RH2M | float64 | 0 | 0 | 2125 | 14.79 … 94.51 |
| WS2M | float64 | 0 | 0 | 572 | 0.52 … 12.25 |
| PRECTOTCORR | float64 | 0 | 0 | 509 | 0.0 … 174.26 |
| ALLSKY_SFC_SW_DWN | float64 | 0 | 1 | 1365 | -999.0 … 28.92 |

### `Crop_Calender.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Crop | object | 0 | 0 | 5 | Chickpea, Cotton, Cumin, Groundnut, Wheat |
| Stage | object | 0 | 0 | 5 | Development, Initial, Late-season, Mid-season, Total season |
| Duration (days) | int64 | 0 | 0 | 14 | 10.0 … 195.0 |
| Root Depth (cm) | int64 | 0 | 0 | 13 | 20.0 … 150.0 |
| Kc (Crop Coefficient) | object | 1 | 4 | 15 | 0.3, 0.4, 0.42, 0.45, 0.5, 0.55, 0.7, 0.75, 0.8, 0.85, 0.97, 1.05, 1.15, 1.2, – |
| ETo (mm/day) | object | 0 | 5 | 14 | 2, 2.29, 2.5, 2.52, 3, 3.43, 3.5, 3.6, 4.5, 5, 5.5, 5.82, 6, – |
| ETc (mm/day) | float64 | 0 | 0 | 19 | 0.0 … 6.9 |
| Effective Rainfall (mm) | object | 0 | 20 | 5 | 248.94, 282.78, 295.32, 438.9, – |
| WHC (mm/m) | int64 | 0 | 0 | 1 | 125.0 … 125.0 |
| Unnamed: 9 | float64 | 25 | 0 | 0 | None … None |
| Unnamed: 10 | float64 | 25 | 0 | 0 | None … None |
| Unnamed: 11 | float64 | 25 | 0 | 0 | None … None |
| Unnamed: 12 | float64 | 25 | 0 | 0 | None … None |
| Unnamed: 13 | float64 | 25 | 0 | 0 | None … None |

### `Crop_recommendation.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| N | int64 | 0 | 0 | 137 | 0.0 … 140.0 |
| P | int64 | 0 | 0 | 117 | 5.0 … 145.0 |
| K | int64 | 0 | 0 | 73 | 5.0 … 205.0 |
| temperature | float64 | 0 | 0 | 2200 | 8.825674745 … 43.67549305 |
| humidity | float64 | 0 | 0 | 2200 | 14.25803981 … 99.98187601 |
| ph | float64 | 0 | 0 | 2200 | 3.504752314 … 9.93509073 |
| rainfall | float64 | 0 | 0 | 2200 | 20.21126747 … 298.5601175 |
| label | object | 0 | 0 | 22 | apple, banana, blackgram, chickpea, coconut, coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango, mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas, pomegranate, rice, watermelon |

### `Crops_data.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Dist Code | int64 | 0 | 0 | 311 | 1.0 … 917.0 |
| Year | int64 | 0 | 0 | 8 | 2010.0 … 2017.0 |
| State Code | int64 | 0 | 0 | 20 | 1.0 … 20.0 |
| State Name | object | 0 | 0 | 20 | Andhra Pradesh, Assam, Bihar, Chhattisgarh, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Orissa, Punjab, Rajasthan, Tamil Nadu, Telangana, Uttar Pradesh, Uttarakhand, West Bengal |
| Dist Name | object | 0 | 0 | 311 | Durg, Durg, Durg (examples only) |
| RICE AREA (1000 ha) | float64 | 0 | 0 | 1979 | 0.0 … 1154.23 |
| RICE PRODUCTION (1000 tons) | float64 | 0 | 0 | 2092 | 0.0 … 3215.01 |
| RICE YIELD (Kg per ha) | float64 | 0 | 0 | 2181 | 0.0 … 5653.83 |
| WHEAT AREA (1000 ha) | float64 | 0 | 0 | 1774 | 0.0 … 879.49 |
| WHEAT PRODUCTION (1000 tons) | float64 | 0 | 0 | 1887 | 0.0 … 4305.5 |
| WHEAT YIELD (Kg per ha) | float64 | 0 | 0 | 2012 | 0.0 … 5541.52 |
| KHARIF SORGHUM AREA (1000 ha) | float64 | 0 | 0 | 833 | 0.0 … 175.0 |
| KHARIF SORGHUM PRODUCTION (1000 tons) | float64 | 0 | 0 | 871 | 0.0 … 271.19 |
| KHARIF SORGHUM YIELD (Kg per ha) | float64 | 0 | 0 | 1212 | 0.0 … 3964.29 |
| RABI SORGHUM AREA (1000 ha) | float64 | 0 | 0 | 454 | 0.0 … 658.5 |
| RABI SORGHUM PRODUCTION (1000 tons) | float64 | 0 | 0 | 449 | 0.0 … 406.83 |
| RABI SORGHUM YIELD (Kg per ha) | float64 | 0 | 0 | 542 | 0.0 … 10000.0 |
| SORGHUM AREA (1000 ha) | float64 | 0 | 0 | 970 | 0.0 … 658.7 |
| SORGHUM PRODUCTION (1000 tons) | float64 | 0 | 0 | 974 | 0.0 … 442.46 |
| SORGHUM YIELD (Kg per ha) | float64 | 0 | 0 | 1337 | 0.0 … 5742.59 |
| PEARL MILLET AREA (1000 ha) | float64 | 0 | 0 | 911 | 0.0 … 945.07 |
| PEARL MILLET PRODUCTION (1000 tons) | float64 | 0 | 0 | 933 | 0.0 … 744.63 |
| PEARL MILLET YIELD (Kg per ha) | float64 | 0 | 0 | 1193 | 0.0 … 10000.0 |
| MAIZE AREA (1000 ha) | float64 | 0 | 0 | 1521 | 0.0 … 295.0 |
| MAIZE PRODUCTION (1000 tons) | float64 | 0 | 0 | 1720 | 0.0 … 1510.95 |
| MAIZE YIELD (Kg per ha) | float64 | 0 | 0 | 1975 | 0.0 … 21428.57 |
| FINGER MILLET AREA (1000 ha) | float64 | 0 | 0 | 422 | 0.0 … 180.84 |
| FINGER MILLET PRODUCTION (1000 tons) | float64 | 0 | 0 | 461 | 0.0 … 366.12 |
| FINGER MILLET YIELD (Kg per ha) | float64 | 0 | 0 | 640 | 0.0 … 4440.0 |
| BARLEY AREA (1000 ha) | float64 | 0 | 0 | 558 | 0.0 … 101.51 |
| BARLEY PRODUCTION (1000 tons) | float64 | 0 | 0 | 690 | 0.0 … 328.71 |
| BARLEY YIELD (Kg per ha) | float64 | 0 | 0 | 928 | 0.0 … 7119.97 |
| CHICKPEA AREA (1000 ha) | float64 | 0 | 0 | 1286 | 0.0 … 455.09 |
| CHICKPEA PRODUCTION (1000 tons) | float64 | 0 | 0 | 1316 | 0.0 … 395.05 |
| CHICKPEA YIELD (Kg per ha) | float64 | 0 | 0 | 1735 | 0.0 … 5000.0 |
| PIGEONPEA AREA (1000 ha) | float64 | 0 | 0 | 1096 | 0.0 … 480.89 |
| PIGEONPEA PRODUCTION (1000 tons) | float64 | 0 | 0 | 1025 | 0.0 … 618.53 |
| PIGEONPEA YIELD (Kg per ha) | float64 | 0 | 0 | 1650 | 0.0 … 3827.59 |
| MINOR PULSES AREA (1000 ha) | float64 | 0 | 0 | 1832 | 0.0 … 698.55 |
| MINOR PULSES PRODUCTION (1000 tons) | float64 | 0 | 0 | 1679 | 0.0 … 385.55 |
| MINOR PULSES YIELD (Kg per ha) | float64 | 0 | 0 | 2104 | 0.0 … 18888.89 |
| GROUNDNUT AREA (1000 ha) | float64 | 0 | 0 | 1047 | 0.0 … 834.07 |
| GROUNDNUT PRODUCTION (1000 tons) | float64 | 0 | 0 | 1140 | 0.0 … 1688.11 |
| GROUNDNUT YIELD (Kg per ha) | float64 | 0 | 0 | 1516 | 0.0 … 4313.05 |
| SESAMUM AREA (1000 ha) | float64 | 0 | 0 | 928 | 0.0 … 134.7 |
| SESAMUM PRODUCTION (1000 tons) | float64 | 0 | 0 | 636 | 0.0 … 71.33 |
| SESAMUM YIELD (Kg per ha) | float64 | 0 | 0 | 1534 | 0.0 … 6625.0 |
| RAPESEED AND MUSTARD AREA (1000 ha) | float64 | 0 | 0 | 1218 | 0.0 … 389.47 |
| RAPESEED AND MUSTARD PRODUCTION (1000 tons) | float64 | 0 | 0 | 1168 | 0.0 … 787.38 |
| RAPESEED AND MUSTARD YIELD (Kg per ha) | float64 | 0 | 0 | 1611 | 0.0 … 2714.29 |
| SAFFLOWER AREA (1000 ha) | float64 | 0 | 0 | 184 | 0.0 … 65.0 |
| SAFFLOWER PRODUCTION (1000 tons) | float64 | 0 | 0 | 160 | 0.0 … 35.1 |
| SAFFLOWER YIELD (Kg per ha) | float64 | 0 | 0 | 254 | 0.0 … 4166.67 |
| CASTOR AREA (1000 ha) | float64 | 0 | 0 | 376 | 0.0 … 234.89 |
| CASTOR PRODUCTION (1000 tons) | float64 | 0 | 0 | 330 | 0.0 … 450.33 |
| CASTOR YIELD (Kg per ha) | float64 | 0 | 0 | 552 | 0.0 … 3737.23 |
| LINSEED AREA (1000 ha) | float64 | 0 | 0 | 332 | 0.0 … 27.67 |
| LINSEED PRODUCTION (1000 tons) | float64 | 0 | 0 | 247 | 0.0 … 27.2 |
| LINSEED YIELD (Kg per ha) | float64 | 0 | 0 | 588 | 0.0 … 7000.0 |
| SUNFLOWER AREA (1000 ha) | float64 | 0 | 0 | 390 | 0.0 … 121.47 |
| SUNFLOWER PRODUCTION (1000 tons) | float64 | 0 | 0 | 390 | 0.0 … 83.14 |
| SUNFLOWER YIELD (Kg per ha) | float64 | 0 | 0 | 733 | 0.0 … 3029.41 |
| SOYABEAN AREA (1000 ha) | float64 | 0 | 0 | 701 | 0.0 … 529.6 |
| SOYABEAN PRODUCTION (1000 tons) | float64 | 0 | 0 | 720 | 0.0 … 940.8 |
| SOYABEAN YIELD (Kg per ha) | float64 | 0 | 0 | 859 | 0.0 … 3884.06 |
| OILSEEDS AREA (1000 ha) | float64 | 0 | 0 | 1490 | 0.0 … 858.6 |
| OILSEEDS PRODUCTION (1000 tons) | float64 | 0 | 0 | 1410 | 0.0 … 1712.92 |
| OILSEEDS YIELD (Kg per ha) | float64 | 0 | 0 | 1497 | 0.0 … 18147.8 |
| SUGARCANE AREA (1000 ha) | float64 | 0 | 0 | 1044 | 0.0 … 342.41 |
| SUGARCANE PRODUCTION (1000 tons) | float64 | 0 | 0 | 1481 | 0.0 … 3252.9 |
| SUGARCANE YIELD (Kg per ha) | float64 | 0 | 0 | 1736 | 0.0 … 22062.3 |
| COTTON AREA (1000 ha) | float64 | 0 | 0 | 902 | 0.0 … 800.89 |
| COTTON PRODUCTION (1000 tons) | float64 | 0 | 0 | 783 | 0.0 … 376.61 |
| COTTON YIELD (Kg per ha) | float64 | 0 | 0 | 1036 | 0.0 … 2857.74 |
| FRUITS AREA (1000 ha) | float64 | 0 | 0 | 1102 | 0.0 … 117.08 |
| VEGETABLES AREA (1000 ha) | float64 | 0 | 0 | 1402 | 0.0 … 191.83 |
| FRUITS AND VEGETABLES AREA (1000 ha) | float64 | 0 | 0 | 1543 | 0.0 … 240.99 |
| POTATOES AREA (1000 ha) | float64 | 0 | 0 | 832 | 0.0 … 111.61 |
| ONION AREA (1000 ha) | float64 | 0 | 0 | 501 | 0.0 … 131.35 |
| FODDER AREA (1000 ha) | float64 | 0 | 0 | 972 | 0.0 … 1162.66 |

### `Karnataka_Crop_Growth_Stage_Reference.xlsx` — `Growth_Stage_Reference`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Crop | object | 0 | 0 | 3 | Finger Millet (Ragi), Maize, Paddy (Rice) |
| Growth Stage | object | 0 | 0 | 8 | Development / Tillering, Development / Vegetative, Harvest, Initial / Establishment, Late-Season / Grain Development & Maturity, Late-Season / Maturity, Mid-Season / Flowering, Mid-Season / Flowering & Grain Development |
| Stage Description | object | 0 | 0 | 13 | Emergence and early establishment, Flowering and peak crop development, Full canopy, flowering and peak water demand, Germination and establishment, Grain development and maturation, Grain filling and maturity, Harvest/end of crop cycle, Panicle initiation through flowering/full canopy, Physiological maturity and senescence, Rapid leaf and canopy development, Tillering and rapid vegetative development, Transplanting/establishment and early canopy development, Vegetative growth and canopy expansion |
| Indicative Duration / Timing | object | 0 | 0 | 13 | 20 days (FAO indicative), 30 days (FAO indicative), 35 days (FAO indicative), 40 days (FAO indicative), Beginning of vegetative phase, Grain development ≈10–12 WAS; maturity ≈13–14 WAS, Reference window; verify locally, ≈0–6 weeks after sowing, ≈112–113 DAT in cited Indian field study, ≈14–34 DAT overlaps cited phenology, ≈27–65 DAT in cited Indian field study, ≈7–9 weeks after sowing, ≈97–101 DAT to maturity |
| Kc Reference | object | 0 | 0 | 13 | Interpolate from Kc_ini toward Kc_mid, Kc curve from initial toward mid-season, Kc increases from initial toward mid-season, Local Hemavathy study Kc_ini = 0.30, Local Kc_end = 0.30, Local Kc_end = 0.35; FAO typical = 0.70, Local Kc_ini = 0.30, Local Kc_mid = 1.00; Bangalore study peak ≈1.02 on day 66, Local Kc_mid = 1.20; FAO typical = 1.15, Terminal reference; harvest timing is variety-specific, Wet paddy Kc_end = 1.05, Wet paddy Kc_ini = 1.05–1.10; local Hemavathy study uses 1.10, Wet paddy Kc_mid = 1.20 |
| Kc Type | object | 0 | 0 | 6 | Interpolated, Kc_end, Kc_ini, Kc_mid, Kc_mid / peak, Terminal |
| Evidence Source | object | 0 | 0 | 7 | FAO-56 + Indian rice study, FAO-56 + Thirumalesha et al. (2026), Indian rice study, Thirumalesha et al. (2026), Thirumalesha et al. (2026) + FAO-56, Thirumalesha et al. (2026) + Indian ragi research, Thirumalesha et al. (2026); IMD MAUSAM |

### `Karnataka_Crop_Growth_Stage_Reference.xlsx` — `Sources`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Source | object | 0 | 0 | 5 | FAO Crop Water Needs, FAO-56 Chapter 6, Patil & Puttanna 2009, TNAU Ragi, Thirumalesha et al. 2026 |
| Supports | object | 0 | 0 | 5 | Bangalore finger-millet study; peak Kc ≈1.02 on day 66, Four general growth stages; Kc curve; ETc = ET0 × Kc, Four-stage crop-factor framework and crop-stage Kc examples, Karnataka/Hemavathy study: paddy, maize, ragi Kc references and CWR methodology, Variety-specific duration and flowering information |
| URL | object | 0 | 0 | 5 | https://agritech.tnau.ac.in/agriculture/millets_ragi.html, https://link.springer.com/article/10.1007/s44288-026-00607-1, https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/1105, https://www.fao.org/4/S2022E/s2022e07.htm, https://www.fao.org/4/X0490E/x0490e0b.htm |

### `Karnataka_Crop_Growth_Stage_Reference.xlsx` — `How_to_Use`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Item | object | 0 | 0 | 4 | For ML, For Ragi, For deployment, Important |
| Note | object | 0 | 0 | 4 | Do not invent daily CWR labels. Build/derive CWR targets using a documented FAO/CROPWAT or validated local methodology., Growth-stage duration varies by crop variety, planting date, climate and location. Treat the durations here as reference values, not universal labels., The local Karnataka study provides Kc_ini, Kc_mid and Kc_end; the development-stage Kc should be generated by a documented interpolation/curve method., Use live weather/rainfall APIs for current predictions; historical data is still required for model training and evaluation. |

### `Market_Wise_Price_Arrival_08-09-2026_08-43-27_AM.xlsx` — `Data_Report`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Commodity Group | object | 0 | 0 | 5 | Cereals, Fibre Crops, Oil Seeds, Pulses, Vegetables |
| Commodity | object | 0 | 0 | 19 | Bajra(Pearl Millet/Cumbu), Bengal Gram(Gram)(Whole), Black Gram(Urd Beans)(Whole), Copra, Cotton, Green Gram(Moong)(Whole), Groundnut, Jowar(Sorghum), Maize, Mustard, Onion, Paddy(Common), Ragi(Finger Millet), Red gram/Arhar/Tur(whole), Safflower, Sesamum(Sesame,Gingelly,Til), Soyabean, Sunflower/Sunflower Seed, Wheat |
| MSP (Rs./Quintal) 2026-27 | object | 0 | 1 | 19 | -, 12100, 2410, 2441, 2585, 2900, 4023, 5205, 5328, 5875, 6200, 6540, 7263, 7710, 7721, 7800, 8000, 8768, 9846 |
| Price on 06 Sep, 2026 | object | 0 | 9 | 11 | -, 20764.71, 2200, 2483, 2916.19, 4000, 5477.95, 6300, 6880, 7851, 7900 |
| Price on 05 Sep, 2026 | float64 | 0 | 0 | 19 | 2344.5 … 22188.18 |
| Price on 04 Sep, 2026 | object | 0 | 2 | 18 | -, 13554, 21703.66, 2480, 2599.71, 3099.6, 3200, 3381.96, 3454.21, 5200.02, 5551, 6931.58, 7068.63, 8054.77, 8082.54, 8127.32, 8177.79, 9454.74 |
| Arrival on 06 Sep, 2026 | object | 0 | 9 | 11 | -, 1.5, 101.9, 11, 124.9, 17, 25.4, 300.1, 38, 652.4, 91.3 |
| Arrival on 05 Sep, 2026 | float64 | 0 | 0 | 19 | 1.9 … 1555.1 |
| Arrival on 04 Sep, 2026 | object | 0 | 2 | 18 | -, 10, 1038.6, 15, 1841.1, 2, 222.1, 298.3, 59.9, 604.6, 695.8, 7.2, 72.8, 74.1, 827.1, 84.7, 9.9, 91.1 |

### `Rainfall_2016_districtwise.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Sl.No | object | 0 | 0 | 30 | 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 3, 30, 4, 5, 6, 7, 8, 9, STATE |
| Districts                     | object | 0 | 0 | 30 | BAGALKOT, BALLARI, BELAGAVI, BENGALURU(R), BIDAR, CHAMARAJANAGAR, CHIKKABALLAPURA, CHIKKAMAGALURU, CHITRADURGA, DAKSHINA KANNADA, DAVANAGERE, DHARAWAD, GADAG, HASSAN, HAVERI, KALABURAGI, KODAGU, KOLAR, KOPPAL, MANDYA, MYSURU, RAICHUR, RAMANAGARA, SHIVAMOGGA, TUMAKURU, Total, UDUPI, UTTARA KANNADA, VIJAYAPURA, YADGIRI |
| RaingaugeStations_Working  R,Gs | int64 | 0 | 0 | 22 | 15.0 … 1136.0 |
| RaingaugeStations_Not Working | int64 | 0 | 0 | 12 | 0.0 … 138.0 |
| Raingauge Stations_Total | int64 | 0 | 0 | 26 | 18.0 … 1274.0 |
| Annual Normal Rainfall_Rainydays | int64 | 0 | 0 | 22 | 34.0 … 129.0 |
| Normal Rainfall | int64 | 0 | 0 | 30 | 507.0 … 4285.0 |

### `Soil data.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| District | object | 0 | 0 | 101 | Yadgir, Yadgir, Yadgir (examples only) |
| Nitrogen Value | float64 | 0 | 0 | 499 | 20.0 … 66.959 |
| Phosphorous value | float64 | 0 | 0 | 817 | 20.045 … 80.0 |
| Potassium value | float64 | 0 | 0 | 837 | 22.91 … 80.0 |
| pH | float64 | 0 | 0 | 616 | 6.0503 … 9.031 |

### `crop_dataset.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| temperature_C | float64 | 0 | 0 | 1836 | 20.0 … 39.99 |
| humidity_% | float64 | 0 | 0 | 3445 | 30.0 … 89.97 |
| rainfall_mm | float64 | 0 | 0 | 3164 | 0.01 … 49.99 |
| water_required_liters | float64 | 0 | 0 | 2232 | 1.62 … 41.14 |

### `crop_water_data.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| crop_type | object | 0 | 0 | 7 | Cotton, Maize, Potato, Rice, Soybean, Sugarcane, Wheat |
| soil_type | object | 0 | 0 | 5 | Clay, Loamy, Peaty, Sandy, Silty |
| growth_stage | object | 0 | 0 | 5 | Flowering, Fruiting, Germination, Maturity, Vegetative |
| temperature | float64 | 0 | 0 | 351 | 10.0 … 45.0 |
| humidity | float64 | 0 | 0 | 751 | 20.0 … 95.0 |
| rainfall_mm | float64 | 0 | 0 | 501 | 0.0 … 50.0 |
| wind_speed_kmh | float64 | 0 | 0 | 401 | 0.0 … 40.0 |
| solar_radiation | float64 | 0 | 0 | 251 | 5.0 … 30.0 |
| field_area_ha | float64 | 0 | 0 | 4289 | 0.51 … 49.99 |
| irrigation_method | object | 0 | 0 | 4 | Drip, Flood, Furrow, Sprinkler |
| crop_age_days | int64 | 0 | 0 | 179 | 1.0 … 179.0 |
| soil_moisture_pct | float64 | 0 | 0 | 501 | 10.0 … 60.0 |
| evapotranspiration | float64 | 0 | 0 | 1400 | 1.0 … 15.0 |
| water_requirement_liters | float64 | 0 | 0 | 8967 | 1.0 … 5000.0 |

### `data_season.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| Year | int64 | 0 | 0 | 16 | 2004.0 … 2019.0 |
| Location | object | 0 | 0 | 11 | Bangalore, Chikmangaluru, Davangere, Gulbarga, Hassan, Kasaragodu, Kodagu, Madikeri, Mangalore, Mysuru, Raichur |
| Area | int64 | 0 | 0 | 156 | 1.0 … 52119.0 |
| Rainfall | float64 | 0 | 0 | 21 | 233.0 … 3729.8 |
| Temperature | float64 | 0 | 0 | 106 | 26.8 … 222.0 |
| Soil type | object | 58 | 0 | 27 | Alluvial, Arid and Desert, Black, Black cotton, Clay, Clay loam, Drained loam, Dry sandy , Gravelly sand, Heavy clay, Heavy cotton, Laterite, Light sandy, Loam, Medium textured , Medium textured clay, Red, Red , Red laterite, River basins, Sandy, Sandy clay loam, Sandy loam, Sandy loam , Teelah, Well drained, loamy sand |
| Irrigation | object | 0 | 0 | 3 | Basin, Drip, Spray |
| yeilds | float64 | 0 | 0 | 162 | 2.0 … 623687.0 |
| Humidity | float64 | 0 | 0 | 19 | 50.0 … 60.0 |
| Crops | object | 0 | 0 | 13 | Arecanut, Blackgram, Cardamum, Cashew, Cocoa, Coconut, Coffee, Cotton, Ginger, Groundnut, Paddy, Pepper, Tea |
| price | int64 | 0 | 0 | 24 | 637.0 … 249978.0 |
| Season | object | 0 | 0 | 3 | Kharif, Rabi, Zaid |

### `rainfall_districtwise_daily_imd.csv` — `CSV`

| Exact field | Inferred type | Nulls | Sentinels | Distinct non-null | Raw range / values |
| --- | --- | --- | --- | --- | --- |
| State | object | 0 | 0 | 39 | ANDAMAN & NICOBAR, ANDHRA PRADESH, ARUNACHAL PRADESH, ASSAM, BIHAR, CHANDIGARH, CHHATISGARH, CHHATTISGARH, DADRA & NAGAR HAVELI, DAMAN & DIU, GOA, GUJARAT, HARYANA, HIMACHAL PRADESH, JAMMU AND KASHMIR, JHARKHAND, KARNATAKA, KERALA, LADAKH, LAKSHADWEEP, MADHYA PRADESH, MAHARASHTRA, MANIPUR, MEGHALAYA, MIZORAM, NAGALAND, NCT of DELHI, ODISHA, PUDUCHERRY, PUNJAB, RAJASTHAN, SIKKIM, TAMIL NADU, TAMILNADU, TELANGANA, TRIPURA, UTTAR PRADESH, UTTARAKHAND, WEST BENGAL |
| District | object | 0 | 0 | 728 | NICOBAR, NICOBAR, NICOBAR (examples only) |
| Date | object | 0 | 0 | 20 | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-22, 2026-08-23, 2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30, 2026-08-31, 2026-09-01, 2026-09-02, 2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06, 2026-09-07 |
| Daily Actual | float64 | 0 | 0 | 658 | 0.0 … 145.7 |
| Daily Normal | float64 | 0 | 0 | 310 | 0.0 … 64.8 |
| Daily Departure Per | object | 182 | 0 | 859 | -94%, -94%, -76% (examples only) |
| Daily Category | object | 0 | 0 | 7 | D, E, LD, LE, N, ND, NR |
| Week Date | object | 0 | 0 | 14 | 01-01-2026 To 07-01-2026, 01-09-2026, 02-09-2026, 04-09-2026, 06-09-2026, 07-09-2026, 13-08-2026 To 19-08-2026, 20-08-2026, 20-08-2026 To 26-08-2026, 21-08-2026, 27-08-2026 To 02-09-2026, 28-08-2026, 29-08-2026, 30-08-2026 |
| Weekly  Actual | float64 | 0 | 0 | 1058 | 0.0 … 407.6 |
| Weekly Normal | float64 | 0 | 0 | 1035 | 0.0 … 255.6 |
| Weekly Departure Per | object | 138 | 0 | 527 | -94%, -61%, -61% (examples only) |
| Weekly Category | object | 0 | 0 | 7 | D, E, LD, LE, N, ND, NR |
| Cumulative Date | object | 0 | 0 | 1 | 2026-06-01 |
| Cumulative Actual | float64 | 0 | 0 | 6201 | 0.0 … 2955.1 |
| Cumulative Normal | float64 | 0 | 0 | 7523 | 6.3 … 3940.4 |
| Cumulative Departue Per | object | 100 | 0 | 222 | -37%, -38%, -37% (examples only) |
| Cumulative  Category | object | 0 | 0 | 6 | D, E, LD, LE, N, ND |
| Monthly Date | object | 0 | 0 | 21 | 01-05-2025 To 05-05-2025 , From 01-08-2026 To 19-08-2026 , From 01-08-2026 To 20-08-2026 , From 01-08-2026 To 21-08-2026 , From 01-08-2026 To 22-08-2026 , From 01-08-2026 To 23-08-2026 , From 01-08-2026 To 24-08-2026 , From 01-08-2026 To 25-08-2026 , From 01-08-2026 To 26-08-2026 , From 01-08-2026 To 27-08-2026 , From 01-08-2026 To 28-08-2026 , From 01-08-2026 To 29-08-2026 , From 01-08-2026 To 30-08-2026 , From 01-08-2026 To 31-08-2026 , From 01-09-2026 To 01-09-2026 , From 01-09-2026 To 02-09-2026 , From 01-09-2026 To 03-09-2026 , From 01-09-2026 To 04-09-2026 , From 01-09-2026 To 05-09-2026 , From 01-09-2026 To 06-09-2026 , From 01-09-2026 To 07-09-2026  |
| Monthly Acutual | float64 | 0 | 0 | 3899 | 0.0 … 928.3 |
| Monthly Normal | float64 | 0 | 0 | 4152 | 0.0 … 976.3 |
| Monthly  Departure Per | object | 105 | 0 | 575 | 31%, 24%, 18% (examples only) |
| Monthly Category | object | 0 | 0 | 7 | D, E, LD, LE, N, ND, NR |

## Appendix B — immutable source fingerprints

| File | SHA-256 |
| --- | --- |
| Climate_Data.csv | e2fec7864c867f9cc69194f9c27aa3e82a7e464c5806285d4e92bd2fd4d2383b |
| Crop_Calender.csv | d5925caa199f47b442063e7cb7c3cf85c6e6a0a8f5e37b62c35c45034ce67149 |
| Crop_recommendation.csv | 808e1d84a544647f1ab2fdae04f434b1842692d6be09eee18a5c2d43eb78d77c |
| Crops_data.csv | eb648adaa125395e62818ed88057b3b620401887696d62f4eb0ad0c6e4921b41 |
| Karnataka_Crop_Growth_Stage_Reference.xlsx | 8988617bbb5300ad4c348a50859fe4559333fabc3a8b7e4ae54e9b712b7bed41 |
| Market_Wise_Price_Arrival_08-09-2026_08-43-27_AM.xlsx | c2c7e4f80769e4881a0828ef73b49bc17a6a59f5fa6cb3e697013b03c9a4bd4a |
| Rainfall_2016_districtwise.csv | 97bbcff2e67f0328f6bc9bcf7622623bc73141d22469a40d8d57ba97becb7113 |
| Soil data.csv | 47fc7ac20cb571f6490d49000949fd60d166fb2918ac0c9da16d0455f042e944 |
| crop_dataset.csv | 5c41683eeafb9ba8743a2c5e48485f2f1af81812513bf0a2cb8eba3cec8f7531 |
| crop_water_data.csv | 05d00c5702a684bd167a760b15fecbf56938fe194e54ccb0aa23e4337cc0dc31 |
| data_season.csv | 57cdfccf559f1efa4d5898051c72a9627feea20d41bdad2b804d97d1ddeb493d |
| rainfall_districtwise_daily_imd.csv | 88936fffe4462a4c3d70c8ed4af2868d39bdc218f2287cc2166779e40b2fa722 |

## Completion record

Created: `docs/dataset_inventory.md`. Modified input files: none. Inspected: all 12 datasets and all 4 workbook sheets. Validation performed: complete row/column/null/duplicate profiling, key uniqueness, date coverage/components, selected physical/semantic checks, workbook structure/metadata and source-reference checks. Original ZIP member bytes matched the extracted copies on final validation. No application tests/builds apply because no application was created. No Phase 1 work was performed. **STOP — Phase 0 only.**
