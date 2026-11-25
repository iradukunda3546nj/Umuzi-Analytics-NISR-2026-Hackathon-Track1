"""Exploratory data analysis of the full SAS history (2018-2026) behind the modelling decision.

Questions, in order:
 1. Which downloaded files (2014 onward) contain district x crop x season yields?
 2. Coverage: how many districts have a reliable yield per release and priority crop?
 3. Internal consistency and units: production = yield x area per release.
 4. Duplicates and revisions: do re-printed national values (the "National 2019 A"
    rows in the 2020-2022 workbooks, the 2024 annual workbook) match the release
    they repeat?
 5. Definition changes: national level shifts, input-use basis, crop columns.
 6. Comparability over time: do district rankings agree between releases?

Writes reports/history_eda.json (read by the app's Data and methods panel).
Run: python -m scripts.history_eda
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.analytics.indicators import crop_panel
from src.config import CROP_ALIASES, DATA_DIR, DISTRICTS, MIN_HARVESTED_HA, ROOT
from src.ingestion.sas_adapter import _clean, parse_workbook, read_tables
from src.services.snapshot_store import SnapshotStore

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean", "cooking_banana", "wheat"]
HISTORY_DIR = DATA_DIR / "incoming" / "nisr_sas_history"
OUT = ROOT / "reports" / "history_eda.json"
DISTRICT_NAMES = [d.lower() for d in DISTRICTS]


def _sheets(path: Path) -> list[tuple[str, list[list]]]:
    """(title text, rows) per sheet of a workbook; empty if the optional .xls reader is missing."""
    if path.suffix == ".xlsx":
        return [(t.title, [list(r) for r in t.rows]) for t in read_tables(path)]
    try:
        import xlrd
    except ImportError:
        return []
    wb = xlrd.open_workbook(str(path))
    out = []
    for sh in wb.sheets():
        rows = [sh.row_values(i) for i in range(sh.nrows)]
        # 2015 stacks many tables in one sheet: split at every "Table N" title.
        starts = [i for i, r in enumerate(rows)
                  if any(re.match(r"\s*table\s*\d", str(v), re.I) for v in r[:3])] or [0]
        for a, b in zip(starts, starts[1:] + [len(rows)]):
            out.append((" ".join(str(v) for v in rows[a][:3]), rows[a:b]))
    return out


def _yield_level(path: Path) -> str:
    """Judge by content, not title: a district table must list at least 20 district names.
    (The 2017 'Yield of main crops by district' table actually has province columns.)"""
    if path.suffix == ".pdf":
        return "report (narrative and tables; not parsed - its workbook is used where one exists)"
    sheets = _sheets(path)
    if not sheets:
        return "not read (xlrd not installed)"
    yield_tables = [(t, rows) for t, rows in sheets if re.search(r"yield", t, re.I)
                    and not re.search(r"large.scale|cip|site", t, re.I)]
    if not yield_tables:
        return "no yield table"
    for _t, rows in yield_tables:
        names = {_clean(v).lower() for r in rows for v in r}
        if len(names & set(DISTRICT_NAMES)) >= 20:
            return "district"
    return "stratum or province only"


def source_audit() -> list[dict]:
    rows = []
    if not HISTORY_DIR.exists():
        return rows
    for p in sorted(HISTORY_DIR.iterdir()):
        year = re.search(r"20\d\d", p.name)
        rows.append(dict(file=p.name, year=int(year.group()) if year else None, kind=p.suffix[1:],
                         yield_level=_yield_level(p)))
    return rows


def coverage(panel: pd.DataFrame, order: list[str]) -> dict:
    p = panel[panel["crop"].isin(PRIORITY)]
    ok = p["yield_kg_ha"].notna() & (p["harvested_ha"] >= MIN_HARVESTED_HA)
    t = p.assign(ok=ok).pivot_table(index="release_id", columns="crop", values="ok", aggfunc="sum")
    return t.reindex(order).fillna(0).astype(int).to_dict(orient="index")


def consistency(records: pd.DataFrame, order: list[str]) -> dict:
    w = records[records["crop"] != "all"].pivot_table(index=["release_id", "district", "crop"],
                                                      columns="metric", values="value")
    t = w.dropna(subset=["yield_kg_ha", "harvested_ha", "production_t"])
    ratio = t["production_t"] / (t["yield_kg_ha"] * t["harvested_ha"] / 1000)
    g = (ratio - 1).abs().le(0.02).groupby(level=0)
    return {r: dict(cells=int(g.size()[r]), share_within_2pct=round(float(g.mean()[r]), 3))
            for r in order if r in g.size()}


def national_levels(records: pd.DataFrame, order: list[str]) -> dict:
    nat = records[records["district"] == "National"]
    y = nat[(nat["metric"] == "yield_kg_ha") & nat["crop"].isin(PRIORITY)]
    y = y.pivot_table(index="release_id", columns="crop", values="value").reindex(order).round(0)
    i = nat[nat["crop"] == "all"].pivot_table(index="release_id", columns="metric", values="value").reindex(order)
    jumps = []
    for s in "AB":
        rels = [r for r in order if r.endswith(s)]
        for a, b in zip(rels, rels[1:]):
            for crop in y.columns:
                va, vb = y.loc[a, crop], y.loc[b, crop]
                if pd.notna(va) and pd.notna(vb) and abs(vb / va - 1) > 0.20:
                    jumps.append(dict(crop=crop, from_release=a, to_release=b, change=round(float(vb / va - 1), 3)))
    return dict(national_yield_kg_ha=json.loads(y.to_json(orient="index")),
                national_inputs_pct=json.loads(i.round(2).to_json(orient="index")),
                yield_shifts_over_20pct=jumps)


def rank_agreement(panel: pd.DataFrame, order: list[str]) -> dict:
    """Median Spearman rho of district yield ratios between every pair of same-season releases."""
    p = panel[panel["yield_kg_ha"].notna() & (panel["harvested_ha"] >= MIN_HARVESTED_HA)]
    wide = {c: p[p["crop"] == c].pivot_table(index="district", columns="release_id", values="yield_ratio")
            for c in ["maize", "bean", "irish_potato", "cassava", "paddy_rice", "soybean"]}
    out = {}
    for s in "AB":
        rels = [r for r in order if r.endswith(s)]
        m = {}
        for a in rels:
            for b in rels:
                if a >= b:
                    continue
                rh = [spearmanr(w[[a, b]].dropna()[a], w[[a, b]].dropna()[b]).statistic
                      for w in wide.values() if a in w and b in w and len(w[[a, b]].dropna()) >= 10]
                if rh:
                    m[f"{a}|{b}"] = round(float(np.median(rh)), 2)
        consecutive = {k: v for k, v in m.items() if rels.index(k.split("|")[1]) - rels.index(k.split("|")[0]) == 1}
        out[s] = dict(pairs=m, consecutive=consecutive)
    return out


def reprinted_national(records: pd.DataFrame) -> list[dict]:
    """Compare 'National <previous year> <season>' rows (printed in the 2020-2022 production
    tables for comparison) with the production published in that earlier release."""
    rows = []
    if not HISTORY_DIR.exists():
        return rows
    nat = records[(records["district"] == "National") & (records["metric"] == "production_t")]
    nat = nat.set_index(["release_id", "crop"])["value"]
    for p in sorted(HISTORY_DIR.glob("*.xlsx")):
        for t in read_tables(p):
            if not re.search(r"crop production by crop type", t.title, re.I) or t.season is None:
                continue
            header = next((r for r in t.rows[:8] if sum(_clean(c).lower() in CROP_ALIASES for c in r) >= 2), None)
            if header is None:
                continue
            cols = {j: CROP_ALIASES[_clean(c).lower()] for j, c in enumerate(header) if _clean(c).lower() in CROP_ALIASES}
            for r in t.rows:
                lab = next((_clean(v) for v in r if _clean(v)), "")
                m = re.match(r"national\s+(20\d\d)\s*([ab])$", lab.lower())
                if not m or (t.season_year and int(m.group(1)) == t.season_year):
                    continue
                rel = f"SAS-{m.group(1)}{m.group(2).upper()}"
                for j, crop in cols.items():
                    v = r[j] if j < len(r) else None
                    if crop in PRIORITY and isinstance(v, (int, float)) and v > 0 and (rel, crop) in nat.index:
                        rows.append(dict(workbook=p.name, release=rel, crop=crop, reprinted=round(float(v), 1),
                                         as_published=round(float(nat[(rel, crop)]), 1),
                                         diff_pct=round(float(v / nat[(rel, crop)] - 1) * 100, 2)))
    return rows


def annual_2024_duplicate(records: pd.DataFrame) -> dict:
    path = DATA_DIR / "raw" / "reference" / "SAS_2024_Annual_Tables.xlsx"
    if not path.exists():
        return {}
    out = {}
    for s in "AB":
        a = parse_workbook(path, f"SAS-2024{s}", 2024, s).records
        b = records[records["release_id"] == f"SAS-2024{s}"]
        m = a.merge(b, on=["district", "crop", "metric"], suffixes=("_annual", "_release"))
        both = m.dropna(subset=["value_annual", "value_release"])
        out[f"SAS-2024{s}"] = dict(cells_compared=len(both),
                                   identical=int(((both["value_annual"] - both["value_release"]).abs() < 1e-6).sum()))
    return out


def main() -> None:
    records, manifest = SnapshotStore().load()
    panel = crop_panel(records)
    order = sorted(records["release_id"].unique(), key=lambda r: (r[-1], r))
    reg = {r["release_id"]: r for r in manifest["releases"]}
    result = dict(
        snapshot_id=manifest["snapshot_id"],
        releases=order,
        missing_releases=["SAS-2025B (not published on the NISR site when downloaded)"],
        source_audit=source_audit(),
        input_basis={r: ("per farmer, all crops pooled" if reg[r].get("inputs_comparable", True)
                         else "per plot or unstated basis: not comparable, not used") for r in order},
        release_notes={r: reg[r].get("notes", "") for r in order if reg[r].get("notes")},
        coverage_reliable_districts=coverage(panel, order),
        production_consistency=consistency(records, order),
        reprinted_national_check=reprinted_national(records),
        annual_2024_vs_releases=annual_2024_duplicate(records),
        rank_agreement=rank_agreement(panel, order),
        **national_levels(records, order),
    )
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["source_audit", "reprinted_national_check",
                                             "annual_2024_vs_releases", "yield_shifts_over_20pct"]}, indent=1))
    for s in "AB":
        print(s, result["rank_agreement"][s]["consecutive"])


if __name__ == "__main__":
    main()
