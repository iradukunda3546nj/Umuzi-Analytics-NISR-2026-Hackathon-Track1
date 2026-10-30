# Data Inventory

All sources were retrieved on **2026-10-29** (UTC timestamps in `data/raw/reference/download_log.txt`). Licence for NISR content: **CC BY 4.0** (https://statistics.gov.rw/terms-use, read 2026-10-29).

## Used in the application

| ID | Publisher | Content | Grain | Status | Local file | SHA-256 |
|---|---|---|---|---|---|---|
| SAS-2024A | NISR | SAS 2024 Season A tables (Excel, 34 sheets) | District, national, LSF/SSF rows | Downloaded, inspected, ingested | `data/raw/nisr_sas/SAS-2024A__6848e1b3c8ca.xlsx` | `6848e1b3c8caadbf68c75916512f435e43a65d07734cbcdb3bcbbef3bb45c358` |
| SAS-2024B | NISR | SAS 2024 Season B tables (33 sheets) | same | same | `data/raw/nisr_sas/SAS-2024B__0be9b2749740.xlsx` | `0be9b2749740d6a9fdb963fddd1874f448dfedf9c54e15fef55f6fdbe459c911` |
| SAS-2025A | NISR | SAS 2025 Season A tables (34 sheets) | same | same | `data/raw/nisr_sas/SAS-2025A__d853e32bdf8e.xlsx` | `d853e32bdf8e1c396ffa487c3a786413e82753d0f89a95679cd56a6c20d2669b` |
| SAS-2026A | NISR | SAS 2026 Season A tables (35 sheets) | same | same | `data/raw/nisr_sas/SAS-2026A__c4e4cb4c4e69.xlsx` | `c4e4cb4c4e697febac1cb332280189a4dc6ff7f10d0de956bff279b284c5d4c2` |
| SAS-2026B | NISR | SAS 2026 Season B tables (33 sheets) | same | same | `data/raw/nisr_sas/SAS-2026B__5ca81c6b0a54.xlsx` | `5ca81c6b0a54c4a282ed718d134423920cc75279a5827bbe772fe6eb1a4e9d27` |
| PSTA5-targets | MINAGRI | PSTA 5 Abridged version, results framework p.21 (yield targets) | National, annual | Downloaded, inspected; 8 rows transcribed | `data/reference/psta5_productivity_targets.csv` | (PDF not redistributed; 11 MB; URL below) |
| RWA-ADM2 | geoBoundaries (wmgeolab), from NISR geodata | District boundaries, simplified, 30 features | District polygons | Downloaded, inspected | `data/raw/boundaries/geoBoundaries-RWA-ADM2_simplified.geojson` | `56b0995c7a7735847659b766e00c5cfa29b1b3a197f231dc396f399948c46c09` |

Source URLs and landing pages for every SAS file are in `data/sources.json`. PSTA 5: https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf. Boundaries: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/RWA/ADM2/geoBoundaries-RWA-ADM2_simplified.geojson (metadata: source "Open Data Rwanda", licence CC BY 4.0, boundary year 2012, 30 units).

## Used for validation only

| ID | Content | Use |
|---|---|---|
| SAS-2024-Annual | SAS 2024 Annual tables (79 sheets; Seasons A, B, C) | Cross-check: the standalone 2024A and 2024B releases match it cell for cell (max difference 0.0); `tests/test_real_data.py`. SHA-256 `5c7c6024d9a7b766d9911348aa3b5d5316555c6aa4a8c53f10dc290e2d8906e6` |
| SAS-2026A report | *SAS 2026 Season A Final Report* (PDF, 65 pp.) | Methodology facts: 1,200 segments allocated at district level (p.13); two-stage design, 25 points per segment (p.14); yields from farmer estimation (p.22); sampling errors national only (p.16-18). Not redistributed (23 MB). |

## Sought but not available

| Item | Status |
|---|---|
| SAS 2025 Season B tables | Not located on statistics.gov.rw on 2026-10-29 (search and URL patterns tried). Treated as missing, never as zero. |
| SAS releases before 2024 | Landing pages for 2019 to 2023 exist but listed no table downloads at the time of inspection. Not ingested. |
| SAS microdata (plot level) | Not requested; access-controlled through the NISR microdata catalogue. Not needed for district planning. |
| Agricultural Household Survey 2024 tables | Not ingested within the deadline. Candidate future source for farm-level constraints. |
| CHIRPS rainfall | Considered, not ingested. Rainfall hypotheses are marked NOT TESTABLE. |

## What these data are, and are not

- **Scale**: published district estimates, plus national and LSF/SSF rows. No household, plot or sector records.
- **Design**: multiple-frame survey; area frame of 1,200 segments (20 in Nyarugenge and Kicukiro to 68 in Nyagatare, 2026A Table 4) plus a list frame of large-scale farmers; design weights applied by NISR.
- **Yield**: farmer-estimated (SAS 2026A report, p.22), kg per harvested ha.
- **Uncertainty**: standard errors and CVs are published only for national crop areas (e.g. 2026A Table 5). District standard errors are not published.
- **Temporal**: Season A (sowing roughly September, harvest roughly February) and Season B (sowing roughly February to March) are different agronomic seasons and are never pooled in the analysis.

## Data-quality observations (computed; see `reports/eda_findings.md`)

- Production equals yield x harvested area / 1000 in all 2,587 district-crop cells where all three were observed.
- Cells printed as 0: 198 (2024A), 125 (2024B), 225 (2025A), 165 (2026A), 138 (2026B). Treated as "not reported".
- Harvested area exceeds cultivated area in 5 (2024A), 22 (2024B) and 11 (2025A) cells, mostly bananas.
- National row labels vary: "National" (crop tables), "Total" (inorganic fertilizer, 2026A), "S/Total" (production). Handled explicitly; a gate rejects any release missing a national value.
- 2026A Table 5, Fruits: printed estimate 8,183 ha lies outside its printed 95% CI (9,050 to 17,975). Not used by the app; reported here as a publication inconsistency.
