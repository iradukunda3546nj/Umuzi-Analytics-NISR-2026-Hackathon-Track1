# Data folder

Everything the app reads, and where it came from. Files marked "never" are written only by the
refresh command, so the published numbers always trace back to an unchanged NISR file.

| Path | Contents | Edited by hand? |
|---|---|---|
| `raw/nisr_sas/` | Unchanged copies of the NISR Seasonal Agricultural Survey table workbooks, named `<survey>__<start of checksum>.xlsx` | Never. Written only by the refresh command. |
| `raw/boundaries/` | geoBoundaries RWA ADM2 simplified GeoJSON (30 districts, from NISR geodata, CC BY 4.0) and its metadata | No |
| `raw/reference/` | SAS 2024 Annual workbook (validation cross-check) and the download log | No |
| `reference/psta5_productivity_targets.csv` | PSTA 5 national yield targets, transcribed from MINAGRI PSTA 5 Abridged, p.21 | Yes, cited |
| `sources.json` | Source URL, landing page and season for each ingested release | Yes |
| `release_registry.json` | Every file loaded: checksum, reader version, tables used, and which file replaced which | No (written by the refresh command) |
| `snapshots/<id>/` | `records.csv` (one row per published cell) and `manifest.json` (surveys included, check results, approval). The older snapshot is kept so the app can be rolled back and so Parts 1-4 of `reports/eda_findings.md` can be reproduced. | No |
| `snapshots/ACTIVE.json` | Pointer to the approved snapshot the app reads | Only via `approve` or `rollback` |
| `chatBOT.png` | Umuzi Assistant icon | - |
| `BackGD.jpg` | Landing-page background photo | - |
| `incoming/` (git-ignored) | Original downloads before staging; `incoming/nisr_sas_history/` holds the 2014-2023 files checked by `scripts/history_eda.py` | - |
| `quarantine/` (git-ignored) | Rejected files with `reason.json` | - |

## Sources and licence

- National Institute of Statistics of Rwanda (NISR), Seasonal Agricultural Survey district tables, 2018 Season A to 2026 Season B (2025 Season B not published). https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey; exact file URLs for 2024-2026 and original file names for the 2018-2023 annual workbooks are in `sources.json`. Licence: Creative Commons Attribution 4.0. Attribution: "National Institute of Statistics of Rwanda".
- MINAGRI, *Strategic Plan for Agriculture Transformation 5 (PSTA 5), Abridged version*, results framework p.21.
- geoBoundaries (Runfola et al.), RWA ADM2, gbOpen release 9469f09, derived from NISR geodata; CC BY 4.0.

All data are published aggregates. No personal or restricted data are stored.

## Rebuild from scratch

```bash
python -m scripts.download_sources          # fetches 2024-2026 into data/incoming/, verifies checksums;
                                            # place the 2018-2023 annual workbooks in data/incoming/nisr_sas_history/
python -m scripts.refresh_data bootstrap --approve   # all releases gated and published as one snapshot
```
