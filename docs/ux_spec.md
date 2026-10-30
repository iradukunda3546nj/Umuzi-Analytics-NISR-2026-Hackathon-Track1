# UX Specification

## Layout
- **Left rail** (Streamlit sidebar): wordmark, eight views, analysis scope (season type, crop, focus district), threshold expander, snapshot ID and source.
- **Header band**: product name, the guiding question, releases in the snapshot, snapshot ID and approval date, current scope.
- **Analytical canvas**: one primary figure per view, followed by a Question / Pattern / Implication / Caveat note generated from computed values, then a table or detail.
- **Evidence panel** (Evidence Map, Evidence Brief): selected district, category badge, latest yield vs national, persistence count, coverage, input uptake vs national, next step.

## Views and the planner journey
1. **Overview**: three computed facts, the national target chart and how to use the workspace.
2. **Evidence Map**: map plus evidence panel plus full table with CSV export.
3. **Persistence**: ranked dot plot across releases (signature view).
4. **Input Context**: seed vs fertilizer scatter with national lines and computed associations.
5. **Triage Matrix**: districts by priority crops grid.
6. **Compare Districts**: two districts, comparability check, trend.
7. **Evidence Brief**: printable brief plus downloads.
8. **Data and Methods**: status, definitions, categories, refresh commands, snapshot history, sources.

## Visual system
- Palette: evergreen `#24493f` (accent), ink `#1f2421`, surface `#fcfcfb`, rail `#f1f1ec`. Evidence categories: brick `#9c3d24`, ochre `#d08a1e`, blue `#2f6db5`, warm grey `#c2beb4`, pale `#f1f3ef`. Validated (`src/viz/charts.py` header).
- Typography: Streamlit sans for UI; charts use a system sans stack (Segoe UI, Roboto, Helvetica Neue, Arial).
- Every chart: conclusion title computed from data, one-line subtitle with the definition, source line with releases and snapshot ID, reference lines labelled directly, hover detail on every mark.
- Missing values: "not reported" in text; open markers for thin coverage; grey category on maps.

## States
- **No active snapshot**: error message with the exact command to fix it; app stops.
- **Thin or missing data in a comparison**: warning naming the district, release and harvested area.
- **Non-default thresholds**: caption under the slider.
- **Missing release**: warning on Data and Methods.
- **Loading**: Streamlit spinner suppressed; cached per snapshot.
