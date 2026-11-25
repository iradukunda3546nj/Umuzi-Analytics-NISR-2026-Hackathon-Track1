"""HTML/SVG visuals for the app: target arrows, survey tiles, input bars, cards.

Pure functions that return HTML strings, so they are testable without a browser
and every number they print comes from a Finding, Explanation or TargetPosition.
Animations are CSS only (see src/ui/style.py) and switch off under
prefers-reduced-motion.
"""
from __future__ import annotations

from html import escape

from src.analytics.indicators import CATEGORY_ORDER
from src.config import GAP_THRESHOLD
from src.decisions.explain import PLAIN_CATEGORY, Explanation, InputSignal
from src.decisions.finding import Finding, TargetPosition, crop_name, pct, release_name
from src.viz.charts import ACCENT, CATEGORY_COLORS, INK, INK_2, INK_3, STATE_COLORS
from src.viz.icons import icon

RED = CATEGORY_COLORS[CATEGORY_ORDER[0]]
GREY = "#c9cec9"
# Marker colour per category on light cards ("not below" is near-white on the map).
MARK_COLORS = {**CATEGORY_COLORS, CATEGORY_ORDER[3]: "#8f8a80", CATEGORY_ORDER[4]: ACCENT}


def ink_on(category: str) -> str:
    return "#ffffff" if category in (CATEGORY_ORDER[0], CATEGORY_ORDER[2]) else INK


def chip_html(category: str) -> str:
    return (f"<span class='umz-chip' style='background:{CATEGORY_COLORS[category]};color:{ink_on(category)}'>"
            f"{escape(PLAIN_CATEGORY[category])}</span>")


def legend_chips_html(counts: dict[str, int], selected: str | None = None) -> str:
    rows = []
    for c in CATEGORY_ORDER:
        sel = " umz-leg-sel" if c == selected else ""
        rows.append(f"<span class='umz-leg{sel}'><span class='umz-sw' style='background:{CATEGORY_COLORS[c]}'></span>"
                    f"{escape(PLAIN_CATEGORY[c])} <b>{counts.get(c, 0)}</b></span>")
    return "<div class='umz-legs'>" + "".join(rows) + "</div>"


