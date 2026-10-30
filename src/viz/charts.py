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
                                      CATEGORY_ORDER, CATEGORY_PERSISTENT_INPUTS_OK,
                                      CATEGORY_PERSISTENT_LOW_INPUT)
from src.config import BOUNDARY_PATH, CROP_LABELS

INK = "#1f2421"
INK_2 = "#55595a"
INK_3 = "#7b7f7f"
GRID = "#e4e4df"
SURFACE = "#fcfcfb"
ACCENT = "#24493f"          # evergreen
REFERENCE = "#55595a"

CATEGORY_COLORS = {
    CATEGORY_PERSISTENT_LOW_INPUT: "#9c3d24",
    CATEGORY_PERSISTENT_INPUTS_OK: "#d08a1e",
    CATEGORY_DIP: "#2f6db5",
    CATEGORY_INSUFFICIENT: "#c2beb4",
    CATEGORY_NOT_BELOW: "#f1f3ef",
}
CATEGORY_SHORT = {
    CATEGORY_PERSISTENT_LOW_INPUT: "Persistent, low inputs",
    CATEGORY_PERSISTENT_INPUTS_OK: "Persistent, inputs not low",
    CATEGORY_DIP: "Latest-season dip",
    CATEGORY_INSUFFICIENT: "Insufficient evidence",
    CATEGORY_NOT_BELOW: "Not below national",
}
# Release markers: oldest to newest within a season type, light to dark.
RELEASE_SHADES = ["#b8c7c1", "#6f8f84", "#24493f"]

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


# ---------------------------------------------------------------- A. challenge size
def target_attainment_chart(nvt: pd.DataFrame, snapshot_id: str) -> go.Figure:
    """Dot plot: national A+B yield in each SAS year as % of the PSTA 5 2025/26 target."""
    latest_year = nvt.dropna(subset=["target_t_ha"])["season_year"].max()
    cur = nvt[nvt["season_year"] == latest_year].dropna(subset=["target_t_ha"])
    cur = cur.sort_values("attainment")
    t_by_crop = cur.set_index("crop")["target_t_ha"]
    fig = go.Figure()
    years = sorted(nvt["season_year"].unique())
    shades = RELEASE_SHADES[-len(years):]
    for y, shade in zip(years, shades):
        d = nvt[(nvt["season_year"] == y) & nvt["crop"].isin(cur["crop"])].set_index("crop").reindex(cur["crop"])
        pct = d["yield_t_ha"] / t_by_crop * 100
        ag = d["agricultural_year"].dropna().iloc[0] if d["agricultural_year"].notna().any() else str(y)
        fig.add_trace(go.Scatter(
            x=pct, y=[crop_label(c) for c in cur["crop"]], mode="markers",
            name=f"SAS {y} ({ag})", marker=dict(size=11, color=shade, line=dict(color=SURFACE, width=2)),
            customdata=np.c_[d["yield_t_ha"].round(2), t_by_crop.values],
            hovertemplate="%{y}<br>Yield %{customdata[0]} t/ha<br>Target 2025/26 %{customdata[1]} t/ha"
                          "<br>%{x:.0f}% of target<extra>" + f"SAS {y}" + "</extra>"))
    fig.add_vline(x=100, line=dict(color=REFERENCE, width=1.5, dash="dot"))
    fig.add_annotation(x=100, y=1.0, yref="paper", text="PSTA 5 target for 2025/26", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11, color=INK_2))
    lo = cur.iloc[0]
    fig.add_annotation(x=lo["attainment"] * 100, y=crop_label(lo["crop"]),
                       text=f"{lo['attainment'] * 100:.0f}% of target", showarrow=False,
                       xanchor="right", xshift=-12, font=dict(size=12, color=INK))
    fig.update_xaxes(title="National Season A+B yield as % of PSTA 5 2025/26 target", ticksuffix="%",
                     range=[40, 110])
    n_below = int((cur["attainment"] < 1).sum())
    lead = "All" if n_below == len(cur) else f"{n_below} of"
    return _base_layout(
        fig, f"{lead} {len(cur)} PSTA 5 priority crops were below their 2025/26 yield target",
        "National yield, Season A + B combined, as % of the 2025/26 target (2023/24 has no PSTA 5 target)",
        _src("2024A, 2024B, 2026A, 2026B", snapshot_id,
             "Targets: MINAGRI PSTA 5 results framework p.21. Yield = (A+B production) / (A+B harvested area); "
             "Season C excluded. PSTA 5's exact aggregation method is not stated in the abridged plan."),
        height=430, margin_l=120)


