"""Figure builders for Umuzi Analytics (Plotly).

Shared by the Streamlit app and scripts/run_analysis.py, so a chart in the
report and the same chart in the app come from one function and one snapshot.

Palette: evidence categories use three validated signal hues plus two neutrals
(validated with the dataviz skill's validate_palette.js, light mode, all-pairs:
worst CVD dE 15.9, worst normal-vision dE 16.0). Ochre and the neutrals are
below 3:1 contrast on the surface, so every chart carries text labels, a
legend and a table view. The app ships a light theme only.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_ORDER, CATEGORY_REPEATED_INPUTS_OK,
                                      CATEGORY_REPEATED_LOW_INPUT, REPEATED)
from src.config import BOUNDARY_PATH, CROP_LABELS, GAP_THRESHOLD, MIN_HARVESTED_HA

INK = "#1f2421"
INK_2 = "#55595a"
INK_3 = "#7b7f7f"
GRID = "#e4e4df"
SURFACE = "#fcfcfb"
ACCENT = "#24493f"          # evergreen
REFERENCE = "#55595a"

CATEGORY_COLORS = {
    CATEGORY_REPEATED_LOW_INPUT: "#9c3d24",
    CATEGORY_REPEATED_INPUTS_OK: "#d08a1e",
    CATEGORY_DIP: "#2f6db5",
    CATEGORY_INSUFFICIENT: "#c2beb4",
    CATEGORY_NOT_BELOW: "#f1f3ef",
}
CATEGORY_SHORT = {
    CATEGORY_REPEATED_LOW_INPUT: "Repeated shortfall, seed and fertilizer use low",
    CATEGORY_REPEATED_INPUTS_OK: "Repeated shortfall, seed and fertilizer use not low",
    CATEGORY_DIP: "One-season dip",
    CATEGORY_INSUFFICIENT: "Not enough data",
    CATEGORY_NOT_BELOW: "On par with Rwanda or above",
}
# Cell states in the pattern grid (same hues as the categories they lead to).
STATE_COLORS = {"below": "#9c3d24", "not below": "#dfe6e1", "thin": "#c2beb4", "missing": "#ffffff"}

# No family with a bare number in its name: an unquoted "Source Sans 3" is
# invalid CSS, which made Plotly measure and render text in different fonts.
FONT = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"


def _base_layout(fig: go.Figure, title: str, subtitle: str, source: str, height: int = 520,
                 margin_l: int = 60) -> go.Figure:
    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='font-size:13px;color:{INK_2}'>{subtitle}</span>",
                   x=0, xanchor="left", y=1, yref="container", yanchor="top", pad=dict(t=14),
                   font=dict(size=17, color=INK)),
        font=dict(family=FONT, size=13, color=INK),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, height=height,
        margin=dict(l=margin_l, r=24, t=118, b=118),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, size=12, color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0, xanchor="left",
                    font=dict(size=12, color=INK_2), bgcolor="rgba(0,0,0,0)"),
    )
    # Source note pinned in pixels below the x-axis title so it never collides.
    fig.add_annotation(text=source, xref="paper", yref="paper", x=0, y=0, yshift=-62,
                       xanchor="left", yanchor="top", showarrow=False, align="left",
                       font=dict(size=11, color=INK_3))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_2))
    return fig


def _src(releases: str, snapshot_id: str, extra: str = "") -> str:
    import textwrap
    s = f"Source: NISR Seasonal Agricultural Survey, {releases}. Snapshot {snapshot_id}. {extra}"
    return "<br>".join(textwrap.wrap(s.strip(), 120))


def crop_label(crop: str) -> str:
    return CROP_LABELS.get(crop, crop)


def _release_short(release_id: str) -> str:
    """'SAS-2026A' -> '2026 A'."""
    return f"{release_id[4:8]} {release_id[-1]}"


# ---------------------------------------------------------------- A. challenge size
def target_attainment_chart(nvt: pd.DataFrame, snapshot_id: str) -> go.Figure:
    """Dot plot: national A+B yield as % of the PSTA 5 target in the latest year with a target."""
    d = nvt.dropna(subset=["target_t_ha"])
    latest_year = d["season_year"].max()
    cur = d[d["season_year"] == latest_year].sort_values("attainment")
    fig = go.Figure(go.Scatter(
        x=cur["attainment"] * 100, y=[crop_label(c) for c in cur["crop"]], mode="markers+text",
        text=[f"{a:.0%}" for a in cur["attainment"]], textposition="middle left",
        textfont=dict(size=12, color=INK), marker=dict(size=13, color=ACCENT, line=dict(color=SURFACE, width=2)),
        customdata=np.c_[cur["yield_t_ha"].round(2), cur["target_t_ha"]], showlegend=False,
        hovertemplate="%{y}<br>Yield %{customdata[0]} t/ha<br>Target %{customdata[1]} t/ha<extra></extra>"))
    fig.add_vline(x=100, line=dict(color=REFERENCE, width=1.5, dash="dot"))
    fig.add_annotation(x=100, y=1.0, yref="paper", text="PSTA 5 target", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11, color=INK_2))
    fig.update_xaxes(title="National Season A+B yield as % of the PSTA 5 target", ticksuffix="%", range=[30, 110])
    ag = cur["agricultural_year"].iloc[0]
    n_below = int((cur["attainment"] < 1).sum())
    lead = "All" if n_below == len(cur) else f"{n_below} of"
    return _base_layout(
        fig, f"{lead} {len(cur)} PSTA 5 priority crops were below their {ag} yield target",
        f"National yield, Season A + B combined, {ag}",
        _src(f"{latest_year} Season A and B", snapshot_id,
             "Targets: MINAGRI PSTA 5 results framework p.21. Yield = (A+B production) / (A+B harvested area); "
             "Season C excluded."),
        height=430, margin_l=120)




# ---------------------------------------------------------------- B. the Rwanda map
def _ring_area(ring) -> float:
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:]))


def _rewind(gj: dict) -> dict:
    """Make exterior rings clockwise and holes counter-clockwise.

    geoBoundaries follows RFC 7946 (exterior counter-clockwise); Plotly's
    d3-geo projection expects the opposite, otherwise each district is drawn
    as its complement (the whole globe minus the district).
    """
    for f in gj["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for k, ring in enumerate(poly):
                clockwise = _ring_area(ring) < 0
                if (k == 0 and not clockwise) or (k > 0 and clockwise):
                    ring.reverse()
    return gj


_GJ_CACHE: dict = {}


def _geojson():
    if "gj" not in _GJ_CACHE:
        _GJ_CACHE["gj"] = _rewind(json.loads(BOUNDARY_PATH.read_text(encoding="utf-8")))
    return _GJ_CACHE["gj"]


def _centroid(district: str) -> tuple[float, float]:
    """Centroid of the district's largest polygon ring (for the map label)."""
    f = next(f for f in _geojson()["features"] if f["properties"]["shapeName"] == district)
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    ring = max((p[0] for p in polys), key=lambda r: abs(_ring_area(r)))
    pairs = list(zip(ring, ring[1:]))
    a = _ring_area(ring) / 2
    cx = sum((x0 + x1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in pairs) / (6 * a)
    cy = sum((y0 + y1) * (x0 * y1 - x1 * y0) for (x0, y0), (x1, y1) in pairs) / (6 * a)
    return cx, cy


def category_map(ev: pd.DataFrame, snapshot_id: str, crop: str, season: str,
                 highlight: str | None = None, compact: bool = False) -> go.Figure:
    """Rwanda choropleth by evidence category with the selected district outlined and labelled.

    `compact=True` is the app's overview map: no title or Plotly legend, because
    the app draws a fuller legend beside it. The report version keeps both.
    """
    gj = _geojson()
    n = len(CATEGORY_ORDER)
    code = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    scale = []
    for i, c in enumerate(CATEGORY_ORDER):
        scale += [[i / n, CATEGORY_COLORS[c]], [(i + 1) / n, CATEGORY_COLORS[c]]]
    pattern = [f"{int(b)} of {int(r)}" for b, r in zip(ev["below_in_window"], ev["reliable_in_window"])]
    fig = go.Figure(go.Choropleth(
        geojson=gj, featureidkey="properties.shapeName", locations=ev["district"],
        z=ev["category"].map(code) + 0.5, zmin=0, zmax=n, colorscale=scale, showscale=False,
        marker=dict(line=dict(color="#6b6f6c", width=0.8)), showlegend=False,
        customdata=np.c_[ev["category"].map(CATEGORY_SHORT), (ev["latest_ratio"] * 100).round(0),
                         pattern, ev["latest_harvested_ha"].round(0)],
        hovertemplate="<b>%{location}</b><br>%{customdata[0]}"
                      "<br>Latest yield: %{customdata[1]:.0f}% of national"
                      "<br>Below national in %{customdata[2]} reliable recent surveys"
                      "<br>Harvested area: %{customdata[3]:,} ha<extra></extra>"))
    if not compact:
        counts = ev["category"].value_counts()
        for c in CATEGORY_ORDER:
            if counts.get(c, 0):
                fig.add_trace(go.Scattergeo(lon=[None], lat=[None], mode="markers",
                                            name=f"{CATEGORY_SHORT[c]} ({counts[c]})",
                                            marker=dict(symbol="square", size=12, color=CATEGORY_COLORS[c],
                                                        line=dict(color="#6b6f6c", width=1))))
    if highlight:
        sub = {"type": "FeatureCollection",
               "features": [f for f in gj["features"] if f["properties"]["shapeName"] == highlight]}
        fig.add_trace(go.Choropleth(
            geojson=sub, featureidkey="properties.shapeName", locations=[highlight], z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker=dict(line=dict(color=INK, width=3.5)), hoverinfo="skip", showlegend=False))
        lon, lat = _centroid(highlight)
        fig.add_trace(go.Scattergeo(
            lon=[lon], lat=[lat], mode="text", text=[f"<b>{highlight}</b>"], hoverinfo="skip",
            textfont=dict(size=13, color=INK, family=FONT), showlegend=False))
    rel = ev["latest_release"].iloc[0]
    n_rep = int(ev["category"].isin(REPEATED).sum())
    fig = _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {n_rep} districts repeatedly below national",
        f"Latest survey {_release_short(rel)}. Repeatedly below = under {GAP_THRESHOLD:.0%} of national in at "
        "least 2 of the last 3 surveys of this season.",
        _src(ev["window_releases"].iloc[0].replace(",", ", "), snapshot_id,
             "Boundaries: geoBoundaries RWA ADM2 (source: NISR geodata, CC BY 4.0). Inputs = all crops pooled."),
        height=560)
    if compact:
        fig.update_layout(title=None, height=470, margin=dict(l=0, r=0, t=0, b=0), annotations=[])
    else:
        fig.update_layout(margin=dict(l=8, r=8, t=128, b=96), legend=dict(y=1.0, yanchor="bottom"))
    # Fixed extent of the 30 district polygons: legend-only proxy traces carry no
    # coordinates and would make fitbounds undefined.
    fig.update_geos(visible=False, bgcolor=SURFACE, fitbounds=False, projection_type="mercator",
                    lonaxis_range=[28.80, 30.96], lataxis_range=[-2.90, -0.99])
    return fig


