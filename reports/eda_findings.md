# What the data showed

This report records what we found when exploring the NISR survey data, in the order the work was done.
Part 0 covers the full 2018-2026 history and the rules the app uses today. Parts 1 to 4 are the first
analysis, done on the five 2024-2026 surveys with the first version of the rules, kept unchanged as the
record of that analysis (its tests were written down before the results were seen).

How to read the statistics:

- **Rank agreement** (Spearman correlation): 1 means districts keep exactly the same order from one survey
  to the next, 0 means the order is unrelated.
- **p-value**: how often a result at least this strong would appear if district positions were shuffled
  at random. Small means "unlikely to be chance".
- **Holm correction**: an adjustment that makes p-values stricter when many tests are run at once.

## Part 0. Full history, 2018-2026 (the data the app uses)

Snapshot `snap-20261125T044618Z-3e5a0b09`, 17 surveys (Season A 2018 to Season B 2026; Season B 2025 was
not published). Reproduced by `python -m scripts.history_eda` (`reports/history_eda.json`) and
`python -m scripts.backtest` (`reports/backtest_results.json`).

| Question | Finding |
|---|---|
| Which years have yields by district? | 2018-2026 only. The 2015 and 2016 workbooks give yields by land type or province; the 2017 table titled "by district" actually has province columns. For 2014 only the PDF report was found; it was not machine-read. |
| Are units and totals consistent? | Every yield table states kg per hectare. Production equals yield times area (within 2%) in 93% (Season B 2018) to 100% of cells; 100% in recent surveys. |
| Duplicates and revisions | 36 national values that 2020-2022 workbooks re-print for the previous year match the original survey exactly. The 2024 annual workbook matches the separate Season A and B files cell for cell. |
| Changes in how tables are laid out | 2018: districts across the top instead of down the side; input use counted per plot, not per farmer (not used); one Season B sheet untitled (named in `data/sources.json`). 2019: one banana column. 2021 A: no all-bean yield, and two different "Bush bean" columns (both dropped rather than guessing). |
| Is input use given per crop? | No. District seed and fertilizer use is for all crops together in every year; per-crop seed use exists only nationally. |
| National jumps | National fertilizer use went from 39% of farmers (2022 A) to 60% (2023 A); national bean yield fell 26% from 2019 A to 2020 A. The files do not explain these, so districts are always compared with the national figure of the same survey. |
| Can old and new years be compared? | District rankings agree weakly from 2018 to 2020 (0.29 and 0.39) and strongly since (0.64 to 0.92), so labels use the last 3 surveys. |
| Rules or a statistical model? | A statistical model did not anticipate next-season shortfalls better than simple rules (0.867 against 0.868), so the rules were kept (`docs/methodology.md`, section 5C). |

With today's rules, maize Season A has 14 districts with a repeated shortfall: 3 where both seed and
fertilizer use are below the national share (Gicumbi, Nyarugenge, Ruhango) and 11 where they are not.

---

## Part 1. Data quality (five 2024-2026 surveys)

Snapshot `snap-20261029T103445Z-e435e56c` (Seasons A and B 2024, A 2025, A and B 2026). Reproduced by
`python -m scripts.run_analysis` (`reports/analysis_results.json`). Category counts in Parts 1 to 4 use
the first version of the rules ("short in every reliable survey").

| Check | Result |
|---|---|
| Districts per survey | 30 plus the national row in every survey and table |
| Finding the tables | Found by title in all 5 surveys, although the yield table was sheet 11, 10, 12, 13 and 11 |
| Internal consistency | Production equals yield times harvested area in all 2,587 cells where all three are published |
| Agreement with other NISR files | The separate 2024 A and B files equal the 2024 annual workbook exactly |
| Printed zeros | 198 / 125 / 225 / 165 / 138 cells, treated as "not reported" |
| Harvested area larger than planted area by more than 1% | 1 / 8 / 1 / 0 / 0 cells; 8 of the 10 are paddy rice, 1 maize; flagged, not changed |
| Label of the national row | "National", "Total" or "S/Total" depending on the table; a check refuses any survey missing a national figure |
| Small crops | Of the 2,587 district yields published in these surveys (all crops), 35% rest on under 500 ha harvested and 20% on under 200 ha |
| Inconsistency in an NISR table | Season B 2026 main report, Table 5 (p.17), Fruits: the area estimate (15,535 ha) lies outside its own printed 95% range (9,235 to 15,347) |
| Missing survey | Season B 2025 not on the NISR site when the data were collected |

Two errors in our own code were found and fixed during this check. The national fertilizer row labelled
"Total" was at first skipped, which quietly made every district look as if its fertilizer use was not low.
A check now refuses to publish any survey that lacks a national figure.

## Part 2. Findings

### A. How big is the gap? National yields are below the PSTA 5 goals

National yield for 2025/26 (Seasons A and B together) against the PSTA 5 goal for that year:
soybean 0.47 vs 0.9 t/ha (52%), bean 0.72 vs 0.9 (79%), Irish potato 7.95 vs 10.1 (79%),
maize 1.80 vs 2.06 (87%), cassava 13.86 vs 15.7 (88%), cooking banana 15.72 vs 17.1 (92%),
wheat 1.21 vs 1.3 (93%), paddy rice 4.36 vs 4.5 (97%).

