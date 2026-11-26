# Umuzi Analytics

**Rwanda's farm survey, turned into a plain answer for every district: where the harvest falls short,
whether it keeps happening, and what to check first.**

NISR Big Data Hackathon 2026, Track 1: Agricultural Productivity.

## The problem

Rwanda's agriculture plan (PSTA 5) restates the NST2 goal of a 50% increase in agricultural
productivity (MINAGRI, PSTA 5 Abridged, p.14) and sets yearly yield targets for eight priority food crops,
measured with NISR's Seasonal Agricultural Survey (p.21). In 2025/26 the national harvest per hectare was below the plan's goal for all eight priority
crops, from 52% of the goal (soybean) to 97% (paddy rice).

The goals are national, but the work happens in districts. The survey is published each season as dozens
of large tables whose numbering and layout change from year to year. From those tables it is hard to
answer three simple questions:

- Is this district's harvest short **again and again**, or was it **one bad season**?
- Do **fewer farmers use improved seed and fertilizer** here, or is the shortfall happening despite them?
- So **what should the district team check first**?

## What the app does

Pick a crop, a district and a season. The app compares the district's harvest per hectare with the
national average in the last three surveys and gives it one of five labels:

| Label | What it means | First thing to check |
|---|---|---|
| Repeated shortfall, seed and fertilizer use low | Under 90% of the national average in at least 2 of the last 3 surveys, and fewer farmers than nationally use both improved seed and fertilizer | Were inputs in stock, affordable and on time? |
| Repeated shortfall, seed and fertilizer use not low | Same repeated shortfall, but input use is not low | Soil, slopes and erosion, varieties, water |
| One-season dip | Short in the latest survey only | Weather, pests, planting dates; look again next season |
| Too uncertain to judge | No figure published, or the crop covers under 500 ha in the district, so the average rests on very few sampled plots | Confirm the harvest locally before acting |
| At or above the national average | At least 90% of the national average in the latest survey | What is working here that could help neighbours? |

These are **things to check, not prescriptions**. The survey shows where harvests are low, not why.

The app has five sections, one question each:

| Section | Question | What you see |
|---|---|---|
| Home | What is this, and who is it for? | One question, four cards (Where, When, Why, What), and the path: pick a district, see how it compares, ask why, take action |
| Your district | How far is it from the national average? | A map you can click, an arrow flying towards a bullseye that stands for the national average, the last 3 surveys as tick or cross tiles, and Rwanda against its national goal |
| Why? | A pattern or a one-off? Enough seed and fertilizer? What to check? | Three numbered cards, a "Take action" card with 1 to 4 field checks, a downloadable brief, and the assistant |
| Ask Umuzi | Anything across districts and crops | The assistant |
| Evidence | Can I trust it? | Every survey since 2018, the district's history, seed and fertilizer compared, the full table, the data checks, the backtest, and sliders to test the cut-offs |

Links can be shared: `?view=why&district=Gasabo&crop=cassava&season=A` opens that page. Percentages are
rounded to whole numbers, except next to the 90% line, where one more decimal shows which side a district
is on (89.6% is short, 90.2% is not).

**Umuzi Assistant.** Answers questions such as *"How is Musanze doing?"*, *"Why?"*, *"What should we
check?"*, *"What about Nyamagabe?"*, *"Which districts do best for beans?"*, *"How has it changed since
2018?"* and *"How far is Rwanda from the maize goal?"*. It does not use an AI language model: every answer
is built from the same data and rules as the map, so it cannot invent a number. It follows the selected
district, understands misspelled district names (and says how it read them), suggests the next question,
and says plainly when it does not understand a question instead of guessing.

## What the data show

- **Shortfalls come back in the same districts.** For seven priority crops, the order of districts barely
  changes from one survey to the next (rank agreement 0.70 to 0.99). 60 district-crop pairs were short in
  all three Season A surveys of 2024-2026, against about 17 if positions were random (chance of 60 or
  more: 0.05%). Both tests were written down before the results were seen.
- **For maize, most repeated shortfalls are not about input supply.** In Season A, 14 districts have a
  repeated maize shortfall. Only 3 (Gicumbi, Nyarugenge, Ruhango) have both seed and fertilizer use below
  the national share. In 8 of the other 11 (Ngororero, Rutsiro, Karongi, Nyabihu, Nyamasheke, Rubavu,
  Gakenke, Nyamagabe), fertilizer use is above the national share but improved seed use is below it, which
  points to seed and varieties rather than fertilizer.
- **Some districts are short in many crops at once:** 11 districts in three or more priority crops in
  Season A, and 8 in Season B.

Details: `reports/eda_findings.md`.

## How it works, briefly

The full explanation, in plain words, is in `docs/methodology.md`.

1. **Reading the tables.** NISR renumbers its tables between surveys, so the app finds each table by its
   title. Each layout change since 2018 is handled explicitly. When something is ambiguous (for example a
   crop printed twice with different values), the value is dropped rather than guessed.
