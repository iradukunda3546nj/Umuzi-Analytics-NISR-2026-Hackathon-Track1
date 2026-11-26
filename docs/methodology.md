# How Umuzi Analytics works

This document explains, in plain words, how the app turns NISR survey tables into a label for each
district, why each rule is set the way it is, and how we checked that the result can be trusted.
File names in brackets point to the code that does each step.

## 1. From NISR workbook to app

1. **Read the workbook.** Each Seasonal Agricultural Survey (SAS) release is an Excel file with about 33
   tables. NISR renumbers the tables between releases, so the code finds each table by its title, not its
   number (`src/ingestion/sas_adapter.py`). Eight tables are used: yield, harvested area, cultivated area,
   production, improved seed use, inorganic fertilizer use, organic fertilizer use and erosion protection.
2. **Check it.** Before a release can reach the app it must pass checks: all 30 districts and the national
   row present, production equal to yield times area, percentages between 0 and 100
   (`src/validation/gates.py`). A release that fails is set aside, and the app keeps the previous data.
3. **Store it.** Every cell becomes one row, with a note saying whether NISR printed a number, a 0 or a
   blank. A printed 0 or blank is stored as "not reported", never as zero, because a district with no
   harvest figure did not harvest nothing.
4. **Publish it.** All releases are saved together as one versioned "snapshot". The app, the assistant, the
   reports and the tests all read the same snapshot (`data/snapshots/ACTIVE.json` names the one in use).

The snapshot holds 17 surveys, Season A 2018 to Season B 2026. Season B 2025 was not published.
Earlier years are not used: the 2015, 2016 and 2017 table workbooks give yields only by province or land
type, not by district, and for 2014 only a PDF report was found (`scripts/history_eda.py`).

## 2. Comparing like with like

For each survey, a district's yield is divided by the **national average yield of the same crop in the
same survey**. A result of 69% means the district harvested 69% of the national average per hectare.

Comparing within one survey removes swings that hit the whole country at once. For example, the
national bean yield fell 26% from Season A 2019 to Season A 2020, and national fertilizer use jumped from
39% to 60% of farmers between 2022 and 2023. Comparing raw numbers across years would mistake those
national swings for district problems.

Season A and Season B are always kept apart. They are different growing seasons, and a district's
position in one says little about the other (for maize in 2026 the correlation is only 0.24).

## 3. The rules that give each district its label

The labels come from a short list of yes/no questions asked in a fixed order. In shape this is a decision
tree, but the questions and cut-offs were set by us in advance rather than learned from the data
(`evidence_table` in `src/analytics/indicators.py`).

Each survey is first marked:

- **Reliable** if NISR published a yield and the crop covered at least 500 ha in the district.
- **Short** if the district harvested under 90% of the national average.

Then, looking at the last 3 surveys of the same season:

```
Latest survey: no yield published, or under 500 ha?
 |- yes -> TOO UNCERTAIN TO JUDGE
 '- no  -> Latest result at or above 90% of the national average?
      |- yes -> AT OR ABOVE THE NATIONAL AVERAGE
      '- no (short now) -> Fewer than 2 of the last 3 surveys reliable?
           |- yes -> TOO UNCERTAIN TO JUDGE
           '- no  -> Short in at least 2 of the last 3?
                |- no  -> ONE-SEASON DIP
                '- yes (repeated) -> Seed and fertilizer use published for this survey?
                     |- no  -> TOO UNCERTAIN TO JUDGE
                     '- yes -> Are BOTH seed use and fertilizer use below the national share?
                          |- yes -> REPEATED SHORTFALL, SEED AND FERTILIZER USE LOW
                          '- no  -> REPEATED SHORTFALL, SEED AND FERTILIZER USE NOT LOW
```

**Worked example: Ruhango, maize, Season A.** The last three surveys gave 79%, 71% and 69% of the national
average. All three are reliable and all three are short, so the shortfall is repeated. In Ruhango both
improved seed use and fertilizer use are below the national share, so the label is "Repeated shortfall,
seed and fertilizer use low", and the first checks are about input stock, price and timing.

