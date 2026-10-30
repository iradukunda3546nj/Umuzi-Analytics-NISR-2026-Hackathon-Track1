"""Pre-specified analysis (docs/research_design.md) on the ACTIVE snapshot.

Writes:
  reports/analysis_results.json   all test statistics, counts and sensitivity grids
  reports/figures/*.html          the storytelling charts (same builders as the app)

Run:  python -m scripts.run_analysis
"""
from __future__ import annotations

import json
from itertools import product

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.analytics.indicators import (CATEGORY_ORDER, Params, crop_panel, evidence_table,
                                      input_panel, load_targets, national_vs_target)
from src.config import MIN_HARVESTED_HA, ROOT
from src.services.snapshot_store import SnapshotStore
from src.viz import charts

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean",
            "cooking_banana", "sweet_potato"]
RNG = np.random.default_rng(20261029)
OUT = ROOT / "reports"
FIG = OUT / "figures"


def holm(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj.tolist()


def perm_spearman(x, y, n_perm=5000) -> tuple[float, float]:
    rho = spearmanr(x, y).statistic
    # Spearman = Pearson on ranks; permute the y-ranks in one vectorised pass.
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rx = (rx - rx.mean()) / rx.std()
    perms = np.argsort(RNG.random((n_perm, len(ry))), axis=1)
    ryp = ry[perms]
    ryp = (ryp - ryp.mean(axis=1, keepdims=True)) / ryp.std(axis=1, keepdims=True)
    null = (ryp * rx).mean(axis=1)
    p = (np.sum(np.abs(null) >= abs(rho)) + 1) / (n_perm + 1)
    return float(rho), float(p)


def h1(panel: pd.DataFrame) -> list[dict]:
    out = []
    pairs = {"A": [("SAS-2024A", "SAS-2025A"), ("SAS-2025A", "SAS-2026A")], "B": [("SAS-2024B", "SAS-2026B")]}
    for crop in PRIORITY:
        c = panel[(panel["crop"] == crop) & (panel["harvested_ha"] >= MIN_HARVESTED_HA)
                  & panel["yield_ratio"].notna()]
        w = c.pivot_table(index="district", columns="release_id", values="yield_ratio")
        for season, plist in pairs.items():
            for a, b in plist:
                if a not in w or b not in w:
                    continue
                d = w[[a, b]].dropna()
                rec = dict(crop=crop, season=season, release_a=a, release_b=b, n=len(d))
                if len(d) < 12:
                    rec.update(rho=None, p=None, status="not tested (n<12)")
                else:
                    rho, p = perm_spearman(d[a].values, d[b].values)
                    rec.update(rho=round(rho, 3), p=p, status="tested")
                out.append(rec)
    tested = [r for r in out if r["status"] == "tested"]
    for r, adj in zip(tested, holm([r["p"] for r in tested])):
        r["p_holm"] = adj
    return out


def h2(panel: pd.DataFrame, threshold: float = 0.9, n_perm: int = 2000) -> dict:
    rels = ["SAS-2024A", "SAS-2025A", "SAS-2026A"]
    per_crop, mats = {}, []
    for crop in PRIORITY:
        c = panel[(panel["crop"] == crop) & (panel["harvested_ha"] >= MIN_HARVESTED_HA)]
        w = c.pivot_table(index="district", columns="release_id", values="yield_ratio")
        if not set(rels) <= set(w.columns):
            continue
        w = w[rels].dropna()
        below = (w < threshold).values
        obs = int(below.all(axis=1).sum())
        per_crop[crop] = dict(n_districts=len(w), observed_persistent=obs,
                              expected_if_independent=round(float(np.prod(below.mean(axis=0)) * len(w)), 2))
        mats.append(below)
    observed = sum(v["observed_persistent"] for v in per_crop.values())
    null = np.empty(n_perm)
    for k in range(n_perm):
        tot = 0
        for b in mats:
            shuffled = np.column_stack([RNG.permutation(b[:, j]) for j in range(b.shape[1])])
            tot += shuffled.all(axis=1).sum()
        null[k] = tot
    p = (np.sum(null >= observed) + 1) / (n_perm + 1)
    return dict(per_crop=per_crop, observed_total=observed, null_mean=round(float(null.mean()), 2),
                null_95th=float(np.percentile(null, 95)), p_one_sided=float(p), n_perm=n_perm)


def h3(records: pd.DataFrame, panel: pd.DataFrame) -> list[dict]:
    inp = input_panel(records)
    out = []
    for crop in ["maize", "bean"]:
        c = panel[(panel["crop"] == crop) & (panel["harvested_ha"] >= MIN_HARVESTED_HA)]
        for rel in sorted(c["release_id"].unique()):
            d = c[c["release_id"] == rel].merge(inp[inp["release_id"] == rel], on=["release_id", "district"])
            for var in ["improved_seed_farmers_pct", "inorganic_fert_farmers_pct"]:
                dd = d[["yield_ratio", var]].dropna()
                rho, p = perm_spearman(dd[var].values, dd["yield_ratio"].values)
                out.append(dict(crop=crop, release=rel, input=var, n=len(dd), rho=round(rho, 3), p=p))
    for r, adj in zip(out, holm([r["p"] for r in out])):
        r["p_holm"] = adj
    return out


def sensitivity(records: pd.DataFrame) -> list[dict]:
    rows = []
    for crop, season in [("maize", "A"), ("bean", "A"), ("irish_potato", "A"), ("maize", "B")]:
        base = evidence_table(records, crop, season).set_index("district")["category"]
        for gap, ha in product([0.80, 0.90, 0.95], [200.0, 500.0, 1000.0]):
            ev = evidence_table(records, crop, season, Params(gap_threshold=gap, min_harvested_ha=ha))
            cat = ev.set_index("district")["category"]
            counts = cat.value_counts().reindex(CATEGORY_ORDER, fill_value=0).to_dict()
            rows.append(dict(crop=crop, season=season, gap_threshold=gap, min_harvested_ha=ha,
                             agreement_with_default=round(float((cat == base.reindex(cat.index)).mean()), 3),
                             **{k: int(v) for k, v in counts.items()}))
    return rows


def main() -> None:
    store = SnapshotStore()
    records, manifest = store.load()
    sid = manifest["snapshot_id"]
    panel = crop_panel(records)
    FIG.mkdir(parents=True, exist_ok=True)

    nvt = national_vs_target(records, load_targets())
    results = dict(snapshot_id=sid, releases=[r["release_id"] for r in manifest["releases"]],
                   national_vs_target=nvt.round(4).to_dict(orient="records"))
    results["H1_rank_persistence"] = h1(panel)
    results["H2_persistence_vs_chance"] = h2(panel)
    results["H3_input_association"] = h3(records, panel)
    results["sensitivity"] = sensitivity(records)

    cats = {}
    for season in ["A", "B"]:
        wide = {}
        for crop in PRIORITY:
            ev = evidence_table(records, crop, season)
            wide[crop] = ev.set_index("district")["category"]
            cats[f"{crop}_{season}"] = ev["category"].value_counts().to_dict()
        cat_wide = pd.DataFrame(wide)
        results[f"districts_persistent_3plus_crops_{season}"] = sorted(
            cat_wide.index[(cat_wide.apply(lambda c: c.str.startswith("Persistent")).sum(axis=1) >= 3)].tolist())
        charts.triage_matrix(cat_wide, sid, season).write_html(FIG / f"triage_matrix_season_{season}.html",
                                                               include_plotlyjs="cdn")
    results["category_counts"] = cats

    charts.target_attainment_chart(nvt, sid).write_html(FIG / "national_target_attainment.html",
                                                        include_plotlyjs="cdn")
    for crop, season in [("maize", "A"), ("bean", "A"), ("irish_potato", "A")]:
        ev = evidence_table(records, crop, season)
        charts.persistence_chart(ev, sid, crop, season).write_html(
            FIG / f"persistence_{crop}_{season}.html", include_plotlyjs="cdn")
        charts.category_map(ev, sid, crop, season).write_html(
            FIG / f"map_{crop}_{season}.html", include_plotlyjs="cdn")
        charts.input_context_chart(ev, sid, crop, season).write_html(
            FIG / f"inputs_{crop}_{season}.html", include_plotlyjs="cdn")

    (OUT / "analysis_results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: results[k] for k in ["H2_persistence_vs_chance"]}, indent=1))
    print("H1:")
    for r in results["H1_rank_persistence"]:
        print(" ", r)
    print("H3:")
    for r in results["H3_input_association"]:
        print(" ", r)
    print("persistent in 3+ crops:", results["districts_persistent_3plus_crops_A"],
          results["districts_persistent_3plus_crops_B"])
    print("sensitivity:")
    for r in results["sensitivity"]:
        print(" ", r)


if __name__ == "__main__":
    main()
