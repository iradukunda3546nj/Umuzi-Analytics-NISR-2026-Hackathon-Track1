"""Data Status summaries for the active snapshot (coverage, freshness, warnings)."""
from __future__ import annotations

import pandas as pd

from src.validation.gates import validate_release


def release_status(records: pd.DataFrame, manifest: dict) -> pd.DataFrame:
    rows = []
    meta = {r["release_id"]: r for r in manifest["releases"]}
    for rel, g in records.groupby("release_id"):
        rep = validate_release(g)
        crops = g[(g["crop"] != "all") & (g["metric"] == "yield_kg_ha") & (g["district"] != "National")]
        m = meta.get(rel, {})
        rows.append(dict(
            release=rel, season_year=int(g["season_year"].iloc[0]), season=g["season"].iloc[0],
            yield_cells_observed=int((crops["value_status"] == "observed").sum()),
            yield_cells_not_reported=int((crops["value_status"] != "observed").sum()),
            gate="passed" if rep.passed else "failed", warnings=" | ".join(rep.warnings),
            sha256=m.get("sha256", "")[:12], adapter=m.get("adapter_version", ""),
            imported_utc=m.get("retrieved_or_imported_utc", ""), published=m.get("publication_date", ""),
            source_url=m.get("source_url", "")))
    return pd.DataFrame(rows).sort_values(["season", "season_year"])


def missing_releases(records: pd.DataFrame) -> list[str]:
    """Season releases absent between the first and last year of each season type."""
    out = []
    for season, g in records.groupby("season"):
        years = sorted(g["season_year"].unique())
        for y in range(years[0], years[-1] + 1):
            if y not in years:
                out.append(f"{y} Season {season}")
    return out
