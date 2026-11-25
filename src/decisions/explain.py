"""Plain-language explanation of a Finding: the three questions a user asks.

1. Is it a pattern or a one-off?        (the last 3 surveys)
2. Were seed and fertilizer part of it? (district share of farmers vs Rwanda)
3. So what should be checked first?     (short, field-ready checks)

The "Why" page, the action card and the Umuzi Assistant all read this object,
so the words a user sees are the same everywhere. Nothing is computed here
that `evidence_table` did not already compute; this module only words it.

Wording rules: "use" rather than "uptake"; "lower than Rwanda" rather than
"below the national mean"; no claim of cause, because the survey records yields
and input use, not why a yield was low.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_REPEATED_INPUTS_OK, CATEGORY_REPEATED_LOW_INPUT)
from src.decisions.finding import Finding, crop_name, pct, release_name

# Short labels for the five categories (map legend, chips, assistant).
PLAIN_CATEGORY = {
    CATEGORY_REPEATED_LOW_INPUT: "Repeated shortfall, seed and fertilizer use low",
    CATEGORY_REPEATED_INPUTS_OK: "Repeated shortfall, seed and fertilizer use not low",
    CATEGORY_DIP: "One-season dip",
    CATEGORY_INSUFFICIENT: "Not enough data",
    CATEGORY_NOT_BELOW: "On par with Rwanda or above",
}

# (icon, check). Short versions of FIELD_CHECKS in finding.py, for cards and chat.
SHORT_CHECKS = {
    CATEGORY_REPEATED_LOW_INPUT: [
        ("store", "Were seed and fertilizer in stock before planting?"),
        ("coin", "Could farmers afford them? Registered for Smart Nkunganire?"),
        ("clock", "Did the inputs arrive in time for planting?"),
        ("field", "Are they applied to this crop, or mostly to others?"),
    ],
    CATEGORY_REPEATED_INPUTS_OK: [
        ("field", "Is fertilizer actually applied to this crop?"),
        ("soil", "What do soil tests say about acidity and organic matter?"),
        ("slope", "Are erosion, steep slopes or waterlogging hurting plots?"),
        ("seed", "Do the varieties suit the altitude and rainfall?"),
    ],
    CATEGORY_DIP: [
        ("rain", "Was there a rain, pest or disease shock this season?"),
        ("clock", "Did planting dates or planted area change?"),
        ("repeat", "Re-check after the next survey before moving resources."),
    ],
    CATEGORY_INSUFFICIENT: [
        ("field", "How much of this crop is really grown here?"),
        ("check", "Can local crop-cut records confirm the yield?"),
    ],
    CATEGORY_NOT_BELOW: [
        ("share", "Could practices here help lower-yielding neighbours?"),
    ],
}


@dataclass
class InputSignal:
    name: str              # "Improved seed" / "Fertilizer"
    district_pct: float | None
    national_pct: float | None
    lower: bool | None     # None when not published on a comparable basis

    @property
    def word(self) -> str:
        if self.lower is None:
            return "Not published"
        return "Lower than Rwanda" if self.lower else "Not lower than Rwanda"


@dataclass
class Explanation:
    category_label: str
    is_shortfall: bool
    pattern_title: str
    pattern_line: str
    seed: InputSignal
    fertilizer: InputSignal
    verdict_title: str
    verdict_line: str
    checks: list[tuple[str, str]]
    survey: str            # e.g. "Season A 2026"


def _signal(name: str, row: pd.Series, col: str, ncol: str) -> InputSignal:
    if not row["inputs_known"]:
        return InputSignal(name, None, None, None)
    d, n = float(row[col]), float(row[ncol])
    return InputSignal(name, d, n, d < n)


def explain(f: Finding) -> Explanation:
    row, cat = f.row, f.category
    c = crop_name(f.crop).lower()
    reliable = [p for p in f.window if p.reliable]
    n_below = sum(p.below for p in reliable)
    latest = release_name(f.latest_release)
    seed = _signal("Improved seed", row, "improved_seed_pct", "national_improved_seed_pct")
    fert = _signal("Fertilizer", row, "inorganic_fert_pct", "national_inorganic_fert_pct")

    if f.is_repeated:
        pattern = ("A repeated shortfall",
                   f"Below 90% of Rwanda's {c} yield in {n_below} of the last {len(reliable)} reliable surveys.")
    elif cat == CATEGORY_DIP:
        pattern = ("A one-season dip", f"Below 90% of Rwanda's yield in {latest} only.")
    elif cat == CATEGORY_NOT_BELOW:
        pattern = ("No shortfall", f"{pct(row['latest_ratio'])} of Rwanda's {c} yield in {latest}.")
    else:
        pattern = ("Not enough data", f"{str(row['limited_reason']).capitalize()}.")

    if cat == CATEGORY_REPEATED_LOW_INPUT:
        verdict = ("Seed and fertilizer use are both low here",
                   "Fewer farmers here use improved seed and fertilizer than across Rwanda. "
                   "Check access to them first.")
    elif cat == CATEGORY_REPEATED_INPUTS_OK:
        if seed.lower and not fert.lower:
            verdict = ("Improved seed use is low, fertilizer use is not",
                       "Inputs alone are unlikely to explain the gap. Check seed supply for this crop, "
                       "then soil, slopes and varieties.")
        elif fert.lower and not seed.lower:
            verdict = ("Fertilizer use is low, improved seed use is not",
                       "Inputs alone are unlikely to explain the gap. Check fertilizer for this crop, "
                       "then soil, slopes and varieties.")
        else:
            verdict = ("Seed and fertilizer use are not low here",
                       "Look beyond inputs: soil, slopes, varieties and water for this crop.")
    elif cat == CATEGORY_DIP:
        verdict = ("It could be a one-season shock",
                   "Check weather, pests and planting dates before moving resources.")
    elif cat == CATEGORY_NOT_BELOW:
        verdict = ("No shortfall to explain", "This district is not below the benchmark for this crop.")
    else:
        verdict = ("Too little evidence to judge", "Confirm the yield in the field before planning.")

    return Explanation(category_label=PLAIN_CATEGORY[cat],
                       is_shortfall=cat in (CATEGORY_REPEATED_LOW_INPUT, CATEGORY_REPEATED_INPUTS_OK,
                                            CATEGORY_DIP),
                       pattern_title=pattern[0], pattern_line=pattern[1], seed=seed, fertilizer=fert,
                       verdict_title=verdict[0], verdict_line=verdict[1], checks=SHORT_CHECKS[cat],
                       survey=latest)