All 8 priority crops are below their goal. Season A maize yield was 2.04, 1.99 and 1.99 t/ha in 2024, 2025
and 2026: flat, not rising. Closing the national gap depends on where it is concentrated, which is the
district question below. Caveats: Season C is left out, and PSTA 5 does not say exactly how it combines
seasons. Chart: `figures/national_target_attainment.html`.

### B. Shortfalls come back in the same districts (tested: H1, H2)

- **H1.** District rankings barely change between surveys. Rank agreement: maize 0.90 and 0.96 (Season A),
  0.87 (B); bean 0.95 and 0.96 (A), 0.905 (B); Irish potato 0.97 and 0.99 (A), 0.95 (B); cassava 0.78 and
  0.85 (A), 0.88 (B); soybean 0.96 and 0.81 (A), 0.70 (B); cooking banana 0.98 and 0.97 (A), 0.85 (B);
  sweet potato 0.89 and 0.95 (A), 0.92 (B). All 21 comparisons: p = 0.004 after Holm correction
  (5,000 shuffles). Paddy rice was not tested (only 11 districts grow enough of it).
- **H2.** 60 district-crop pairs were short in all three Season A surveys. Random shuffling gives about 17
  on average (95th percentile 21); the chance of 60 or more is 0.05% (2,000 shuffles).

A district that is short this season was almost always short before, so a single-season table understates
how lasting the gap is. Caveat: the reports do not say whether the same land is surveyed each season; if
it is, part of this stability comes from measuring the same plots again. Charts:
`figures/pattern_maize_A.html`, `figures/map_maize_A.html`.

### C. Season and crop matter (exploratory)

- A district's maize position in Season A 2026 says little about Season B 2026 (correlation 0.24), which
  is why seasons are never combined.
- Under the first rules, Season A had 10 districts short every time in three or more priority crops
  (Gasabo, Gisagara, Karongi, Kayonza, Ngororero, Nyamagabe, Nyamasheke, Nyanza, Ruhango, Rwamagana) and
  Season B had 6 (Bugesera, Kamonyi, Kayonza, Muhanga, Ruhango, Rwamagana). Under today's rules the counts
  are 11 and 8.
- Repeated Irish potato shortfalls sit in eastern lowland districts (Kayonza, Ngoma, Kirehe, Gatsibo,
  Nyagatare), where the crop is minor and poorly suited. A gap there is not proof of a fixable gap, so the
  field checks ask about variety and site suitability. Chart: `figures/triage_matrix_season_A.html`.

### D. Seed and fertilizer use give a mixed signal (tested: H3)

District input use (all crops) compared with the crop's yield ratio, 27 to 30 districts, Holm-corrected
over 20 tests:

- Bean and fertilizer: rank agreement 0.67 to 0.74 in all 5 surveys, p = 0.004 each.
- Bean and improved seed: -0.235 to -0.399; none significant.
- Maize and improved seed: 0.24 to 0.47 (one nominal p-value as low as 0.009); none significant after
  correction.
- Maize and fertilizer: 0.12 to 0.41; none significant after correction.

Under the first rules, 9 of the 12 maize Season A districts short every time did not have low input use.
Five Western Province districts and Nyamagabe had fertilizer use of 72.1% to 84.1% of farmers (national
67.2%) but improved seed use of only 15.0% to 30.8% (national 37.0%). Only Gicumbi, Ruhango and Nyarugenge
had both below national.

For most repeated maize shortfalls, "more inputs" is not the obvious first answer; seed and variety
choice, soil acidity, erosion and altitude are the questions to check. Caveat: input use is for all crops,
and the bean-fertilizer link may reflect climate or where programmes were targeted rather than any effect
of fertilizer. Chart: `figures/inputs_maize_A.html`.

### E. Label counts under the first rules

Maize Season A: 3 short every time with low inputs, 9 short every time with inputs not low, 3 one-season
dips, 15 not below. Bean Season A: 3 / 7 / 2 / 18. Maize Season B: 4 / 8 / 1 dip, 3 too uncertain, 14 not
below.

## Part 3. How much do the cut-offs change the labels? (current data, today's rules)

Share of districts whose label stays the same when one setting is changed (1.00 = no change):

| Crop, season | "Reliable" from 200 / 500 / 1,000 ha (short = under 90%) | "Short" under 80% / 95% (reliable from 500 ha) |
|---|---|---|
| Maize A | 1.00 / 1.00 / 0.97 | 0.77 / 0.83 |
| Bean A | 1.00 / 1.00 / 1.00 | 0.80 / 0.93 |
| Irish potato A | 0.77 / 1.00 / 0.90 | 0.93 / 1.00 |
| Maize B | 0.90 / 1.00 / 0.87 | 0.70 / 0.83 |

The area cut-off hardly matters for maize and beans but does for Irish potato. The 90% line matters more,
mainly for districts close to it. Both can be changed in the app (Evidence, Data and methods), and any
non-default setting is labelled on screen.

## What a planner would otherwise miss

District maize and bean shortfalls are not a lottery: they come back in the same districts. Most repeated
maize shortfalls are in districts where fertilizer use is already above the national share and improved
seed use is low, which calls for a different field check from input supply.
