"""Verified indicators and evidence categories derived from canonical SAS records.

All formulas used by the app, the analysis scripts, the planner brief and the
tests are defined here once. The UI never computes an indicator itself.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import (DISTRICT_PROVINCE, DISTRICTS, GAP_THRESHOLD, MIN_HARVESTED_HA,
                        MIN_MATCHED_SEASONS)

CATEGORY_INSUFFICIENT = "Insufficient evidence - field verification required"
CATEGORY_PERSISTENT_LOW_INPUT = "Persistent shortfall, low input uptake"
CATEGORY_PERSISTENT_INPUTS_OK = "Persistent shortfall, inputs at or above national"
CATEGORY_DIP = "Latest-season dip"
CATEGORY_NOT_BELOW = "Not below national"

CATEGORY_ORDER = [CATEGORY_PERSISTENT_LOW_INPUT, CATEGORY_PERSISTENT_INPUTS_OK, CATEGORY_DIP,
                  CATEGORY_INSUFFICIENT, CATEGORY_NOT_BELOW]

CATEGORY_ACTION = {
    CATEGORY_PERSISTENT_LOW_INPUT: (
        "Investigate input access first: verify improved-seed and fertilizer availability, "
        "affordability and delivery timing for this crop with the district agronomist and "
        "Farm Service Centre before the next season."),
    CATEGORY_PERSISTENT_INPUTS_OK: (
        "Input uptake is not low here, so input access alone is unlikely to explain the gap. "
        "Commission a field diagnosis of soil fertility and acidity, erosion, variety "
        "suitability and water constraints for this crop."),
    CATEGORY_DIP: (
        "Below national in the latest season only. Check for a season-specific shock "
        "(rainfall, pest or disease outbreak, late sowing) before reallocating resources; "
        "re-check after the next release."),
    CATEGORY_INSUFFICIENT: (
        "Published estimates are too thin or too few to support a conclusion. "
        "Field verification is required before any planning decision."),
    CATEGORY_NOT_BELOW: "No shortfall against the national yield in the latest season.",
}


@dataclass(frozen=True)
class Params:
    gap_threshold: float = GAP_THRESHOLD
    min_harvested_ha: float = MIN_HARVESTED_HA
    min_matched: int = MIN_MATCHED_SEASONS


def release_label(season_year: int, season: str) -> str:
    return f"{season_year} Season {season}"


def crop_panel(records: pd.DataFrame) -> pd.DataFrame:
    """Wide district x crop x release panel with yield, areas, production and ratio.

    Yield cells NISR printed as 0 or blank are kept as NaN with their status, so
    they appear as "not reported" rather than as a zero yield.
    """
    crops = records[records["crop"] != "all"]
    val = crops.pivot_table(index=["release_id", "season_year", "season", "district", "crop"],
                            columns="metric", values="value", aggfunc="first")
    status = crops.pivot_table(index=["release_id", "season_year", "season", "district", "crop"],
                               columns="metric", values="value_status", aggfunc="first")
    panel = val.join(status[["yield_kg_ha"]].rename(columns={"yield_kg_ha": "yield_status"}))
    panel = panel.reset_index()
    for col in ["yield_kg_ha", "harvested_ha", "cultivated_ha", "production_t"]:
        if col not in panel:
            panel[col] = np.nan
    nat = panel[panel["district"] == "National"][["release_id", "crop", "yield_kg_ha"]]
    nat = nat.rename(columns={"yield_kg_ha": "national_yield_kg_ha"})
    panel = panel[panel["district"] != "National"].merge(nat, on=["release_id", "crop"], how="left")
    panel["yield_ratio"] = panel["yield_kg_ha"] / panel["national_yield_kg_ha"]
    panel["province"] = panel["district"].map(DISTRICT_PROVINCE)
    return panel


def input_panel(records: pd.DataFrame) -> pd.DataFrame:
    """District input uptake per release with the national value alongside."""
    inp = records[records["crop"] == "all"]
    wide = inp.pivot_table(index=["release_id", "season_year", "season", "district"],
                           columns="metric", values="value", aggfunc="first").reset_index()
    nat = wide[wide["district"] == "National"].drop(columns=["season_year", "season", "district"])
    nat = nat.rename(columns={c: f"national_{c}" for c in nat.columns if c != "release_id"})
    return wide[wide["district"] != "National"].merge(nat, on="release_id", how="left")


def evidence_table(records: pd.DataFrame, crop: str, season: str, params: Params = Params(),
                   releases: list[str] | None = None) -> pd.DataFrame:
    """One row per district: latest-season position, persistence and evidence category.

    Only releases of the selected season type are compared (A with A, B with B).
    """
    panel = crop_panel(records)
    panel = panel[(panel["crop"] == crop) & (panel["season"] == season)]
    if releases is not None:
        panel = panel[panel["release_id"].isin(releases)]
    rel_order = (panel[["release_id", "season_year"]].drop_duplicates()
                 .sort_values("season_year")["release_id"].tolist())
    if not rel_order:
        return pd.DataFrame()
    latest = rel_order[-1]
    panel = panel.copy()
    panel["adequate"] = panel["yield_kg_ha"].notna() & (panel["harvested_ha"] >= params.min_harvested_ha)
    panel["below"] = panel["yield_ratio"] < params.gap_threshold

    inputs = input_panel(records)
    inputs = inputs[inputs["release_id"] == latest]

    rows = []
    for d in DISTRICTS:
        sub = panel[panel["district"] == d].set_index("release_id").reindex(rel_order)
        ok = sub[sub["adequate"].fillna(False).astype(bool)]
        lt = sub.loc[latest]
        n_ok = len(ok)
        n_below = int(ok["below"].sum())
        latest_ok = bool(lt["adequate"]) if pd.notna(lt["adequate"]) else False
        persistent = latest_ok and n_ok >= params.min_matched and n_below == n_ok
        inp = inputs[inputs["district"] == d]
        seed = inp["improved_seed_farmers_pct"].iloc[0] if len(inp) else np.nan
        fert = inp["inorganic_fert_farmers_pct"].iloc[0] if len(inp) else np.nan
        nseed = inp["national_improved_seed_farmers_pct"].iloc[0] if len(inp) else np.nan
        nfert = inp["national_inorganic_fert_farmers_pct"].iloc[0] if len(inp) else np.nan
        inputs_known = all(pd.notna(v) for v in (seed, fert, nseed, nfert))
        inputs_low = inputs_known and seed < nseed and fert < nfert

        if not latest_ok or (persistent and not inputs_known):
            category = CATEGORY_INSUFFICIENT
        elif not bool(lt["below"]):
            category = CATEGORY_NOT_BELOW
        elif n_ok < params.min_matched:
            category = CATEGORY_INSUFFICIENT
        elif persistent:
            category = CATEGORY_PERSISTENT_LOW_INPUT if inputs_low else CATEGORY_PERSISTENT_INPUTS_OK
        else:
            category = CATEGORY_DIP

        hist = {f"ratio_{r}": sub.loc[r, "yield_ratio"] for r in rel_order}
        rows.append(dict(
            district=d, province=DISTRICT_PROVINCE[d], crop=crop, season=season,
            latest_release=latest,
            latest_yield_kg_ha=lt["yield_kg_ha"], national_yield_kg_ha=lt["national_yield_kg_ha"],
            latest_ratio=lt["yield_ratio"], latest_harvested_ha=lt["harvested_ha"],
            latest_yield_status=lt["yield_status"],
            matched_seasons_adequate=n_ok, seasons_below=n_below, persistent_shortfall=persistent,
            improved_seed_pct=seed, national_improved_seed_pct=nseed,
            inorganic_fert_pct=fert, national_inorganic_fert_pct=nfert,
            category=category, next_step=CATEGORY_ACTION[category], **hist,
        ))
    out = pd.DataFrame(rows)
    out["mean_ratio"] = out[[c for c in out.columns if c.startswith("ratio_")]].mean(axis=1)
    out["range_ratio"] = (out[[c for c in out.columns if c.startswith("ratio_")]].max(axis=1)
                          - out[[c for c in out.columns if c.startswith("ratio_")]].min(axis=1))
    out["category_rank"] = out["category"].map({c: i for i, c in enumerate(CATEGORY_ORDER)})
    return out.sort_values(["category_rank", "latest_ratio"]).reset_index(drop=True)


def load_targets(path=None) -> pd.DataFrame:
    from src.config import DATA_DIR
    return pd.read_csv(path or DATA_DIR / "reference" / "psta5_productivity_targets.csv")


def national_vs_target(records: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """National Season A+B yield per SAS year against the PSTA 5 annual target.

    Approximation, stated in every view that uses it: Season A + B production
    divided by Season A + B harvested area. Season C (marshland, small for most
    priority crops) is not in the ingested releases. SAS year Y covers the
    agricultural year (Y-1)/Y, so SAS 2026 is compared with the 2025/26 target.
    Only years with both A and B releases are computed; a missing season is
    never imputed.
    """
    nat = records[(records["district"] == "National") & (records["crop"] != "all")]
    w = nat.pivot_table(index=["season_year", "season", "crop"], columns="metric",
                        values="value", aggfunc="first").reset_index()
    rows = []
    for (year, crop), g in w.groupby(["season_year", "crop"]):
        seasons = set(g["season"])
        if not {"A", "B"} <= seasons:
            continue
        g = g[g["season"].isin(["A", "B"])]
        prod, ha = g["production_t"].sum(min_count=2), g["harvested_ha"].sum(min_count=2)
        if pd.isna(prod) or pd.isna(ha) or ha <= 0:
            continue
        t = targets[targets["crop"] == crop]
        col = f"target_{year - 1}_{str(year)[-2:]}"
        target = float(t[col].iloc[0]) if len(t) and col in t else np.nan
        baseline = float(t["baseline_2023"].iloc[0]) if len(t) else np.nan
        rows.append(dict(season_year=year, agricultural_year=f"{year - 1}/{str(year)[-2:]}",
                         crop=crop, yield_t_ha=prod / ha, target_t_ha=target,
                         baseline_2023_t_ha=baseline, attainment=(prod / ha) / target
                         if pd.notna(target) else np.nan))
    return pd.DataFrame(rows)


def input_association(records: pd.DataFrame, crop: str, release_id: str,
                      params: Params = Params()) -> pd.DataFrame:
    """Spearman association between district input uptake and yield ratio (one release).

    Descriptive only: n <= 30 districts, inputs pooled over all crops.
    """
    from scipy.stats import spearmanr

    panel = crop_panel(records)
    p = panel[(panel["crop"] == crop) & (panel["release_id"] == release_id)
              & (panel["harvested_ha"] >= params.min_harvested_ha)]
    inp = input_panel(records)
    d = p.merge(inp[inp["release_id"] == release_id], on=["release_id", "district"])
    rows = []
    for var in ["improved_seed_farmers_pct", "inorganic_fert_farmers_pct"]:
        dd = d[["yield_ratio", var]].dropna()
        if len(dd) < 12:
            rows.append(dict(input=var, n=len(dd), rho=np.nan, p=np.nan))
            continue
        res = spearmanr(dd[var], dd["yield_ratio"])
        rows.append(dict(input=var, n=len(dd), rho=float(res.statistic), p=float(res.pvalue)))
    return pd.DataFrame(rows)


def national_series(records: pd.DataFrame, crop: str) -> pd.DataFrame:
    p = records[(records["district"] == "National") & (records["crop"] == crop)]
    p = p.pivot_table(index=["release_id", "season_year", "season"], columns="metric",
                      values="value", aggfunc="first").reset_index()
    return p.sort_values(["season", "season_year"])