Choices built into the rules:

- **The latest survey decides first.** A district that was short twice but is fine now is not flagged.
- **Missing or thin data never counts as good news.** It gives "too uncertain to judge".
- **Inputs must both be low.** NISR publishes seed and fertilizer use for all crops together, not per
  crop, so the rule only points to inputs when both are below the national share.
- **The label is a lead, not a cause.** Each label comes with a short list of things to check in the field
  (`src/decisions/explain.py`). Nothing in the app claims that inputs, soil or weather caused a shortfall.

## 4. Why these numbers

| Setting | Value | Why |
|---|---|---|
| Short | under 90% of the national average | NISR publishes no margin of error for district yields, so small gaps cannot be told apart from survey noise. A 10% allowance was fixed before the analysis. It is a judgement call, not an agronomic standard, so it is tested at 80% and 95% too (section 5D). |
| Reliable | at least 500 ha of the crop in the district | See below. |
| Window | last 3 surveys of the same season | District rankings in 2018 and 2019 agree only weakly with later years (rank agreement 0.29 and 0.39, against 0.64 to 0.92 since 2020), so older surveys are shown for context but do not decide the label. |
| Repeated | short in at least 2 of the 3 | Tolerates one noisy survey while still meaning "more than once". |

**Why 500 ha.** The survey does not visit every field. NISR samples 1,200 squares of land, each 300 by
300 m, and records the plot under each of 25 points inside every square (SAS Season B 2026 main report,
pp.10-12). A crop that covers little land in a district therefore appears on few sampled plots, and its
average rests on few farmers' answers.

The report's Table 5 (p.17) gives, for each crop, the national area and the number of plots actually
observed. Dividing one by the other gives the plots observed per 1,000 ha. For the five main seasonal
crops this is 21 to 42: sweet potato 20.9, beans 23.3, cassava 25.2, Irish potato 33.4, maize 42.2
(other crops range from 19.4 for sorghum to 148 for paddy rice, which is mostly grown on large farms
that are counted in full). So, at the national rate:

- 500 ha corresponds to about 10 (sweet potato) to 21 (maize) sampled plots;
- 37 ha of cassava (Musanze, Season B 2026) corresponds to about 1 plot (37 x 25.2 / 1,000 = 0.9);
- 179 ha of Irish potato (Ruhango, Season A 2026) corresponds to about 6 plots (179 x 33.4 / 1,000 = 6.0).

The 500 ha line separates averages built on a reasonable number of farmers from averages built on a
handful. Three cautions:

- Sampling density differs by district (Musanze samples 0.75% of its farmland squares, Nyagatare 0.39%,
  Nyarugenge 2.1%; report Tables 3 and 4), so the plot count for the same area can be half or double.
- These figures describe how many plots were seen, not how precise each yield is. Even 20 farmer-reported
  yields can vary widely. That is one more reason the rules ask for a shortfall in 2 of 3 surveys.
- Crops grown mainly by large farms (for example paddy rice) are counted in full rather than sampled, so
  for them a small area does not mean few observations.

**The 10 ha "large-scale farmer" rule is a different thing.** NISR lists every farm of at least 10 ha
(2 ha for horticulture) and visits it in full (report p.7). That rule is about one farm's size. Our 500 ha
is about the total area of one crop in a whole district, which tells us how much evidence the district
average rests on. NISR's district yield table combines both kinds of farm.

## 5. How the results are checked

**A. Does the code do what the rules say?** Automated tests run on every change (`tests/`):

- every branch of the rules has a test case (`tests/test_analytics.py`);
- known numbers trace back to the exact NISR cells, production equals yield times area, raw files match
  their recorded checksums, and no "not reported" cell turned into a number (`tests/test_real_data.py`);
- each historical table layout is read correctly (`tests/test_historical_layouts.py`);
- a bad release is refused and the app keeps the previous data (`tests/test_pipeline.py`);
- the assistant and the map give the same label for every district, six crops and both seasons
  (`tests/test_assistant.py`), and every page of the app renders (`tests/test_app.py`).

