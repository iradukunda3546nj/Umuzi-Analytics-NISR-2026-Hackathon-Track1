"""Umuzi Analytics - what Rwanda's agricultural survey says about each district, and what to check next.

Run locally:  streamlit run app.py

Five sections, one question each:
  Home           what this is and who it is for
  Your district  how far the district is from Rwanda's yield (map + target arrow)
  Why?           pattern, seed and fertilizer, verdict, and what to check first
  Ask Umuzi      the assistant, for questions across districts and crops
  Evidence       survey-by-survey tables, data checks, the backtest, sensitivity

All numbers come from the ACTIVE data snapshot (data/snapshots/ACTIVE.json),
built by scripts/refresh_data.py from published NISR Seasonal Agricultural
Survey tables. No observation is written into this file; every page and the
assistant read the same Finding (src/decisions/finding.py) and its wording
(src/decisions/explain.py).
"""
from __future__ import annotations

import base64
import json
from html import escape

import pandas as pd
import streamlit as st

from src.analytics.indicators import CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW, REPEATED, Params
from src.assistant.umuzi import Selection, UmuziData, answer, suggestions_for
from src.config import (DATA_DIR, DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA, PRODUCT_NAME,
                        ROOT)
from src.decisions.brief import brief_csv, build_brief
from src.decisions.explain import PLAIN_CATEGORY, explain
from src.decisions.finding import crop_name, pct, release_name, target_position
from src.services.snapshot_store import SnapshotStore
from src.services.status import missing_releases, release_status
from src.ui.style import CSS, background_css
from src.viz import charts
from src.viz.icons import icon
from src.viz.visuals import (action_card_html, chip_html, district_target_svg, flow_html, hook_cards_html,
                             inputs_html, legend_chips_html, pattern_tiles_html, stats_html,
                             target_arrow_svg, verdict_html)

st.set_page_config(page_title=PRODUCT_NAME, layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean", "cooking_banana",
            "sweet_potato", "wheat"]
BOT_ICON = str(DATA_DIR / "chatBOT.png")
VIEWS = {"home": "Home", "explore": "Your district", "why": "Why?", "ask": "Ask Umuzi", "evidence": "Evidence"}
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}


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


@st.cache_data(show_spinner=False)
def background_b64() -> str | None:
    p = DATA_DIR / "BackGD.jpg"
    return base64.b64encode(p.read_bytes()).decode("ascii") if p.exists() else None


store = get_store()
SID = store.active_id()
if SID is None:
    st.error("No approved data snapshot is active. Run: python -m scripts.refresh_data bootstrap --approve")
    st.stop()

# ------------------------------------------------------------------ state
# Persistent keys (district, crop, season, gap, min_ha, view) live outside widgets,
# because Streamlit drops a widget's key on any run where that widget is not drawn.
ss = st.session_state
qp = st.query_params                     # shareable links: ?view=why&district=Gasabo&crop=cassava&season=A
ss.setdefault("view", qp.get("view") if qp.get("view") in VIEWS else "home")
ss.setdefault("season", qp.get("season") if qp.get("season") in ("A", "B") else "A")
ss.setdefault("district", qp.get("district") if qp.get("district") in DISTRICTS else "Ruhango")
if "crop" not in ss and qp.get("crop"):
    ss["crop"] = qp.get("crop")
ss.setdefault("gap", GAP_THRESHOLD)
ss.setdefault("min_ha", MIN_HARVESTED_HA)
ss.setdefault("chat", [])

data = get_data(SID, ss["gap"], ss["min_ha"])
records, manifest = data.records, data.manifest
releases = sorted(records["release_id"].unique(), key=lambda r: (int(r[4:8]), r[-1]))


def crop_options(season: str) -> list[str]:
    p = data.panel[(data.panel["season"] == season) & data.panel["yield_kg_ha"].notna()]
    counts = p.groupby("crop")["district"].nunique()
    return ([c for c in PRIORITY if counts.get(c, 0) >= 10]
            + sorted(c for c in counts.index if counts[c] >= 10 and c not in PRIORITY))


