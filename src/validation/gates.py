"""Schema and quality gates applied to every candidate release before publication.

A gate returns errors (block publication) and warnings (published, but shown on
the Data Status screen). Thresholds are deliberately strict about structure and
lenient about content, because content anomalies are real survey features that
must be disclosed, not hidden.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.config import DISTRICTS

REQUIRED_COLUMNS = ["release_id", "season_year", "season", "district", "crop", "metric",
                    "value", "value_status", "source_table"]
REQUIRED_METRICS = ["yield_kg_ha", "harvested_ha", "cultivated_ha", "production_t",
                    "improved_seed_farmers_pct", "inorganic_fert_farmers_pct"]
REQUIRED_CROPS = ["maize", "bean", "irish_potato", "paddy_rice", "cassava"]
VALID_STATUS = {"observed", "reported_zero", "blank", "invalid_negative", "invalid_range"}


@dataclass
class GateReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {"passed": self.passed, "errors": self.errors, "warnings": self.warnings}


def validate_release(df: pd.DataFrame) -> GateReport:
    rep = GateReport()
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        rep.errors.append(f"missing columns: {missing_cols}")
        return rep
    if df.empty:
        rep.errors.append("release produced no records")
        return rep
    if df["release_id"].nunique() != 1:
        rep.errors.append("a release file must contain exactly one release_id")
    if not set(df["season"].unique()) <= {"A", "B", "C"}:
        rep.errors.append(f"unknown season codes: {sorted(df['season'].unique())}")

    districts = set(df["district"].unique()) - {"National"}
    unknown = districts - set(DISTRICTS)
    missing = set(DISTRICTS) - districts
    if unknown:
        rep.errors.append(f"unknown district names: {sorted(unknown)}")
    if missing:
        rep.errors.append(f"missing districts: {sorted(missing)}")
    if "National" not in set(df["district"]):
        rep.errors.append("national reference row missing")

    metrics = set(df["metric"].unique())
    for m in REQUIRED_METRICS:
        if m not in metrics:
            rep.errors.append(f"required metric missing: {m}")
    crops = set(df["crop"].unique())
    for c in REQUIRED_CROPS:
        if c not in crops:
            rep.errors.append(f"required crop missing: {c}")

    nat = df[df["district"] == "National"]
    for m in REQUIRED_METRICS:
        sub = nat[nat["metric"] == m]
        if m in metrics and not (sub["value_status"] == "observed").any():
            rep.errors.append(f"no national reference value for {m}")

    bad_status = set(df["value_status"].unique()) - VALID_STATUS
    if bad_status:
        rep.errors.append(f"unknown value_status: {bad_status}")
    observed = df[df["value_status"] == "observed"]
    if observed["value"].isna().any():
        rep.errors.append("observed rows with empty value")
    zero_like = df[df["value_status"] != "observed"]
    if zero_like["value"].notna().any():
        rep.errors.append("non-observed rows carry a value (absence must not become a number)")

    dup = df.duplicated(["release_id", "district", "crop", "metric"]).sum()
    if dup:
        rep.errors.append(f"{dup} duplicate district-crop-metric rows")

    invalid = df["value_status"].isin(["invalid_negative", "invalid_range"]).sum()
    if invalid:
        rep.warnings.append(f"{invalid} cells failed range checks and were excluded")

    # Internal consistency: production = yield x harvested area / 1000.
    crops_df = df[df["crop"] != "all"]
    w = crops_df.pivot_table(index=["district", "crop"], columns="metric", values="value",
                             aggfunc="first")
    if {"yield_kg_ha", "harvested_ha", "production_t"} <= set(w.columns):
        implied = w["yield_kg_ha"] * w["harvested_ha"] / 1000
        ratio = (w["production_t"] / implied).replace([np.inf, -np.inf], np.nan).dropna()
        off = int(((ratio - 1).abs() > 0.02).sum())
        if len(ratio) and off / len(ratio) > 0.10:
            rep.errors.append(f"production != yield x area in {off}/{len(ratio)} cells")
        elif off:
            rep.warnings.append(f"production differs from yield x area by >2% in {off} cells")
        if "cultivated_ha" in w:
            over = int((w["harvested_ha"] > w["cultivated_ha"] * 1.001).sum())
            if over:
                rep.warnings.append(
                    f"harvested area exceeds cultivated area in {over} district-crop cells "
                    "(as published; common for perennial bananas)")
        yields = w["yield_kg_ha"].dropna()
        if (yields > 80000).any():
            rep.warnings.append("yields above 80 t/ha present; check units")
    nz = (df["value_status"] == "reported_zero").sum()
    if nz:
        rep.warnings.append(f"{nz} cells published as 0 are treated as 'not reported', not as zero")
    return rep