**B. Is the "repeated" pattern real, or could it be chance?** Two tests were written down before any
district result was computed, using the 2024-2026 surveys (`scripts/run_analysis.py`,
`reports/analysis_results.json`):

- **Do districts keep their place?** For seven priority crops, the ranking of districts in one survey
  closely matches the next (rank agreement 0.70 to 0.99 across 21 comparisons). In 5,000 random shuffles
  no comparison was matched; after allowing for the number of tests run (Holm correction), every
  p-value is 0.004.
- **Is "short every time" more common than luck would give?** 60 district-crop pairs were short in all
  three Season A surveys. If district positions were shuffled at random, about 17 would be (average
  16.9; 21 or fewer in 95% of 2,000 shuffles). The chance of 60 or more is 0.05%.

**C. Does the label anticipate the next survey?** (`scripts/backtest.py`, `reports/backtest_results.json`).
For 754 cases in 2024-2026, each method used only earlier surveys to say whether the district would be
short in the next survey of the same season. "Balanced accuracy" weighs shortfalls caught and false
alarms equally (0.5 is guessing, 1.0 is perfect).

| Method | Balanced accuracy | Shortfalls caught | Flags that were right |
|---|---|---|---|
| Short in the latest survey | 0.868 | 85% | 81% |
| Statistical model (logistic regression) | 0.867 | 84% | 83% |
| Short in 2 of the last 3 (our "repeated") | 0.844 | 81% | 80% |
| Short in every survey since 2018 (first version of the rules) | 0.693 | 40% | 93% |

What this shows:

- **The statistical model is no better than simple rules.** The gap to the best rule is between -0.019 and
  +0.015 (95% range), so it flags the same districts. The model's probabilities are better calibrated, but
  for deciding where to send a field visit it adds complexity without changing the answer. The rule for
  switching to a model was fixed in advance (better calibration *and* at least +0.02 balanced accuracy),
  and the model did not meet it. **The rules were kept.**
- **The first version of the rules missed most shortfalls** (40% caught), so it was replaced.
- **"2 of 3" was chosen for its meaning, not because it scored highest.** "Short in the latest survey"
  scored slightly higher, but it cannot tell a one-off from a pattern, which is the point of the tool. The
  app still flags every district that is short in the latest survey, as either "repeated" or "one-season
  dip", so nothing that rule would catch is hidden.

**D. How much do the cut-offs matter?** The labels are recomputed with "short" at 80%, 90% and 95% and
"reliable" at 200, 500 and 1,000 ha (`reports/eda_findings.md`, Part 3). Moving the 90% line to 80% or 95%
changes 17% to 23% of maize Season A labels, mostly for districts close to the line. The area cut-off
changes almost nothing for maize and beans, but lowering it to 200 ha changes 23% of Irish potato labels,
because that crop is grown on small areas in many districts. The sliders under Evidence in the
app let anyone repeat this.

## 6. What has not been validated

The checks above show that the labels are computed correctly, rest on a real pattern, and anticipate the
next survey about as well as a statistical model. They do not show that the suggested field checks are
the right next step. That needs review by agronomists or district officers, and follow-up visits that
record what the cause turned out to be. No one has reviewed the thresholds or checklists yet.

## 7. Comparing Rwanda with the national goal

The goal comes from MINAGRI's agriculture plan (PSTA 5, results framework p.21). The national yield for a
year is Season A plus Season B production divided by Season A plus Season B harvested area, computed only
when both seasons are published. Season C is not included. PSTA 5 does not state its exact method, so the
comparison is approximate. The goal is national; there are no district goals.

## 8. Keeping the method honest over time

- The thresholds are named settings in `src/config.py`, and the rule version is saved in every snapshot.
- Changing a threshold in the app is labelled on screen and never changes the stored data.
- A release missing a table the rules need is refused, unless `data/sources.json` records why that table
  is not comparable (2018 input use, which NISR reported per plot, not per farmer).
- After each new release, rerun `python -m scripts.backtest`. A model would be worth adopting if it clears
  the criterion above, or if reliable district rainfall or soil data become available.
