# Data Dictionary

## Canonical record (`data/snapshots/<id>/records.csv`)

| Column | Type | Description |
|---|---|---|
| `release_id` | text | e.g. `SAS-2026A`; one per NISR season release, 2018 A to 2026 B |
| `season_year` | int | SAS year (2026 = agricultural year 2025/26) |
| `season` | A or B | Season type |
| `district` | text | One of the 30 districts (spelling as in NISR tables and boundaries) or `National` |
| `crop` | text | Canonical crop key (below) or `all` for district-level input indicators |
| `metric` | text | See metrics |
| `value` | float or empty | Empty unless `value_status = observed` |
| `value_status` | text | `observed`, `reported_zero` (NISR printed 0), `blank`, `invalid_negative`, `invalid_range` |
| `source_table` | text | Sheet name and title of the source table, e.g. `Table 13: Season A 2026_Average yield...` |

Join key: (`release_id`, `district`, `crop`, `metric`). District names join to the boundary file on `properties.shapeName` (all 30 match exactly).

## Metrics

| Metric | Unit | NISR table (title pattern) | Notes |
|---|---|---|---|
| `yield_kg_ha` | kg per harvested ha | "Average yield by crop type and/per district (Kg/Ha)"; 2018: "Yield of main crops by District (Kg/Ha)", transposed | Excludes large-scale-farmer, CIP-crop and Season C site tables. A title without kg/ha is rejected. Farmer-estimated. |
| `harvested_ha` | ha | "Harvested area by crop type and district (Ha)" | Coverage denominator |
| `cultivated_ha` | ha | "Cultivated area by crop type and district (Ha)" | |
| `production_t` | metric tonnes | "Crop production by crop type and district (MT)" | National row printed as "S/Total" |
| `improved_seed_farmers_pct` | % of farmers | "Use of (improved) seeds by farmer type/categories per district", farmers Overall column | All crops pooled; 2018 not comparable (not loaded) |
| `inorganic_fert_farmers_pct` | % of farmers | "Use of Inorganic fertilizer by farmer type per district", Overall | National row sometimes "Total" |
| `organic_fert_farmers_pct` | % of farmers | "Use of organic fertilizer by farmer type per district", Overall | Context only |
| `erosion_protection_farmers_pct` | % of farmers | "Percentage of farmers who practiced agricultural practices", erosion column | Optional; context only |

## Crop keys

`maize, sorghum, paddy_rice, wheat, cassava, sweet_potato, irish_potato, yams_taro, cooking_banana, dessert_banana, beer_banana, bean, bush_bean, climbing_bean, pea, groundnut, soybean, vegetables, fruits`. Crop-group subtotal columns (Cereals, Tubers and Roots, and so on) are deliberately not ingested. `bean` is NISR's all-bean column (bush plus climbing).

## Derived indicators (`src/analytics/indicators.py`)

| Indicator | Formula |
|---|---|
| `yield_ratio` | district `yield_kg_ha` / national `yield_kg_ha`, same crop and release |
| `reliable` | yield observed and `harvested_ha` >= 500 (configurable) |
| `below` | `yield_ratio` < 0.90 (configurable) |
| `window_releases` | the last 3 releases of the season type, ending at the latest |
| `reliable_in_window`, `below_in_window` | counts over the window, reliable releases only |
| `repeated_below` | latest release reliable, at least 2 reliable and at least 2 below in the window |
| `limited_reason` | plain-language reason when the category is "Evidence too limited to judge" |
| `inputs_low` | district improved-seed and inorganic-fertilizer uptake both below national, latest release; unknown if any value is missing |
| `category` | see `docs/methodology.md` |
| National A+B yield | (A production + B production) / (A harvested + B harvested), same SAS year, both seasons required |

## Reference table: `data/reference/psta5_productivity_targets.csv`

`crop, baseline_2023, target_2024_25 ... target_2028_29, unit (MT/ha), source`. Transcribed from PSTA 5 Abridged, p.21.
