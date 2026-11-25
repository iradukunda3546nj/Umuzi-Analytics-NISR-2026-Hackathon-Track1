"""Does a statistical model beat the rules at anticipating next season's shortfall?

Design (fixed before the results were seen):

Task. For each district, crop and season type, predict whether the district's
yield will be "below national" (ratio < 0.90, as in the app) in the next release
of the same season type. Only reliable observations count (yield reported and
harvested area >= 500 ha). A prediction may use only releases published before
the target release.

Units. District x priority crop x target release, where the target is reliable
and at least 2 of the 3 previous releases of that season type are reliable (the
same evidence minimum the app applies), so every rule below is defined.

Rule baselines (no fitting beyond counting), over the previous 3 releases:
  last_1        behind in the most recent reliable one
  last_2_both   behind in the 2 most recent reliable ones
  last_3_all    behind in every reliable one of the 3
  last_3_two    behind in at least 2 of the 3
  all_history   behind in every earlier reliable release since 2018 (rule set 1.0)
Model: L2-regularised logistic regression on the most recent ratio, the mean
ratio and the share behind over the 3 previous releases, the number of reliable
ones, log harvested area, and the district's pooled improved-seed and
inorganic-fertilizer gaps to national at the last release (0 + a missing flag
where not comparable, i.e. 2018). Refit for every target release on all units
whose target is earlier (expanding window).

Probabilities. A rule's probability is the share of training units in the same
rule state that turned out behind, so rules and model are compared on Brier
score as well as on balanced accuracy.

Periods. Selection: targets 2021-2023 (A and B). Held-out test: 2024A, 2025A,
2026A, 2024B, 2026B, the releases the app reports on.

Adoption criterion. Replace the rules with the model only if, on the test
period, the model's Brier score is lower than the best rule's with a 95%
district-cluster bootstrap interval that excludes zero AND balanced accuracy
improves by at least 0.02. Otherwise keep the rules.

Writes reports/backtest_results.json.   Run: python -m scripts.backtest
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.analytics.indicators import crop_panel, input_panel
from src.config import GAP_THRESHOLD, MIN_HARVESTED_HA, ROOT
from src.services.snapshot_store import SnapshotStore

PRIORITY = ["maize", "bean", "irish_potato", "paddy_rice", "cassava", "soybean", "cooking_banana", "wheat"]
SELECTION = {2021, 2022, 2023}
TEST = ["SAS-2024A", "SAS-2025A", "SAS-2026A", "SAS-2024B", "SAS-2026B"]
RULES = ["last_1", "last_2_both", "last_3_all", "last_3_two", "all_history"]
FEATURES = ["last_ratio", "mean3_ratio", "share3_below", "n_prior", "log_area", "seed_gap", "fert_gap", "inputs_missing"]
RNG = np.random.default_rng(20261125)
OUT = ROOT / "reports" / "backtest_results.json"


def build_units(records: pd.DataFrame) -> pd.DataFrame:
    p = crop_panel(records)
    p = p[p["crop"].isin(PRIORITY)]
    reliable = p["yield_kg_ha"].notna() & (p["harvested_ha"] >= MIN_HARVESTED_HA)
    # Unreliable observations stay in the series as gaps, so windows count releases.
    p = p.assign(ratio=p["yield_ratio"].where(reliable))
    releases = {s: sorted(p.loc[p["season"] == s, "release_id"].unique(),
                          key=lambda r: int(r[4:8])) for s in ("A", "B")}
    inp = input_panel(records)
    inp = inp.assign(seed_gap=inp["improved_seed_farmers_pct"] - inp["national_improved_seed_farmers_pct"],
                     fert_gap=inp["inorganic_fert_farmers_pct"] - inp["national_inorganic_fert_farmers_pct"])
    inp = inp.set_index(["release_id", "district"])[["seed_gap", "fert_gap"]]
    rows = []
    for (district, crop, season), g in p.groupby(["district", "crop", "season"]):
        s = g.set_index("release_id").reindex(releases[season])
        for i in range(3, len(s)):
            if pd.isna(s["ratio"].iloc[i]):
                continue
            hist = s["ratio"].iloc[:i].dropna()
            win = s.iloc[i - 3:i].dropna(subset=["ratio"])
            if len(win) < 2:
                continue
            below = win["ratio"] < GAP_THRESHOLD
            last_rel = win.index[-1]
            gaps = inp.loc[(last_rel, district)] if (last_rel, district) in inp.index else None
            missing = gaps is None or gaps.isna().any()
            rows.append(dict(
                district=district, crop=crop, season=season, target_release=s.index[i],
                target_year=int(s["season_year"].iloc[i]), y=bool(s["ratio"].iloc[i] < GAP_THRESHOLD),
                last_1=bool(below.iloc[-1]), last_2_both=bool(below.iloc[-2:].all()),
                last_3_all=bool(below.all()), last_3_two=int(below.sum()) >= 2,
                all_history=bool((hist < GAP_THRESHOLD).all()),
                last_ratio=float(win["ratio"].iloc[-1]), mean3_ratio=float(win["ratio"].mean()),
                share3_below=float(below.mean()), n_prior=len(win),
                log_area=float(np.log(win["harvested_ha"].iloc[-1])),
                seed_gap=0.0 if missing else float(gaps["seed_gap"]),
                fert_gap=0.0 if missing else float(gaps["fert_gap"]),
                inputs_missing=float(missing)))
    return pd.DataFrame(rows)


def fit_logistic(X: np.ndarray, y: np.ndarray, lam: float = 1.0, iters: int = 50) -> np.ndarray:
    """Newton-Raphson for L2-penalised logistic regression (intercept unpenalised)."""
    Xb = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(Xb.shape[1])
    pen = np.full(Xb.shape[1], lam)
    pen[0] = 0.0
    for _ in range(iters):
        pr = 1 / (1 + np.exp(-Xb @ w))
        grad = Xb.T @ (pr - y) + pen * w
        H = (Xb * (pr * (1 - pr))[:, None]).T @ Xb + np.diag(pen)
        step = np.linalg.solve(H, grad)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def predict(units: pd.DataFrame) -> pd.DataFrame:
    """Out-of-sample probabilities for every unit whose target has earlier training units."""
    out = []
    for rel in sorted(units["target_release"].unique()):
        test = units[units["target_release"] == rel]
        year = test["target_year"].iloc[0]
        train = units[units["target_year"] < year]
        if len(train) < 100:
            continue
        res = test.copy()
        for r in RULES:
            freq = train.groupby(r)["y"].mean()
            res[f"p_{r}"] = test[r].map(freq).fillna(train["y"].mean()).to_numpy()
        mu, sd = train[FEATURES].mean(), train[FEATURES].std().replace(0, 1)
        w = fit_logistic(((train[FEATURES] - mu) / sd).to_numpy(), train["y"].to_numpy(float))
        Xt = np.column_stack([np.ones(len(test)), ((test[FEATURES] - mu) / sd).to_numpy()])
        res["p_model"] = 1 / (1 + np.exp(-Xt @ w))
        out.append(res)
    return pd.concat(out, ignore_index=True)


def scores(d: pd.DataFrame, name: str) -> dict:
    y = d["y"].to_numpy(bool)
    pred = d[name].to_numpy(bool) if name in RULES else (d["p_model"] >= 0.5).to_numpy()
    prob = d[f"p_{name}"].to_numpy(float)
    tpr = (pred & y).sum() / max(y.sum(), 1)
    tnr = (~pred & ~y).sum() / max((~y).sum(), 1)
    prec = (pred & y).sum() / max(pred.sum(), 1)
    return dict(balanced_accuracy=round(float((tpr + tnr) / 2), 3), recall=round(float(tpr), 3),
                precision=round(float(prec), 3), brier=round(float(np.mean((prob - y) ** 2)), 4),
                flagged=int(pred.sum()))


def cluster_bootstrap(d: pd.DataFrame, a: str, b: str, n: int = 2000) -> dict:
    """95% interval for score(a) - score(b), resampling whole districts."""
    groups = {k: g for k, g in d.groupby("district")}
    keys = list(groups)
    dbrier, dba = [], []
    for _ in range(n):
        s = pd.concat([groups[k] for k in RNG.choice(keys, len(keys))])
        sa, sb = scores(s, a), scores(s, b)
        dbrier.append(sa["brier"] - sb["brier"])
        dba.append(sa["balanced_accuracy"] - sb["balanced_accuracy"])
    q = lambda v: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]
    return dict(brier_diff_ci=q(dbrier), balanced_accuracy_diff_ci=q(dba))


def main() -> None:
    records, manifest = SnapshotStore().load()
    units = build_units(records)
    preds = predict(units)
    sel = preds[preds["target_year"].isin(SELECTION)]
    test = preds[preds["target_release"].isin(TEST)]
    names = RULES + ["model"]
    result = dict(
        snapshot_id=manifest["snapshot_id"], design=__doc__.split("Writes")[0].strip(),
        n_units=dict(selection=len(sel), test=len(test)),
        base_rate=dict(selection=round(float(sel["y"].mean()), 3), test=round(float(test["y"].mean()), 3)),
        selection={n: scores(sel, n) for n in names},
        test={n: scores(test, n) for n in names},
        test_by_release={rel: {n: scores(g, n) for n in names} for rel, g in test.groupby("target_release")},
    )
    best_rule = max(RULES, key=lambda r: result["selection"][r]["balanced_accuracy"])
    result["best_rule_on_selection"] = best_rule
    boot = cluster_bootstrap(test, "model", best_rule)
    result["model_vs_best_rule_test"] = boot
    t = result["test"]
    adopt = boot["brier_diff_ci"][1] < 0 and t["model"]["balanced_accuracy"] - t[best_rule]["balanced_accuracy"] >= 0.02
    result["decision"] = "adopt model" if adopt else "keep rules"
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "design"}, indent=1))


if __name__ == "__main__":
    main()