# ------------------------------------------------------------------ district vs Rwanda
def district_target_svg(f: Finding, gap: float = GAP_THRESHOLD) -> str:
    """Arrow flying towards a bullseye that stands for Rwanda's yield (100%).

    The arrow stops at the district's yield as a share of Rwanda's; the dashed
    line is the 90% benchmark under which a survey counts as "below".
    """
    r = f.row
    ratio = r["latest_ratio"]
    w, h, x0, x1 = 540, 196, 22, 490
    known = ratio == ratio
    hi = max(1.15, (ratio if known else 0) + 0.08)
    lo = max(0.0, min(0.4, (ratio if known else 1) - 0.12))   # the arrow never falls off the left edge
    uncertain = not bool(r["latest_reliable"])                 # too few fields: draw it faint, claim no gap
    bx = x0 + (1.0 - lo) / (hi - lo) * (x1 - x0)            # bullseye centre
    sx = lambda v: x0 + (max(min(v, hi), lo) - lo) / (hi - lo) * (x1 - x0)
    y = 92
    color = "#a8a398" if uncertain else MARK_COLORS[f.category]
    parts = [f"<svg class='umz-target-svg' viewBox='0 0 {w} {h}' width='100%' role='img' "
             f"aria-label='{escape(f.district)} {escape(crop_name(f.crop))} yield as a share of Rwanda&#39;s'>"]
    # benchmark zone and line
    gx = sx(gap)
    parts += [
        f"<line x1='{gx:.1f}' y1='{y - 46}' x2='{gx:.1f}' y2='{y + 34}' stroke='{INK_3}' stroke-width='1.4' stroke-dasharray='4 4'/>",
        # key for the dashed line, at the foot of the drawing so it never meets the bullseye labels
        f"<line x1='{x0}' y1='{h - 12}' x2='{x0 + 22}' y2='{h - 12}' stroke='{INK_3}' stroke-width='1.4' stroke-dasharray='4 4'/>",
        f"<text x='{x0 + 30}' y='{h - 8}' font-size='13' fill='{INK_2}'>shortfall line: {gap:.0%} of the Rwanda average</text>",
        # bullseye = Rwanda
        f"<g class='umz-bull'><circle cx='{bx:.1f}' cy='{y}' r='34' fill='#ffffff' stroke='{RED}' stroke-width='3'/>",
        f"<circle cx='{bx:.1f}' cy='{y}' r='23' fill='{RED}'/><circle cx='{bx:.1f}' cy='{y}' r='13' fill='#ffffff'/>",
        f"<circle cx='{bx:.1f}' cy='{y}' r='5' fill='{RED}'/></g>",
        f"<text x='{bx:.1f}' y='{y + 56}' text-anchor='middle' font-size='16' font-weight='700' fill='{INK}'>Rwanda</text>",
    ]
    if r["national_yield_kg_ha"] == r["national_yield_kg_ha"]:
        parts.append(f"<text x='{bx:.1f}' y='{y + 72}' text-anchor='middle' font-size='14' fill='{INK_2}'>"
                     f"average {r['national_yield_kg_ha'] / 1000:.2f} t/ha</text>")
    if ratio != ratio:                                          # NaN: nothing published
        parts.append(f"<text x='{x0}' y='{y + 5}' font-size='15' fill='{INK_2}'>No harvest figure published for "
                     f"{escape(release_name(f.latest_release))}</text></svg>")
        return "".join(parts)
    hx = sx(ratio)
    tail = x0 + 4
    length = max(hx - tail, 1)
    parts += [
        f"<line class='umz-shaft' x1='{tail}' y1='{y}' x2='{hx - 14:.1f}' y2='{y}' stroke='{color}' "
        f"stroke-width='7' stroke-linecap='round' style='--len:{length:.0f}'/>",
        f"<g class='umz-head' style='--from:{-length:.0f}px'>"
        f"<polygon points='{hx - 20:.1f},{y - 12} {hx + 2:.1f},{y} {hx - 20:.1f},{y + 12}' fill='{color}'/>"
        f"<line x1='{hx - 8:.1f}' y1='{y - 30}' x2='{hx - 8:.1f}' y2='{y - 12}' stroke='{color}' stroke-width='1.5'/>"
        f"<text x='{min(max(hx - 8, 80), 440):.1f}' y='{y - 36}' text-anchor='middle' font-size='20' font-weight='700' "
        f"fill='{INK_2 if uncertain else INK}'>{escape(f.district)} {pct(ratio)}{'?' if uncertain else ''}</text></g>",
        # fletching
        f"<path d='M{tail + 2} {y} l-10 -10 M{tail + 2} {y} l-10 10 M{tail + 12} {y} l-10 -10 M{tail + 12} {y} l-10 10' "
        f"stroke='{color}' stroke-width='2.5' stroke-linecap='round'/>",
    ]
    short = (r["national_yield_kg_ha"] - r["latest_yield_kg_ha"]) / 1000
    if uncertain:
        parts.append(f"<text x='{x0}' y='{y + 36}' font-size='14' font-style='italic' fill='{INK_2}'>"
                     "Too few fields surveyed to be sure</text>")
    elif short > 0 and hx < bx - 70:
        mid = (hx + bx - 34) / 2
        parts.append(f"<text x='{mid:.1f}' y='{y + 30}' text-anchor='middle' font-size='15' font-weight='600' fill='{RED}'>"
                     f"{short:.2f} t/ha less</text>")
    parts.append("</svg>")
    return "".join(parts)


def pattern_tiles_html(f: Finding) -> str:
    """The last three surveys as tiles: tick = not below, cross = below, dash = no reliable value."""
    tiles = []
    for i, p in enumerate(f.window):
        if p.ratio is None:
            state, ic, val, lab = "missing", "dash", "&ndash;", "no figure"
        elif not p.reliable:
            state, ic, val, lab = "thin", "dash", pct(p.ratio) + "?", "too few fields"
        elif p.below:
            state, ic, val, lab = "below", "cross", pct(p.ratio), "short"
        else:
            state, ic, val, lab = "not below", "check", pct(p.ratio), "on par or above"
        ink = "#ffffff" if state == "below" else INK
        tiles.append(
            f"<div class='umz-tile' style='background:{STATE_COLORS[state]};color:{ink};animation-delay:{0.15 * i:.2f}s'>"
            f"{icon(ic, 22)}<div class='umz-tile-rel'>{escape(release_name(p.release_id))}</div>"
            f"<div class='umz-tile-val'>{val}</div><div class='umz-tile-lab'>{lab}</div></div>")
    return "<div class='umz-tiles'>" + "".join(tiles) + "</div>"


