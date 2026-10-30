# Chart Storyboard

Shared palette: three signal hues for evidence categories (brick: persistent with low inputs; ochre: persistent with inputs not low; blue: latest-season dip) plus two neutrals (insufficient evidence; not below national). Validated with the dataviz validator in light mode, all pairs (worst CVD dE 15.9, normal-vision dE 16.0). Ochre and the neutrals fall below 3:1 contrast, so every chart has a legend, direct labels or hover text, and a table view. Light theme only.

## 1. National target attainment (Overview)
- **Audience decision**: does the national gap justify district-level prioritisation?
- **Question**: how far is each priority crop from its PSTA 5 2025/26 target?
- **Calculation**: (A+B production) / (A+B harvested area) per SAS year, divided by the target (`national_vs_target`).
- **Encoding**: dot plot on a percentage-of-target axis with a 100% reference line; two dots per crop (SAS 2024, SAS 2026), dark for latest. A dot plot avoids a bar baseline at zero that would hide differences between 80% and 97%.
- **Insight (after computation)**: all 8 crops are below target, soybean lowest at 52%.
- **Limitations**: aggregation approximates PSTA 5's method; Season C excluded.
- **Product link**: leads to the district views.

## 2. Evidence map (Evidence Map)
- **Audience decision**: where are the shortfalls, geographically?
- **Calculation**: `evidence_table` category per district.
- **Encoding**: choropleth with real NISR-derived boundaries; categorical fill; focus district outlined; legend counts. A map is justified because geographic clustering (for example western maize) is part of the interpretation.
- **Insight**: maize Season A persistent shortfalls include all 3 Kigali City districts and 5 of the 7 Western Province districts; the other 4 (Ruhango, Nyamagabe, Gicumbi, Rwamagana) are scattered.
- **Limitations**: area dominates perception; small districts (Kigali) are hard to see, so the table is always shown.
- **Product link**: click-through via focus district to the evidence panel and brief.

## 3. Persistence dot plot (Persistence; signature chart)
- **Audience decision**: recurring problem or one-off?
- **Calculation**: yield ratio per matched release; persistence flag.
- **Encoding**: ranked dot plot, one dot per release shaded old to new, grey range bar, reference lines at 1.0 and the threshold; brick square marks persistent districts.
- **Insight**: 12 maize Season A districts below 0.9 x national in all three releases; median range 0.06.
- **Limitations**: thin-coverage ratios are plotted but excluded from persistence.
- **Product link**: defines the "persistent" input to the category.

## 4. Input context scatter (Input Context)
- **Audience decision**: input access, or another constraint?
- **Calculation**: district improved-seed % vs inorganic-fertilizer %, national reference lines, category colour.
- **Encoding**: scatter with quadrant reference lines; direct labels only for persistent districts.
- **Insight**: 9 of 12 persistent maize districts are not in the low-low quadrant; a western cluster is high-fertilizer, low-seed.
- **Limitations**: inputs pooled across crops; association, not effect.
- **Product link**: drives the two persistent categories and their next steps.

## 5. Triage matrix (Triage Matrix)
- **Audience decision**: district-wide constraint or crop-specific?
- **Calculation**: category per district for each priority crop.
- **Encoding**: heatmap grid with 2px gaps, categorical fills, legend proxies.
- **Insight**: 10 districts have persistent shortfalls in three or more crops in Season A.
- **Limitations**: sparse crops (wheat, rice) are mostly insufficient evidence.

## 6. District comparison (Compare Districts)
- **Audience decision**: which peer district to compare or learn from?
- **Encoding**: line chart of yields per release with a dotted national line; open markers for thin coverage; comparability warning above the chart.
