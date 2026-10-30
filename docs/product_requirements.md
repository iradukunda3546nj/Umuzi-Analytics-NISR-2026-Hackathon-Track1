# Product Requirements - Umuzi Analytics

## Primary user
District agronomist or Director of Agriculture, and MINAGRI/RAB planning staff preparing for the next Season A or B. They read tables and charts but do not write code.

## Core decision
Which district-crop combinations should receive field diagnosis first, and which constraint should that visit examine?

## Functional requirements (all implemented)

| ID | Requirement | Where |
|---|---|---|
| F1 | Global scope (season type, crop, focus district) propagates to every view, table and export | Sidebar; `tests/test_app.py::test_filters_propagate_to_header_brief_and_exports` |
| F2 | Classify every district into one evidence category for the chosen crop and season | Evidence Map, table |
| F3 | Show persistence across all matched releases | Persistence |
| F4 | Show district input uptake against national with category | Input Context |
| F5 | Cross-crop overview per district | Triage Matrix |
| F6 | Compare two districts on the same basis, warning when coverage is thin or a value is not reported | Compare Districts |
| F7 | Export a brief (Markdown) and evidence row (CSV); export the full table (CSV) | Evidence Brief, Evidence Map |
| F8 | National context against PSTA 5 targets | Overview |
| F9 | Data status: releases, checksums, gates, warnings, missing releases, snapshot history | Data and Methods |
| F10 | Adjustable thresholds with a visible non-default label | Sidebar expander |
| F11 | New validated releases appear without UI code changes | Refresh pipeline |

## Non-functional requirements

- No login; publicly readable once deployed.
- Loads within the Streamlit Community Cloud free tier (about 2.7 GB memory): snapshot is 12,400 rows; boundaries 289 KB.
- No emojis, no decorative imagery; light theme with a validated chart palette.
- Every number traceable to a release, table and snapshot.

## Out of scope
Forecasting, intervention effect estimates, input allocation, sector-level analysis, user accounts, uploads from the browser.
