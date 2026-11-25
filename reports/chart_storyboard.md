# Chart Storyboard

Shared palette: three signal hues for evidence categories (brick: repeatedly below with low input uptake; ochre: repeatedly below with input uptake not low; blue: below in the latest season only) plus two neutrals (evidence too limited; not below national). Validated with the dataviz validator in light mode, all pairs (worst CVD dE 15.9, normal-vision dE 16.0). Ochre and the neutrals fall below 3:1 contrast, so every view has a legend with plain-language meanings and counts, hover text or labels, and a table. Light theme only.

The app is map first: the overview answers the question in one screen, and every chart below is on demand.

## 1. Rwanda map with the selected district (overview)
- **Decision it supports**: where are this crop's shortfalls, and where does my district sit?
- **Calculation**: `evidence_table` category per district (rules 2.0: below 90% of national in at least 2 of the last 3 surveys; input split on pooled uptake).
- **Encoding**: choropleth on NISR-derived boundaries; the selected district is outlined in black and labelled. The legend sits under the map and states each category's meaning and count, so colour is never the only carrier of meaning.
- **Insight**: maize Season A, 14 districts repeatedly below national, concentrated in Western Province and Kigali; only 3 of the 14 have low input uptake.
- **Limitations**: area dominates perception; small Kigali districts are hard to see, so the table is one click away.

## 2. Finding card and last-3-surveys strip (overview, beside the map)
- **Decision**: what is the pattern here, and what do I check first?
- **Encoding**: one sentence from `build_finding`; three pills (one per survey in the window) showing % of national, coloured below / not below / thin; then the figures, the survey releases used, the next check and the limitations.
- **Product link**: identical text in the evidence brief and the Umuzi Assistant.

## 3. Target arrow (overview)
- **Decision**: how far is Rwanda from the PSTA 5 target for this crop?
- **Calculation**: national (A+B production) / (A+B harvested area) for the latest year with a target (`target_position`).
- **Encoding**: a road from the PSTA baseline to a bullseye at the target; a marker for where Rwanda stands, with its % of target, and the remaining gap in t/ha written on the road. One number in context beats a gauge.
- **Insight**: maize 1.80 t/ha in 2025/26, 87% of the 2.06 t/ha target, 0.26 t/ha to go.
- **Limitations**: aggregation approximates PSTA 5's method; Season C excluded; targets are national only.

## 4. Survey-by-survey grid (details)
- **Decision**: is this a recurring problem or a one-off, and since when?
- **Encoding**: districts x surveys since 2018, each cell the % of national, coloured by state; the 3-survey window is outlined and the selected district boxed. Rows follow the map's category order.
- **Limitations**: 2018-2019 positions are weakly comparable with later years (shown for context only).

## 5. District history (details)
- **Encoding**: the selected district's % of national in every survey of the season, with lines at national and at the 90% benchmark; open markers for thin coverage; the window shaded.

## 6. Input uptake scatter (details)
- **Decision**: input access, or another constraint?
- **Encoding**: improved-seed % vs inorganic-fertilizer % with national reference lines and category colour; labels on repeatedly-below districts; the selected district ringed.
- **Insight**: 11 of 14 repeatedly-below maize districts are not in the low-low quadrant; a western cluster combines above-national fertilizer with below-national seed uptake.
- **Limitations**: inputs pooled across crops; association, not effect.

## 7. Triage matrix (report figure)
- **Encoding**: district x priority crop grid of categories (`reports/figures/triage_matrix_season_*.html`).
- **Insight**: 11 districts are repeatedly below national in three or more priority crops in Season A, 8 in Season B.