def _input_row(s: InputSignal, ic: str, i: int, here: str = "Here") -> str:
    if s.lower is None:
        return (f"<div class='umz-inp'><div class='umz-inp-ic'>{icon(ic, 30)}</div><div class='umz-inp-body'>"
                f"<div class='umz-inp-name'>{escape(s.name)}</div><div class='umz-inp-note'>Not published per "
                f"farmer for this survey</div></div></div>")
    col = RED if s.lower else ACCENT
    return (
        f"<div class='umz-inp'><div class='umz-inp-ic' style='color:{col}'>{icon(ic, 30)}</div>"
        f"<div class='umz-inp-body'><div class='umz-inp-name'>{escape(s.name)} "
        f"<span class='umz-inp-word' style='color:{col}'>{escape(s.word)}</span></div>"
        f"<div class='umz-bar'><span class='umz-bar-lab'>{escape(here)}</span><span class='umz-bar-track'>"
        f"<span class='umz-bar-fill' style='width:{s.district_pct:.1f}%;background:{col};animation-delay:{0.2 * i:.1f}s'></span>"
        f"</span><b>{s.district_pct:.0f}%</b></div>"
        f"<div class='umz-bar'><span class='umz-bar-lab'>Rwanda</span><span class='umz-bar-track'>"
        f"<span class='umz-bar-fill' style='width:{s.national_pct:.1f}%;background:{GREY};animation-delay:{0.2 * i:.1f}s'></span>"
        f"</span><b>{s.national_pct:.0f}%</b></div></div></div>")


def inputs_html(e: Explanation, here: str = "Here") -> str:
    return (_input_row(e.seed, "seed", 0, here) + _input_row(e.fertilizer, "bag", 1, here)
            + "<div class='umz-fine'>Share of farmers using it, on any crop, in "
              f"{escape(e.survey)}. The survey does not split this by crop for each district.</div>")


def verdict_html(e: Explanation, category: str) -> str:
    col = MARK_COLORS[category]
    ic = {CATEGORY_ORDER[0]: "bag", CATEGORY_ORDER[1]: "soil", CATEGORY_ORDER[2]: "rain",
          CATEGORY_ORDER[3]: "question", CATEGORY_ORDER[4]: "check"}[category]
    return (f"<div class='umz-verdict'><div class='umz-verdict-ic' style='color:{col}'>{icon(ic, 44, 1.6)}</div>"
            f"<div><div class='umz-verdict-t'>{escape(e.verdict_title)}</div>"
            f"<div class='umz-verdict-l'>{escape(e.verdict_line)}</div></div></div>")


def action_card_html(e: Explanation, who: str) -> str:
    items = "".join(f"<li style='animation-delay:{0.12 * i:.2f}s'><span>{icon(ic, 22)}</span>{escape(t)}</li>"
                    for i, (ic, t) in enumerate(e.checks))
    return (f"<div class='umz-action'><div class='umz-action-head'><span class='umz-action-ic'>"
            f"{icon('megaphone', 30, 2)}</span><div><div class='umz-action-t'>Take action</div>"
            f"<div class='umz-action-s'>{escape(who)}: check these first</div></div></div>"
            f"<ul class='umz-checks'>{items}</ul></div>")


# ------------------------------------------------------------------ landing page
def hook_cards_html(cards: list[tuple[str, str, str, str]]) -> str:
    """(icon, kicker word, question, one line) per card."""
    out = []
    for i, (ic, kick, title, line) in enumerate(cards):
        out.append(f"<div class='umz-hook' style='animation-delay:{0.12 * i + 0.1:.2f}s'>"
                   f"<div class='umz-hook-top'><div class='umz-hook-ic'>{icon(ic, 30, 1.7)}</div>"
                   f"<span class='umz-hook-k'>{escape(kick)}</span></div><div class='umz-hook-t'>{escape(title)}</div>"
                   f"<div class='umz-hook-l'>{escape(line)}</div></div>")
    return "<div class='umz-hooks'>" + "".join(out) + "</div>"


