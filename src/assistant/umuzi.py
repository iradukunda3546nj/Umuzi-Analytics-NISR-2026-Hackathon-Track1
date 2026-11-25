"""Umuzi Assistant: answers practical questions from the validated NISR snapshot.

Design choice: the assistant is deterministic. It recognises the district, crop,
season and kind of question, then answers only through the same functions the
map uses (`evidence_table`, `build_finding`, `target_position`). It never
generates a number of its own, so for the same selection it cannot disagree
with the map, and every answer can be traced to survey releases. A language
model was not used: it would add an API key and running cost to a public app and
could phrase a figure differently from the map.

Each answer carries the evidence behind it and the limitation that changes how
it should be read (for example, that input uptake is pooled across crops).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from functools import lru_cache

import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_NOT_BELOW,
                                      CATEGORY_REPEATED_INPUTS_OK, CATEGORY_REPEATED_LOW_INPUT,
                                      REPEATED, Params, crop_panel, evidence_table)
from src.config import DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA
from src.decisions.finding import (CAUSE_NOTE, EARLY_YEARS_NOTE, POOLED_NOTE, YIELD_NOTE, Finding,
                                   build_finding, crop_name, pct, release_name, target_position)

# Longest phrases first so "sweet potato" wins over "potato".
CROP_WORDS = [
    ("cooking banana", "cooking_banana"), ("sweet potato", "sweet_potato"), ("irish potato", "irish_potato"),
    ("paddy rice", "paddy_rice"), ("climbing bean", "climbing_bean"), ("bush bean", "bush_bean"),
    ("soybean", "soybean"), ("soya", "soybean"), ("cassava", "cassava"), ("maize", "maize"), ("corn", "maize"),
    ("beans", "bean"), ("bean", "bean"), ("potato", "irish_potato"), ("rice", "paddy_rice"),
    ("banana", "cooking_banana"), ("wheat", "wheat"), ("sorghum", "sorghum"),
]
INTENTS = [
    ("help", r"\b(help|what can you|how do i use)\b"),
    ("method", r"\b(data|sources?|methodology|method|calculated?|how reliable|trust|backtest|model)\b"),
    ("target", r"\b(target|psta|nst2|goal)\b"),
    ("inputs", r"\b(fertili[sz]er|seed|input|npk|dap|urea|agro.?dealer|subsid|nkunganire)\b"),
    ("cause", r"\b(why|cause|reason|explain|because)\b"),
    ("list", r"\b(which districts|list|other districts|where else|worst|lowest|ranking|most affected)\b"),
    ("trend", r"\b(trend|over time|history|since 20\d\d|over the years|changed?|improv\w*|getting (better|worse))\b"),
    ("status", r"\b(below|stayed|how is|how are|doing|pattern|status|yield|benchmark|national)\b"),
]


@dataclass
class Selection:
    district: str
    crop: str
    season: str
    last_intent: str = "status"


@dataclass
class Answer:
    text: str
    evidence: list[str] = field(default_factory=list)
    keep_in_mind: list[str] = field(default_factory=list)
    selection: Selection | None = None


class UmuziData:
    """The snapshot plus cached derived tables, shared by the map and the assistant."""

    def __init__(self, records: pd.DataFrame, manifest: dict, params: Params = Params()):
        self.records, self.manifest, self.params = records, manifest, params
        self.panel = crop_panel(records)
        self._ev = lru_cache(maxsize=64)(self._evidence)

    def _evidence(self, crop: str, season: str) -> pd.DataFrame:
        return evidence_table(self.records, crop, season, self.params)

    def evidence(self, crop: str, season: str) -> pd.DataFrame:
        return self._ev(crop, season)

    def finding(self, sel: Selection) -> Finding:
        return build_finding(self.evidence(sel.crop, sel.season), self.panel, sel.district, self.params)

    def has_crop(self, crop: str, season: str) -> bool:
        p = self.panel
        return bool(((p["crop"] == crop) & (p["season"] == season) & p["yield_kg_ha"].notna()).any())


def parse(question: str, sel: Selection) -> tuple[Selection, str, list[str]]:
    """Return the updated selection, the intent and any districts named in the question."""
    q = question.lower()
    named = sorted((d for d in DISTRICTS if re.search(rf"\b{d.lower()}\b", q)), key=lambda d: q.find(d.lower()))
    crop = sel.crop
    for word, key in CROP_WORDS:
        if re.search(rf"\b{word}", q):
            crop = key
            break
    season = sel.season
    m = re.search(r"\bseason\s*([ab])\b|\b([ab])\s*season\b", q)
    if m:
        season = (m.group(1) or m.group(2)).upper()
    intent = next((name for name, pat in INTENTS if re.search(pat, q)), None)
    if len(named) >= 2:
        intent = "compare"
    # "What about Nyamagabe?" repeats the previous question for the new selection.
    if intent is None or (re.search(r"\bwhat about\b|\band (for|in)\b", q) and intent == "status"):
        intent = sel.last_intent if (named or crop != sel.crop or season != sel.season) else (intent or "help")
    new = replace(sel, district=named[0] if named else sel.district, crop=crop, season=season,
                  last_intent=intent if intent != "compare" else sel.last_intent)
    return new, intent, named


def _sources(data: UmuziData, f: Finding) -> str:
    return (f"NISR Seasonal Agricultural Survey, {', '.join(release_name(r) for r in f.releases)} "
            f"(snapshot {data.manifest['snapshot_id']})")


def _status(data: UmuziData, f: Finding) -> Answer:
    text = f"**{f.category}.** {f.headline}\n\n**What to check next:** {f.next_step}"
    ev = [f"{k}: {v}" for k, v in f.figures] + [f"Source: {_sources(data, f)}"]
    return Answer(text, ev, f.limitations)


def _inputs(data: UmuziData, f: Finding, question: str) -> Answer:
    r = f.row
    if not r["inputs_known"]:
        return Answer(f"Input uptake for {f.district} is not available on a comparable basis for "
                      f"{release_name(f.latest_release)}, so I cannot relate it to the yield pattern.",
                      [f"Source: {_sources(data, f)}"], [POOLED_NOTE])
    seed, nseed = r["improved_seed_pct"], r["national_improved_seed_pct"]
    fert, nfert = r["inorganic_fert_pct"], r["national_inorganic_fert_pct"]
    focus = "fertilizer" if re.search(r"fertili[sz]er|npk|dap|urea", question.lower()) else "seed and fertilizer"
    pos = lambda a, b: "below" if a < b else "at or above"
    lines = [f"In {release_name(f.latest_release)}, {fert:.1f}% of farmers in {f.district} used inorganic "
             f"fertilizer ({pos(fert, nfert)} the national {nfert:.1f}%) and {seed:.1f}% used improved seed "
             f"({pos(seed, nseed)} the national {nseed:.1f}%). These shares cover all crops, not "
             f"{crop_name(f.crop).lower()} alone."]
    if f.category == CATEGORY_REPEATED_LOW_INPUT:
        lines.append(f"Because {crop_name(f.crop).lower()} yield has repeatedly been below national here "
                     f"and both inputs are below national, {focus} access is the first thing to verify:")
    elif f.category == CATEGORY_REPEATED_INPUTS_OK:
        lines.append(f"{crop_name(f.crop)} yield has repeatedly been below national even though district input "
                     "uptake is not low, so first confirm the inputs reach this crop, then look beyond inputs:")
    elif f.category == CATEGORY_DIP:
        lines.append("The shortfall appears in the latest season only, so a one-season shock is as likely as an "
                     "access problem. Worth verifying:")
    elif f.category == CATEGORY_NOT_BELOW:
        lines.append(f"{crop_name(f.crop)} yield here is not below the national benchmark, so input access is not "
                     "flagged by the survey for this crop. If you still check, ask:")
    else:
        lines.append("The yield evidence is too limited to link to input use. Before acting, verify:")
    checks = "\n".join(f"- {q}" for q in f.field_checks)
    ev = [k + ": " + v for k, v in f.figures if "Farmers" in k or "Yield" in k] + [f"Source: {_sources(data, f)}"]
    return Answer("\n\n".join(lines) + "\n" + checks, ev, [POOLED_NOTE, CAUSE_NOTE])


def _cause(data: UmuziData, f: Finding) -> Answer:
    text = (f"The survey tables cannot show what caused {f.district}'s {crop_name(f.crop).lower()} result; "
            f"they record yields and input use, not soils, rainfall or practices. What the data do show: "
            f"{f.headline}\n\nA field check that follows from this pattern:\n"
            + "\n".join(f"- {q}" for q in f.field_checks))
    return Answer(text, [k + ": " + v for k, v in f.figures] + [f"Source: {_sources(data, f)}"],
                  [CAUSE_NOTE] + ([POOLED_NOTE] if f.row["inputs_known"] else []))


def _list(data: UmuziData, sel: Selection) -> Answer:
    ev = data.evidence(sel.crop, sel.season)
    rep = ev[ev["category"].isin(REPEATED)].sort_values("latest_ratio")
    latest = release_name(ev["latest_release"].iloc[0])
    if rep.empty:
        return Answer(f"No district is repeatedly below national for {crop_name(sel.crop).lower()} in Season "
                      f"{sel.season} (latest: {latest}).", [], [YIELD_NOTE])
    low = rep[rep["category"] == CATEGORY_REPEATED_LOW_INPUT]["district"].tolist()
    ok = rep[rep["category"] == CATEGORY_REPEATED_INPUTS_OK]["district"].tolist()
    text = (f"{len(rep)} districts were below the national {crop_name(sel.crop).lower()} benchmark in at least "
            f"2 of the last 3 Season {sel.season} surveys (latest: {latest}).\n\n"
            f"- With low seed and fertilizer uptake ({len(low)}): {', '.join(low) or 'none'}\n"
            f"- With input uptake not low ({len(ok)}): {', '.join(ok) or 'none'}")
    evid = [f"{r.district}: {pct(r.latest_ratio)} of national in {latest}" for r in rep.itertuples()]
    return Answer(text, evid, [YIELD_NOTE, POOLED_NOTE])


def _trend(data: UmuziData, f: Finding) -> Answer:
    h = data.panel[(data.panel["district"] == f.district) & (data.panel["crop"] == f.crop)
                   & (data.panel["season"] == f.season)].sort_values("season_year")
    rows = []
    for r in h.itertuples():
        if pd.isna(r.yield_ratio):
            rows.append(f"{release_name(r.release_id)}: not reported")
        else:
            thin = "" if r.harvested_ha >= MIN_HARVESTED_HA else " (thin coverage)"
            rows.append(f"{release_name(r.release_id)}: {r.yield_kg_ha / 1000:.2f} t/ha, "
                        f"{pct(r.yield_ratio)} of national{thin}")
    reliable = h[h["yield_ratio"].notna() & (h["harvested_ha"] >= MIN_HARVESTED_HA)]
    n_below = int((reliable["yield_ratio"] < GAP_THRESHOLD).sum())
    text = (f"Across all {len(h)} Season {f.season} surveys since {int(h['season_year'].min())}, "
            f"{f.district}'s {crop_name(f.crop).lower()} yield was below the national benchmark in {n_below} "
            f"of {len(reliable)} reliable ones. The current label uses the last three: {f.headline}")
    return Answer(text, rows, [EARLY_YEARS_NOTE, YIELD_NOTE])


def _target(data: UmuziData, f: Finding) -> Answer:
    t = target_position(data.records, f.crop)
    if t is None:
        return Answer(f"PSTA 5 sets no national yield target for {crop_name(f.crop).lower()}.", [], [])
    gap = t.target_t_ha - t.yield_t_ha
    text = (f"Nationally, {crop_name(f.crop).lower()} yielded {t.yield_t_ha:.2f} t/ha in {t.agricultural_year} "
            f"against a PSTA 5 target of {t.target_t_ha:.2f} t/ha: {t.attainment:.0%} of the target, "
            + (f"{gap:.2f} t/ha short." if gap > 0 else "target met.")
            + f" PSTA 5 aims for {t.final_target_t_ha:.2f} t/ha by 2028/29. Targets are national; PSTA 5 does "
              f"not set district targets, so {f.district} is compared with the national yield instead.")
    return Answer(text, [f"National Season A + B yield {t.agricultural_year}: {t.yield_t_ha:.2f} t/ha",
                         f"PSTA 5 target {t.agricultural_year}: {t.target_t_ha:.2f} t/ha (results framework p.21)"],
                  ["The national yield is computed as Season A + B production divided by A + B harvested area; "
                   "PSTA 5 does not state its exact aggregation."])


def _compare(data: UmuziData, sel: Selection, named: list[str]) -> Answer:
    parts, ev = [], []
    for d in named[:3]:
        f = data.finding(replace(sel, district=d))
        parts.append(f"- **{d}** ({f.category}): {f.headline}")
        ev += [f"{d}, {k}: {v}" for k, v in f.figures if k.startswith("Yield") or k == "Recent pattern"]
    return Answer("\n".join(parts), ev, [YIELD_NOTE])


def _method(data: UmuziData) -> Answer:
    rel = [r["release_id"] for r in data.manifest["releases"]]
    text = ("I use only NISR Seasonal Agricultural Survey district tables, checked before publication "
            "(30 districts present, national row present, production = yield x area). A district counts as "
            f"below national when its yield is under {GAP_THRESHOLD:.0%} of the national yield of the same "
            "season and survey. 'Repeatedly below' means below in at least 2 of the last 3 surveys of the same "
            "season type, counting only reliable estimates (yield reported, at least "
            f"{MIN_HARVESTED_HA:,.0f} ha harvested). A statistical model was tested against these rules on the "
            "2024-2026 surveys and did not flag shortfalls more accurately, so the rules were kept.")
    return Answer(text, [f"{len(rel)} survey releases: {rel[0]} to {rel[-1]} (2025 Season B not published)",
                         f"Snapshot {data.manifest['snapshot_id']}"], [YIELD_NOTE])


HELP = ("Ask me about the district, crop and season selected on the map, or name others. For example:\n"
        "- Has Ruhango's maize yield stayed below national in Season A?\n"
        "- What about Nyamagabe?\n"
        "- What should I verify about fertilizer access?\n"
        "- Which other districts are repeatedly below for beans?\n"
        "- How has it changed since 2018?\n"
        "- How far is Rwanda from the maize target?")


def answer(data: UmuziData, question: str, sel: Selection) -> Answer:
    new, intent, named = parse(question, sel)
    if not data.has_crop(new.crop, new.season):
        return Answer(f"NISR publishes no district {crop_name(new.crop).lower()} yields for Season {new.season} "
                      "in these surveys.", [], [], new)
    if intent == "help":
        a = Answer(HELP)
    elif intent == "method":
        a = _method(data)
    elif intent == "list":
        a = _list(data, new)
    elif intent == "compare":
        a = _compare(data, new, named)
    else:
        f = data.finding(new)
        a = {"inputs": lambda: _inputs(data, f, question), "cause": lambda: _cause(data, f),
             "trend": lambda: _trend(data, f), "target": lambda: _target(data, f)}.get(
            intent, lambda: _status(data, f))()
    a.selection = new
    return a

