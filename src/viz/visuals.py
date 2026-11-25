"""Small HTML/SVG visuals for the overview panel: legend, target arrow and survey strip.

Pure functions that return HTML strings, so they are testable without a browser
and every number they print comes from a Finding or TargetPosition.
"""
from __future__ import annotations

from html import escape

from src.analytics.indicators import CATEGORY_ORDER
from src.config import GAP_THRESHOLD
from src.decisions.finding import Finding, TargetPosition, crop_name, release_name
from src.viz.charts import ACCENT, CATEGORY_COLORS, CATEGORY_SHORT, INK, INK_2, INK_3, STATE_COLORS

LEGEND_MEANING = {
    CATEGORY_ORDER[0]: "Below 90% of national in at least 2 of the last 3 surveys, and both seed and fertilizer uptake below national.",
    CATEGORY_ORDER[1]: "Below 90% of national in at least 2 of the last 3 surveys, but input uptake is not low.",
    CATEGORY_ORDER[2]: "Below in the latest survey only: watch, it may be a one-season shock.",
    CATEGORY_ORDER[3]: "Too little reliable data (not reported, or under 500 ha harvested).",
    CATEGORY_ORDER[4]: "At or above 90% of the national yield in the latest survey.",
}


def legend_html(counts: dict[str, int], selected_category: str | None = None) -> str:
    rows = []
    for c in CATEGORY_ORDER:
        mark = "font-weight:700;" if c == selected_category else ""
        rows.append(
            f"<div class='umz-leg-row'><span class='umz-sw' style='background:{CATEGORY_COLORS[c]}'></span>"
            f"<div><div style='{mark}'>{escape(CATEGORY_SHORT[c])} "
            f"<span class='umz-count'>{counts.get(c, 0)}</span></div>"
            f"<div class='umz-leg-note'>{escape(LEGEND_MEANING[c])}</div></div></div>")
    return "<div class='umz-legend'>" + "".join(rows) + "</div>"


def window_strip_html(f: Finding) -> str:
    """One pill per survey in the label window: % of national and its state."""
    pills = []
    for p in f.window:
        if p.ratio is None:
            state, val, label = "missing", "n/r", "not reported"
        elif not p.reliable:
            state, val, label = "thin", f"{p.ratio:.0%}", "thin coverage"
        elif p.below:
            state, val, label = "below", f"{p.ratio:.0%}", "below benchmark"
        else:
            state, val, label = "not below", f"{p.ratio:.0%}", "not below"
        ink = "#ffffff" if state == "below" else INK
        pills.append(
            f"<div class='umz-pill' style='background:{STATE_COLORS[state]};color:{ink}'>"
            f"<div class='umz-pill-rel'>{escape(release_name(p.release_id))}</div>"
            f"<div class='umz-pill-val'>{val}</div><div class='umz-pill-lab'>{label}</div></div>")
    return ("<div class='umz-strip-cap'>Yield as % of national, last 3 surveys "
            f"(benchmark {GAP_THRESHOLD:.0%})</div><div class='umz-strip'>" + "".join(pills) + "</div>")


def target_arrow_svg(t: TargetPosition) -> str:
    """An arrow heading to a bullseye at the PSTA 5 target, with Rwanda's position marked on it."""
    w, h, x0, x1 = 560, 150, 24, 470          # x1: centre of the bullseye
    lo = min(t.baseline_t_ha, t.yield_t_ha) * 0.85
    hi = t.target_t_ha
    sx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    y = 82
    cur, base = sx(min(t.yield_t_ha, hi)), sx(t.baseline_t_ha)
    lx = min(max(cur, 95), x1 - 120)          # keep the "now" label inside the frame
    gap = t.target_t_ha - t.yield_t_ha
    red, grey = CATEGORY_COLORS[CATEGORY_ORDER[0]], "#c9cec9"
    parts = [
        f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:760px;display:block' role='img' aria-label='National {escape(crop_name(t.crop))} "
        f"yield {t.yield_t_ha:.2f} t/ha against a target of {t.target_t_ha:.2f} t/ha'>",
        # road to the target
        f"<line x1='{x0}' y1='{y}' x2='{x1 - 30}' y2='{y}' stroke='{grey}' stroke-width='6' stroke-linecap='round'/>",
        f"<line x1='{x0}' y1='{y}' x2='{cur}' y2='{y}' stroke='{ACCENT}' stroke-width='6' stroke-linecap='round'/>",
        f"<polygon points='{x1 - 32},{y - 9} {x1 - 16},{y} {x1 - 32},{y + 9}' fill='{grey}'/>",
        # bullseye
        f"<circle cx='{x1}' cy='{y}' r='26' fill='#ffffff' stroke='{red}' stroke-width='3'/>",
        f"<circle cx='{x1}' cy='{y}' r='17' fill='{red}'/>",
        f"<circle cx='{x1}' cy='{y}' r='9' fill='#ffffff'/>",
        f"<circle cx='{x1}' cy='{y}' r='4' fill='{red}'/>",
        f"<text x='{x1}' y='{y + 46}' text-anchor='middle' font-size='13' font-weight='700' fill='{INK}'>"
        f"Target {t.target_t_ha:.2f} t/ha</text>",
        f"<text x='{x1}' y='{y + 62}' text-anchor='middle' font-size='11' fill='{INK_2}'>{escape(t.agricultural_year)}</text>",
        # baseline tick
        f"<line x1='{base}' y1='{y + 8}' x2='{base}' y2='{y + 18}' stroke='{INK_3}' stroke-width='1.5'/>",
        f"<text x='{base}' y='{y + 32}' text-anchor='middle' font-size='11' fill='{INK_3}'>"
        f"PSTA baseline {t.baseline_t_ha:.2f}</text>",
        # where Rwanda is now
        f"<circle cx='{cur}' cy='{y}' r='9' fill='{ACCENT}' stroke='#ffffff' stroke-width='3'/>",
        f"<line x1='{cur}' y1='{y - 12}' x2='{cur}' y2='{y - 30}' stroke='{ACCENT}' stroke-width='1.5'/>",
        f"<text x='{lx}' y='{y - 52}' text-anchor='middle' font-size='13' font-weight='700' fill='{INK}'>"
        f"Rwanda now: {t.yield_t_ha:.2f} t/ha</text>",
        f"<text x='{lx}' y='{y - 36}' text-anchor='middle' font-size='12' fill='{INK_2}'>"
        f"{t.attainment:.0%} of the target</text>",
    ]
    if gap > 0:
        mid = (cur + x1 - 26) / 2
        parts.append(f"<text x='{mid}' y='{y - 10}' text-anchor='middle' font-size='11' fill='{red}'>"
                     f"{gap:.2f} t/ha to go</text>")
    parts.append("</svg>")
    return "".join(parts)
