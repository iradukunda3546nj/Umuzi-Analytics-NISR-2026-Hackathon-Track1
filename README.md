# Umuzi Analytics

**What Rwanda's agricultural survey says about each district's crop yields, and what to check next.**
NISR Big Data Hackathon 2026, Track 1: Agricultural Productivity.

## The problem

Rwanda's NST2 and the PSTA 5 agriculture plan aim for a 50% increase in priority food crop productivity, with yield targets measured by the NISR Seasonal Agricultural Survey (SAS) (MINAGRI, PSTA 5 Abridged, p.14 and p.21). In 2025/26, national Season A+B yields for all eight PSTA 5 priority crops were below their targets, from 52% of target (soybean) to 97% (paddy rice).

The targets are national, but the work happens in districts. The survey is published one season at a time, as large tables whose numbering and layout change between years. From those tables it is hard to tell a district that is **repeatedly** below national from one that had **one bad season**, or to see whether a shortfall coincides with **low input uptake** or happens despite it.

## What Umuzi Analytics does

Choose a crop and a district (type to search), then a season. The Rwanda map shows every district's position; the selected district is outlined, and one short finding sits beside the map with the figures and survey releases behind it.

| Map colour | Meaning | Suggested check |
|---|---|---|
| Repeatedly below national, low input uptake | Under 90% of the national yield in at least 2 of the last 3 surveys of that season; improved-seed and fertilizer uptake both below national | Input access and timing first |
| Repeatedly below national, input uptake not low | Same pattern, but input uptake is not low | Soils, erosion, varieties, water |
| Below national in the latest season only | One-season drop | Check for a season shock; re-check next survey |
| Evidence too limited to judge | Not reported, or under 500 ha harvested | Verify in the field before acting |
| Not below national | At or above 90% of national now | - |

These are **checks, not prescriptions**. The survey shows where yields are low, not why.

Also in the app:
- **Rwanda against the PSTA 5 target**: an arrow running to a bullseye at the target, with where Rwanda stands marked on it and the gap still to cover.
- **Umuzi Assistant** (chatbot): answers questions such as *"Has Ruhango's maize yield stayed below national in Season A?"*, *"What about Nyamagabe?"* and *"What should I verify about fertilizer access?"*. It follows the map's selection, cites the survey releases behind each answer, and states the limitation that changes its meaning, for example that input uptake is pooled across crops.
- **Details on demand**: every district survey by survey since 2018, the selected district's history, input uptake, the full table, and Data and methods.

### Findings (latest surveys; details in `reports/`)
- District positions are persistent: rank correlations between consecutive 2024-2026 surveys of 0.70 to 0.99 for seven priority crops (all Holm-adjusted p = 0.004); 60 district-crop pairs were below national in all three Season A surveys of 2024-2026, against 16.9 expected by chance (p = 0.0005). These tests were pre-specified.
- Maize, Season A: 14 districts are repeatedly below national. Only 3 (Gicumbi, Nyarugenge, Ruhango) have both seed and fertilizer uptake below national; 11 do not. Eight of those 11 (Ngororero, Rutsiro, Karongi, Nyabihu, Nyamasheke, Rubavu, Gakenke, Nyamagabe) combine above-national fertilizer uptake with below-national improved-seed uptake.
- Season A: 11 districts are repeatedly below national in three or more priority crops; Season B: 8.

## How the data were used (and why)

**1. Sources checked from 2014 onward** (`scripts/history_eda.py`, `reports/history_eda.json`). Only the 2018 to 2026 workbooks contain district x crop x season yields; 2014-2016 report yields by land-use stratum and 2017 by province (its table titled "by district" has province columns). Season B 2025 was not published. Result: 17 comparable surveys, 2018 A to 2026 B.

**2. Strict ingestion** (`src/ingestion/sas_adapter.py`). Tables are found by title, not number. The adapter handles each layout change explicitly and refuses to guess:
- 2018 prints crops as rows and districts as columns; the national value is a "Grand Total" or "Overall Yield" column, never the province subtotal.
- 2020-2022 tables re-print the previous year's national value ("National 2019 A"); only the row for the survey's own year is the reference. All 36 re-printed values match the earlier survey exactly (no revisions).
- A crop printed twice with different values (2021 A "Bush bean") is dropped, not chosen.
- A yield table must state kg/ha. A printed 0 or blank is stored as "not reported", never as zero.
- 2018 reports input use per plot or without a stated basis, not per farmer, so it is not used; 2018 B harvested area has no season in its title, so `data/sources.json` names the sheet and the production = yield x area gate confirms it.
- Every survey passes the same gates (30 districts, national row, production = yield x area) and all 17 are published together as one snapshot, or none are.

