# Analytical Methods: model tested, rules kept

## The decision, driven by the data

With the 2018-2026 history (9 Season A and 8 Season B releases), a forecasting task can be tested honestly: will a district be below 90% of the national yield in the next release of the same season, using only earlier releases?

| Step | Finding | Source |
|---|---|---|
| Usable history | District x crop x season yields exist from 2018 only; 2014-2017 are by stratum or province | `reports/history_eda.json`, `source_audit` |
| Comparability | Consecutive Season A rank agreement 0.29 and 0.39 for 2018-2020, 0.64 to 0.92 since | `rank_agreement` |
| Predictors available | Past yield ratios; district input uptake pooled over all crops (2019 onward); no validated district rainfall or soil series | `input_basis` |
| Backtest, held-out 2024-2026 (754 cases) | Logistic model balanced accuracy 0.867, best rule 0.868; 95% interval of the difference -0.019 to +0.015 | `reports/backtest_results.json` |
| Calibration | Model Brier 0.093 vs 0.111 for the best rule | same |

The pre-stated criterion required a lower Brier score (interval excluding zero) **and** at least +0.02 balanced accuracy. The model met the first and not the second: it estimates probabilities better but flags the same districts. For a planner deciding where to send a field check, it adds complexity and apparent authority without changing the decision, so **the rules were kept**.

The backtest also tested the rules themselves. "Below in every release" (rules 1.0) caught 40% of next-season shortfalls once nine years were available; "below in at least 2 of the last 3" caught 81% with similar precision. That is rules 2.0.

## Methods used

- Descriptive estimands on published estimates (ratios to the same-release national yield, counts over a 3-release window).
- Permutation tests (Spearman, persistence count) with Holm correction, pre-specified on 2024-2026 (`docs/methodology.md`, section 4).
- Deterministic, versioned decision rules (`evidence-rules-2.0`), with sensitivity analysis over thresholds.
- Expanding-window backtest with a district-cluster bootstrap (`scripts/backtest.py`).

## Governance of the rule set

- The ruleset version is recorded in every snapshot manifest; thresholds are named settings in `src/config.py`.
- A release lacking a metric the rules require is rejected before it can reach the app (`tests/test_pipeline.py`), unless its entry in `data/sources.json` documents that the metric is not comparable (2018 inputs).
- Threshold changes in the app are labelled as non-default and do not alter the stored snapshot.
- The Umuzi Assistant answers only through the same rules (`src/assistant/umuzi.py`); `tests/test_assistant.py` checks agreement with the map.

## When to revisit

Re-run `python -m scripts.backtest` after each new release. A model would be worth adopting if it clears the criterion above, or if validated district rainfall or soil series become available as predictors.
