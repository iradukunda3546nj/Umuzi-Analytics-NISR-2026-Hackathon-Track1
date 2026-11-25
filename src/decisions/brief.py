"""Planner Evidence Brief: a shareable, source-traceable summary for one district and crop.

Built from the same Finding as the map panel and the Umuzi Assistant, so the
three never disagree. It states the category, the figures, the survey releases,
the suggested check, field questions and the limits of the evidence.
"""
from __future__ import annotations

import io

from src.config import PRODUCT_NAME
from src.decisions.finding import Finding, crop_name, pct, release_name

LIMITS_ALWAYS = [
    "Persistence means a consistent position in repeated published estimates; NISR does not state whether "
    "the same sample segments are revisited across seasons, so this is not independent replication.",
]


def build_brief(f: Finding, manifest: dict) -> str:
    r = f.row
    history = "\n".join(
        f"| {release_name(c.replace('ratio_', ''))} | {pct(r[c])} |" for c in r.index if c.startswith("ratio_"))
    rel = [x for x in manifest["releases"] if x["release_id"] == f.latest_release]
    src = (rel[0].get("source_url") or rel[0].get("landing_page") or "see Data and methods") if rel else "see Data and methods"
    figures = "\n".join(f"- {k}: {v}" for k, v in f.figures)
    questions = "\n".join(f"- {q}" for q in f.field_checks)
    limits = "\n".join(f"- {x}" for x in f.limitations + LIMITS_ALWAYS)
    return f"""# {PRODUCT_NAME} - Evidence Brief

**{f.district} District ({r['province']}) | {crop_name(f.crop)} | Season {f.season}**
Data snapshot: `{manifest['snapshot_id']}` | Latest survey: {release_name(f.latest_release)}

## Finding
**{f.category}.** {f.headline}

## Figures
{figures}

| Survey | Yield as % of national |
|---|---|
{history}

## Suggested next step (a check, not a prescription)
{f.next_step}

## Questions to verify in the field
{questions}

## Limits of this evidence
{limits}

## Source
National Institute of Statistics of Rwanda, Seasonal Agricultural Survey district tables (CC BY 4.0).
Latest survey file: {src}
Comparison basis: same crop, same season type; district yield divided by the national yield of the same survey.
"""


def brief_csv(f: Finding) -> bytes:
    buf = io.StringIO()
    f.row.to_frame().T.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

