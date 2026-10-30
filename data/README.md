# Data folder

| Path | Contents | Edited by hand? |
|---|---|---|
| `raw/nisr_sas/` | Immutable copies of NISR Seasonal Agricultural Survey table workbooks, named `<release>__<sha256 prefix>.xlsx` | Never. Written only by the refresh command. |
| `raw/boundaries/` | geoBoundaries RWA ADM2 simplified GeoJSON (30 districts, from NISR geodata, CC BY 4.0) and its metadata | No |
| `raw/reference/` | SAS 2024 Annual workbook (validation cross-check) and the download log | No |
| `reference/psta5_productivity_targets.csv` | PSTA 5 national yield targets, transcribed from MINAGRI PSTA 5 Abridged, p.21 | Yes, cited |
| `sources.json` | Source URL, landing page and season for each ingested release | Yes |
| `release_registry.json` | Every ingested raw file: checksum, adapter version, tables used, supersession lineage | No (written by pipeline) |
| `snapshots/<id>/` | `records.csv` (canonical long records) and `manifest.json` (releases, gates, approval) | No |
| `snapshots/ACTIVE.json` | Pointer to the approved snapshot the app reads | Only via `approve` or `rollback` |
| `incoming/` (git-ignored) | Original downloads before staging | - |
| `quarantine/` (git-ignored) | Rejected files with `reason.json` | - |

## Sources and licence

- National Institute of Statistics of Rwanda (NISR), Seasonal Agricultural Survey, 2024 Season A, 2024 Season B, 2025 Season A, 2026 Season A, 2026 Season B: district tables. https://statistics.gov.rw (exact file URLs in `sources.json`). Licence: Creative Commons Attribution 4.0. Attribution: "National Institute of Statistics of Rwanda".
- MINAGRI, *Strategic Plan for Agriculture Transformation 5 (PSTA 5), Abridged version*, results framework p.21.
- geoBoundaries (Runfola et al.), RWA ADM2, gbOpen release 9469f09, derived from NISR geodata; CC BY 4.0.

All data are published aggregates. No personal or restricted data are stored.

## Rebuild from scratch

```bash
python -m scripts.download_sources          # fetches into data/incoming/, verifies checksums
python -m scripts.refresh_data bootstrap --approve
```