def stats_html(stats: list[tuple[str, str]]) -> str:
    return "<div class='umz-stats'>" + "".join(
        f"<div><b>{escape(v)}</b><span>{escape(k)}</span></div>" for v, k in stats) + "</div>"


def flow_html(steps: list[tuple[str, str]]) -> str:
    out = []
    for i, (ic, t) in enumerate(steps):
        if i:
            out.append(f"<span class='umz-flow-arrow'>{icon('arrow', 22)}</span>")
        out.append(f"<span class='umz-flow-step'>{icon(ic, 22)}{escape(t)}</span>")
    return "<div class='umz-flow'>" + "".join(out) + "</div>"


# ------------------------------------------------------------------ Rwanda vs the national goal
def target_arrow_svg(t: TargetPosition) -> str:
    """Rwanda's yield today on an arrow heading to a bullseye at the PSTA 5 goal.

    Only two labels sit on the drawing (today, goal) so nothing collides; the PSTA
    starting point is stated in the caption under it instead.
    """
    w, h, x0, x1 = 560, 140, 24, 470          # x1: centre of the bullseye
    lo = min(t.baseline_t_ha, t.yield_t_ha) * 0.6
    hi = t.target_t_ha
    sx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    y = 78
    cur = sx(min(t.yield_t_ha, hi))
    lx = min(max(cur, 90), x1 - 150)          # keep the "today" label clear of the goal label
    gap = t.target_t_ha - t.yield_t_ha
    parts = [
        f"<svg viewBox='0 0 {w} {h}' width='100%' style='max-width:760px;display:block' role='img' aria-label='Rwanda "
        f"{escape(crop_name(t.crop))} yield {t.yield_t_ha:.2f} t/ha against a goal of {t.target_t_ha:.2f} t/ha'>",
        f"<line x1='{x0}' y1='{y}' x2='{x1 - 30}' y2='{y}' stroke='{GREY}' stroke-width='6' stroke-linecap='round'/>",
        f"<line class='umz-shaft' x1='{x0}' y1='{y}' x2='{cur}' y2='{y}' stroke='{ACCENT}' stroke-width='6' "
        f"stroke-linecap='round' style='--len:{max(cur - x0, 1):.0f}'/>",
        f"<polygon points='{x1 - 32},{y - 9} {x1 - 16},{y} {x1 - 32},{y + 9}' fill='{GREY}'/>",
        f"<g class='umz-bull'><circle cx='{x1}' cy='{y}' r='26' fill='#ffffff' stroke='{RED}' stroke-width='3'/>",
        f"<circle cx='{x1}' cy='{y}' r='17' fill='{RED}'/><circle cx='{x1}' cy='{y}' r='9' fill='#ffffff'/>",
        f"<circle cx='{x1}' cy='{y}' r='4' fill='{RED}'/></g>",
        f"<text x='{x1}' y='{y + 48}' text-anchor='middle' font-size='15' font-weight='700' fill='{INK}'>"
        f"Goal {t.target_t_ha:.2f} t/ha</text>",
        f"<text x='{x1}' y='{y - 36}' text-anchor='middle' font-size='12' fill='{INK_2}'>by {escape(t.agricultural_year)}</text>",
        f"<circle cx='{cur}' cy='{y}' r='9' fill='{ACCENT}' stroke='#ffffff' stroke-width='3'/>",
        f"<text x='{lx}' y='{y - 22}' text-anchor='middle' font-size='15' font-weight='700' fill='{INK}'>"
        f"Rwanda today: {t.yield_t_ha:.2f} t/ha</text>",
        f"<text x='{lx}' y='{y + 30}' text-anchor='middle' font-size='13' fill='{INK_2}'>"
        f"{t.attainment:.0%} of the goal</text>",
    ]
    if gap > 0:
        # Below the line, right of the "% of the goal" label; left out when it would not fit
        # (the caption under the drawing states it anyway).
        gx = max((cur + x1 - 26) / 2, lx + 105)
        if gx + 48 < x1 - 30:
            parts.append(f"<text x='{gx:.1f}' y='{y + 30}' text-anchor='middle' font-size='13' "
                         f"font-weight='600' fill='{RED}'>{gap:.2f} t/ha to go</text>")
    parts.append("</svg>")
    return "".join(parts)
