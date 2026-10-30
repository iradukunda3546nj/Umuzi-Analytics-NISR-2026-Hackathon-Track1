# Analytical Methods (no ML model card: no predictive model is used)

## Decision: predictive ML deliberately omitted

| Consideration | Finding |
|---|---|
| Time points per district-crop | 3 (Season A) or 2 (Season B) |
| Honest out-of-sample test | A time-aware split leaves 1 to 2 training seasons; an evaluation would be anecdotal |
| Baseline | Persistence (last season's ratio) is already very strong: H1 rank correlations are 0.78 to 0.99 for most crops, so a model would be unlikely to beat it measurably on this data |
| Covariates | No validated rainfall or soil data joined at district-season level |
| Decision need | The planner needs to know where gaps recur and what to check, not a point forecast |

A model would add complexity and apparent authority without measurable value. The tool's value comes from harmonisation, persistence classification, input context and traceability.

## Methods used

- Descriptive estimands on published estimates (ratios, ranges, counts).
- Permutation tests (Spearman, persistence count) with Holm correction (`docs/methodology.md`, section 4).
- Deterministic, versioned decision rules (`evidence-rules-1.0`), with sensitivity analysis over thresholds.

## Governance analogue

Because there is no model, "model governance" applies to the rule set:
- The ruleset version is recorded in every snapshot manifest.
- A release lacking a metric the rules require (for example inorganic-fertilizer uptake) is rejected before it can reach the app (`tests/test_pipeline.py::test_release_incompatible_with_decision_rules_is_blocked`).
- Threshold changes in the app are labelled as non-default and do not alter the stored snapshot.

## When ML would become justified

With 6 or more seasons per type, validated district rainfall anomalies, and a stated forecasting need (for example pre-harvest food-balance planning), a regularised panel model could be tested against the persistence baseline with season-ahead splits.