2. **Checking the data.** Every survey must include all 30 districts and the national figure, production
   must equal yield times area, and percentages must lie between 0 and 100. A printed 0 or a blank is
   stored as "not reported", never as zero. A survey that fails is refused, and the app keeps the previous
   data.
3. **Comparing like with like.** Each district is compared with the national average of the same survey,
   which removes national swings such as the 26% drop in the national bean yield from Season A 2019 to Season A 2020. Seasons A and B are
   never mixed. Only the last 3 surveys decide the label, because district rankings from 2018 and 2019
   agree poorly with later years.
4. **Why 500 ha.** NISR measures a sample of plots: for the five main seasonal crops it observes 21 to 42
   plots per 1,000 ha (SAS Season B 2026 main report, Table 5), so 500 ha corresponds to about 10 to 21
   plots. Below that, a district average may rest on only a handful of farmers' answers, so the app marks
   it "too uncertain to judge".
5. **Rules or a statistical model?** We tested whether a statistical model (logistic regression) could
   anticipate next season's shortfalls better than simple rules, using only earlier surveys, on 754 cases
   from 2024-2026. It could not: balanced accuracy 0.867 for the model against 0.868 for the simplest rule
   ("short in the latest survey"), a difference between -0.019 and +0.015. So the app uses transparent
   rules that anyone can check by hand.
6. **Why "2 of the last 3".** It was chosen for its meaning, not because it scored highest. It separates a
   pattern from a one-off, which "short in the latest survey" cannot, and it still catches 81% of next-season
   shortfalls (the first version, "short in every survey since 2018", caught only 40%). The app also flags
   every district short in the latest survey as a "one-season dip", so nothing is hidden.

## Data

| Source | Used for |
|---|---|
| NISR Seasonal Agricultural Survey, district tables, Season A 2018 to Season B 2026 (Season B 2025 was not published); statistics.gov.rw, CC BY 4.0 | Harvest per hectare, harvested and planted area, production, seed and fertilizer use |
| NISR SAS Season B 2026 main report | How the survey samples land, which justifies the 500 ha rule |
| MINAGRI PSTA 5 abridged plan, results framework p.21 | National yield goals |
| geoBoundaries RWA ADM2 (from NISR geodata, CC BY 4.0) | District map |

Unchanged copies of every workbook used are in `data/raw/nisr_sas/`, named with their checksum, and the
origin of each is recorded in `data/sources.json`. See `docs/data_inventory.md` for every source.

Credit: **National Institute of Statistics of Rwanda**, Seasonal Agricultural Survey.

## Running the app

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Adding a new NISR survey

```bash
python -m scripts.refresh_data ingest --file "<Tables_2027 Season A.xlsx>" --release-id SAS-2027A \
       --season-year 2027 --season A --source-url <url>
python -m scripts.refresh_data approve --snapshot <id printed above>
```

The new survey is checked before it can be approved. A file that fails is set aside and the app keeps the
previous data. To go back: `python -m scripts.refresh_data rollback --snapshot <id>`. Updates are started
by an analyst; nothing runs on a schedule.

## Reproducing everything

```bash
pip install -r requirements-dev.txt
python -m scripts.refresh_data bootstrap --approve  # rebuild the data from data/sources.json
python -m scripts.history_eda                       # which years can be used: reports/history_eda.json
python -m scripts.backtest                          # rules against the model: reports/backtest_results.json
python -m scripts.run_analysis                      # tests and charts: reports/analysis_results.json, reports/figures/
python -m pytest                                    # 74 automated tests
```

`bootstrap` and `history_eda` read the original downloads from `data/incoming/`, which is not committed.
Every workbook the app uses is committed in `data/raw/nisr_sas/`, and the app, tests and scripts read the
published data in `data/snapshots/`.

## What is where

```
app.py               the app: Home, Your district, Why?, Ask Umuzi, Evidence
src/ingestion/       reads NISR workbooks (finds tables by title; 2018-2026 layouts)
src/validation/      the checks a survey must pass before it is used
src/services/        stores each version of the data and allows rollback
src/analytics/       the comparisons and the labelling rules (one place for every formula)
src/decisions/       the finding for a district, its plain-language explanation, and the downloadable brief
src/assistant/       Umuzi Assistant (answers from the same finding as the map)
src/viz/             map, charts, target arrows, tiles, bars and hand-drawn icons
src/ui/              page style and animations (animations switch off if the device asks for less motion)
scripts/             refresh the data, check history, backtest, run the analysis, download sources
tests/               automated tests for every step
data/                NISR files, stored data versions, sources, national goals, images
docs/                how it works (methodology), limitations, data inventory and dictionary, AI use
reports/             analysis results and charts
demo/                demo video and slides
```

## Limitations

Yields are reported by farmers, and NISR publishes no margin of error for districts. Seed and fertilizer
use are for all crops together. Patterns are not causes. "Below the national average" is not "below what
is possible". Small crops rest on few sampled plots. Season B 2025 is missing. The app has not yet been
tested with planners, and no agronomist has reviewed the thresholds or field checks. Full list:
`docs/limitations.md`.

## AI use

Disclosed in `docs/AI_USE_DISCLOSURE.md`.
