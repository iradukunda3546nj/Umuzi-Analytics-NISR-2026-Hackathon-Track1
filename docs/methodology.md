# Methodology

## 1. Pipeline

`NISR workbook -> title-based adapter (src/ingestion/sas_adapter.py) -> schema and quality gates (src/validation/gates.py) -> candidate snapshot (src/services/snapshot_store.py) -> approval -> ACTIVE snapshot -> indicators and evidence rules (src/analytics/indicators.py) -> Finding (src/decisions/finding.py) -> map panel and charts (app.py, src/viz/), evidence brief (src/decisions/brief.py), Umuzi Assistant (src/assistant/umuzi.py)`.

The app, assistant, analysis scripts, brief and tests all call the same functions on the same snapshot. The map panel, the brief and the assistant print the same Finding; `tests/test_assistant.py` checks that the assistant and the map agree for every district, six crops and both seasons.

The snapshot holds 17 surveys, 2018 A to 2026 B (2025 B not published). `data/sources.json` records, per survey, the source file, any sheet override and whether its input tables are comparable. `scripts/history_eda.py` documents why 2014-2017 are not used: those years publish yields only by land-use stratum or province.

## 2. Comparison basis

Every district comparison holds **crop, season type and release** fixed. The district yield is divided by the national yield of the same crop in the same release (`yield_ratio`). This cancels season-wide shocks (a poor national season lowers everyone) and makes releases comparable without assuming yields are stationary. Season A and Season B are analysed separately; the observed A-B district correlation for maize in 2026 is only 0.24.

## 3. Evidence categories (decision rules, ruleset `evidence-rules-2.0`)

For a chosen crop and season type, using the **last 3 releases of that type** (the window). A release counts only if it is *reliable*: yield reported and harvested area of at least 500 ha.

| Step | Rule | Category |
|---|---|---|
| 1 | Latest release not reliable | Evidence too limited to judge |
| 2 | Latest ratio >= 0.90 | Not below national |
| 3 | Latest below, but fewer than 2 reliable releases in the window | Evidence too limited to judge |
| 4 | Below in at least 2 reliable releases of the window, and district improved-seed and inorganic-fertilizer uptake both below national (latest release) | Repeatedly below national, low input uptake |
| 5 | Same, with at least one input at or above national | Repeatedly below national, input uptake not low |
| 4/5 | Repeatedly below but an input value missing (for example 2018) | Evidence too limited to judge (unknown is never treated as "not low") |
| 6 | Below in the latest release only | Below national in the latest season only |

**Why a 3-release window (change from rules 1.0).** Rules 1.0 required a district to be below in *every* reliable release. With five releases that was reasonable; with nine Season A releases it is too strict, and the older releases are less comparable: median rank agreement of district ratios between consecutive Season A releases is 0.29 (2018 to 2019) and 0.39 (2019 to 2020), against 0.64 to 0.92 since 2020. In the backtest (section 7), rule 1.0 caught 40% of next-season shortfalls on 2024-2026; "at least 2 of the last 3" caught 81% with similar precision, and still means *repeatedly*, not one season.

**Threshold provenance.** 0.90 is a 10% tolerance chosen before the analysis to absorb part of the unpublished district sampling error; 500 ha is about the median harvested area of observed district-crop cells (906 ha), so it excludes the thinnest third. Neither threshold comes from an agronomic standard. Both are adjustable in the app, and their influence is reported (`reports/eda_findings.md`, Part 3).

**Routes, not prescriptions.** Each category maps to an investigation route (`CATEGORY_ACTION` in `indicators.py`). No category recommends an input quantity, budget or intervention effect.

## 4. Statistical tests (pre-specified before any district outcome was computed; the research design file is in the git history)

- H1: Spearman rank correlation between consecutive matched releases; two-sided permutation p-value (5,000 permutations, vectorised on ranks); Holm correction over all tested crop-pairs; minimum n = 12.
- H2: count of district-crop pairs below threshold in all three Season A releases; null distribution from 2,000 independent within-release shuffles of district positions.
- H3: Spearman correlation between district input uptake and yield ratio, per release; permutation p-values; Holm correction over 20 tests.
- Random seed 20261029; results in `reports/analysis_results.json`.

Survey weights are applied by NISR in the published estimates; this project does not re-weight. Districts are treated as units of description, not as a random sample, so p-values are best read as "would this pattern arise if district positions were arbitrary?"

## 5. National target comparison

National yield for SAS year Y = (Season A production + Season B production) / (Season A harvested area + Season B harvested area), computed only when both seasons are present. It is compared with the PSTA 5 target for agricultural year (Y-1)/Y. Season C is excluded because it is not in the ingested releases.

## 6. Missing and zero values

A cell NISR printed as 0 or left blank is stored with `value_status` `reported_zero` or `blank` and an empty value. It never enters a ratio, mean or chart as 0. The app shows "not reported".

## 7. Model or rules: the backtest (`scripts/backtest.py`)

Task: predict whether a district will be below national (ratio < 0.90) in the next reliable release of the same season, using only earlier releases. Candidates: five counting rules over the previous 3 releases or all history, and an L2-regularised logistic regression (last ratio, mean and share below over the window, number of reliable releases, log harvested area, pooled seed and fertilizer gaps). The model is refit for every target release on earlier targets only. Selection period: targets 2021-2023; held-out test: 2024 A, 2025 A, 2026 A, 2024 B, 2026 B (754 cases).

Adoption criterion, fixed in advance: the model replaces the rules only if its Brier score is lower than the best rule's with a 95% district-cluster bootstrap interval excluding zero **and** balanced accuracy improves by at least 0.02. Result: balanced accuracy 0.867 (model) vs 0.868 ("below in the previous release"), difference interval -0.019 to +0.015; Brier 0.093 vs 0.111. The model is better calibrated but flags the same districts, so the rules were kept (`reports/backtest_results.json`).