# ---------------------------------------------------------------- C. the pattern behind the map
def pattern_grid(ev: pd.DataFrame, panel: pd.DataFrame, snapshot_id: str, crop: str, season: str,
                 highlight: str | None = None) -> go.Figure:
    """District x survey grid: below national, not below, thin coverage or not reported.

    Districts are ordered as on the map (category, then latest ratio), so the
    rows that make up "repeatedly below" sit together at the top.
    """
    rels = [c.replace("ratio_", "") for c in ev.columns if c.startswith("ratio_")]
    h = panel[(panel["crop"] == crop) & (panel["season"] == season)].set_index(["district", "release_id"])
    states = {"missing": 0, "thin": 1, "not below": 2, "below": 3}
    z, text = [], []
    for d in ev["district"]:
        zr, tr = [], []
        for rel in rels:
            r = h.loc[(d, rel)] if (d, rel) in h.index else None
            if r is None or pd.isna(r["yield_ratio"]):
                s, t = "missing", "n/r"
            elif r["harvested_ha"] < MIN_HARVESTED_HA:
                s, t = "thin", f"{r['yield_ratio']:.0%}"
            else:
                s = "below" if r["yield_ratio"] < GAP_THRESHOLD else "not below"
                t = f"{r['yield_ratio']:.0%}"
            zr.append(states[s])
            tr.append(t)
        z.append(zr)
        text.append(tr)
    scale = []
    for name, i in states.items():
        scale += [[i / 4, STATE_COLORS[name]], [(i + 1) / 4, STATE_COLORS[name]]]
    fig = go.Figure(go.Heatmap(
        z=np.array(z) + 0.5, x=[_release_short(r) for r in rels], y=ev["district"], zmin=0, zmax=4,
        colorscale=scale, showscale=False, xgap=2, ygap=2, text=text, texttemplate="%{text}",
        textfont=dict(size=10), hovertemplate="%{y}, %{x}: %{text} of national<extra></extra>"))
    for name, label in [("below", f"Below {GAP_THRESHOLD:.0%} of national"), ("not below", "Not below"),
                        ("thin", f"Under {MIN_HARVESTED_HA:,.0f} ha harvested (not counted)"),
                        ("missing", "Not reported (n/r)")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=label,
                                 marker=dict(size=11, symbol="square", color=STATE_COLORS[name],
                                             line=dict(color="#6b6f6c", width=1))))
    window = ev["window_releases"].iloc[0].split(",")
    x0 = rels.index(window[0]) - 0.5
    fig.add_shape(type="rect", x0=x0, x1=len(rels) - 0.5, y0=-0.5, y1=len(ev) - 0.5,
                  line=dict(color=INK, width=1.5), fillcolor="rgba(0,0,0,0)")
    if highlight:
        yi = list(ev["district"]).index(highlight)
        fig.add_shape(type="rect", x0=-0.5, x1=len(rels) - 0.5, y0=yi - 0.5, y1=yi + 0.5,
                      line=dict(color=INK, width=2.5), fillcolor="rgba(0,0,0,0)")
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=INK))
    fig.update_xaxes(side="top", showgrid=False, type="category", tickfont=dict(size=11, color=INK))
    n_rep = int(ev["category"].isin(REPEATED).sum())
    fig = _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: each district against national, survey by survey",
        f"{n_rep} districts are below in at least 2 of the last 3 surveys (outlined block). "
        "Cells: district yield as % of national.",
        _src(f"Season {season} {rels[0][4:8]}-{rels[-1][4:8]}", snapshot_id,
             "District rankings from 2018-2019 agree only weakly with later years, so labels use the last 3 surveys."),
        height=max(640, 22 * len(ev) + 240), margin_l=110)
    fig.update_layout(margin=dict(t=170), legend=dict(y=1.07))
    return fig


