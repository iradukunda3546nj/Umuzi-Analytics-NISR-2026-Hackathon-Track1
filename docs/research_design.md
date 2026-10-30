# Research Design - Umuzi Analytics

Written on 2026-10-29 **before** any district outcome relationship (yield ratios, persistence, input association) was computed. At the time of writing, only data structure, coverage counts and internal-consistency checks had been inspected (see `EXECUTION_LOG.md`, Stage C). Anything not listed here and reported later is labelled **exploratory**.

## Primary research question

Across Rwanda's 30 districts, which below-national crop yields **recur across matched NISR Seasonal Agricultural Survey (SAS) seasons** rather than appearing in a single season, and do these recurring shortfalls co-occur with low district uptake of improved seed and inorganic fertilizer?

## Data and unit of analysis

- Source: NISR SAS published district tables, releases 2024A, 2025A, 2026A (Season A) and 2024B, 2026B (Season B). 2025B was not located on the NISR website on 2026-10-29 and is treated as missing, not as zero.
- Unit: district x crop x season release (published district estimate). There is no farm-level or plot-level data in this project.
- These are **survey estimates**, not censuses. NISR publishes sampling errors only at national level (e.g. 2026A Table 5). District-level standard errors are not published, so district uncertainty is approximated through a coverage flag (harvested area) and through cross-season consistency, never through invented confidence intervals.

## Outcome definitions

| Estimand | Definition | Why |
|---|---|---|
| `yield_kg_ha` | NISR published average yield, kg per harvested ha | Productivity, the PSTA 5 headline metric |
| `yield_ratio` | district yield / national yield, **same crop, same season release** | Removes season-wide shocks that affect all districts (e.g. a poor national season), so the comparison is relative position, not absolute level |
| `below_national` | `yield_ratio < 0.90` | 10% tolerance absorbs part of district sampling noise; sensitivity tested at 0.80 and 0.95 |
| `persistent_shortfall` | below national in **every** available matched season of the same type (A with A, B with B), with at least 2 matched seasons | Separates recurring patterns from one-off dips |
| `thin_coverage` | harvested area < 500 ha in that district-crop-season | Small harvested area implies few sampled plots and less reliable district estimates; sensitivity tested at 200 and 1000 ha |

Season A and Season B are **never pooled or compared as if equivalent**: they differ in rainfall regime, crop mix and calendar.

## Pre-specified hypotheses

**H1 - Rank persistence.** For each priority crop (maize, bean, Irish potato, paddy rice, cassava, soybean, cooking banana, sweet potato), district `yield_ratio` in one Season A release is positively rank-correlated with the next Season A release (2024A to 2025A, 2025A to 2026A), and 2024B with 2026B.
Test: Spearman rho on districts with adequate coverage in both releases; two-sided permutation p-value (5,000 permutations); Holm correction across crop-pair tests. Minimum 12 districts per test, otherwise **not tested**.

**H2 - Persistence exceeds chance.** The number of district-crop pairs below national in all three Season A releases exceeds the number expected if each district's position were independent across seasons.
Test: permutation null shuffling district labels independently within each crop-release (2,000 permutations); report the observed count, null mean and one-sided p-value.

**H3 - Input association (association only).** In each release, district improved-seed uptake and inorganic-fertilizer uptake (percent of farmers, all crops pooled, SAS "Overall" column) are positively associated with the district maize `yield_ratio`, and separately with the bean `yield_ratio`.
Test: Spearman rho, n = 30, per release, with permutation p-values; Holm correction across the release x input x crop family.
Limitation stated in advance: inputs are **not crop-specific** in the published district tables, so this is an ecological association that cannot attribute yield to input use.

## Hypotheses marked NOT TESTABLE with the acquired data

- Rainfall anomaly effects on yields: no rainfall data was acquired and validated within the deadline (CHIRPS considered; not ingested).
- Soil health, farm-gate prices, credit access and extension contact at district level: not in the published SAS district tables.
- Causal effect of inputs on yield: observational district aggregates with n = 30 and unmeasured confounding (altitude, soils, rainfall, crop varieties).
- Within-district heterogeneity: district averages only.

## Confounders (DAG, described in text)

Agro-ecology (altitude, soil, rainfall) -> both input uptake (via profitability and programme targeting) and yield. Programme targeting (e.g. input subsidies concentrated in favourable zones) -> input uptake. Crop mix -> pooled input uptake. Sampling noise -> measured yield. Because these are not measured here, H3 can only describe co-occurrence, and the product uses it to **route a field question**, not to recommend an input allocation.

## Decision-rule design (pre-specified, see `docs/methodology.md`)

Each district-crop for a selected season type is placed in exactly one evidence category:

1. **Insufficient evidence - field verification required**: fewer than 2 matched seasons with adequate coverage, or thin coverage in the latest season.
2. **Persistent shortfall, low input uptake**: persistent shortfall and latest improved-seed and inorganic-fertilizer uptake both below the national value.
3. **Persistent shortfall, inputs at or above national**: persistent shortfall but at least one of the two input uptakes at or above national. The constraint is less likely to be input access alone; investigate soils, erosion, varieties and water.
4. **Latest-season dip**: below national in the latest season only. Monitor; check for a season-specific shock before acting.
5. **Not below national**: no shortfall in the latest season.

These are investigation routes, not prescriptions.

## Multiple testing and reporting

All tests in H1-H3 are reported, including null results. p-values are reported with effect sizes, and statistical significance is not equated with practical importance. With n <= 30 districts, rank correlations below about 0.36 in absolute value cannot reach nominal significance, so a non-significant result is weak evidence of absence.