if ss.get("crop") not in crop_options(ss["season"]):
    ss["crop"] = "maize"


def why_question(category: str) -> str:
    """The question the "Why" step answers, in the user's words, for this kind of finding."""
    if category == CATEGORY_NOT_BELOW:
        return "What is going well here?"
    if category == CATEGORY_INSUFFICIENT:
        return "Why can't we be sure?"
    return "Why is the harvest low here?"


def go(view: str) -> None:
    ss["view"] = view


def sync(name: str) -> None:
    ss[name] = ss[f"w_{name}"]


# A click on the map selects that district (handled before the selectors are drawn).
_click = ss.get("map_click")
if _click and _click.get("selection", {}).get("points"):
    pt = _click["selection"]["points"][0]
    token = json.dumps(pt, sort_keys=True, default=str)
    loc = pt.get("location")
    if loc in DISTRICTS and ss.get("_map_token") != token:
        ss["_map_token"] = token
        ss["district"] = loc

# ------------------------------------------------------------------ top bar
view = ss["view"]
if view == "home":
    qp.clear()
    qp["view"] = "home"
else:
    qp.update(view=view, district=ss["district"], crop=ss["crop"], season=ss["season"])
bar_l, bar_r = st.columns([1, 2.2], vertical_alignment="center")
bar_l.markdown(f"<div class='umz-brand'>{icon('target', 26, 2)}Umuzi Analytics</div>", unsafe_allow_html=True)
with bar_r.container(key="nav", horizontal=True, horizontal_alignment="right", gap="small"):
    for k, label in VIEWS.items():
        st.button(label, key=f"nav_{k}", on_click=go, args=(k,), width="content",
                  type="primary" if k == view else "secondary")


def selection_bar() -> tuple[str, str, str]:
    for name in ("crop", "district", "season"):
        ss[f"w_{name}"] = ss[name]
    c1, c2, c3 = st.columns([1.1, 1.1, 0.8])
    c1.selectbox("Crop (type to search)", crop_options(ss["season"]), key="w_crop", on_change=sync, args=("crop",),
                 format_func=crop_name)
    c2.selectbox("District (type to search)", DISTRICTS, key="w_district", on_change=sync, args=("district",))
    c3.radio("Season", ["A", "B"], key="w_season", on_change=sync, args=("season",), horizontal=True,
             format_func=lambda s: f"Season {s}",
             help="Season A runs September to February, Season B March to June. They are never mixed.")
    if ss.get("crop") not in crop_options(ss["season"]):
        ss["crop"] = "maize"
    if ss["gap"] != GAP_THRESHOLD or ss["min_ha"] != MIN_HARVESTED_HA:
        st.markdown(f"<div class='umz-warn'>Testing non-default cut-offs (short = under {ss['gap']:.0%} of the "
                    f"national average, counted from {ss['min_ha']:,.0f} ha). Reset them in Evidence.</div>",
                    unsafe_allow_html=True)
    return ss["crop"], ss["district"], ss["season"]


# ------------------------------------------------------------------ assistant
def ask(question: str) -> None:
    sel = ss.get("asst_sel") or Selection(ss["district"], ss["crop"], ss["season"])
    a = answer(data, question, sel)
    ss["asst_sel"] = a.selection
    ss["chat"].append(dict(role="user", text=question))
    ss["chat"].append(dict(role="assistant", text=a.text, evidence=a.evidence, keep=a.keep_in_mind,
                           sel=a.selection, sugg=a.suggestions))


def show_on_map(s: Selection) -> None:
    ss["district"], ss["crop"], ss["season"] = s.district, s.crop, s.season
    ss["view"] = "explore"


