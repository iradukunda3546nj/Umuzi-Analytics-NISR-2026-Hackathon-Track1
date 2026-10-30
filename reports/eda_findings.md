# EDA Findings and Visual Evidence Report

Snapshot `snap-20261029T103445Z-e435e56c` (releases SAS-2024A, 2024B, 2025A, 2026A, 2026B). All numbers are reproduced by `python -m scripts.run_analysis` (output `reports/analysis_results.json`, log `reports/analysis_run_log.txt`). Interactive figures are in `reports/figures/` and in the app, built by the same functions in `src/viz/charts.py`.

Pre-specified tests are labelled **[H1] [H2] [H3]**; anything else is **[exploratory]**.

## Part 1. Data-quality diagnostic

| Check | Result |
|---|---|
| Districts per release | 30 plus national in every release and table |
| Table location | Found by title in all 5 releases although sheet numbers differ (yield table: 11, 10, 12, 13, 11) |
| Internal consistency | Production = yield x harvested area / 1000 in 2,587 of 2,587 fully observed cells (within 2%) |
| Cross-publication consistency | Standalone 2024A and 2024B releases equal the 2024 Annual workbook cell for cell (max difference 0.0) |
| Published zeros | 198 / 125 / 225 / 165 / 138 cells (2024A / 2024B / 2025A / 2026A / 2026B), treated as "not reported" |
| Harvested > cultivated | 5 / 22 / 11 / 0 / 0 cells, mostly bananas; flagged, not corrected |
| National row labels | "National", "Total", "S/Total" vary by table; a gate rejects any release missing a national value |
| Thin coverage | 34% of observed district yields rest on under 500 ha harvested; 19% on under 200 ha |
| Publication inconsistency | 2026A Table 5, Fruits: estimate 8,183 ha outside its own 95% CI (9,050 to 17,975) |
| Missing release | 2025 Season B not found on the NISR site at retrieval |

Two pipeline defects were found and fixed during this diagnostic (documented in `EXECUTION_LOG.md`). The national fertilizer row labelled "Total" was first dropped, which silently classified every district as "inputs at or above national". The fix added a gate so a missing national reference now blocks publication.

## Part 2. Findings (story arc)

### A. Size of the challenge: national yields are below the PSTA 5 trajectory
- **Question.** Is national productivity on track for the PSTA 5 targets that SAS is meant to measure?
- **Evidence.** National Season A+B yield in SAS 2026 (agricultural year 2025/26) against the 2025/26 target: soybean 0.47 vs 0.9 t/ha (52%), bean 0.72 vs 0.9 (79%), Irish potato 7.95 vs 10.1 (79%), maize 1.80 vs 2.06 (87%), cassava 13.86 vs 15.7 (88%), wheat 1.21 vs 1.3 (93%), cooking banana 15.72 vs 17.1 (92%), paddy rice 4.36 vs 4.5 (97%).
- **Pattern.** All 8 priority crops are below their 2025/26 target. Season A maize yield was 2.04, 1.99 and 1.99 t/ha in 2024A, 2025A and 2026A: flat, not rising.
- **Implication.** Closing the national gap depends on where it is concentrated. That is the district question below.
- **Alternative explanation / uncertainty.** The A+B aggregation excludes Season C. PSTA 5 does not state its exact aggregation in the abridged plan, so the attainment percentages are approximate. National estimates have small sampling errors (e.g. maize area CV 2.5% in 2026A), but yields are farmer-estimated.
- Figure: `figures/national_target_attainment.html` (app: Overview).

### B. Where it concentrates: shortfalls recur in the same districts [H1, H2]
- **Question.** Are below-national district yields stable across seasons, or do they reshuffle?
- **Evidence [H1].** Spearman correlation of district yield ratios between consecutive matched releases: maize 0.90 and 0.96 (Season A), 0.87 (B); bean 0.95 and 0.96 (A), 0.91 (B); Irish potato 0.97 and 0.99 (A), 0.95 (B); cassava 0.78 and 0.85 (A), 0.88 (B); soybean 0.96 and 0.81 (A), 0.70 (B); cooking banana 0.98 and 0.97 (A), 0.85 (B); sweet potato 0.89 and 0.95 (A), 0.92 (B). All 21 tested pairs: Holm-adjusted p = 0.004 (5,000 permutations). Paddy rice not tested (11 districts with adequate coverage).
- **Evidence [H2].** 60 district-crop pairs are below 0.9 x national in all three Season A releases, against a permutation-null mean of 16.9 (95th percentile 21); one-sided p = 0.0005 (2,000 permutations).
- **Pattern.** The median spread of a district's maize Season A position across three releases is 0.06 x national. District rankings are very stable.
- **Implication.** A district that is low this season was almost always low before, so a single-season table understates how structural the gap is.
- **Uncertainty.** High stability may partly reflect sample design: the report does not say whether the same segments are revisited across seasons. This is consistency of published estimates, not independent replication.
- Figures: `figures/persistence_maize_A.html`, `figures/map_maize_A.html` (app: Persistence, Evidence Map).