# ---------------------------------------------------------------- B. where it concentrates
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


def category_map(ev: pd.DataFrame, snapshot_id: str, crop: str, season: str,
                 highlight: str | None = None, threshold: float = 0.9) -> go.Figure:
    """One choropleth trace (the boundary GeoJSON is embedded once) with a stepped
    colour scale; legend entries are marker-only proxies."""
    gj = _geojson()
    n = len(CATEGORY_ORDER)
    code = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    scale = []
    for i, c in enumerate(CATEGORY_ORDER):
        scale += [[i / n, CATEGORY_COLORS[c]], [(i + 1) / n, CATEGORY_COLORS[c]]]
    fig = go.Figure(go.Choropleth(
        geojson=gj, featureidkey="properties.shapeName", locations=ev["district"],
        z=ev["category"].map(code) + 0.5, zmin=0, zmax=n, colorscale=scale, showscale=False,
        marker=dict(line=dict(color="#6b6f6c", width=0.8)), showlegend=False,
        customdata=np.c_[ev["category"].map(CATEGORY_SHORT), ev["latest_ratio"].round(2),
                         ev["matched_seasons_adequate"], ev["seasons_below"],
                         ev["latest_harvested_ha"].round(0)],
        hovertemplate="<b>%{location}</b><br>%{customdata[0]}"
                      "<br>Latest yield / national: %{customdata[1]}"
                      "<br>Below national in %{customdata[3]} of %{customdata[2]} adequate seasons"
                      "<br>Harvested area: %{customdata[4]:,} ha<extra></extra>"))
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
            marker=dict(line=dict(color=INK, width=3)), hoverinfo="skip", showlegend=False))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor=SURFACE)
    n_persist = ev["persistent_shortfall"].sum()
    rel = ev["latest_release"].iloc[0]
    fig = _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {n_persist} districts persistently below national",
        f"Latest release {rel}. Below national = yield under {threshold:.0%} of national.",
        _src(f"all Season {season} releases in snapshot", snapshot_id,
             "Boundaries: geoBoundaries RWA ADM2 (source: NISR geodata, CC BY 4.0). Inputs = all crops pooled."),
        height=580)
    # Legend stays in the standard top position so it never takes width from the map.
    fig.update_layout(margin=dict(l=8, r=8, t=128, b=96), legend=dict(y=1.0, yanchor="bottom"))
    # Fixed extent of the 30 district polygons. fitbounds is not used: the legend-only
    # proxy traces carry no coordinates and made the computed bounds undefined.
    fig.update_geos(fitbounds=False, projection_type="mercator",
                    lonaxis_range=[28.80, 30.96], lataxis_range=[-2.90, -0.99])
    return fig


