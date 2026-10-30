"""Umuzi Analytics - district crop productivity evidence for agricultural planners.

Run locally:  streamlit run app.py
All numbers come from the ACTIVE data snapshot (data/snapshots/ACTIVE.json),
built by scripts/refresh_data.py from published NISR Seasonal Agricultural
Survey tables. No observation is written into this file.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW,
                                      CATEGORY_ORDER, CATEGORY_PERSISTENT_INPUTS_OK,
                                      CATEGORY_PERSISTENT_LOW_INPUT, Params, crop_panel,
                                      evidence_table, input_association, load_targets,
                                      national_vs_target)
from src.config import (CROP_LABELS, DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA, PRODUCT_NAME)
from src.decisions.brief import brief_csv, build_brief
from src.services.snapshot_store import SnapshotStore
from src.services.status import missing_releases, release_status
from src.viz import charts

st.set_page_config(page_title=PRODUCT_NAME, layout="wide", initial_sidebar_state="expanded")

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean", "cooking_banana",
            "sweet_potato", "wheat"]
VIEWS = ["Overview", "Evidence Map", "Persistence", "Input Context", "Triage Matrix",
         "Compare Districts", "Evidence Brief", "Data and Methods"]
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}

st.markdown("""
<style>
  .block-container {padding-top: 4.5rem; padding-bottom: 2rem; max-width: 1440px;}
  [data-testid="stSidebar"] {border-right: 1px solid #e4e4df;}
  [data-testid="stSidebar"] .block-container {padding-top: 1rem;}
  .umz-header {display:flex; justify-content:space-between; align-items:flex-end;
               border-bottom: 1px solid #d9d9d2; padding-bottom: 10px; margin-bottom: 16px;}
  .umz-word {font-size: 22px; font-weight: 700; color:#24493f; letter-spacing: .2px;}
  .umz-sub {font-size: 13px; color:#55595a;}
  .umz-meta {font-size: 12px; color:#55595a; text-align:right; line-height:1.5;}
  .umz-panel {border:1px solid #dcdcd5; border-radius:4px; padding:14px 16px; background:#ffffff;}
  .umz-label {font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#7b7f7f; margin-top:10px;}
  .umz-value {font-size:15px; color:#1f2421;}
  .umz-cat {display:inline-block; padding:2px 8px; border-radius:3px; font-size:13px; font-weight:600;
            border:1px solid #6b6f6c;}
  .umz-note {font-size:13px; color:#55595a; border-left:3px solid #c2beb4; padding:4px 10px; margin:8px 0;}
  .umz-fact {border-top:2px solid #24493f; padding-top:8px;}
  .umz-fact b {font-size:26px; color:#1f2421; display:block; line-height:1.2;}
  .umz-fact span {font-size:13px; color:#55595a;}
  h2, h3 {color:#1f2421;}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data access
@st.cache_resource
def get_store() -> SnapshotStore:
    return SnapshotStore()


@st.cache_data(show_spinner=False)
def load_snapshot(snapshot_id: str):
    return get_store().load(snapshot_id)


@st.cache_data(show_spinner=False)
def cached_evidence(snapshot_id: str, crop: str, season: str, gap: float, min_ha: float) -> pd.DataFrame:
    records, _ = load_snapshot(snapshot_id)
    return evidence_table(records, crop, season, Params(gap_threshold=gap, min_harvested_ha=min_ha))


@st.cache_data(show_spinner=False)
def cached_panel(snapshot_id: str) -> pd.DataFrame:
    return crop_panel(load_snapshot(snapshot_id)[0])


@st.cache_data(show_spinner=False)
def cached_status(snapshot_id: str):
    records, manifest = load_snapshot(snapshot_id)
    return release_status(records, manifest), missing_releases(records)


store = get_store()
SID = store.active_id()
if SID is None:
    st.error("No approved data snapshot is active. Run: python -m scripts.refresh_data bootstrap --approve")
    st.stop()
records, manifest = load_snapshot(SID)
release_ids = sorted(records["release_id"].unique())


def crop_options(season: str) -> list[str]:
    panel = cached_panel(SID)
    p = panel[(panel["season"] == season) & panel["yield_kg_ha"].notna()]
    counts = p.groupby("crop")["district"].nunique()
    available = [c for c in PRIORITY if counts.get(c, 0) >= 10]
    others = sorted(c for c in counts.index if counts[c] >= 10 and c not in PRIORITY)
    return available + others


# ------------------------------------------------------------------ sidebar: navigation + global scope
with st.sidebar:
    st.markdown(f"<div class='umz-word'>{PRODUCT_NAME}</div>"
                "<div class='umz-sub'>District crop productivity evidence</div>", unsafe_allow_html=True)
    st.write("")
    view = st.radio("View", VIEWS, key="view", label_visibility="collapsed")
    st.divider()
    st.markdown("<div class='umz-label'>Analysis scope</div>", unsafe_allow_html=True)
    season = st.radio("Season type", ["A", "B"], horizontal=True, key="season",
                      help="Season A (September to February) and Season B (March to June) are never pooled.")
    copts = crop_options(season)
    if st.session_state.get("crop") not in copts:
        st.session_state["crop"] = copts[0]
    crop = st.selectbox("Crop", copts, format_func=lambda c: CROP_LABELS.get(c, c), key="crop")
    district = st.selectbox("Focus district", DISTRICTS, key="district",
                            index=DISTRICTS.index("Ruhango"))
    with st.expander("Thresholds (sensitivity)"):
        gap = st.slider("Below national if yield ratio under", 0.70, 0.98, GAP_THRESHOLD, 0.01, key="gap",
                        help="Pre-specified default 0.90. Change to test how sensitive categories are.")
        min_ha = st.select_slider("Minimum harvested area (ha)", [100.0, 200.0, 500.0, 1000.0, 2000.0],
                                  MIN_HARVESTED_HA, key="min_ha",
                                  help="District-crop estimates below this area are treated as thin coverage.")
        if gap != GAP_THRESHOLD or min_ha != MIN_HARVESTED_HA:
            st.caption("Non-default thresholds in use. Results differ from the pre-specified analysis.")
    st.divider()
    st.caption(f"Snapshot {SID}")
    st.caption("Source: NISR Seasonal Agricultural Survey, CC BY 4.0")

ev = cached_evidence(SID, crop, season, gap, min_ha)
latest = ev["latest_release"].iloc[0]
crop_name = CROP_LABELS.get(crop, crop)
season_releases = [r for r in release_ids if r.endswith(season)]

st.markdown(f"""
<div class='umz-header'>
  <div><div class='umz-word'>{PRODUCT_NAME}</div>
       <div class='umz-sub'>Where are district crop yields persistently below national, and what should be checked first?</div></div>
  <div class='umz-meta'>Releases: {', '.join(release_ids)}<br>
       Snapshot {SID[-8:]} &middot; approved {html.escape(manifest.get('approval', {}).get('approved_utc', 'n/a')[:10])}<br>
       Scope: {crop_name}, Season {season} ({', '.join(season_releases)})</div>
</div>""", unsafe_allow_html=True)


def caption_block(question: str, pattern: str, implication: str, caveat: str) -> None:
    st.markdown(
        f"<div class='umz-note'><b>Question.</b> {question}<br><b>Pattern.</b> {pattern}<br>"
        f"<b>Implication.</b> {implication}<br><b>Caveat.</b> {caveat}</div>", unsafe_allow_html=True)


def category_badge(cat: str) -> str:
    col = charts.CATEGORY_COLORS[cat]
    ink = "#ffffff" if cat in (CATEGORY_PERSISTENT_LOW_INPUT, CATEGORY_DIP) else "#1f2421"
    return f"<span class='umz-cat' style='background:{col};color:{ink}'>{html.escape(cat)}</span>"


def evidence_panel(row: pd.Series) -> None:
    def f(v, nd=2, s=""):
        return "not reported" if pd.isna(v) else f"{v:,.{nd}f}{s}"
    st.markdown(f"""
<div class='umz-panel'>
  <div class='umz-label'>Selected</div>
  <div class='umz-value'><b>{row['district']}</b> ({row['province']}) &middot; {crop_name} &middot; Season {season}</div>
  <div class='umz-label'>Evidence category</div>{category_badge(row['category'])}
  <div class='umz-label'>Latest yield ({row['latest_release']})</div>
  <div class='umz-value'>{f(row['latest_yield_kg_ha'] / 1000)} t/ha vs national {f(row['national_yield_kg_ha'] / 1000)} t/ha
       (ratio {f(row['latest_ratio'])})</div>
  <div class='umz-label'>Persistence</div>
  <div class='umz-value'>Below {gap:.0%} of national in {int(row['seasons_below'])} of {int(row['matched_seasons_adequate'])} adequate Season {season} releases</div>
  <div class='umz-label'>Coverage</div>
  <div class='umz-value'>{f(row['latest_harvested_ha'], 0)} ha harvested (threshold {min_ha:,.0f} ha)</div>
  <div class='umz-label'>Input uptake, all crops (district / national)</div>
  <div class='umz-value'>Improved seed {f(row['improved_seed_pct'], 1, '%')} / {f(row['national_improved_seed_pct'], 1, '%')}<br>
       Inorganic fertilizer {f(row['inorganic_fert_pct'], 1, '%')} / {f(row['national_inorganic_fert_pct'], 1, '%')}</div>
  <div class='umz-label'>Next step</div>
  <div class='umz-value'>{html.escape(row['next_step'])}</div>
</div>""", unsafe_allow_html=True)
    if view != "Evidence Brief":
        st.caption("Open the Evidence Brief view to export this as a shareable brief.")


def focus_row() -> pd.Series:
    return ev[ev["district"] == district].iloc[0]


TABLE_COLS = {"district": "District", "province": "Province", "category": "Evidence category",
              "latest_ratio": "Yield / national (latest)", "seasons_below": "Seasons below",
              "matched_seasons_adequate": "Seasons with adequate coverage",
              "latest_harvested_ha": "Harvested ha (latest)", "improved_seed_pct": "Improved seed %",
              "inorganic_fert_pct": "Inorganic fertilizer %"}


def evidence_dataframe(df: pd.DataFrame) -> None:
    show = df[list(TABLE_COLS)].rename(columns=TABLE_COLS)
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "Yield / national (latest)": st.column_config.NumberColumn(format="%.2f"),
        "Harvested ha (latest)": st.column_config.NumberColumn(format="%.0f"),
        "Improved seed %": st.column_config.NumberColumn(format="%.1f"),
        "Inorganic fertilizer %": st.column_config.NumberColumn(format="%.1f")})
    st.download_button("Download table (CSV)", df.to_csv(index=False).encode("utf-8"),
                       file_name=f"umuzi_{crop}_season{season}_{SID}.csv", mime="text/csv")


# ------------------------------------------------------------------ views
if view == "Overview":
    nvt = national_vs_target(records, load_targets())
    cur = nvt.dropna(subset=["target_t_ha"])
    n_below_target = int((cur["attainment"] < 1).sum()) if len(cur) else 0
    persist_pairs, crops_checked = 0, 0
    for c in crop_options(season):
        if c in PRIORITY:
            e = cached_evidence(SID, c, season, gap, min_ha)
            persist_pairs += int(e["persistent_shortfall"].sum())
            crops_checked += 1
    insufficient = int((ev["category"] == CATEGORY_INSUFFICIENT).sum())

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='umz-fact'><b>{n_below_target} of {len(cur)}</b><span>PSTA 5 priority crops below "
                f"their 2025/26 national yield target (Season A+B)</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='umz-fact'><b>{persist_pairs}</b><span>district-crop pairs below national in every "
                f"matched Season {season} release ({crops_checked} priority crops)</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div class='umz-fact'><b>{insufficient}</b><span>districts where {crop_name} Season {season} "
                f"evidence is too thin to classify</span></div>", unsafe_allow_html=True)
    st.write("")
    if len(cur):
        st.plotly_chart(charts.target_attainment_chart(nvt, SID), width="stretch", config=PLOT_CONFIG, theme=None)
        lo = cur.sort_values("attainment").iloc[0]
        caption_block(
            "Is national productivity on the PSTA 5 trajectory for priority crops?",
            f"In {cur['agricultural_year'].iloc[0]}, national yields ranged from "
            f"{cur['attainment'].min():.0%} ({CROP_LABELS.get(lo['crop'])}) to {cur['attainment'].max():.0%} of target.",
            "A national gap is delivered or closed in districts. The next views show which district-crop gaps recur.",
            "Approximation: A+B production over A+B harvested area; Season C and PSTA 5's own aggregation method are not reproduced.")
    st.markdown("#### How to use this workspace")
    st.markdown(
        "1. Choose a **season type** and **crop** in the left rail. Every view, table and export follows that scope.\n"
        "2. **Evidence Map** shows where shortfalls sit; **Persistence** shows whether they recur or are one-off dips.\n"
        "3. **Input Context** separates shortfalls with low input uptake from those where inputs are not low.\n"
        "4. **Compare Districts** checks two districts on the same basis; **Evidence Brief** exports a shareable note "
        "with field-check questions and limits.")

elif view == "Evidence Map":
    left, right = st.columns([0.66, 0.34], gap="medium")
    with left:
        st.plotly_chart(charts.category_map(ev, SID, crop, season, highlight=district, threshold=gap),
                        width="stretch", config=PLOT_CONFIG, theme=None)
    with right:
        evidence_panel(focus_row())
    counts = ev["category"].value_counts()
    caption_block(
        f"Where are {crop_name} Season {season} yields below national, and is that position stable?",
        f"{int(counts.get(CATEGORY_PERSISTENT_LOW_INPUT, 0) + counts.get(CATEGORY_PERSISTENT_INPUTS_OK, 0))} districts "
        f"are below national in every adequately covered Season {season} release; "
        f"{int(counts.get(CATEGORY_DIP, 0))} are below in the latest release only.",
        "Persistent shortfalls are candidates for diagnosis before the next season; latest-season dips call for monitoring.",
        "District estimates rely on farmer-reported yields; district standard errors are not published by NISR.")
    evidence_dataframe(ev)

elif view == "Persistence":
    st.plotly_chart(charts.persistence_chart(ev, SID, crop, season, gap, highlight=district),
                    width="stretch", config=PLOT_CONFIG, theme=None)
    n_p = int(ev["persistent_shortfall"].sum())
    wide = ev.dropna(subset=["range_ratio"])
    caption_block(
        "Is a low yield a recurring pattern or a single bad season?",
        f"{n_p} districts sit below {gap:.2f} x national in every adequately covered Season {season} release. "
        f"Median spread of a district's position across releases: {wide['range_ratio'].median():.2f}.",
        "A recurring shortfall justifies a field diagnosis; a one-off dip should first be checked against season shocks.",
        "Consistency across releases may partly reflect repeated sampling of similar areas; it is not independent replication.")
    st.dataframe(ev[["district", "category", "mean_ratio", "range_ratio"] +
                    [c for c in ev.columns if c.startswith("ratio_")]].round(2),
                 hide_index=True, width="stretch")

elif view == "Input Context":
    st.plotly_chart(charts.input_context_chart(ev, SID, crop, season), width="stretch", config=PLOT_CONFIG, theme=None)
    assoc = input_association(records, crop, latest, Params(gap_threshold=gap, min_harvested_ha=min_ha))
    a = assoc.set_index("input")

    def describe(var, label):
        r = a.loc[var]
        if pd.isna(r["rho"]):
            return f"{label}: not computed (fewer than 12 districts with adequate coverage)."
        return f"{label}: Spearman rho {r['rho']:+.2f} (n = {int(r['n'])}, nominal p = {r['p']:.3f})."
    st.markdown(f"<div class='umz-note'><b>Association across districts in {latest}</b> (descriptive, not causal)<br>"
                f"{describe('improved_seed_farmers_pct', 'Improved seed uptake vs yield ratio')}<br>"
                f"{describe('inorganic_fert_farmers_pct', 'Inorganic fertilizer uptake vs yield ratio')}</div>",
                unsafe_allow_html=True)
    n_ok = int((ev["category"] == CATEGORY_PERSISTENT_INPUTS_OK).sum())
    caption_block(
        "Do persistent shortfalls coincide with low input uptake?",
        f"{n_ok} persistent-shortfall districts have improved-seed or fertilizer uptake at or above national.",
        "Where inputs are not low, sending more inputs is not the obvious first response; soils, erosion, varieties "
        "and water deserve a field check.",
        "Uptake is published for all crops pooled; crop-specific use may differ. n = 30 districts.")

elif view == "Triage Matrix":
    crops_here = [c for c in crop_options(season) if c in PRIORITY]
    wide = pd.DataFrame({c: cached_evidence(SID, c, season, gap, min_ha).set_index("district")["category"]
                         for c in crops_here}).reindex(DISTRICTS)
    st.plotly_chart(charts.triage_matrix(wide, SID, season), width="stretch", config=PLOT_CONFIG, theme=None)
    multi = wide.apply(lambda c: c.str.startswith("Persistent")).sum(axis=1).sort_values(ascending=False)
    top = multi[multi >= 3]
    caption_block(
        "Are shortfalls crop-specific or district-wide?",
        (f"{len(top)} districts show persistent shortfalls in three or more priority crops: "
         f"{', '.join(top.index)}." if len(top) else "No district has persistent shortfalls in three or more crops."),
        "District-wide patterns point to shared constraints (soils, terrain, services); single-crop patterns point to "
        "crop-specific constraints.",
        "Each cell is classified independently; crops with sparse district coverage show more insufficient-evidence cells.")

elif view == "Compare Districts":
    c1, c2 = st.columns(2)
    d1 = c1.selectbox("District 1", DISTRICTS, index=DISTRICTS.index(district), key="cmp1")
    alt = [d for d in DISTRICTS if d != d1]
    d2 = c2.selectbox("District 2", alt, index=0, key="cmp2")
    panel = cached_panel(SID)
    sub = panel[(panel["crop"] == crop) & (panel["season"] == season) & panel["district"].isin([d1, d2])]
    thin = sub[(sub["harvested_ha"] < min_ha) | sub["yield_kg_ha"].isna()]
    if len(thin):
        st.warning("Comparability limit: " + "; ".join(
            f"{r.district} {r.release_id} " + ("not reported" if pd.isna(r.yield_kg_ha) else f"{r.harvested_ha:,.0f} ha")
            for r in thin.itertuples()) + f". Estimates under {min_ha:,.0f} ha are thin.")
    else:
        st.caption(f"Comparable basis: same crop ({crop_name}), same season type ({season}), "
                   f"same releases, both above the {min_ha:,.0f} ha coverage threshold.")
    st.plotly_chart(charts.district_trend_chart(panel, [d1, d2], crop, season, SID),
                    width="stretch", config=PLOT_CONFIG, theme=None)
    e2 = ev.set_index("district").loc[[d1, d2]]
    cols = st.columns(2)
    for col, d in zip(cols, [d1, d2]):
        r = e2.loc[d]
        col.markdown(category_badge(r["category"]), unsafe_allow_html=True)
        col.markdown(f"Ratio latest **{r['latest_ratio']:.2f}**, mean **{r['mean_ratio']:.2f}**, "
                     f"range **{r['range_ratio']:.2f}** across releases; improved seed "
                     f"{r['improved_seed_pct']:.1f}%, inorganic fertilizer {r['inorganic_fert_pct']:.1f}%.")
    diff = e2["latest_ratio"].diff().iloc[-1]
    caption_block(
        f"How do {d1} and {d2} differ on the same basis?",
        f"Latest yield ratios differ by {abs(diff):.2f} x national.",
        "Use the comparison to pick a reference district for peer learning or field-team exchange.",
        "Differences of a few hundredths are within plausible survey noise; district standard errors are not published.")

elif view == "Evidence Brief":
    row = focus_row()
    left, right = st.columns([0.62, 0.38], gap="medium")
    text = build_brief(row, manifest, Params(gap_threshold=gap, min_harvested_ha=min_ha))
    with left:
        # Demote headings for on-screen reading; the downloaded file keeps its structure.
        st.markdown(text.replace("\n## ", "\n##### ").replace("# ", "#### ", 1))
    with right:
        evidence_panel(row)
        st.download_button("Download brief (Markdown)", text.encode("utf-8"),
                           file_name=f"umuzi_brief_{district}_{crop}_{season}.md", mime="text/markdown")
        st.download_button("Download evidence row (CSV)", brief_csv(row),
                           file_name=f"umuzi_brief_{district}_{crop}_{season}.csv", mime="text/csv")
        st.caption("Change the focus district or crop in the left rail to regenerate the brief.")

elif view == "Data and Methods":
    status, missing = cached_status(SID)
    st.markdown("#### Data status")
    st.markdown(f"Active snapshot **{SID}** (ruleset {manifest['ruleset_version']}), "
                f"{manifest['n_records']:,} canonical records, approved "
                f"{manifest.get('approval', {}).get('approved_utc', 'n/a')}.")
    if missing:
        st.warning("Releases not in the snapshot (not located on the NISR website at import): "
                   + ", ".join(missing) + ". They are treated as missing, never as zero.")
    st.dataframe(status, hide_index=True, width="stretch")
    st.markdown("#### Definitions")
    st.markdown(f"""
- **Yield ratio**: district yield divided by the national yield of the same crop in the same release.
- **Below national**: yield ratio under {gap:.2f} (default {GAP_THRESHOLD:.2f}).
- **Adequate coverage**: yield reported and harvested area at least {min_ha:,.0f} ha (default {MIN_HARVESTED_HA:,.0f}).
- **Persistent shortfall**: below national in every adequately covered release of the same season type, at least 2 releases, including the latest.
- **Low input uptake**: improved-seed and inorganic-fertilizer uptake (farmers, all crops) both below national in the latest release.
- Cells NISR printed as 0 or left blank are shown as **not reported**, never as a zero yield.""")
    st.markdown("#### Evidence categories and their meaning")
    st.dataframe(pd.DataFrame({"Category": CATEGORY_ORDER,
                               "Route": [cached_evidence(SID, crop, season, gap, min_ha)
                                         .query("category == @c")["next_step"].iloc[0]
                                         if (ev["category"] == c).any() else "" for c in CATEGORY_ORDER]}),
                 hide_index=True, width="stretch")
    st.markdown("#### Refreshing data")
    st.code("python -m scripts.refresh_data ingest --file <NISR tables.xlsx> --release-id SAS-2027A "
            "--season-year 2027 --season A --source-url <url>\n"
            "python -m scripts.refresh_data approve --snapshot <snapshot id>\n"
            "python -m scripts.refresh_data rollback --snapshot <earlier snapshot id>", language="bash")
    st.markdown("New releases are validated (districts, crops, units, national reference rows, production = "
                "yield x area) before they can be approved. A failed release is quarantined and the active "
                "snapshot is unchanged. Refresh is analyst-initiated; there is no scheduled retrieval.")
    with st.expander("Snapshot history"):
        st.dataframe(pd.DataFrame([{"snapshot": s["snapshot_id"], "created": s["created_utc"],
                                    "change": f"{s['change']['kind']} {s['change']['release_id']}",
                                    "approval": s.get("approval", {}).get("status")}
                                   for s in store.list_snapshots()]), hide_index=True, width="stretch")
    st.markdown("#### Sources and licences")
    st.markdown(
        "- National Institute of Statistics of Rwanda, Seasonal Agricultural Survey tables, 2024A to 2026B, CC BY 4.0.\n"
        "- MINAGRI, Strategic Plan for Agriculture Transformation 5 (abridged), results framework p.21 (targets).\n"
        "- District boundaries: geoBoundaries RWA ADM2 (derived from NISR geodata), CC BY 4.0.\n"
        "- Full methodology and limitations: `docs/methodology.md`, `docs/limitations.md` in the repository.")
