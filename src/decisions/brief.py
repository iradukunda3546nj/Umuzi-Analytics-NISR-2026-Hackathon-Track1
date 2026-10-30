"""Planner Evidence Brief: a shareable, source-traceable summary for one district and crop.

The brief is assembled only from the evidence-table row and the snapshot
manifest. It states the observed position, the comparison basis, the evidence
category, the investigation route, field-check questions and the limits.
"""
from __future__ import annotations

import io

import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_PERSISTENT_INPUTS_OK, CATEGORY_PERSISTENT_LOW_INPUT,
                                      Params)
from src.config import CROP_LABELS, PRODUCT_NAME

FIELD_QUESTIONS = {
    CATEGORY_PERSISTENT_LOW_INPUT: [
        "Were improved seed and fertilizer for this crop available at the Farm Service Centre or agro-dealer before sowing?",
        "What share of growers of this crop could afford the subsidised price, and did they register in the Smart Nkunganire System?",
        "Did input delivery arrive after the main sowing window?",
    ],
    CATEGORY_PERSISTENT_INPUTS_OK: [
        "Is input use on this crop specifically as high as the district all-crop figure suggests?",
        "What do soil tests (acidity, organic matter) show in the main production sectors for this crop?",
        "Are erosion, slope or waterlogging affecting the plots planted with this crop?",
        "Are the varieties grown suited to the altitude and rainfall of the district?",
    ],
    CATEGORY_DIP: [
        "Was there a rainfall, pest or disease shock in the latest season in this district?",
        "Did sowing dates shift compared with earlier seasons?",
    ],
    CATEGORY_INSUFFICIENT: [
        "How large is the area actually planted with this crop in the district, and where?",
        "Can the district agronomist confirm yields from local records or crop-cut observations?",
    ],
    CATEGORY_NOT_BELOW: [
        "No shortfall flagged. Check whether practices in this district could inform lower-performing neighbours.",
    ],
}

LIMITS = [
    "District yields are NISR survey estimates based on farmer-reported yield (SAS report 2026A, p.22); "
    "district-level standard errors are not published.",
    "Input uptake is the share of farmers using the input on any crop in the district, not on this crop.",
    "Co-occurrence of low yield and low input uptake is not evidence that inputs would close the gap.",
    "Persistence means a consistent position in repeated published estimates; whether NISR revisits the "
    "same sample segments across seasons is not stated in the report, so this is not independent replication.",
]


def _fmt(v, nd=2, suffix=""):
    return "not reported" if v is None or pd.isna(v) else f"{v:,.{nd}f}{suffix}"


def build_brief(row: pd.Series, manifest: dict, params: Params = Params()) -> str:
    crop = CROP_LABELS.get(row["crop"], row["crop"])
    ratio_cols = [c for c in row.index if c.startswith("ratio_")]
    history = "\n".join(f"| {c.replace('ratio_', '')} | {_fmt(row[c])} |" for c in ratio_cols)
    rel = [r for r in manifest["releases"] if r["release_id"] == row["latest_release"]]
    src_url = rel[0]["source_url"] if rel else "see Data and Methods"
    questions = "\n".join(f"- {q}" for q in FIELD_QUESTIONS[row["category"]])
    limits = "\n".join(f"- {x}" for x in LIMITS)
    return f"""# {PRODUCT_NAME} - Evidence Brief

**{row['district']} District ({row['province']}) | {crop} | Season {row['season']}**
Data snapshot: `{manifest['snapshot_id']}` | Latest release: {row['latest_release']}

## Evidence category
**{row['category']}**

## What the published data show
- Latest {crop.lower()} yield: {_fmt(row['latest_yield_kg_ha'] / 1000)} t/ha against a national {_fmt(row['national_yield_kg_ha'] / 1000)} t/ha (ratio {_fmt(row['latest_ratio'])}).
- Harvested area in the latest release: {_fmt(row['latest_harvested_ha'], 0)} ha (coverage threshold {params.min_harvested_ha:,.0f} ha).
- Below {params.gap_threshold:.0%} of national in {int(row['seasons_below'])} of {int(row['matched_seasons_adequate'])} Season {row['season']} releases with adequate coverage.
- Farmers using improved seed (all crops): {_fmt(row['improved_seed_pct'], 1, '%')} vs national {_fmt(row['national_improved_seed_pct'], 1, '%')}.
- Farmers applying inorganic fertilizer (all crops): {_fmt(row['inorganic_fert_pct'], 1, '%')} vs national {_fmt(row['national_inorganic_fert_pct'], 1, '%')}.

| Release | Yield / national |
|---|---|
{history}

## Suggested next step (investigation, not prescription)
{row['next_step']}

## Questions to verify in the field
{questions}

## Limits of this evidence
{limits}

## Source
National Institute of Statistics of Rwanda, Seasonal Agricultural Survey district tables (CC BY 4.0).
Latest release file: {src_url}
Comparison basis: same crop, same season type, district yield divided by the national yield of the same release.
"""


def brief_csv(row: pd.Series) -> bytes:
    buf = io.StringIO()
    row.to_frame().T.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