# ---------------------------------------------------------------- C. persistence (signature)
def persistence_chart(ev: pd.DataFrame, snapshot_id: str, crop: str, season: str,
                      threshold: float = 0.9, highlight: str | None = None) -> go.Figure:
    """Ranked dot plot: each district's yield ratio in every matched release."""
    ratio_cols = [c for c in ev.columns if c.startswith("ratio_")]
    rels = [c.replace("ratio_", "") for c in ratio_cols]
    d = ev.dropna(subset=["mean_ratio"]).sort_values("mean_ratio", ascending=True)
    fig = go.Figure()
    # Range bar per district (min to max across matched seasons).
    for _, r in d.iterrows():
        vals = r[ratio_cols].dropna().astype(float)
        if len(vals) < 2:
            continue
        fig.add_trace(go.Scatter(x=[vals.min(), vals.max()], y=[r["district"]] * 2, mode="lines",
                                 line=dict(color="#c9cec9", width=4), hoverinfo="skip", showlegend=False))
    shades = RELEASE_SHADES[-len(rels):]
    for col, rel, shade in zip(ratio_cols, rels, shades):
        fig.add_trace(go.Scatter(
            x=d[col], y=d["district"], mode="markers", name=rel,
            marker=dict(size=9, color=shade, line=dict(color=SURFACE, width=1.5)),
            hovertemplate="%{y}<br>" + rel + ": %{x:.2f} x national<extra></extra>"))
    persist = d[d["persistent_shortfall"]]
    fig.add_trace(go.Scatter(
        x=[0.02] * len(persist), y=persist["district"], mode="markers", name="Persistent shortfall",
        marker=dict(symbol="square", size=8, color=CATEGORY_COLORS[CATEGORY_PERSISTENT_LOW_INPUT]),
        hovertemplate="%{y}: below national in every adequately covered release<extra></extra>"))
    fig.add_vline(x=1.0, line=dict(color=REFERENCE, width=1))
    fig.add_vline(x=threshold, line=dict(color=CATEGORY_COLORS[CATEGORY_PERSISTENT_LOW_INPUT],
                                         width=1, dash="dot"))
    fig.add_annotation(x=threshold, y=1.0, yref="paper", text=f"{threshold:.2f} x national",
                       showarrow=False, xanchor="right", yanchor="bottom", xshift=-4,
                       font=dict(size=11, color=INK_2))
    fig.add_annotation(x=1.0, y=1.0, yref="paper", text="national", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11, color=INK_2))
    if highlight and highlight in set(d["district"]):
        fig.add_hrect(y0=list(d["district"]).index(highlight) - 0.5,
                      y1=list(d["district"]).index(highlight) + 0.5,
                      fillcolor="#e9efe9", line_width=0, layer="below")
    xmax = max(1.6, float(np.nanmax(d[ratio_cols].values)) * 1.05) if len(d) else 2
    fig.update_xaxes(title="District yield relative to national yield, same season release (1.0 = national)",
                     range=[0, xmax])
    fig.update_yaxes(title=None, tickfont=dict(size=11, color=INK), showgrid=False)
    n_p = int(d["persistent_shortfall"].sum())
    return _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {n_p} districts sit below national in every matched season",
        "Each dot is one release; the grey bar spans the range. Sorted by mean position across releases.",
        _src(", ".join(rels), snapshot_id,
             "Ratios with harvested area under the coverage threshold are still plotted but do not count toward persistence."),
        height=max(560, 22 * len(d) + 180), margin_l=110)