def district_history_chart(panel: pd.DataFrame, district: str, crop: str, season: str,
                           window: list[str], snapshot_id: str) -> go.Figure:
    """One district's yield as % of national in every survey of the season type."""
    d = panel[(panel["district"] == district) & (panel["crop"] == crop)
              & (panel["season"] == season)].sort_values("season_year")
    x = [_release_short(r) for r in d["release_id"]]
    y = d["yield_ratio"] * 100
    thin = ((d["harvested_ha"] < MIN_HARVESTED_HA) | d["yield_ratio"].isna()).tolist()
    below = [(not t) and r < GAP_THRESHOLD for t, r in zip(thin, d["yield_ratio"])]
    red = CATEGORY_COLORS[CATEGORY_REPEATED_LOW_INPUT]
    colors = [red if b else ACCENT for b in below]
    fig = go.Figure()
    in_win = [r in window for r in d["release_id"]]
    if any(in_win):
        i0 = in_win.index(True)
        fig.add_vrect(x0=i0 - 0.4, x1=len(x) - 0.6, fillcolor="#eef2ee", line_width=0, layer="below")
        fig.add_annotation(x=len(x) - 1, y=1.0, yref="paper", text="last 3 surveys (used for the label)",
                           showarrow=False, xanchor="right", yanchor="bottom", font=dict(size=11, color=INK_2))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", name=district, line=dict(color="#9aa8a2", width=1.5),
        marker=dict(size=11, color=colors, symbol=["circle-open" if t else "circle" for t in thin],
                    line=dict(color=colors, width=2)), showlegend=False,
        customdata=np.c_[(d["yield_kg_ha"] / 1000).round(2), (d["national_yield_kg_ha"] / 1000).round(2),
                         d["harvested_ha"].round(0)],
        hovertemplate="%{x}: %{y:.0f}% of national<br>%{customdata[0]} t/ha vs national %{customdata[1]} t/ha"
                      "<br>harvested %{customdata[2]:,} ha<extra></extra>"))
    fig.add_hline(y=100, line=dict(color=REFERENCE, width=1))
    fig.add_hline(y=GAP_THRESHOLD * 100, line=dict(color=red, width=1, dash="dot"))
    fig.add_annotation(x=0, xref="paper", y=100, text="national", showarrow=False, xanchor="left",
                       yanchor="bottom", font=dict(size=11, color=INK_2))
    fig.add_annotation(x=0, xref="paper", y=GAP_THRESHOLD * 100, text=f"{GAP_THRESHOLD:.0%} benchmark",
                       showarrow=False, xanchor="left", yanchor="top", font=dict(size=11, color=INK_2))
    top = max(130.0, float(np.nanmax(y)) + 10) if y.notna().any() else 130.0
    fig.update_yaxes(title="Yield as % of national", ticksuffix="%", range=[0, top])
    fig.update_xaxes(title=None, type="category")
    return _base_layout(
        fig, f"{district}, {crop_label(crop).lower()}, Season {season}: every survey since {x[0][:4]}",
        "Red dot: below the benchmark. Open circle: thin coverage or not reported (not counted).",
        _src(f"Season {season} {x[0][:4]}-{x[-1][:4]}", snapshot_id), height=420)