### C. How patterns differ: season and crop matter [exploratory]
- In 2026 the Spearman correlation between a district's maize position in Season A and in Season B is 0.24. A district's standing in one season says little about the other, which is why seasons are never pooled.
- Season A: 10 districts have persistent shortfalls in three or more of the 9 priority crops (Gasabo, Gisagara, Karongi, Kayonza, Ngororero, Nyamagabe, Nyamasheke, Nyanza, Ruhango, Rwamagana). Season B: 6 (Bugesera, Kamonyi, Kayonza, Muhanga, Ruhango, Rwamagana). Ruhango, Kayonza and Rwamagana appear in both.
- Persistent Irish potato shortfalls are concentrated in Eastern Province lowland districts (Kayonza, Ngoma, Kirehe, Gatsibo, Nyagatare), where the crop is a minor, agro-ecologically marginal one. A relative gap there is not evidence of a fixable gap. The brief's field questions ask about variety and site suitability for this reason.
- Figure: `figures/triage_matrix_season_A.html` (app: Triage Matrix).

### D. What correlates with shortfalls: input uptake gives a mixed, crop-specific signal [H3]
- **Evidence [H3]** (Spearman, district input uptake for all crops vs crop yield ratio, n = 27 to 30, Holm-adjusted across 20 tests):
  - Bean vs inorganic fertilizer: rho 0.67 to 0.74 in all 5 releases, adjusted p = 0.004 each.
  - Bean vs improved seed: rho -0.24 to -0.40; none significant after adjustment.
  - Maize vs improved seed: rho 0.24 to 0.47; nominal p as low as 0.009 (2026A), none significant after adjustment.
  - Maize vs inorganic fertilizer: rho 0.12 to 0.41; none significant after adjustment.
- **Pattern (signature).** Of the 12 persistent maize Season A shortfall districts, 9 do not have low input uptake. Five Western Province districts plus Nyamagabe combine fertilizer uptake of 72.1% to 84.1% of farmers (national 67.2%) with improved-seed uptake of 15.0% to 30.8% (national 37.0%). Only Gicumbi, Ruhango and Nyarugenge have both inputs below national.
- **Implication.** For most persistent maize shortfalls, "more inputs" is not the obvious first response. Seed and variety suitability, soil acidity, erosion and altitude are the field questions.
- **Uncertainty.** Input uptake is pooled over all crops; the bean-fertilizer association may reflect agro-ecology or programme targeting (confounding) rather than any effect of fertilizer on beans.
- Figure: `figures/inputs_maize_A.html` (app: Input Context).

### E. What a planner should do next
Category counts (default thresholds): maize Season A, 3 persistent with low inputs, 9 persistent with inputs not low, 3 latest-season dips, 15 not below. Bean Season A: 3 / 7 / 2 / 18. Maize Season B: 4 / 8 / 1 dip, 3 insufficient, 14 not below. Each category maps to an investigation route (`docs/methodology.md`).

## Part 3. Sensitivity of the classification

| Crop, season | Coverage 200 / 500 / 1000 ha (gap 0.90): agreement with default | Gap 0.80 / 0.95 (500 ha): agreement |
|---|---|---|
| Maize A | 1.00 / 1.00 / 0.97 | 0.63 / 0.77 |
| Bean A | 1.00 / 1.00 / 1.00 | 0.77 / 0.93 |
| Irish potato A | 0.77 / 1.00 / 0.90 | 0.90 / 1.00 |
| Maize B | 0.90 / 1.00 / 0.83 | 0.70 / 0.83 |

Classification is robust to the coverage threshold for maize and bean and **sensitive to the gap threshold**, mainly at the boundary between "not below" and "persistent". The app exposes both thresholds and labels non-default results.

## What the data revealed that a planner would otherwise miss

District maize and bean shortfalls are not a reshuffling lottery. They recur in the same districts. Most recurring maize shortfalls occur where fertilizer uptake is already above national and improved-seed uptake is low, which is a different field question from input access.
