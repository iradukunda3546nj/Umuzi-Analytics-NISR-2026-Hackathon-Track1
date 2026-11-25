"""Umuzi Assistant: answers practical questions from the validated NISR snapshot.

Design choice: the assistant is deterministic. It recognises the district
(tolerating misspellings), crop, season and kind of question, then answers only
through the functions the pages use (`evidence_table`, `build_finding`,
`explain`, `target_position`). It never generates a number of its own, so for
the same selection it cannot disagree with the map or the Why page, and every
answer can be traced to survey releases. A language model was not used: it
would add an API key and running cost to a public app and could phrase a
figure differently from the map.

What it adds beyond the pages: it answers across districts and crops in one
place (compare, list, best, trend since 2018), keeps the conversation's focus
("what about Nyamagabe?"), and offers the next useful question as a button.
When it does not understand, it says so in one line and offers questions it can
answer, instead of guessing.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field, replace
from functools import lru_cache

import pandas as pd

from src.analytics.indicators import (CATEGORY_DIP, CATEGORY_NOT_BELOW,
                                      CATEGORY_REPEATED_INPUTS_OK, CATEGORY_REPEATED_LOW_INPUT,
                                      REPEATED, Params, crop_panel, evidence_table)
from src.config import DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA
from src.decisions.explain import PLAIN_CATEGORY, InputSignal, explain
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
    ("greet", r"^\s*(hi|hello|hey|muraho|mwiriwe|mwaramutse|good (morning|afternoon|evening))\b[\s!.,]*$"),
    ("thanks", r"\b(thanks?|thank you|murakoze)\b"),
    ("help", r"\b(help|what can you|how do i use)\b"),
    ("method", r"\b(data|sources?|methodology|method|calculated?|how reliable|trust|backtest|model)\b"),
    ("target", r"\b(target|psta|nst2|goal)\b"),
    ("inputs", r"\b(fertili[sz]er|seeds?|inputs?|npk|dap|urea|agro.?dealer|subsid\w*|nkunganire)\b"),
    ("action", r"\b(what (should|can|do) (we|i)|recommend\w*|next steps?|to do|actions?|check first|"
               r"what to check|advi[cs]e|verify)\b"),
    ("cause", r"\b(why|cause|reason|explain|because)\b"),
    ("best", r"\b(best|highest|top|leading|doing well)\b"),
    ("list", r"\b(which districts|list|other districts|where else|worst|lowest|ranking|most affected)\b"),
    ("trend", r"\b(trend|over time|history|since 20\d\d|over the years|changed?|improv\w*|getting (better|worse))\b"),
    ("status", r"\b(below|stayed|how is|how are|doing|pattern|status|yields?|benchmark|national|shortfall|"
               r"perform\w*)\b"),
]
# A generic "how is ... doing" only counts as a status question when it is about
# something the survey covers; "how is the weather?" is not.
_DOMAIN = re.compile(r"\b(yields?|harvest\w*|production|below|benchmark|national|shortfall|crops?|"
                     r"it|this|there|here|they|district)\b")
_STOP = {"what", "about", "which", "where", "there", "their", "these", "those", "should", "would", "could",
         "season", "yield", "yields", "maize", "beans", "district", "districts", "rwanda", "national",
         "fertilizer", "fertiliser", "seeds", "inputs", "check", "below", "doing", "compare", "since"}
_DISTRICT_LOWER = {d.lower(): d for d in DISTRICTS}


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
    suggestions: list[str] = field(default_factory=list)


class UmuziData:
    """The snapshot plus cached derived tables, shared by the pages and the assistant."""

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


def find_districts(q: str) -> tuple[list[str], dict[str, str]]:
    """Districts named in the question, in order of mention, and any spelling corrections made."""
    hits: list[tuple[int, str]] = []
    corrected: dict[str, str] = {}
    for m in re.finditer(r"[a-z]+", q):
        w = m.group()
        if w in _DISTRICT_LOWER:
            hits.append((m.start(), _DISTRICT_LOWER[w]))
        elif len(w) >= 5 and w not in _STOP:
            close = difflib.get_close_matches(w, _DISTRICT_LOWER, n=1, cutoff=0.8)
            if close:
                hits.append((m.start(), _DISTRICT_LOWER[close[0]]))
                corrected[w] = _DISTRICT_LOWER[close[0]]
    out: list[str] = []
    for _, d in sorted(hits):
        if d not in out:
            out.append(d)
    return out, corrected


def parse(question: str, sel: Selection) -> tuple[Selection, str, list[str]]:
    """Return the updated selection, the intent and any districts named in the question."""
    q = question.lower().replace("'s", "")
    named, _ = find_districts(q)
    crop = sel.crop
    for word, key in CROP_WORDS:
        if re.search(rf"\b{word}", q):
            crop = key
            break
    season = sel.season
    m = re.search(r"\bseason\s*([ab])\b|\b([ab])\s*season\b", q)
    if m:
        season = (m.group(1) or m.group(2)).upper()
    changed = bool(named) or crop != sel.crop or season != sel.season
    intent = next((name for name, pat in INTENTS if re.search(pat, q)), None)
    if intent == "status" and not changed and not _DOMAIN.search(q):
        intent = None
    if len(named) >= 2:
        intent = "compare"
    # "What about Nyamagabe?" repeats the previous question for the new selection.
    if intent is None or (re.search(r"\bwhat about\b|\band (for|in)\b", q) and intent == "status"):
        intent = sel.last_intent if changed else (intent or "unknown")
    keep = intent in ("compare", "unknown", "greet", "thanks", "help")
    new = replace(sel, district=named[0] if named else sel.district, crop=crop, season=season,
                  last_intent=sel.last_intent if keep else intent)
    return new, intent, named


def suggestions_for(sel: Selection) -> list[str]:
    c = crop_name(sel.crop).lower()
    return [f"How is {sel.district} doing for {c}?", "Why?", "What should we check?",
            f"Which districts are repeatedly below for {c}?"]


def _sources(data: UmuziData, f: Finding) -> str:
    return (f"NISR Seasonal Agricultural Survey, {', '.join(release_name(r) for r in f.releases)} "
            f"(snapshot {data.manifest['snapshot_id']})")


def _status(data: UmuziData, f: Finding) -> Answer:
    text = f"**{PLAIN_CATEGORY[f.category]}.** {f.headline}"
    ev = [f"{k}: {v}" for k, v in f.figures] + [f"Source: {_sources(data, f)}"]
    nxt = ["Why?", "What should we check?", "How has it changed since 2018?"]
    if f.category == CATEGORY_NOT_BELOW:
        nxt = [f"Which districts are repeatedly below for {crop_name(f.crop).lower()}?",
               "How has it changed since 2018?"]
    return Answer(text, ev, f.limitations, suggestions=nxt)


def _signal_text(s: InputSignal) -> str:
    if s.lower is None:
        return "not published per farmer for this survey"
    return f"{s.district_pct:.0f}% of farmers here vs {s.national_pct:.0f}% in Rwanda ({s.word[0].lower() + s.word[1:]})"


def _cause(data: UmuziData, f: Finding) -> Answer:
    e = explain(f)
    text = (f"**{e.verdict_title}.** {e.verdict_line}\n\n"
            f"- Pattern: {e.pattern_line}\n"
            f"- Improved seed: {_signal_text(e.seed)}\n"
            f"- Fertilizer: {_signal_text(e.fertilizer)}\n\n"
            "The survey shows where yields are low, not why, so treat this as a lead for a field check.")
    return Answer(text, [k + ": " + v for k, v in f.figures] + [f"Source: {_sources(data, f)}"],
                  [CAUSE_NOTE] + ([POOLED_NOTE] if f.row["inputs_known"] else []),
                  suggestions=["What should we check?", "How has it changed since 2018?"])


def _action(data: UmuziData, f: Finding) -> Answer:
    e = explain(f)
    text = (f"**Check first in {f.district}** ({crop_name(f.crop).lower()}, Season {f.season}, "
            f"{e.category_label.lower()}):\n" + "\n".join(f"- {t}" for _, t in e.checks))
    return Answer(text, [f"Rule: {f.next_step}", f"Source: {_sources(data, f)}"], [CAUSE_NOTE],
                  suggestions=["Why?", "What about seed and fertilizer?"])


def _inputs(data: UmuziData, f: Finding, question: str) -> Answer:
    r = f.row
    if not r["inputs_known"]:
        return Answer(f"Seed and fertilizer use for {f.district} is not published on a comparable basis for "
                      f"{release_name(f.latest_release)}, so I cannot relate it to the yield pattern.",
                      [f"Source: {_sources(data, f)}"], [POOLED_NOTE])
    seed, nseed = r["improved_seed_pct"], r["national_improved_seed_pct"]
    fert, nfert = r["inorganic_fert_pct"], r["national_inorganic_fert_pct"]
    focus = "fertilizer" if re.search(r"fertili[sz]er|npk|dap|urea", question.lower()) else "seed and fertilizer"
    pos = lambda a, b: "fewer than" if a < b else "at least as many as"
    lines = [f"In {release_name(f.latest_release)}, {fert:.1f}% of farmers in {f.district} used inorganic "
             f"fertilizer ({pos(fert, nfert)} across Rwanda, {nfert:.1f}%) and {seed:.1f}% used improved seed "
             f"({pos(seed, nseed)} across Rwanda, {nseed:.1f}%). These shares cover all crops, not "
             f"{crop_name(f.crop).lower()} alone."]
    if f.category == CATEGORY_REPEATED_LOW_INPUT:
        lines.append(f"With a repeated {crop_name(f.crop).lower()} shortfall and both inputs low, "
                     f"{focus} access is the first thing to verify:")
    elif f.category == CATEGORY_REPEATED_INPUTS_OK:
        lines.append("The shortfall repeats although input use is not low on both counts, so first confirm "
                     "the inputs reach this crop, then look beyond inputs:")
    elif f.category == CATEGORY_DIP:
        lines.append("The shortfall is in the latest season only, so a one-season shock is as likely as an "
                     "access problem. Worth verifying:")
    elif f.category == CATEGORY_NOT_BELOW:
        lines.append(f"{crop_name(f.crop)} yield here is not below the benchmark, so the survey does not flag "
                     "input access for this crop. If you still check, ask:")
    else:
        lines.append("The yield evidence is too limited to link to input use. Before acting, verify:")
    checks = "\n".join(f"- {q}" for q in f.field_checks)
    ev = [k + ": " + v for k, v in f.figures if "Farmers" in k or "Yield" in k] + [f"Source: {_sources(data, f)}"]
    return Answer("\n\n".join(lines) + "\n" + checks, ev, [POOLED_NOTE, CAUSE_NOTE],
                  suggestions=["Why?", "Which districts are repeatedly below?"])


def _list(data: UmuziData, sel: Selection) -> Answer:
    ev = data.evidence(sel.crop, sel.season)
    rep = ev[ev["category"].isin(REPEATED)].sort_values("latest_ratio")
    latest = release_name(ev["latest_release"].iloc[0])
    if rep.empty:
        return Answer(f"No district is repeatedly below Rwanda's {crop_name(sel.crop).lower()} yield in Season "
                      f"{sel.season} (latest: {latest}).", [], [YIELD_NOTE])
    low = rep[rep["category"] == CATEGORY_REPEATED_LOW_INPUT]["district"].tolist()
    ok = rep[rep["category"] == CATEGORY_REPEATED_INPUTS_OK]["district"].tolist()
    text = (f"{len(rep)} districts were below 90% of Rwanda's {crop_name(sel.crop).lower()} yield in at least "
            f"2 of the last 3 Season {sel.season} surveys (latest: {latest}).\n\n"
            f"- Seed and fertilizer use both low ({len(low)}): {', '.join(low) or 'none'}\n"
            f"- Seed and fertilizer use not both low ({len(ok)}): {', '.join(ok) or 'none'}")
    evid = [f"{r.district}: {pct(r.latest_ratio)} of national in {latest}" for r in rep.itertuples()]
    first = rep["district"].iloc[0]
    return Answer(text, evid, [YIELD_NOTE, POOLED_NOTE],
                  suggestions=[f"Why is {first} below?", f"Which districts do best for {crop_name(sel.crop).lower()}?"])


def _best(data: UmuziData, sel: Selection) -> Answer:
    ev = data.evidence(sel.crop, sel.season)
    ok = ev[ev["latest_reliable"].astype(bool)].sort_values("latest_ratio", ascending=False).head(5)
    latest = release_name(ev["latest_release"].iloc[0])
    lines = [f"- {r.district}: {pct(r.latest_ratio)} of the Rwanda average ({r.latest_yield_kg_ha / 1000:.2f} t/ha)"
             for r in ok.itertuples()]
    text = (f"Highest {crop_name(sel.crop).lower()} yields relative to Rwanda in {latest} "
            f"(reliable estimates only):\n" + "\n".join(lines))
    return Answer(text, [f"Source: NISR SAS {latest}, snapshot {data.manifest['snapshot_id']}"], [YIELD_NOTE],
                  suggestions=[f"Which districts are repeatedly below for {crop_name(sel.crop).lower()}?"])


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
    return Answer(text, rows, [EARLY_YEARS_NOTE, YIELD_NOTE], suggestions=["Why?", "What should we check?"])


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
        parts.append(f"- **{d}** ({PLAIN_CATEGORY[f.category].lower()}): {pct(f.row['latest_ratio'])} of "
                     f"the Rwanda average in {release_name(f.latest_release)}")
        ev += [f"{d}, {k}: {v}" for k, v in f.figures if k.startswith("Yield") or k == "Recent pattern"]
    return Answer("\n".join(parts), ev, [YIELD_NOTE], suggestions=[f"Why is {named[0]} below?"])


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


HELP = ("I answer from NISR survey tables: crop yields for Rwanda's 30 districts, seed and fertilizer use, "
        "and what to check next. I follow the district you picked; name another district, crop or season to "
        "switch.")
UNKNOWN = ("Sorry, I didn't catch that. I can answer questions about crop yields, seed and fertilizer use, "
           "and what to check, for any of Rwanda's 30 districts. Try one of these:")


def answer(data: UmuziData, question: str, sel: Selection) -> Answer:
    new, intent, named = parse(question, sel)
    _, corrected = find_districts(question.lower())
    if intent in ("unknown", "greet", "thanks", "help"):
        text = {"unknown": UNKNOWN, "help": HELP,
                "greet": "Muraho! " + HELP,
                "thanks": "Murakoze. Ask me anything else about a district, crop or season."}[intent]
        return Answer(text, selection=new, suggestions=suggestions_for(new))
    if not data.has_crop(new.crop, new.season):
        return Answer(f"NISR publishes no district {crop_name(new.crop).lower()} yields for Season {new.season} "
                      "in these surveys.", [], [], new, suggestions=suggestions_for(replace(new, crop=sel.crop)))
    if intent == "method":
        a = _method(data)
    elif intent == "list":
        a = _list(data, new)
    elif intent == "best":
        a = _best(data, new)
    elif intent == "compare":
        a = _compare(data, new, named)
    else:
        f = data.finding(new)
        a = {"inputs": lambda: _inputs(data, f, question), "cause": lambda: _cause(data, f),
             "action": lambda: _action(data, f), "trend": lambda: _trend(data, f),
             "target": lambda: _target(data, f)}.get(intent, lambda: _status(data, f))()
    if corrected:
        a.text = "(" + "; ".join(f"I read '{w}' as {d}" for w, d in corrected.items()) + ")\n\n" + a.text
    a.selection = new
    return a
