"""The finding for one district, crop and season: the single source of every sentence.

The map side panel, the evidence brief and the Umuzi Assistant all call
`build_finding`, so for the same selection they state the same category, the
same figures and the same survey releases. Nothing here computes an indicator:
every number comes from `evidence_table` (src/analytics/indicators.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_REPEATED_INPUTS_OK, CATEGORY_REPEATED_LOW_INPUT,
                                      Params, load_targets, national_vs_target)
from src.config import CROP_LABELS

POOLED_NOTE = ("Seed and fertilizer uptake is published per district for all crops together, "
               "not for this crop, so it shows the district's general input use.")
YIELD_NOTE = ("District yields are survey estimates from farmers' reported harvests; NISR does not "
              "publish district-level margins of error, so differences under 10% are not flagged.")
CAUSE_NOTE = ("The survey shows where yields are low, not why. Low input uptake occurring together with "
              "a low yield is not proof that more inputs would close the gap.")
EARLY_YEARS_NOTE = ("District rankings from 2018 and 2019 agree only weakly with later years, so the "
                    "pattern uses the three most recent releases of this season.")

FIELD_CHECKS = {
    CATEGORY_REPEATED_LOW_INPUT: [
        "Were improved seed and fertilizer for this crop in stock at the Farm Service Centre or agro-dealer before planting?",
        "Could growers of this crop afford them, and were they registered for the subsidy (Smart Nkunganire)?",
        "Did inputs arrive after the main planting window?",
        "Do growers of this crop actually apply fertilizer to it, or mainly to other crops?",
    ],
    CATEGORY_REPEATED_INPUTS_OK: [
        "Is fertilizer actually applied to this crop, or does the district's all-crop figure come from other crops?",
        "What do soil tests show for acidity and organic matter where this crop is grown?",
        "Are erosion, steep slopes or waterlogging affecting these plots?",
        "Are the varieties planted suited to the district's altitude and rainfall?",
    ],
    CATEGORY_DIP: [
        "Was there a rainfall, pest or disease shock in this district in the latest season?",
        "Did planting dates or the area planted change compared with earlier seasons?",
    ],
    CATEGORY_INSUFFICIENT: [
        "How much of this crop is actually planted in the district, and where?",
        "Can the district agronomist confirm yields from local records or crop-cut measurements?",
    ],
    CATEGORY_NOT_BELOW: [
        "No shortfall flagged. Check whether practices here could help lower-yielding neighbouring districts.",
    ],
}


def crop_name(crop: str) -> str:
    return CROP_LABELS.get(crop, crop).replace(" (all)", "")


def release_name(release_id: str) -> str:
    """'SAS-2026A' -> 'Season A 2026'."""
    return f"Season {release_id[-1]} {release_id[4:8]}"


def pct(v: float) -> str:
    return "not reported" if v is None or pd.isna(v) else f"{v:.0%}"


@dataclass
class WindowPoint:
    release_id: str
    ratio: float | None
    reliable: bool
    below: bool


@dataclass
class Finding:
    district: str
    crop: str
    season: str
    category: str
    headline: str
    latest_release: str
    window: list[WindowPoint]
    figures: list[tuple[str, str]]
    releases: list[str]
    limitations: list[str]
    next_step: str
    field_checks: list[str]
    row: pd.Series = field(repr=False)

    @property
    def is_repeated(self) -> bool:
        return self.category in (CATEGORY_REPEATED_LOW_INPUT, CATEGORY_REPEATED_INPUTS_OK)


def _window(row: pd.Series, params: Params, harvested: dict[str, float]) -> list[WindowPoint]:
    pts = []
    for rel in row["window_releases"].split(","):
        r = row.get(f"ratio_{rel}")
        ha = harvested.get(rel, np.nan)
        reliable = pd.notna(r) and pd.notna(ha) and ha >= params.min_harvested_ha
        pts.append(WindowPoint(rel, None if pd.isna(r) else float(r), bool(reliable),
                               bool(reliable and r < params.gap_threshold)))
    return pts


def _years(points: list[WindowPoint]) -> str:
    ys = [p.release_id[4:8] for p in points]
    return ys[0] if len(ys) == 1 else f"{ys[0]}-{ys[-1]}"


def build_finding(ev: pd.DataFrame, panel: pd.DataFrame, district: str,
                  params: Params = Params()) -> Finding:
    """`ev` is the evidence table for one crop and season; `panel` is crop_panel(records)."""
    row = ev.set_index("district").loc[district].copy()
    row["district"] = district
    crop, season, latest = row["crop"], row["season"], row["latest_release"]
    c, cat = crop_name(crop), row["category"]
    h = panel[(panel["district"] == district) & (panel["crop"] == crop) & (panel["season"] == season)]
    window = _window(row, params, h.set_index("release_id")["harvested_ha"].to_dict())
    reliable = [p for p in window if p.reliable]
    n_below = sum(p.below for p in reliable)
    span = f"Season {season} {_years(window)}"
    ratio = row["latest_ratio"]

    if cat in (CATEGORY_REPEATED_LOW_INPUT, CATEGORY_REPEATED_INPUTS_OK):
        count = f"all {n_below}" if n_below == len(reliable) else f"{n_below} of the {len(reliable)}"
        lead = f"{district}'s {c.lower()} yield was below the national benchmark in {count} reliable surveys of {span}."
        if cat == CATEGORY_REPEATED_LOW_INPUT:
            tail = " Reported uptake of both improved seed and fertilizer is also below national."
        else:
            tail = (" Reported input uptake is not low, so input access alone is unlikely to explain the gap.")
        headline = lead + tail
    elif cat == CATEGORY_DIP:
        headline = (f"{district}'s {c.lower()} yield fell below the national benchmark in "
                    f"{release_name(latest)}, but not in the other reliable surveys of {span}.")
    elif cat == CATEGORY_NOT_BELOW:
        headline = (f"{district}'s {c.lower()} yield was {pct(ratio)} of the national yield in "
                    f"{release_name(latest)}, not below the 90% benchmark.")
    else:
        headline = (f"There is not enough reliable evidence to judge {district}'s {c.lower()} yield in "
                    f"Season {season}: {row['limited_reason']}.")

    figures = []
    if pd.notna(row["latest_yield_kg_ha"]):
        figures.append((f"Yield, {release_name(latest)}",
                        f"{row['latest_yield_kg_ha'] / 1000:.2f} t/ha vs national "
                        f"{row['national_yield_kg_ha'] / 1000:.2f} t/ha ({pct(ratio)} of national)"))
    if pd.notna(row["latest_harvested_ha"]):
        figures.append(("Harvested area", f"{row['latest_harvested_ha']:,.0f} ha "
                                          f"(reliable from {params.min_harvested_ha:,.0f} ha)"))
    figures.append(("Recent pattern", "; ".join(
        f"{release_name(p.release_id)}: " + (pct(p.ratio) if p.reliable else
                                             ("not reported" if p.ratio is None else f"{pct(p.ratio)}, thin coverage"))
        for p in window)))
    if row["inputs_known"]:
        figures.append(("Farmers using improved seed (all crops)",
                        f"{row['improved_seed_pct']:.1f}% vs national {row['national_improved_seed_pct']:.1f}%"))
        figures.append(("Farmers using inorganic fertilizer (all crops)",
                        f"{row['inorganic_fert_pct']:.1f}% vs national {row['national_inorganic_fert_pct']:.1f}%"))

    limitations = [YIELD_NOTE]
    if row["inputs_known"]:
        limitations.append(POOLED_NOTE)
    if cat in (CATEGORY_REPEATED_LOW_INPUT, CATEGORY_REPEATED_INPUTS_OK, CATEGORY_DIP):
        limitations.append(CAUSE_NOTE)
    if any(not p.reliable for p in window):
        limitations.append("At least one recent survey has no reliable value here (not reported or under "
                           f"{params.min_harvested_ha:,.0f} ha harvested); it is shown but not counted.")

    return Finding(district=district, crop=crop, season=season, category=cat, headline=headline,
                   latest_release=latest, window=window, figures=figures,
                   releases=[p.release_id for p in window], limitations=limitations,
                   next_step=row["next_step"], field_checks=FIELD_CHECKS[cat], row=row)


@dataclass
class TargetPosition:
    crop: str
    agricultural_year: str
    yield_t_ha: float
    target_t_ha: float
    baseline_t_ha: float
    final_target_t_ha: float
    attainment: float


def target_position(records: pd.DataFrame, crop: str) -> TargetPosition | None:
    """Latest national Season A+B yield against its PSTA 5 target (None if no target)."""
    targets = load_targets()
    nvt = national_vs_target(records, targets)
    d = nvt[(nvt["crop"] == crop)].dropna(subset=["target_t_ha"])
    if d.empty:
        return None
    r = d.sort_values("season_year").iloc[-1]
    t = targets[targets["crop"] == crop].iloc[0]
    return TargetPosition(crop=crop, agricultural_year=r["agricultural_year"], yield_t_ha=float(r["yield_t_ha"]),
                          target_t_ha=float(r["target_t_ha"]), baseline_t_ha=float(t["baseline_2023"]),
                          final_target_t_ha=float(t["target_2028_29"]), attainment=float(r["attainment"]))