# ---------------------------------------------------------------- D. input context
def input_context_chart(ev: pd.DataFrame, snapshot_id: str, crop: str, season: str,
                        highlight: str | None = None) -> go.Figure:
    d = ev[ev["inputs_known"].astype(bool)]
    if d.empty:
        return _base_layout(go.Figure(), "Seed and fertilizer use is not published per farmer for this survey", "", "")
    nseed = d["national_improved_seed_pct"].iloc[0]
    nfert = d["national_inorganic_fert_pct"].iloc[0]
    fig = go.Figure()
    for cat in CATEGORY_ORDER:
        g = d[d["category"] == cat]
        if g.empty:
            continue
        prominent = cat in REPEATED
        labels = [n if (prominent or n == highlight) else "" for n in g["district"]]
        fig.add_trace(go.Scatter(
            x=g["improved_seed_pct"], y=g["inorganic_fert_pct"], mode="markers+text",
            text=labels, textposition="top center", textfont=dict(size=10, color=INK_2),
            name=CATEGORY_SHORT[cat],
            marker=dict(size=12 if prominent else 9, color=CATEGORY_COLORS[cat],
                        line=dict(color=SURFACE if prominent else "#6b6f6c", width=1)),
            customdata=np.c_[(g["latest_ratio"] * 100).round(0)], hovertext=g["district"],
            hovertemplate="<b>%{hovertext}</b><br>Improved seed: %{x:.1f}% of farmers"
                          "<br>Inorganic fertilizer: %{y:.1f}% of farmers"
                          "<br>Yield: %{customdata[0]:.0f}% of national<extra></extra>"))
    if highlight in set(d["district"]):
        r = d.set_index("district").loc[highlight]
        fig.add_trace(go.Scatter(x=[r["improved_seed_pct"]], y=[r["inorganic_fert_pct"]], mode="markers",
                                 marker=dict(size=22, color="rgba(0,0,0,0)", line=dict(color=INK, width=2)),
                                 hoverinfo="skip", showlegend=False))
    fig.add_vline(x=nseed, line=dict(color=REFERENCE, width=1, dash="dot"))
    fig.add_hline(y=nfert, line=dict(color=REFERENCE, width=1, dash="dot"))
    fig.add_annotation(x=nseed, y=1.0, yref="paper", text=f"national {nseed:.0f}%", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11, color=INK_2))
    fig.add_annotation(x=1.0, xref="paper", y=nfert, text=f"national {nfert:.0f}%", showarrow=False,
                       xanchor="right", yanchor="bottom", font=dict(size=11, color=INK_2))
    fig.add_annotation(x=0.01, y=0.01, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
                       text="Lower left: both inputs below national", showarrow=False,
                       font=dict(size=11, color=INK_3))
    fig.update_xaxes(title="Farmers using improved seed (%, all crops)", ticksuffix="%")
    fig.update_yaxes(title="Farmers using inorganic fertilizer (%, all crops)", ticksuffix="%")
    n_ok = int((d["category"] == CATEGORY_REPEATED_INPUTS_OK).sum())
    n_low = int((d["category"] == CATEGORY_REPEATED_LOW_INPUT).sum())
    rel = _release_short(d["latest_release"].iloc[0])
    return _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {n_ok} of {n_ok + n_low} repeatedly-below districts "
             "do not have both seed and fertilizer use low",
        f"Share of farmers using each input in {rel}, all crops pooled. Occurring together is not proof of cause.",
        _src(rel, snapshot_id, "Seed and fertilizer use is published per district for all crops combined, not per crop."),
        height=560)


