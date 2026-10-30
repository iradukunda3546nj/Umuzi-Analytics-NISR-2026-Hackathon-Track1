# Methodology

## 1. Pipeline

`NISR workbook -> title-based adapter (src/ingestion/sas_adapter.py) -> schema and quality gates (src/validation/gates.py) -> candidate snapshot (src/services/snapshot_store.py) -> approval -> ACTIVE snapshot -> indicators and evidence rules (src/analytics/indicators.py) -> charts (src/viz/charts.py), brief (src/decisions/brief.py), app (app.py)`.

The app, analysis script, brief and tests all call the same functions on the same snapshot.

## 2. Comparison basis

Every district comparison holds **crop, season type and release** fixed. The district yield is divided by the national yield of the same crop in the same release (`yield_ratio`). This cancels season-wide shocks (a poor national season lowers everyone) and makes releases comparable without assuming yields are stationary. Season A and Season B are analysed separately; the observed A-B district correlation for maize in 2026 is only 0.24.

## 3. Evidence categories (decision rules, ruleset `evidence-rules-1.0`)

For a chosen crop and season type, with the releases of that type in the snapshot:

| Step | Rule | Category |
|---|---|---|
| 1 | Latest release not adequate (yield not reported, or harvested area < 500 ha) | Insufficient evidence - field verification required |
| 2 | Latest ratio >= 0.90 | Not below national |
| 3 | Latest below, but fewer than 2 adequate releases | Insufficient evidence - field verification required |
| 4 | Below in every adequate release, and district improved-seed and inorganic-fertilizer uptake both below national (latest release) | Persistent shortfall, low input uptake |
| 5 | Below in every adequate release, at least one input at or above national | Persistent shortfall, inputs at or above national |
| 4/5 | Persistent but any input value missing | Insufficient evidence (unknown is never treated as "not low") |
| 6 | Below in the latest release but not in every adequate release | Latest-season dip |

**Threshold provenance.** 0.90 is a 10% tolerance chosen before the analysis to absorb part of the unpublished district sampling error; 500 ha is about the median harvested area of observed district-crop cells (906 ha), so it excludes the thinnest third. Neither threshold comes from an agronomic standard. Both are adjustable in the app, and their influence is reported (`reports/eda_findings.md`, Part 3).

**Routes, not prescriptions.** Each category maps to an investigation route (`CATEGORY_ACTION` in `indicators.py`). No category recommends an input quantity, budget or intervention effect.

## 4. Statistical tests (pre-specified in `docs/research_design.md`)

- H1: Spearman rank correlation between consecutive matched releases; two-sided permutation p-value (5,000 permutations, vectorised on ranks); Holm correction over all tested crop-pairs; minimum n = 12.
- H2: count of district-crop pairs below threshold in all three Season A releases; null distribution from 2,000 independent within-release shuffles of district positions.
- H3: Spearman correlation between district input uptake and yield ratio, per release; permutation p-values; Holm correction over 20 tests.
- Random seed 20261029; results in `reports/analysis_results.json`.

Survey weights are applied by NISR in the published estimates; this project does not re-weight. Districts are treated as units of description, not as a random sample, so p-values are best read as "would this pattern arise if district positions were arbitrary?"

## 5. National target comparison

National yield for SAS year Y = (Season A production + Season B production) / (Season A harvested area + Season B harvested area), computed only when both seasons are present. It is compared with the PSTA 5 target for agricultural year (Y-1)/Y. Season C is excluded because it is not in the ingested releases.

## 6. Missing and zero values

A cell NISR printed as 0 or left blank is stored with `value_status` `reported_zero` or `blank` and an empty value. It never enters a ratio, mean or chart as 0. The app shows "not reported".

## 7. Why there is no predictive model

See `reports/analytical_methods.md`.
