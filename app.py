"""Umuzi Analytics - what Rwanda's agricultural survey says about each district, and what to check next.

Run locally:  streamlit run app.py
All numbers come from the ACTIVE data snapshot (data/snapshots/ACTIVE.json),
built by scripts/refresh_data.py from published NISR Seasonal Agricultural
Survey tables. No observation is written into this file; the map panel, the
evidence brief and the Umuzi Assistant all read the same Finding
(src/decisions/finding.py).
"""
from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st

from src.analytics.indicators import CATEGORY_ORDER, Params
from src.assistant.umuzi import HELP, Selection, UmuziData, answer
from src.config import (DATA_DIR, DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA, PRODUCT_NAME,
                        ROOT)
from src.decisions.brief import brief_csv, build_brief
from src.decisions.finding import crop_name, release_name, target_position
from src.services.snapshot_store import SnapshotStore
from src.services.status import missing_releases, release_status
from src.viz import charts
from src.viz.visuals import legend_html, target_arrow_svg, window_strip_html

st.set_page_config(page_title=PRODUCT_NAME, layout="wide", initial_sidebar_state="collapsed")

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean", "cooking_banana",
            "sweet_potato", "wheat"]
BOT_ICON = str(DATA_DIR / "chatBOT.png")
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}

st.markdown("""
<style>
  .block-container {padding-top: 4.5rem; padding-bottom: 2rem; max-width: 1440px;}
  .umz-header {display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap;
               border-bottom:1px solid #d9d9d2; padding-bottom:10px; margin-bottom:14px;}
  .umz-word {font-size:24px; font-weight:700; color:#24493f;}
  .umz-sub {font-size:14px; color:#55595a;}
  .umz-meta {font-size:12px; color:#55595a; text-align:right; line-height:1.5;}
  .umz-card {border:1px solid #dcdcd5; border-radius:6px; padding:16px 18px; background:#ffffff;}
  .umz-cat {display:inline-block; padding:3px 10px; border-radius:3px; font-size:13px; font-weight:600;
            border:1px solid #6b6f6c;}
  .umz-sel {font-size:13px; color:#55595a; margin:8px 0 4px 0;}
  .umz-head {font-size:17px; line-height:1.45; color:#1f2421; margin:6px 0 12px 0;}
  .umz-label {font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#7b7f7f; margin-top:12px;}
  .umz-fig {font-size:13.5px; color:#1f2421; margin:3px 0;}
  .umz-fig b {color:#55595a; font-weight:600;}
  .umz-next {font-size:14px; color:#1f2421; border-left:3px solid #24493f; padding:4px 10px; margin-top:6px;}
  .umz-keep {font-size:12.5px; color:#55595a; margin:2px 0;}
  .umz-strip-cap {font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:#7b7f7f; margin-top:6px;}
  .umz-strip {display:flex; gap:6px; margin-top:6px;}
  .umz-pill {flex:1; border-radius:5px; padding:6px 8px; border:1px solid #c9cec9; text-align:center;}
  .umz-pill-rel {font-size:11px;} .umz-pill-val {font-size:20px; font-weight:700; line-height:1.2;}
  .umz-pill-lab {font-size:11px;}
  .umz-legend {display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:8px 16px; margin-top:6px;}
  .umz-leg-row {display:flex; gap:9px; align-items:flex-start; font-size:13px; color:#1f2421;}
  .umz-sw {flex:0 0 16px; height:16px; border:1px solid #6b6f6c; border-radius:2px; margin-top:2px;}
  .umz-count {display:inline-block; min-width:20px; padding:0 6px; border-radius:9px; background:#eef0ec;
              font-size:12px; font-weight:600; text-align:center;}
  .umz-leg-note {font-size:11.5px; color:#7b7f7f; line-height:1.35;}
  .umz-target {border:1px solid #dcdcd5; border-radius:6px; padding:10px 16px 4px 16px; background:#ffffff;}
  .umz-target-cap {font-size:13px; color:#55595a;}
  .umz-warn {font-size:13px; background:#fbf0dc; border:1px solid #e6c88f; padding:6px 10px; border-radius:4px;}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data access
@st.cache_resource
def get_store() -> SnapshotStore:
    return SnapshotStore()


@st.cache_resource(show_spinner=False)
def get_data(snapshot_id: str, gap: float, min_ha: float) -> UmuziData:
    records, manifest = get_store().load(snapshot_id)
    return UmuziData(records, manifest, Params(gap_threshold=gap, min_harvested_ha=min_ha))


@st.cache_data(show_spinner=False)
def cached_status(snapshot_id: str):
    records, manifest = get_store().load(snapshot_id)
    return release_status(records, manifest), missing_releases(records)


@st.cache_data(show_spinner=False)
def report(name: str) -> dict:
    p = ROOT / "reports" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


store = get_store()
SID = store.active_id()
if SID is None:
    st.error("No approved data snapshot is active. Run: python -m scripts.refresh_data bootstrap --approve")
    st.stop()

gap = st.session_state.get("gap", GAP_THRESHOLD)
min_ha = st.session_state.get("min_ha", MIN_HARVESTED_HA)
data = get_data(SID, gap, min_ha)
records, manifest = data.records, data.manifest
releases = sorted(records["release_id"].unique(), key=lambda r: (int(r[4:8]), r[-1]))


def crop_options(season: str) -> list[str]:
    p = data.panel[(data.panel["season"] == season) & data.panel["yield_kg_ha"].notna()]
    counts = p.groupby("crop")["district"].nunique()
    return ([c for c in PRIORITY if counts.get(c, 0) >= 10]
            + sorted(c for c in counts.index if counts[c] >= 10 and c not in PRIORITY))


# ------------------------------------------------------------------ header and selection
st.markdown(f"""
<div class='umz-header'>
  <div><div class='umz-word'>{PRODUCT_NAME}</div>
       <div class='umz-sub'>What Rwanda's agricultural survey says about each district's crop yields, and what to check next</div></div>
  <div class='umz-meta'>NISR Seasonal Agricultural Survey: {len(releases)} surveys, {release_name(releases[0])} to {release_name(releases[-1])}
       (Season B 2025 not published)<br>Validated snapshot {SID[-8:]}</div>
</div>""", unsafe_allow_html=True)

st.session_state.setdefault("season", "A")
st.session_state.setdefault("district", "Ruhango")
c1, c2, c3 = st.columns([1.1, 1.1, 0.8])
season_now = st.session_state["season"]
copts = crop_options(season_now)
if st.session_state.get("crop") not in copts:
    st.session_state["crop"] = "maize" if "maize" in copts else copts[0]
crop = c1.selectbox("Crop (type to search)", copts, key="crop", format_func=lambda c: crop_name(c))
district = c2.selectbox("District (type to search)", DISTRICTS, key="district")
season = c3.radio("Season", ["A", "B"], key="season", horizontal=True,
                  format_func=lambda s: f"Season {s}",
                  help="Season A runs September to February, Season B March to June. They are never mixed.")

if gap != GAP_THRESHOLD or min_ha != MIN_HARVESTED_HA:
    st.markdown(f"<div class='umz-warn'>Testing non-default benchmark settings (below = under {gap:.0%} of national, "
                f"reliable from {min_ha:,.0f} ha). Reset them in Data and methods.</div>", unsafe_allow_html=True)

ev = data.evidence(crop, season)
sel = Selection(district, crop, season)
finding = data.finding(sel)

# ------------------------------------------------------------------ overview: map + finding
left, right = st.columns([1.35, 1], gap="large")
with left:
    n_rep = int(ev["category"].isin(CATEGORY_ORDER[:2]).sum())
    st.markdown(f"**{crop_name(crop)}, Season {season}: {n_rep} of 30 districts were repeatedly below the national "
                f"yield benchmark** (latest survey {release_name(ev['latest_release'].iloc[0])})")
    st.plotly_chart(charts.category_map(ev, SID, crop, season, highlight=district, compact=True),
                    width="stretch", config=PLOT_CONFIG)
    st.markdown(legend_html(ev["category"].value_counts().to_dict(), finding.category), unsafe_allow_html=True)

with right:
    color = charts.CATEGORY_COLORS[finding.category]
    ink = "#ffffff" if finding.category in (CATEGORY_ORDER[0], CATEGORY_ORDER[2]) else "#1f2421"
    figs = "".join(f"<div class='umz-fig'><b>{escape(k)}:</b> {escape(v)}</div>" for k, v in finding.figures)
    keep = "".join(f"<div class='umz-keep'>- {escape(x)}</div>" for x in finding.limitations)
    st.markdown(f"""
<div class='umz-card'>
  <span class='umz-cat' style='background:{color};color:{ink}'>{escape(finding.category)}</span>
  <div class='umz-sel'>{escape(district)} ({escape(finding.row['province'])}) &middot; {escape(crop_name(crop))} &middot; Season {season}</div>
  <div class='umz-head'>{escape(finding.headline)}</div>
  {window_strip_html(finding)}
  <div class='umz-label'>The figures</div>{figs}
  <div class='umz-label'>Surveys used</div>
  <div class='umz-fig'>{escape(', '.join(release_name(r) for r in finding.releases))} (NISR, snapshot {SID[-8:]})</div>
  <div class='umz-label'>What to check next</div><div class='umz-next'>{escape(finding.next_step)}</div>
  <div class='umz-label'>Keep in mind</div>{keep}
</div>""", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    b1.download_button("Download brief (Markdown)", build_brief(finding, manifest).encode("utf-8"),
                       file_name=f"umuzi_brief_{district}_{crop}_season{season}.md", mime="text/markdown")
    b2.download_button("Download figures (CSV)", brief_csv(finding),
                       file_name=f"umuzi_{district}_{crop}_season{season}.csv", mime="text/csv")

t = target_position(records, crop)
if t is not None:
    gap_t = t.target_t_ha - t.yield_t_ha
    st.markdown(f"""
<div class='umz-target'>
  <div class='umz-label' style='margin-top:0'>Rwanda against the PSTA 5 {escape(crop_name(crop).lower())} target</div>
  {target_arrow_svg(t)}
  <div class='umz-target-cap'>National {escape(crop_name(crop).lower())} yield, Season A + B, {t.agricultural_year}:
  {t.yield_t_ha:.2f} t/ha, {t.attainment:.0%} of the {t.target_t_ha:.2f} t/ha target
  {f'({gap_t:.2f} t/ha short)' if gap_t > 0 else '(target met)'}. PSTA 5 aims for {t.final_target_t_ha:.2f} t/ha by 2028/29.
  Targets are national only; districts are compared with the national yield. Source: MINAGRI PSTA 5 results framework p.21; NISR SAS.</div>
</div>""", unsafe_allow_html=True)
else:
    st.caption(f"PSTA 5 sets no national yield target for {crop_name(crop).lower()}.")

st.write("")

# ------------------------------------------------------------------ details on demand
tab_ask, tab_grid, tab_hist, tab_inp, tab_all, tab_meth = st.tabs(
    ["Ask the Umuzi Assistant", "Survey by survey, all districts", f"{district} over time",
     "Input uptake", "All districts table", "Data and methods"])

# ---- Umuzi Assistant: follows the map selection; a named district or crop carries into follow-ups.
map_key = (district, crop, season)
if st.session_state.get("asst_map_key") != map_key:
    st.session_state["asst_map_key"] = map_key
    st.session_state["asst_sel"] = Selection(district, crop, season)
st.session_state.setdefault("chat", [])


def ask(question: str) -> None:
    a = answer(data, question, st.session_state["asst_sel"])
    st.session_state["asst_sel"] = a.selection
    st.session_state["chat"].append(dict(role="user", text=question))
    st.session_state["chat"].append(dict(role="assistant", text=a.text, evidence=a.evidence,
                                         keep=a.keep_in_mind, sel=a.selection))


def show_on_map(s: Selection) -> None:
    st.session_state["district"], st.session_state["crop"], st.session_state["season"] = s.district, s.crop, s.season


with tab_ask:
    st.caption(f"Answers use the same validated NISR figures and rules as the map. Current focus: "
               f"{st.session_state['asst_sel'].district}, {crop_name(st.session_state['asst_sel'].crop).lower()}, "
               f"Season {st.session_state['asst_sel'].season}.")
    s_ = st.session_state["asst_sel"]
    examples = [f"Has {s_.district}'s {crop_name(s_.crop).lower()} yield stayed below national in Season {s_.season}?",
                "What should I verify about fertilizer access?",
                f"Which other districts are repeatedly below for {crop_name(s_.crop).lower()}?",
                "How has it changed since 2018?"]
    ec = st.columns(len(examples))
    for col, q in zip(ec, examples):
        col.button(q, on_click=ask, args=(q,), width="stretch")
    with st.container(height=460):
        if not st.session_state["chat"]:
            with st.chat_message("assistant", avatar=BOT_ICON):
                st.markdown("Muraho. I am the Umuzi Assistant. " + HELP)
        for i, m in enumerate(st.session_state["chat"]):
            if m["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(m["text"])
                continue
            with st.chat_message("assistant", avatar=BOT_ICON):
                st.markdown(m["text"])
                if m["evidence"]:
                    st.markdown("**Evidence**\n" + "\n".join(f"- {e}" for e in m["evidence"]))
                if m["keep"]:
                    st.markdown("**Keep in mind**\n" + "\n".join(f"- {k}" for k in m["keep"]))
                s = m["sel"]
                if s and (s.district, s.crop, s.season) != map_key and i == len(st.session_state["chat"]) - 1:
                    st.button(f"Show {s.district}, {crop_name(s.crop).lower()}, Season {s.season} on the map",
                              key=f"show_{i}", on_click=show_on_map, args=(s,))
    q = st.chat_input("Ask about a district, crop or season")
    if q:
        ask(q)
        st.rerun()

with tab_grid:
    st.caption("Each cell is the district's yield as % of the national yield in that survey. The outlined block is "
               "the last 3 surveys, which decide the map colour.")
    st.plotly_chart(charts.pattern_grid(ev, data.panel, SID, crop, season, highlight=district),
                    width="stretch", config=PLOT_CONFIG)

with tab_hist:
    st.plotly_chart(charts.district_history_chart(data.panel, district, crop, season, finding.releases, SID),
                    width="stretch", config=PLOT_CONFIG)
    st.caption("District rankings from 2018 and 2019 agree only weakly with later years (see Data and methods), "
               "so the label uses the last 3 surveys; the earlier years are shown for context.")

with tab_inp:
    st.plotly_chart(charts.input_context_chart(ev, SID, crop, season, highlight=district),
                    width="stretch", config=PLOT_CONFIG)
    st.caption("Input uptake is the share of farmers using the input on any crop in the district; NISR does not "
               "publish it per crop at district level.")

with tab_all:
    cols = {"district": "District", "province": "Province", "category": "Finding",
            "latest_ratio": "Yield as % of national (latest)", "below_in_window": "Below in last 3 surveys",
            "reliable_in_window": "Reliable of last 3", "latest_harvested_ha": "Harvested ha (latest)",
            "improved_seed_pct": "Improved seed %", "inorganic_fert_pct": "Inorganic fertilizer %"}
    show = ev[list(cols)].rename(columns=cols)
    show["Yield as % of national (latest)"] = show["Yield as % of national (latest)"] * 100
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "Yield as % of national (latest)": st.column_config.NumberColumn(format="%.0f%%"),
        "Harvested ha (latest)": st.column_config.NumberColumn(format="%.0f"),
        "Improved seed %": st.column_config.NumberColumn(format="%.1f"),
        "Inorganic fertilizer %": st.column_config.NumberColumn(format="%.1f")})
    st.download_button("Download table (CSV)", ev.to_csv(index=False).encode("utf-8"),
                       file_name=f"umuzi_{crop}_season{season}_{SID}.csv", mime="text/csv")

with tab_meth:
    eda, bt = report("history_eda.json"), report("backtest_results.json")
    st.markdown(f"""
**How a district is labelled.** For the chosen crop and season, each district's yield is divided by the national
yield of the same survey. It is *below national* when under {GAP_THRESHOLD:.0%} (NISR publishes no district margins
of error, so smaller gaps are not flagged). An estimate is *reliable* when a yield is reported and at least
{MIN_HARVESTED_HA:,.0f} ha were harvested. *Repeatedly below* means below in at least 2 of the last 3 surveys of
that season, with at least 2 reliable. Input uptake is then compared with national: both improved seed and
inorganic fertilizer below national gives the "low input uptake" label.""")

    st.markdown("**1. Which survey years can be used.** Every downloaded file was checked for district-level yield tables.")
    if eda.get("source_audit"):
        st.dataframe(pd.DataFrame(eda["source_audit"]).sort_values(["year", "kind"]), hide_index=True, width="stretch")
    st.markdown("2014-2017 report yields only by land-use stratum or province, so district analysis starts in 2018. "
                "Season B 2025 was not published. 2018 reports input use per plot or without a stated basis, not per farmer, so its input "
                "figures are not used.")

    st.markdown("**2. Checks on every survey** (run automatically before data can go live).")
    status, missing = cached_status(SID)
    st.dataframe(status[["release", "gate", "yield_cells_observed", "yield_cells_not_reported", "warnings", "notes"]],
                 hide_index=True, width="stretch")
    if missing:
        st.caption("Missing between first and last survey: " + ", ".join(missing))
    if eda.get("reprinted_national_check"):
        d = pd.DataFrame(eda["reprinted_national_check"])
        st.markdown(f"Duplicates and revisions: {len(d)} national production values that later workbooks re-print "
                    f"for the previous year match the original survey with a largest difference of "
                    f"{d['diff_pct'].abs().max():.2f}%. The 2024 annual workbook matches the separate 2024 Season A and "
                    "B files cell for cell.")

    st.markdown("**3. Do districts keep their position over time?** Median rank agreement (Spearman) of district "
                "yield ratios between consecutive surveys of the same season, across six priority crops.")
    if eda.get("rank_agreement"):
        ra = [dict(season=s, surveys=k.replace("SAS-", "").replace("|", " to "), median_rho=v)
              for s in "AB" for k, v in eda["rank_agreement"][s]["consecutive"].items()]
        st.dataframe(pd.DataFrame(ra), hide_index=True, width="stretch")
        early = [r["median_rho"] for r in ra if r["season"] == "A" and r["surveys"][:4] in ("2018", "2019")]
        later = [r["median_rho"] for r in ra if r["season"] == "A" and r["surveys"][:4] >= "2020"]
        st.markdown(f"Season A agreement is weak from 2018 to 2020 ({', '.join(f'{v:.2f}' for v in early)}) and "
                    f"{min(later):.2f} to {max(later):.2f} since, so the label uses the most recent three surveys "
                    "rather than all history.")

    st.markdown("**4. Would a statistical model flag next season's shortfalls better than the rules?**")
    if bt:
        rows = [dict(method=k.replace("_", " "), balanced_accuracy=v["balanced_accuracy"],
                     shortfalls_caught=v["recall"], precision=v["precision"], brier_score=v["brier"])
                for k, v in bt["test"].items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        ci = bt["model_vs_best_rule_test"]["balanced_accuracy_diff_ci"]
        st.markdown(
            f"Tested on the {bt['n_units']['test']} district-crop cases of 2024-2026, using only earlier surveys to "
            f"predict each one. The logistic model was no more accurate than the best rule (difference "
            f"{ci[0]:+.3f} to {ci[1]:+.3f}, 95% interval), so **the rules were kept** ({bt['decision']}). The old rule "
            f"'below in every survey' caught only {bt['test']['all_history']['recall']:.0%} of next-season shortfalls; "
            f"'below in 2 of the last 3' catches {bt['test']['last_3_two']['recall']:.0%}, which is why it is the "
            "rule now used.")

    with st.expander("Test the benchmark settings (sensitivity)"):
        st.slider("Below national if yield is under this share of national", 0.70, 0.98, GAP_THRESHOLD, 0.01, key="gap")
        st.select_slider("Reliable from this harvested area (ha)", [100.0, 200.0, 500.0, 1000.0, 2000.0],
                         MIN_HARVESTED_HA, key="min_ha")
        st.caption("Defaults: 90% and 500 ha. Changing them recolours the map and the assistant's answers.")
