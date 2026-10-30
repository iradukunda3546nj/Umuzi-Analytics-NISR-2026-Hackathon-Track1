# AI Use Disclosure

The competition rules allow AI tools as assistants but require disclosure; undisclosed use leads to disqualification (2026 Hackathon Competition announcement, p.3). This file is that disclosure. **The team must review it, correct it and add the sections marked TEAM before submitting.**

## Tool used
- **Claude (Anthropic), model Claude Opus 5.5**, through Claude Code (a coding agent running in VS Code), on 2026-10-29.

## What the AI did
Working from a detailed project specification written by the team (`UMUZI_ANALYTICS_FINAL_CLAUDE_CODE_PROMPT.md`), the AI agent:
- read the two competition PDFs and drafted the compliance matrix;
- searched the NISR website, downloaded the SAS table workbooks, the PSTA 5 abridged plan and district boundaries, and recorded checksums;
- proposed and compared candidate problems and drafted the value proposition;
- wrote all Python code in this repository (adapter, validation gates, snapshot store, analytics, charts, Streamlit app, tests, scripts);
- wrote the pre-specified research design, ran the statistical tests and drafted every document in `docs/` and `reports/`;
- inspected screenshots of the app and fixed layout defects.

## What the AI did not do
- It did not invent data. Every number in the app and reports is computed from NISR or MINAGRI documents downloaded on 2026-10-29, and the tests trace values back to source cells.
- It did not deploy the app, push to GitHub, submit the entry, or contact anyone.
- It did not test the tool with real users.

## Human responsibility (TEAM to complete)
- Which decisions the team made or changed (problem choice, thresholds, wording):
- Which parts each team member reviewed and verified:
- Any code or text the team rewrote:

The team is fully responsible for the submitted work, as the rules require.

## Other sources
All data and document sources are cited in `README.md`, `data/README.md` and `docs/data_inventory.md`.
