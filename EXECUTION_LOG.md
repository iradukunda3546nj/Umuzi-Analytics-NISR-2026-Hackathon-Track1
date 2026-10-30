# Execution Log

All work on 2026-10-29 (local time, UTC+2). Environment: Windows 11, Python 3.14.8, virtual environment outside the Box-synced folder (`C:\Users\jeanc\.venvs\umuzi`) so package files are not synced to Box.

## Plan
A. Inspect repository and rules. B. Choose one decision problem. C. Acquire and verify NISR data; build ingestion. D. Pre-specify hypotheses; analyse. E. Build the app. F. Test. G. Document and package.

## Stage A - Inspect
- Workspace contained only the specification and two competition PDFs; **no datasets**.
- Read both PDFs in full; wrote `docs/compliance_matrix.md`.
- Network: statistics.gov.rw reachable (www. prefix timed out); PyPI and GitHub reachable.

## Stage B/C - Data discovery and acquisition
- Found SAS publication pages by URL pattern and site search. Downloaded table workbooks for 2024A, 2024B, 2025A, 2026A, 2026B, plus the 2024 Annual workbook. **2025B not found.** Pages for 2019 to 2023 listed no table downloads.
- Downloaded MINAGRI PSTA 5 Abridged (targets, p.14, 21, 22), the SAS 2026A report (methodology pages), and geoBoundaries RWA ADM2 (30 districts, names match SAS exactly).
- Verified NISR terms of use: CC BY 4.0.
- Chose the problem (`docs/problem_discovery.md`, decision matrix) and wrote `docs/research_design.md` **before** computing any outcome relationship.

## Stage C - Ingestion
- Table numbers differ by release, so the adapter locates tables by title.
- Defect 1: season tag regex used `\b`, which fails on `Season A_Harvested`; the annual workbook's Season B parse picked Season A tables. Fixed.
- Cross-check: standalone 2024A/2024B equal the annual workbook cell for cell.
- Defect 2: national rows labelled "Total" (fertilizer) and "S/Total" (production) were dropped, which made every persistent district look "inputs at or above national". Found by inspecting implausible category counts. Fixed in adapter 1.1; added a gate that rejects a release without national reference values. During the fix, the gate correctly rejected two intermediate parser versions and kept the active snapshot unchanged.
- An attempted deletion of the buggy snapshots was blocked by a safety check. Instead, the adapter now carries a version and re-processing creates `correction` snapshots with lineage. The five adapter-1.0 snapshots remain in `data/snapshots/` as history.

## Stage D - Analysis
- `python -m scripts.run_analysis` (seed 20261029). H1 supported for 7 crops (rice not testable, n = 11). H2 supported (60 vs 16.9, p = 0.0005). H3 mixed: bean-fertilizer strong (rho 0.67 to 0.74); maize associations not significant after Holm.
- Read SAS 2026A methodology: yields are farmer estimates (p.22); segments per district 20 to 68 (Table 4); whether segments repeat across seasons is not stated.
- ML deliberately not used (`reports/analytical_methods.md`).

## Stage E - App
- Streamlit app with 8 views. Screenshot review (Playwright plus installed Chrome) at 1366, 1440, 1920 and 900 px found and fixed: inverted map polygons (winding order), map payload duplication, map bounds failing, legend overlap from an invalid font-family string, Streamlit theme override, clipped titles and source notes, oversized brief headings.
- Open issue: at 900 px with the sidebar open, the map does not draw.

## Stage F - Tests
- `python -m pytest`: **38 passed** (pipeline on synthetic fixtures, decision rules, real-data integrity and traceability, export consistency, 16 view renders, state propagation).

## Stage G - Package
- Documentation in `docs/`, `reports/`, `demo/`; README.

## Not done / blocked (needs the team)
- GitHub repository, Streamlit deployment and submission form: need the team's accounts and explicit authorisation.
- Demo video recording.
- Student eligibility documents (privacy decision on publishing them).
- User testing with planners.
- Completing the TEAM sections of the AI disclosure.