**3. What the EDA found.**
- District input uptake (seed, fertilizer) is published only for all crops together, in every year. Crop-specific seed use exists only nationally.
- National levels shift between years in ways the files do not explain (for example national inorganic-fertilizer uptake goes from 39% of farmers in 2022 A to 60% in 2023 A, and national bean yield falls 26% from 2019 A to 2020 A). Comparing each district with the national value of the same survey removes such shifts.
- District rankings agree weakly between consecutive Season A surveys from 2018 to 2020 (median rho 0.29 and 0.39) and much more strongly since (0.64 to 0.92; Season B 0.75 to 0.91 since 2019).

**4. Model or rules?** (`scripts/backtest.py`, `reports/backtest_results.json`). The task: predict whether a district will be below national in the next survey of the same season, using only earlier surveys. On the held-out 2024-2026 surveys (754 district-crop cases), a logistic regression was no better at flagging shortfalls than the simple rule "below in the previous survey" (balanced accuracy 0.867 vs 0.868; 95% interval of the difference -0.019 to +0.015). It was better calibrated (Brier 0.093 vs 0.111), but that does not change which districts are flagged, so **the rules were kept**. The backtest also showed that the old rule, "below in every survey", caught only 40% of next-season shortfalls with nine years of history. "Below in at least 2 of the last 3 surveys" catches 81% and tolerates one noisy survey, so it is the rule now used (evidence rules 2.0).

## Data

| Source | Use |
|---|---|
| NISR Seasonal Agricultural Survey district tables, 2018 A to 2026 B except 2025 B (statistics.gov.rw, CC BY 4.0) | Yields, harvested and cultivated area, production, improved-seed and fertilizer uptake |
| MINAGRI PSTA 5 Abridged plan, results framework p.21 | National yield targets |
| geoBoundaries RWA ADM2 (from NISR geodata, CC BY 4.0) | District map |

Checksum-named copies of every workbook used are in `data/raw/nisr_sas/`; provenance is in `data/sources.json` and `data/release_registry.json`. The 2024-2026 files have exact download URLs; the 2018-2023 annual workbooks were downloaded from the [NISR SAS page](https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey) and keep their original file names in `data/sources.json`.

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

The survey is validated before it can be approved. A failing file is quarantined and the app keeps the previous snapshot. Rollback: `python -m scripts.refresh_data rollback --snapshot <id>`. Refresh is analyst-initiated; nothing is scheduled.

## Reproducing everything

```bash
pip install -r requirements-dev.txt
python -m scripts.refresh_data bootstrap --approve  # rebuild the snapshot from data/sources.json
python -m scripts.history_eda                       # reports/history_eda.json
python -m scripts.backtest                          # reports/backtest_results.json
python -m scripts.run_analysis                      # reports/analysis_results.json, reports/figures/
python -m pytest                                    # 57 tests
```

`bootstrap` and the source audit in `history_eda` read the original downloads from `data/incoming/` (not committed). Every workbook actually used is committed as a checksum-named copy in `data/raw/nisr_sas/`, and the published snapshot in `data/snapshots/` is what the app, tests and other scripts read.

## Repository map

```
app.py                      Streamlit application (map overview, finding, assistant, details)
src/ingestion/              NISR SAS adapter (title-based discovery, 2018-2026 layouts)
src/validation/             schema and quality gates
src/services/               versioned snapshot store, data status
src/analytics/              indicators and evidence rules (single source of formulas)
src/decisions/              the Finding (shared by map, brief and assistant) and the Evidence Brief
src/assistant/              Umuzi Assistant (deterministic, answers from the same Finding)
src/viz/                    charts, map, target arrow, legend
scripts/                    refresh_data, history_eda, backtest, run_analysis, download_sources
tests/                      pipeline and historical layouts (synthetic fixtures), rules, real data, assistant, app
data/                       raw files, snapshots, registry, sources, PSTA 5 targets, assistant icon
docs/  reports/  demo/      methodology and limitations, analysis outputs, demo
```

## Limitations (full list in `docs/limitations.md`)
Yields are farmer-reported and NISR publishes no district margins of error; input uptake is pooled across crops; associations are not effects; "below national" is not "below potential"; 2018-2019 district rankings are weakly comparable with later years, so labels use the last 3 surveys; Season B 2025 is missing; the tool has not yet been tested with planners.

## Competition notes
- AI use is disclosed in `docs/AI_USE_DISCLOSURE.md`.