def render_chat(height: int) -> None:
    key = (ss["district"], ss["crop"], ss["season"])
    if ss.get("asst_key") != key:                   # follow the page's selection
        if ss["chat"]:                              # older answers were about something else: say so
            ss["chat"].append(dict(role="note", text=f"Now looking at {key[0]}, {crop_name(key[1]).lower()}, "
                                                     f"Season {key[2]}"))
        ss["asst_key"] = key
        ss["asst_sel"] = Selection(*key)
    s_ = ss["asst_sel"]
    st.markdown(f"<div class='umz-ask-head'><img src='data:image/png;base64,{bot_b64()}' width='34'>"
                f"Ask Umuzi<span class='umz-fine' style='margin:0 0 0 6px'>following {escape(s_.district)}, "
                f"{escape(crop_name(s_.crop).lower())}, Season {s_.season}</span></div>", unsafe_allow_html=True)
    with st.container(height=height):
        if not ss["chat"]:
            with st.chat_message("assistant", avatar=BOT_ICON):
                st.markdown("Muraho! Ask me about any district's crop yields, seed and fertilizer use, "
                            "or what to check next.")
            sugg = suggestions_for(s_)
        else:
            sugg = []
        for i, m in enumerate(ss["chat"]):
            if m["role"] == "note":
                st.markdown(f"<div class='umz-chat-note'>{escape(m['text'])}</div>", unsafe_allow_html=True)
                if i == len(ss["chat"]) - 1:
                    sugg = suggestions_for(s_)
                continue
            if m["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(m["text"])
                continue
            last = i == len(ss["chat"]) - 1
            with st.chat_message("assistant", avatar=BOT_ICON):
                st.markdown(m["text"])
                if m["evidence"] or m["keep"]:
                    with st.expander("Evidence and limits"):
                        st.markdown("\n".join(f"- {e}" for e in m["evidence"] + m["keep"]))
                s = m["sel"]
                if last and s and (s.district, s.crop, s.season) != key:
                    st.button(f"Show {s.district}, {crop_name(s.crop).lower()}, Season {s.season} on the map",
                              key=f"show_{i}", on_click=show_on_map, args=(s,))
            if last:
                sugg = m.get("sugg") or []
        if sugg:
            with st.container(horizontal=True, gap="small"):
                for j, q in enumerate(sugg):
                    st.button(q, key=f"sugg_{len(ss['chat'])}_{j}", on_click=ask, args=(q,), width="content")
    q = st.chat_input("Ask about a district, crop or season")
    if q:
        ask(q)
        st.rerun()


@st.cache_data(show_spinner=False)
def bot_b64() -> str:
    return base64.b64encode((DATA_DIR / "chatBOT.png").read_bytes()).decode("ascii")


# ------------------------------------------------------------------ pages
def page_home() -> None:
    bg = background_b64()
    if bg:
        st.markdown(background_css(bg), unsafe_allow_html=True)
    n_crops = len(set(crop_options("A")) | set(crop_options("B")))
    st.markdown(
        "<div class='umz-hero'><h1>Umuzi <span>Analytics</span></h1>"
        "<div class='umz-q'>How is the harvest going in your district? The answer is in Rwanda's farm survey, "
        "but it is hidden in pages of numbers.</div>"
        "<p><b>Don't worry, we've got you covered.</b> Umuzi reads the survey for you and tells you, in plain words, "
        "where to act, when it matters, and what to do first.</p></div>"
        + hook_cards_html([
            ("pin", "WHERE", "Where is the harvest low?",
             "See which districts harvest less than the national average, crop by crop."),
            ("repeat", "WHEN", "Bad luck, or a pattern?",
             "One poor season can happen anywhere. We show which districts fall short season after season."),
            ("seed", "WHY", "Enough seed and fertilizer?",
             "See if fewer farmers here use improved seed and fertilizer than the national average."),
            ("megaphone", "WHAT", "What to do first",
             "A short checklist for the district team, in plain words."),
        ])
        + stats_html([(str(len(releases)), "surveys read"), ("30", "districts"), (str(n_crops), "crops"),
                      (f"{releases[0][4:8]}-{releases[-1][4:8]}", "both farming seasons")])
        + flow_html([("pin", "Pick a district"), ("target", "See how it compares"), ("question", "Ask why"),
                     ("megaphone", "Take action")]),
        unsafe_allow_html=True)
    _, a, b, _ = st.columns([1.2, 1, 0.8, 1.2])
    a.button("Find your district", key="cta_explore", on_click=go, args=("explore",), width="stretch")
    b.button("Ask Umuzi", key="cta_ask", on_click=go, args=("ask",), width="stretch")
    st.markdown("<div class='umz-who'>Built for district agronomists, MINAGRI and RAB planners, and partners in the "
                "field. Data: National Institute of Statistics of Rwanda, Seasonal Agricultural Survey "
                f"({escape(release_name(releases[0]))} to {escape(release_name(releases[-1]))}).</div>",
                unsafe_allow_html=True)


def page_explore() -> None:
    crop, district, season = selection_bar()
    ev = data.evidence(crop, season)
    f = data.finding(Selection(district, crop, season))
    r = f.row
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        n_rep = int(ev["category"].isin(REPEATED).sum())
        st.markdown(f"<div class='umz-kicker'>{escape(crop_name(crop))} &middot; "
                    f"{escape(release_name(f.latest_release))}</div>"
                    f"<div class='umz-sub'><b>{n_rep} of 30</b> districts harvested under 90% of the national average "
                    "in at least 2 of the last 3 surveys</div>", unsafe_allow_html=True)
        st.plotly_chart(charts.category_map(ev, SID, crop, season, highlight=district, compact=True),
                        width="stretch", config=PLOT_CONFIG, key="map_click", on_select="rerun",
                        selection_mode="points")
        st.markdown(legend_chips_html(ev["category"].value_counts().to_dict(), f.category)
                    + "<div class='umz-fine'>Click a district on the map, or type it above.</div>",
                    unsafe_allow_html=True)
    with right:
        here_t, rw_t = r["latest_yield_kg_ha"] / 1000, r["national_yield_kg_ha"] / 1000
        when = release_name(f.latest_release)
        if pd.isna(r["latest_ratio"]):
            big, sub = "No harvest figure published", f"The survey has no {crop_name(crop).lower()} figure here for {when}."
        elif not r["latest_reliable"]:
            # A number exists but rests on too few fields: say so before showing it.
            big = "Too few fields to be sure"
            sub = (f"The survey shows {pct(r['latest_ratio'])} of the national average ({here_t:.2f} vs {rw_t:.2f} tonnes "
                   f"per hectare), but this crop covered only {r['latest_harvested_ha']:,.0f} ha here in {when}, so the survey likely "
                   "measured very few plots of it.")
        else:
            big = f"{pct(r['latest_ratio'])} of the national average"
            sub = (f"Farmers here harvested {here_t:.2f} tonnes per hectare; the national average was "
                   f"{rw_t:.2f} ({when}).")
            if f.category == CATEGORY_INSUFFICIENT:
                sub += f" But {r['limited_reason']}, so the pattern is unclear."
        st.markdown(
            f"<div class='umz-card'><div class='umz-kicker'>{escape(district)} ({escape(r['province'])}) &middot; "
            f"{escape(crop_name(crop))} &middot; Season {season}</div>"
            f"<div class='umz-big'>{escape(big)}</div><div class='umz-sub'>{escape(sub)}</div>"
            f"<div style='margin:10px 0 2px 0'>{chip_html(f.category)}</div>"
            f"{district_target_svg(f, ss['gap'])}"
            f"<div class='umz-kicker' style='margin:4px 0 6px 0'>Last 3 surveys</div>{pattern_tiles_html(f)}</div>",
            unsafe_allow_html=True)
        st.write("")
        st.button(why_question(f.category), key="why_btn", icon=":material/help:", on_click=go, args=("why",),
                  width="stretch")
    t = target_position(records, crop)
    if t is not None:
        gap_t = t.target_t_ha - t.yield_t_ha
        st.markdown(
            f"<div class='umz-card' style='margin-top:18px'><div class='umz-kicker'>Rwanda as a whole: "
            f"{escape(crop_name(crop).lower())} harvest against the national goal</div>{target_arrow_svg(t)}"
            f"<div class='umz-fine'>Seasons A and B together, {escape(t.agricultural_year)}, so it differs from the "
            f"single-season figures above. {t.yield_t_ha:.2f} t/ha today against a goal of {t.target_t_ha:.2f} t/ha"
            f"{f' ({gap_t:.2f} t/ha to go)' if gap_t > 0 else ' (goal met)'}; the plan started from "
            f"{t.baseline_t_ha:.2f} t/ha. The goal is set for Rwanda only, not per district. Sources: MINAGRI PSTA 5 "
            "results framework p.21; NISR Seasonal Agricultural Survey.</div></div>", unsafe_allow_html=True)


def page_why() -> None:
    crop, district, season = selection_bar()
    f = data.finding(Selection(district, crop, season))
    e = explain(f)
    st.markdown(f"<div class='umz-kicker' style='margin-top:6px'>{escape(district)} &middot; "
                f"{escape(crop_name(crop).lower())} &middot; Season {season}</div>"
                f"<div class='umz-big'>{escape(why_question(f.category))}</div>"
                f"<div style='margin:6px 0 14px 0'>{chip_html(f.category)}</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.15, 1], gap="medium")
    c1.markdown(f"<div class='umz-card'><div class='umz-step'><span class='umz-step-n'>1</span>Is it a pattern?</div>"
                f"{pattern_tiles_html(f)}<div class='umz-line'><b>{escape(e.pattern_title)}.</b> "
                f"{escape(e.pattern_line)}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='umz-card' style='animation-delay:.12s'><div class='umz-step'><span class='umz-step-n'>2"
                f"</span>Enough seed and fertilizer?</div>{inputs_html(e, district)}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='umz-card' style='animation-delay:.24s'><div class='umz-step'><span class='umz-step-n'>3"
                f"</span>What it suggests</div>{verdict_html(e, f.category)}"
                "<div class='umz-fine'>The survey shows where harvests are low, not why. Treat this as a lead to "
                "check, not a proven cause.</div></div>", unsafe_allow_html=True)
    st.write("")
    a, b = st.columns([1, 1.15], gap="large")
    with a:
        st.markdown(action_card_html(e, f"{district} district team"), unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        d1.download_button("Download brief", build_brief(f, manifest).encode("utf-8"),
                           file_name=f"umuzi_brief_{district}_{crop}_season{season}.md", mime="text/markdown",
                           width="stretch")
        d2.download_button("Download figures (CSV)", brief_csv(f),
                           file_name=f"umuzi_{district}_{crop}_season{season}.csv", mime="text/csv",
                           width="stretch")
        with st.expander("The figures and their limits"):
            st.markdown("\n".join(f"- **{k}:** {v}" for k, v in f.figures)
                        + f"\n- **Surveys used:** {', '.join(release_name(x) for x in f.releases)} "
                          f"(NISR, snapshot {SID[-8:]})\n\n"
                        + "\n".join(f"- {x}" for x in f.limitations))
    with b:
        render_chat(height=360)


def page_ask() -> None:
    selection_bar()
    render_chat(height=520)


def page_evidence() -> None:
    crop, district, season = selection_bar()
    ev = data.evidence(crop, season)
    f = data.finding(Selection(district, crop, season))
    tab_grid, tab_hist, tab_inp, tab_all, tab_meth = st.tabs(
        ["Survey by survey", f"{district} over time", "Seed and fertilizer", "All districts table",
         "Data and methods"])
    with tab_grid:
        st.caption("Each cell is the district's harvest per hectare as a share of the national average in that survey. "
                   "The outlined block is the last 3 surveys, which decide the label.")
        st.plotly_chart(charts.pattern_grid(ev, data.panel, SID, crop, season, highlight=district),
                        width="stretch", config=PLOT_CONFIG)
    with tab_hist:
        st.plotly_chart(charts.district_history_chart(data.panel, district, crop, season, f.releases, SID),
                        width="stretch", config=PLOT_CONFIG)
        st.caption("District rankings from 2018 and 2019 agree only weakly with later years (see Data and methods), "
                   "so the label uses the last 3 surveys; the earlier years are shown for context.")
    with tab_inp:
        st.plotly_chart(charts.input_context_chart(ev, SID, crop, season, highlight=district),
                        width="stretch", config=PLOT_CONFIG)
        st.caption("Share of farmers in the district who used the input on any crop. NISR does not publish it per "
                   "crop for each district.")
    with tab_all:
        cols = {"district": "District", "province": "Province", "category": "Label",
                "latest_ratio": "Share of national average (latest)", "below_in_window": "Short in last 3 surveys",
                "reliable_in_window": "Surveys with enough fields (of 3)", "latest_harvested_ha": "Harvested ha (latest)",
                "improved_seed_pct": "Farmers using improved seed %", "inorganic_fert_pct": "Farmers using fertilizer %"}
        show = ev[list(cols)].rename(columns=cols)
        show["Label"] = show["Label"].map(PLAIN_CATEGORY)
        show["Share of national average (latest)"] = show["Share of national average (latest)"] * 100
        st.dataframe(show, hide_index=True, width="stretch", column_config={
            "Share of national average (latest)": st.column_config.NumberColumn(format="%.1f%%"),
            "Harvested ha (latest)": st.column_config.NumberColumn(format="%.0f"),
            "Farmers using improved seed %": st.column_config.NumberColumn(format="%.1f"),
            "Farmers using fertilizer %": st.column_config.NumberColumn(format="%.1f")})
        st.download_button("Download table (CSV)", ev.to_csv(index=False).encode("utf-8"),
                           file_name=f"umuzi_{crop}_season{season}_{SID}.csv", mime="text/csv")
    with tab_meth:
        methods()


BACKTEST_NAMES = {
    "last_1": "Short in the latest survey",
    "last_2_both": "Short in both of the last 2",
    "last_3_all": "Short in all of the last 3",
    "last_3_two": "Short in 2 of the last 3 (used by the app)",
    "all_history": "Short in every survey since 2018 (first version)",
    "model": "Statistical model (logistic regression)",
}


def methods() -> None:
    eda, bt = report("history_eda.json"), report("backtest_results.json")
    st.markdown(f"""
**How a district gets its label.** For the chosen crop and season, the district's harvest per hectare is divided
by the national average of the same survey. A survey counts as *short* when the district is under
{GAP_THRESHOLD:.0%} of the national average: NISR publishes no margin of error for district yields, so smaller gaps
cannot be told apart from survey noise. A survey counts only if a yield was published and the crop covered at
least {MIN_HARVESTED_HA:,.0f} ha in the district. *Repeated* means short in at least 2 of the last 3 surveys of
that season. Seed and fertilizer use are then compared with the national share: when both are lower, the label
points to inputs first. The full explanation is in `docs/methodology.md` in the repository.

**Why {MIN_HARVESTED_HA:,.0f} ha.** NISR does not measure every field. It samples 1,200 squares of land and
records the plot under each of 25 points in every square. Its Season B 2026 report (Table 5, p.17) shows that for
the five main seasonal crops the survey observes 21 to 42 plots per 1,000 ha, so 500 ha corresponds to about 10 to
21 plots. Below that, a district average may rest on only a few farmers' answers.""")

    st.markdown("**1. Which survey years can be used.** Every downloaded file was checked for yield tables by district.")
    if eda.get("source_audit"):
        st.dataframe(pd.DataFrame(eda["source_audit"]).sort_values(["year", "kind"]), hide_index=True, width="stretch")
    st.markdown("The 2015-2017 tables give yields only by land type or province, and for 2014 only a PDF report was "
                "found, so district analysis starts in 2018. "
                "Season B 2025 was not published. In 2018, seed and fertilizer use were counted per plot rather than "
                "per farmer, so those figures are not used.")

    st.markdown("**2. Checks every survey must pass** (run automatically before the data can be used).")
    status, missing = cached_status(SID)
    st.dataframe(status[["release", "gate", "yield_cells_observed", "yield_cells_not_reported", "warnings", "notes"]],
                 hide_index=True, width="stretch")
    if missing:
        st.caption("Missing between the first and last survey: " + ", ".join(missing))
    if eda.get("reprinted_national_check"):
        d = pd.DataFrame(eda["reprinted_national_check"])
        st.markdown(f"Duplicates and revisions: {len(d)} national production figures that later workbooks re-print "
                    f"for the previous year match the original survey (largest difference "
                    f"{d['diff_pct'].abs().max():.2f}%). The 2024 annual workbook matches the separate 2024 Season A and "
                    "B files cell for cell.")

    st.markdown("**3. Do districts keep their place over time?** How closely the order of districts in one survey "
                "matches the next survey of the same season (1 = same order, 0 = unrelated), middle value across "
                "six priority crops.")
    if eda.get("rank_agreement"):
        ra = [dict(season=s, surveys=k.replace("SAS-", "").replace("|", " to "), agreement=v)
              for s in "AB" for k, v in eda["rank_agreement"][s]["consecutive"].items()]
        st.dataframe(pd.DataFrame(ra), hide_index=True, width="stretch")
        early = [r["agreement"] for r in ra if r["season"] == "A" and r["surveys"][:4] in ("2018", "2019")]
        later = [r["agreement"] for r in ra if r["season"] == "A" and r["surveys"][:4] >= "2020"]
        st.markdown(f"In Season A the order agrees weakly from 2018 to 2020 ({', '.join(f'{v:.2f}' for v in early)}) "
                    f"and {min(later):.2f} to {max(later):.2f} since, so the label uses the three most recent surveys "
                    "rather than all history.")

    st.markdown("**4. Could a statistical model spot next season's shortfalls better than simple rules?**")
    if bt:
        rows = [dict(method=BACKTEST_NAMES.get(k, k), balanced_accuracy=v["balanced_accuracy"],
                     shortfalls_caught=v["recall"] * 100, flags_that_were_right=v["precision"] * 100)
                for k, v in bt["test"].items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
            "shortfalls_caught": st.column_config.NumberColumn(format="%.0f%%"),
            "flags_that_were_right": st.column_config.NumberColumn(format="%.0f%%")})
        ci = bt["model_vs_best_rule_test"]["balanced_accuracy_diff_ci"]
        st.markdown(
            f"Each method used only earlier surveys to say whether a district would be short in the next survey, for "
            f"{bt['n_units']['test']} district-crop cases in 2024-2026. Balanced accuracy weighs shortfalls caught and "
            f"false alarms equally (0.5 is guessing, 1.0 is perfect). The model was no more accurate than the best "
            f"rule (difference {ci[0]:+.3f} to {ci[1]:+.3f}, 95% range), so **the rules were kept**. "
            f"'Short in 2 of the last 3' was chosen for its meaning rather than its score: it tells a pattern from a "
            f"one-off and still catches {bt['test']['last_3_two']['recall']:.0%} of next-season shortfalls, against "
            f"{bt['test']['all_history']['recall']:.0%} for the first version of the rules. Every district short in "
            "the latest survey is still flagged, as a repeated shortfall or a one-season dip.")

    with st.expander("Try other cut-offs"):
        ss["w_gap"], ss["w_min_ha"] = ss["gap"], ss["min_ha"]
        st.slider("Count a survey as short when the district is under this share of the national average", 0.70, 0.98,
                  key="w_gap", step=0.01, on_change=sync, args=("gap",))
        st.select_slider("Count a survey only when the crop covers at least this area (ha)",
                         [100.0, 200.0, 500.0, 1000.0, 2000.0], key="w_min_ha", on_change=sync, args=("min_ha",))
        st.caption("Defaults: 90% and 500 ha. Changing them recolours the map and changes the assistant's answers.")


{"home": page_home, "explore": page_explore, "why": page_why, "ask": page_ask,
 "evidence": page_evidence}[view]()