# ---------------------------------------------------------------- D. input context
def input_context_chart(ev: pd.DataFrame, snapshot_id: str, crop: str, season: str) -> go.Figure:
    d = ev.dropna(subset=["improved_seed_pct", "inorganic_fert_pct"])
    nseed = d["national_improved_seed_pct"].iloc[0]
    nfert = d["national_inorganic_fert_pct"].iloc[0]
    fig = go.Figure()
    for cat in CATEGORY_ORDER:
        g = d[d["category"] == cat]
        if g.empty:
            continue
        prominent = cat in (CATEGORY_PERSISTENT_LOW_INPUT, CATEGORY_PERSISTENT_INPUTS_OK)
        fig.add_trace(go.Scatter(
            x=g["improved_seed_pct"], y=g["inorganic_fert_pct"], mode="markers+text" if prominent else "markers",
            text=g["district"] if prominent else None, textposition="top center",
            textfont=dict(size=10, color=INK_2),
            name=CATEGORY_SHORT[cat],
            marker=dict(size=12 if prominent else 9, color=CATEGORY_COLORS[cat],
                        line=dict(color="#6b6f6c" if not prominent else SURFACE, width=1)),
            customdata=np.c_[g["latest_ratio"].round(2)],
            hovertemplate="<b>%{hovertext}</b><br>Improved seed: %{x:.1f}% of farmers"
                          "<br>Inorganic fertilizer: %{y:.1f}% of farmers"
                          "<br>Yield / national: %{customdata[0]}<extra></extra>",
            hovertext=g["district"]))
    fig.add_vline(x=nseed, line=dict(color=REFERENCE, width=1, dash="dot"))
    fig.add_hline(y=nfert, line=dict(color=REFERENCE, width=1, dash="dot"))
    fig.add_annotation(x=nseed, y=1.0, yref="paper", text=f"national {nseed:.0f}%", showarrow=False,
                       xanchor="left", yanchor="bottom", xshift=4, font=dict(size=11, color=INK_2))
    fig.add_annotation(x=1.0, xref="paper", y=nfert, text=f"national {nfert:.0f}%", showarrow=False,
                       xanchor="right", yanchor="bottom", font=dict(size=11, color=INK_2))
    fig.add_annotation(x=0.01, y=0.01, xref="paper", yref="paper", xanchor="left", yanchor="bottom",
                       text="Lower-left quadrant: both inputs below national", showarrow=False,
                       font=dict(size=11, color=INK_3))
    fig.update_xaxes(title="Farmers using improved seed (% , all crops)", ticksuffix="%")
    fig.update_yaxes(title="Farmers applying inorganic fertilizer (% , all crops)", ticksuffix="%")
    n_ok = int((d["category"] == CATEGORY_PERSISTENT_INPUTS_OK).sum())
    n_low = int((d["category"] == CATEGORY_PERSISTENT_LOW_INPUT).sum())
    return _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {n_ok} of {n_ok + n_low} persistent-shortfall districts do not have low input uptake",
        f"District input uptake in {d['latest_release'].iloc[0]}, all crops pooled. Co-occurrence, not a causal estimate.",
        _src(d["latest_release"].iloc[0], snapshot_id,
             "Input uptake is published per district for all crops combined, not per crop."),
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
        z=z.values, x=[crop_label(c) for c in cat_wide.columns], y=cat_wide.index,
        zmin=0, zmax=n, colorscale=scale, showscale=False, xgap=2, ygap=2,
        text=text.values, hovertemplate="%{y}, %{x}<br>%{text}<extra></extra>"))
    for c in cats:   # legend proxies
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=CATEGORY_SHORT[c],
                                 marker=dict(size=11, symbol="square", color=CATEGORY_COLORS[c],
                                             line=dict(color="#6b6f6c", width=1))))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11, color=INK))
    fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=12, color=INK))
    counts = (cat_wide.isin([CATEGORY_PERSISTENT_LOW_INPUT, CATEGORY_PERSISTENT_INPUTS_OK])).sum(axis=1)
    multi = int((counts >= 3).sum())
    fig = _base_layout(
        fig, f"Season {season}: {multi} districts show persistent shortfalls in three or more priority crops",
        "Evidence category for each district and PSTA 5 priority crop, latest release of this season type",
        _src(f"Season {season} releases", snapshot_id), height=820, margin_l=110)
    fig.update_layout(margin=dict(t=150), legend=dict(y=1.09))
    return fig


# ---------------------------------------------------------------- district comparison
def district_trend_chart(panel: pd.DataFrame, districts: list[str], crop: str, season: str,
                         snapshot_id: str) -> go.Figure:
    d = panel[(panel["crop"] == crop) & (panel["season"] == season)].sort_values("season_year")
    fig = go.Figure()
    nat = d.drop_duplicates("release_id")
    fig.add_trace(go.Scatter(x=nat["release_id"], y=nat["national_yield_kg_ha"] / 1000, mode="lines+markers",
                             name="National", line=dict(color=REFERENCE, width=2, dash="dot"),
                             marker=dict(size=8), hovertemplate="National %{y:.2f} t/ha<extra></extra>"))
    colors = [ACCENT, CATEGORY_COLORS[CATEGORY_DIP]]
    for dist, col in zip(districts, colors):
        g = d[d["district"] == dist]
        thin = g["harvested_ha"] < 500
        fig.add_trace(go.Scatter(
            x=g["release_id"], y=g["yield_kg_ha"] / 1000, mode="lines+markers", name=dist,
            line=dict(color=col, width=2), marker=dict(size=9, symbol=["circle-open" if t else "circle" for t in thin]),
            customdata=np.c_[g["harvested_ha"].round(0)],
            hovertemplate=dist + " %{y:.2f} t/ha<br>harvested %{customdata[0]:,} ha<extra></extra>"))
    fig.update_yaxes(title="Yield, t per harvested ha", rangemode="tozero")
    fig.update_xaxes(title=None, type="category")
    return _base_layout(
        fig, f"{crop_label(crop)}, Season {season}: {' vs '.join(districts)} against the national yield",
        "Same crop, same season type, published district estimates. Open markers: harvested area under 500 ha.",
        _src(", ".join(nat["release_id"]), snapshot_id), height=420)
