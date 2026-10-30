# UX Acceptance Record

Tested locally on 2026-10-29 with Streamlit 1.66.1 in Chrome (headless, driven by Playwright), against snapshot `snap-20261029T103445Z-e435e56c`. These are developer checks, **not user tests**: no planner has used the app yet.

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Every view renders without error, both seasons | `tests/test_app.py` (AppTest, 16 combinations) | Pass |
| 2 | Scope propagates to header, brief and downloads | `test_filters_propagate_to_header_brief_and_exports` | Pass |
| 3 | Non-default thresholds are labelled | `test_sensitivity_threshold_is_flagged` | Pass |
| 4 | 1366 x 768 layout | Screenshots of all 8 views | Pass after fixes (see below) |
| 5 | 1440 x 900 layout | Screenshots | Pass |
| 6 | 1920 x 1080 layout | Screenshot (Evidence Map) | Pass |
| 7 | Narrow window (900 px) with sidebar open | Screenshot | **Partial**: header, panel and table usable; **map does not draw** in the narrow column. Workaround: collapse the sidebar. Open issue. |
| 8 | Chart text legibility | Visual review | Pass after fixing legend overlap (invalid font-family string) and clipped source notes |
| 9 | Colour accessibility | dataviz validator, all pairs, light mode | Pass for separation; contrast relief via labels, legend and tables |
| 10 | Keyboard use | Streamlit native widgets (radio, select, slider, buttons) are keyboard-focusable | Not formally audited with a screen reader |
| 11 | Dead controls | Every control changes output (covered by tests 1 to 3) | Pass |
| 12 | Empty and error states | Code review: no-snapshot stop, comparability warning, missing-release warning | Implemented; no-snapshot state not screenshot-tested |
| 13 | Does it look like a generic AI dashboard? | Self-review against `docs/ux_spec.md`: no KPI tile wall, no gradients, no emojis, one figure per view with evidence notes | Judged pass by the developer; needs external review |

## Defects found and fixed during acceptance
- Map drew each district as its complement (polygon winding order); fixed by rewinding rings.
- Map blank at some widths (bounds computed from legend-only traces); fixed with explicit extent.
- Legends overlapping (unquoted "Source Sans 3" in the font family made Plotly measure and render in different fonts).
- Streamlit's Plotly theme overrode layout; disabled with `theme=None`.
- Map payload reduced from about 1.2 MB to 265 KB by embedding boundaries once.
- Brief headings oversized on screen; demoted for display.
