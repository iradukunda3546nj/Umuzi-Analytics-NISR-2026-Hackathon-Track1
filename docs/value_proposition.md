# Value Proposition

## 1. Job to be done

When a **district agronomist or Director of Agriculture (with MINAGRI/RAB planning staff)** must decide **which district-crop combinations get field diagnosis and extension attention before the next Season A or B**, they currently struggle to **tell a persistent yield shortfall from a one-season dip, and to see whether a shortfall coincides with low input uptake**. The evidence exists only as one-season-per-file NISR tables of about 27 crops by 30 districts per indicator.

## 2. Differentiation matrix

| Approach | Grounded strengths | Limits for this decision | How Umuzi Analytics differs |
|---|---|---|---|
| NISR SAS reports and Excel tables (verified: inspected 5 releases) | Official, design-based, district grain, free (CC BY 4.0) | One season per file; tables renumber between releases; no cross-season view; zeros mixed with "not grown" | Harmonises releases by title, separates "not reported" from zero, compares matched seasons, keeps the cell-level source |
| Smart Nkunganire System (verified: MINAGRI news item, ILRI note) | Operational input registration and subsidy delivery to farmers | Allocates inputs; does not assess where yields fall short or why | Identifies where input access is *not* the likely first constraint, so attention is not spent only on inputs |
| PSTA 5 results framework (verified: abridged plan p.21) | Clear national yield targets | National only; no district view | Shows the national gap, then the districts where it recurs |
| Spreadsheet comparison by a district officer (plausible incumbent; not verified with users) | Flexible, familiar | Error-prone, one crop at a time, no persistence logic, no audit trail | Same comparison in seconds, with fixed rules, thresholds you can adjust and an exportable brief |

No verified public tool was found that combines persistence classification, input context and source traceability for SAS district data. That is a search result, not a proof that none exists.

## 3. Value proposition

**Umuzi Analytics helps district agronomists and MINAGRI/RAB planners decide which district-crop yield gaps to diagnose in the field first, by classifying every district for a chosen crop and season from all matched NISR Seasonal Agricultural Survey releases, as a persistent shortfall, a one-season dip or insufficient evidence, alongside district input uptake. A field visit can then target recurring problems and the right constraint, unlike the current single-season tables that make one bad season and a structural gap look the same.**

## 4. Signature insight and interaction

**Signature insight (computed, 2026A snapshot).** For maize in Season A, 12 districts sit below 0.9 x national in all three releases (2024A, 2025A, 2026A). In **9 of those 12, input uptake is not low**. Six of them, five in Western Province (Ngororero, Rutsiro, Karongi, Nyabihu, Nyamasheke) plus Nyamagabe in Southern Province, combine above-national inorganic-fertilizer uptake (72.1% to 84.1% of farmers vs 67.2% nationally) with below-national improved-seed uptake (15.0% to 30.8% vs 37.0%). Only 3 (Gicumbi, Ruhango, Nyarugenge) combine a persistent shortfall with both inputs below national. A planner reading one season, or reading yields without input context, would treat all 12 the same way.

**Signature interaction.** Choose a crop and season, then a district. The evidence panel states the category, the persistence count, coverage, input context and a next step, and the Evidence Brief exports field-check questions and limits with the snapshot ID.

## 5. Evidence-to-action chain

1. **Observed indicators**: district and national yield per release; harvested area; farmer input uptake (NISR SAS).
2. **Interpretation**: yield ratio to national in the same release; persistence across matched seasons; coverage flag.
3. **Constraints and uncertainty**: farmer-reported yields; no district standard errors; inputs pooled across crops; possible sample overlap across seasons; agro-ecological suitability not modelled.
4. **Planning options**: input-access check (persistent and low inputs); constraint diagnosis for soils, erosion, varieties or water (persistent, inputs not low); monitor (dip); verify first (insufficient).
5. **Field verification**: category-specific questions in the brief.

## 6. Success metrics (defined; not yet measured)

| Metric | Baseline method | Target for a pilot |
|---|---|---|
| Time for a planner to list persistent maize Season A shortfall districts | Timed task with the NISR Excel files (3 releases) | At least 5x faster with the app; verified by observation |
| Share of brief statements traceable to a source cell | Audit 10 briefs against workbooks | 100% |
| Correct pairwise comparison (same crop, season, coverage) | Task with planted invalid comparisons | Planner detects the invalid case from the app warning |
| Unsupported claims shown | Review of all views | 0; "insufficient evidence" shown instead |
| Field confirmation | Agronomist visits to 5 flagged district-crop pairs | Category judged plausible in at least 3 of 5 |

## 7. Scope boundary

The MVP does **not**: predict yields; estimate the effect of inputs or any intervention; recommend input quantities; diagnose soils; rank districts for funding; assess sector or household variation; judge whether a crop suits a district; or update automatically from NISR. It routes attention and states what to verify.

## One-page proof of value

- **Before**: open 3 workbooks, find the yield table in each (Table 11, 12 or 13 depending on the release), copy 30 districts for one crop, compute ratios, compare by hand, then find the seed and fertilizer tables (also renumbered) and compare again. Zeros must be told apart from missing cells manually.
- **With the app**: select crop and season; the classification, map, persistence chart, input context and brief come from one validated snapshot. Every number carries its release and snapshot ID.
- **Exact evidence**: `reports/analysis_results.json`; tests in `tests/test_real_data.py` trace values to workbook cells.
- **Still unknown**: whether planners find the categories useful; whether flagged constraints hold in the field; how much time is actually saved (not measured).
- **Credible pilot**: `docs/field_validation_plan.md`.
