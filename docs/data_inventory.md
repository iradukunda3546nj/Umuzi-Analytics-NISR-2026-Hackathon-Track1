# Data inventory

Every source the app uses or relies on, where it came from, and what it can and cannot tell us.
NISR content is published under Creative Commons Attribution 4.0 (https://statistics.gov.rw/terms-use).

## Used in the app

| Source | What it is | Local copy |
|---|---|---|
| NISR Seasonal Agricultural Survey (SAS), 2018 to 2023 | Annual table workbooks, each holding Season A and Season B tables, downloaded from the [NISR SAS page](https://statistics.gov.rw/data-sources/surveys/Seasonal-Agricultural-Survey). Original file names are recorded in `data/sources.json`. | `data/raw/nisr_sas/SAS-2018A__...xlsx` to `SAS-2023A__...xlsx` (one file per year, named after its first season) |
| NISR SAS 2024 Season A | Table workbook, 34 sheets | `data/raw/nisr_sas/SAS-2024A__6848e1b3c8ca.xlsx` (SHA-256 `6848e1b3c8caadbf68c75916512f435e43a65d07734cbcdb3bcbbef3bb45c358`) |
| NISR SAS 2024 Season B | Table workbook, 33 sheets | `data/raw/nisr_sas/SAS-2024B__0be9b2749740.xlsx` (`0be9b2749740d6a9fdb963fddd1874f448dfedf9c54e15fef55f6fdbe459c911`) |
| NISR SAS 2025 Season A | Table workbook, 34 sheets | `data/raw/nisr_sas/SAS-2025A__d853e32bdf8e.xlsx` (`d853e32bdf8e1c396ffa487c3a786413e82753d0f89a95679cd56a6c20d2669b`) |
| NISR SAS 2026 Season A | Table workbook, 35 sheets | `data/raw/nisr_sas/SAS-2026A__c4e4cb4c4e69.xlsx` (`c4e4cb4c4e697febac1cb332280189a4dc6ff7f10d0de956bff279b284c5d4c2`) |
| NISR SAS 2026 Season B | Table workbook, 33 sheets | `data/raw/nisr_sas/SAS-2026B__5ca81c6b0a54.xlsx` (`5ca81c6b0a54c4a282ed718d134423920cc75279a5827bbe772fe6eb1a4e9d27`) |
| MINAGRI PSTA 5, abridged plan | National yield goals, results framework p.21 ([PDF](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf)) | 8 rows copied by hand into `data/reference/psta5_productivity_targets.csv` |
| District boundaries | geoBoundaries RWA ADM2, simplified, 30 districts, from NISR geodata, CC BY 4.0 ([file](https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/RWA/ADM2/geoBoundaries-RWA-ADM2_simplified.geojson)) | `data/raw/boundaries/` (SHA-256 `56b0995c7a7735847659b766e00c5cfa29b1b3a197f231dc396f399948c46c09`) |

Every file name carries the start of its checksum, so any change to a file can be detected
(`tests/test_real_data.py` checks this). Exact download links for 2024-2026 are in `data/sources.json`;
download times are in `data/raw/reference/download_log.txt`.

## Used to check the data or explain the method (not loaded into the app)

| Source | How it is used |
|---|---|
| NISR SAS 2024 annual workbook | The separate 2024 Season A and B files match it cell for cell (`tests/test_real_data.py`). Stored at `data/raw/reference/SAS_2024_Annual_Tables.xlsx`. |
| [NISR SAS Season B 2026 main report](https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf) | How the survey works: 1,200 sample squares of 300 by 300 m, 25 points each (pp.10-12); squares per district (Tables 3 and 4); large-scale farmers are farms of at least 10 ha, or 2 ha for horticulture (p.7); yields are farmer-reported (p.20); margins of error and plot counts for national crop areas only (Table 5, p.17). This is the basis for the 500 ha rule (`docs/methodology.md`, section 4). Not stored in the repository (about 10 MB). |
| [MINAGRI PSTA 5 abridged plan](https://www.minagri.gov.rw/fileadmin/user_upload/Minagri/Publications/Policies_and_strategies/PSTA_5_Abridged_version_Final.pdf) | The 50% productivity goal (p.14) and the yield targets (p.21), checked against `data/reference/psta5_productivity_targets.csv` (all 8 rows match). Not stored (11 MB). |

## Looked for but not used

| Item | Status |
|---|---|
| SAS Season B 2025 tables | Not found on statistics.gov.rw. Treated as missing, never as zero. |
| SAS 2014 to 2017 | Checked with `scripts/history_eda.py`. The 2015, 2016 and 2017 table workbooks give yields only by land type or province (the 2017 table titled "by district" has province columns). For 2014 only the PDF report was found, and it was not machine-read. None of these years is used. |
| SAS plot-level microdata | Access is by request through the NISR microdata catalogue. With it, real margins of error for district yields could be computed, replacing the 500 ha rule. Not requested within the hackathon. |
| Agricultural Household Survey 2024 | Not used within the deadline. A possible future source for farm-level constraints. |
| Rainfall (CHIRPS) | Considered, not used, so the app makes no claim about rainfall. |

## What these data are, and are not

- **Level:** published district averages plus national figures. No household, plot or sector records.
- **How the survey is drawn:** NISR samples 1,200 squares of land (20 in Nyarugenge to 68 in Nyagatare) and
  separately visits every large farm in full. NISR applies the weights; we use its published averages.
- **Yield:** kilograms per harvested hectare; the harvest amount is reported by the farmer, the area is
  measured by GPS.
- **Uncertainty:** margins of error are published only for national crop areas, not for district yields.
- **Seasons:** Season A (sown around September, harvested around February) and Season B (sown around
  March) are different growing seasons and are never combined.

## Data-quality notes (details in `reports/eda_findings.md`)

- Production equals yield times harvested area in all 2,587 cells of the 2024-2026 surveys where all three
  are published.
- Cells printed as 0 in 2024-2026: 198, 125, 225, 165 and 138. All are treated as "not reported".
- Harvested area is larger than planted area by more than 1% in 1, 8 and 1 cells (2024 A, 2024 B,
  2025 A), 8 of them paddy rice. Flagged, not changed.
- The national row is labelled "National", "Total" or "S/Total" depending on the table. Handled
  explicitly; a check refuses any survey missing a national figure.
- Season B 2026 main report, Table 5 (p.17), Fruits: the printed estimate (15,535 ha) lies outside its own
  printed 95% range (9,235 to 15,347). Not used by the app; noted as a publication inconsistency.