# ---------------------------------------------------------------- E. triage matrix
def triage_matrix(cat_wide: pd.DataFrame, snapshot_id: str, season: str) -> go.Figure:
    """District x crop grid coloured by evidence category."""
    cats = CATEGORY_ORDER
    code = {c: i for i, c in enumerate(cats)}
    z = cat_wide.apply(lambda col: col.map(code))
    n = len(cats)
    scale = []
    for i, c in enumerate(cats):
        scale += [[i / n, CATEGORY_COLORS[c]], [(i + 1) / n, CATEGORY_COLORS[c]]]
    text = cat_wide.apply(lambda col: col.map(CATEGORY_SHORT))
    fig = go.Figure(go.Heatmap(
        z=z.values + 0.5, x=[crop_label(c) for c in cat_wide.columns], y=cat_wide.index,
        zmin=0, zmax=n, colorscale=scale, showscale=False, xgap=2, ygap=2,
        text=text.values, hovertemplate="%{y}, %{x}<br>%{text}<extra></extra>"))
    for c in cats:   # legend proxies
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=CATEGORY_SHORT[c],
                                 marker=dict(size=11, symbol="square", color=CATEGORY_COLORS[c],
                                             line=dict(color="#6b6f6c", width=1))))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=INK))
    fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=12, color=INK))
    multi = int((cat_wide.isin(REPEATED).sum(axis=1) >= 3).sum())
    fig = _base_layout(
        fig, f"Season {season}: {multi} districts are repeatedly below national in three or more priority crops",
        "Evidence category for each district and PSTA 5 priority crop, latest survey of this season",
        _src(f"Season {season} surveys", snapshot_id), height=820, margin_l=110)
    fig.update_layout(margin=dict(t=150), legend=dict(y=1.09))
    return fig
