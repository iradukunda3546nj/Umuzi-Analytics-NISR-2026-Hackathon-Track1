# Product Requirements - Umuzi Analytics

## Primary user
District agronomist or Director of Agriculture, and MINAGRI/RAB planning staff preparing for the next Season A or B. They read tables and charts but do not write code.

## Core decision
Which district-crop combinations should receive field diagnosis first, and which constraint should that visit examine?

## Functional requirements (all implemented)

| ID | Requirement | Where |
|---|---|---|
| F1 | Type to select crop and district, then season; the selection drives the map, finding, charts, exports and assistant | Top of page; `tests/test_app.py` |
| F2 | Rwanda map: every district's category for the chosen crop and season, selected district outlined, legend with meanings and counts | Overview |
| F3 | One short finding beside the map with its figures, the last 3 surveys and the survey releases used | Overview finding card |
| F4 | District input uptake against national, with category | Input uptake tab |
| F5 | Survey-by-survey pattern since 2018, all districts and the selected district | Detail tabs |
| F6 | Practical questions answered from the same data and rules as the map, including comparisons of districts | Umuzi Assistant; `tests/test_assistant.py` |
| F7 | Export a brief (Markdown) and figures (CSV); export the full table (CSV) | Overview, All districts table |
| F8 | National position against the PSTA 5 target | Target arrow (overview) |
| F9 | Data status: usable years, gates and warnings per survey, missing surveys, duplicate checks, backtest | Data and methods tab |
| F10 | Adjustable thresholds with a visible non-default label | Data and methods tab |
| F11 | New validated releases appear without UI code changes | Refresh pipeline |
| F12 | Cross-crop overview per district | Report figure `reports/figures/triage_matrix_season_*.html` (not an app view) |

## Non-functional requirements

- No login; publicly readable once deployed.
- Loads within the Streamlit Community Cloud free tier (about 2.7 GB memory): snapshot is 40,052 rows (6.7 MB); boundaries 289 KB.
- No emojis, no decorative imagery; light theme with a validated chart palette.
- Every number traceable to a release, table and snapshot.

## Out of scope
Forecasting (tested and not adopted, see docs/methodology.md section 7), intervention effect estimates, input allocation, sector-level analysis, user accounts, uploads from the browser.
