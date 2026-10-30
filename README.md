# Umuzi Analytics

**District crop productivity evidence for agricultural planners in Rwanda.**
NISR Big Data Hackathon 2026, Track 1: Agricultural Productivity.


## The problem

Rwanda's NST2 and the PSTA 5 agriculture plan aim for a 50% increase in priority food crop productivity, with yield targets measured by the NISR Seasonal Agricultural Survey (SAS) (MINAGRI, PSTA 5 Abridged, p.14 and p.21). In the 2025/26 agricultural year, national Season A+B yields for all eight PSTA 5 priority crops were below their targets, from 52% of target (soybean) to 97% (paddy rice).

The targets are national, but the work happens in districts. A district agronomist planning the next season has SAS tables for one season at a time: about 27 crops by 30 districts per indicator, with table numbers that change between releases. From those tables it is hard to tell a district that is **persistently** below national from one that had **one bad season**, or to see whether a shortfall coincides with **low input uptake** or occurs despite it.

## What Umuzi Analytics does

For a chosen crop and season type, it classifies each of the 30 districts using every matched SAS release:

| Category | Meaning | Suggested route |
|---|---|---|
| Persistent shortfall, low input uptake | Below 90% of national in every adequately covered release; improved seed and fertilizer uptake both below national | Check input access and timing first |
| Persistent shortfall, inputs at or above national | Same, but input uptake is not low | Diagnose soils, erosion, varieties, water |
| Latest-season dip | Below national in the latest release only | Check for a season shock; monitor |
| Insufficient evidence - field verification required | Too little harvested area or too few releases | Verify before acting |
| Not below national | No shortfall in the latest release | - |

These are **investigation routes, not prescriptions**. The tool does not estimate what any intervention would achieve.

### What the data revealed (pre-specified tests; details in `reports/eda_findings.md`)
- District yield positions are highly persistent: Spearman rank correlations between consecutive matched releases of 0.70 to 0.99 for seven priority crops (all Holm-adjusted p = 0.004).
- 60 district-crop pairs are below national in all three Season A releases, against 16.9 expected by chance (p = 0.0005).
- For maize in Season A, 9 of the 12 persistent-shortfall districts do **not** have low input uptake. Five Western Province districts and Nyamagabe combine above-national fertilizer uptake with below-national improved-seed uptake. Only Gicumbi, Ruhango and Nyarugenge have both inputs below national.

## Data

| Source | Use |
|---|---|
| NISR Seasonal Agricultural Survey district tables: 2024 Season A, 2024 Season B, 2025 Season A, 2026 Season A, 2026 Season B (statistics.gov.rw, CC BY 4.0) | Yields, harvested and cultivated area, production, improved-seed and fertilizer uptake |
| MINAGRI PSTA 5 Abridged plan, results framework p.21 | National yield targets |
| geoBoundaries RWA ADM2 (from NISR geodata, CC BY 4.0) | District map |

Raw files are in `data/raw/` (redistribution allowed under CC BY 4.0) with checksums. Exact URLs are in `data/sources.json`, and full provenance in `docs/data_inventory.md`. 2025 Season B could not be found on the NISR site and is shown as missing.

Credit: **National Institute of Statistics of Rwanda**, Seasonal Agricultural Survey.

## Using the app

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

1. In the left rail choose a **season type**, a **crop** and a **focus district**. Every view, table and download follows this scope.
2. **Overview**: the national gap against PSTA 5 targets.
3. **Evidence Map**: the category of every district plus an evidence panel for the focus district.
4. **Persistence**: each district's position in every release (the signature view).
5. **Input Context**: seed and fertilizer uptake against national, with the category of each district.
6. **Triage Matrix**: all priority crops at once.
7. **Compare Districts**: two districts on the same basis, with a warning when coverage is thin.
8. **Evidence Brief**: a shareable Markdown brief and CSV for the focus district and crop.
9. **Data and Methods**: data status, definitions, refresh commands, sources.

## Adding a new NISR release

```bash
python -m scripts.refresh_data ingest --file "<Tables_2027 Season A.xlsx>" --release-id SAS-2027A \
       --season-year 2027 --season A --source-url <url>
python -m scripts.refresh_data approve --snapshot <id printed above>
```

The release is validated (districts, crops, national rows, production = yield x area) before it can be approved. A failing file is quarantined and the app keeps the previous snapshot. Rollback: `python -m scripts.refresh_data rollback --snapshot <id>`. See `docs/data_refresh_architecture.md` and `docs/operations_runbook.md`. Refresh is analyst-initiated; nothing is scheduled.

## Reproducing the analysis and tests

```bash
pip install -r requirements-dev.txt
python -m scripts.download_sources                  # re-download NISR files (optional)
python -m scripts.refresh_data bootstrap --approve  # rebuild snapshots from data/incoming (optional)
python -m scripts.run_analysis                      # reports/analysis_results.json, reports/figures/
python -m pytest                                    # 38 tests
```

## Repository map

```
app.py                      Streamlit application
src/ingestion/              NISR SAS adapter (title-based table discovery)
src/validation/             schema and quality gates
src/services/               versioned snapshot store, data status
src/analytics/              indicators and evidence rules (single source of formulas)
src/decisions/              Evidence Brief
src/viz/                    chart builders shared by app and reports
scripts/                    refresh_data, download_sources, run_analysis
tests/                      pipeline (synthetic fixtures), rules, real-data integrity, app
data/                       raw files, snapshots, registry, sources, PSTA 5 targets
docs/  reports/  demo/      documentation (incl. EXECUTION_LOG.md), findings, demo script
deliverables/               plain-English guide (guide.pdf) and presentation deck
```

## Limitations (summary; full list in `docs/limitations.md`)
Yields are farmer-reported; NISR does not publish district standard errors; input uptake is pooled across crops; associations are not effects; "below national" is not "below potential" (for example Irish potato in the eastern lowlands); only five releases; the tool has not been tested with planners.

## Competition notes
- AI use is disclosed in `docs/AI_USE_DISCLOSURE.md`..

