"""Integrity tests on the ACTIVE snapshot built from real NISR SAS releases."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analytics.indicators import crop_panel, evidence_table, load_targets, national_vs_target
from src.config import DATA_DIR, DISTRICTS
from src.decisions.brief import brief_csv, build_brief
from src.ingestion.sas_adapter import parse_workbook
from src.services.snapshot_store import SnapshotStore

store = SnapshotStore()
pytestmark = pytest.mark.skipif(store.active_id() is None, reason="no active snapshot")


@pytest.fixture(scope="module")
def snap():
    return store.load()


def test_snapshot_coverage(snap):
    rec, manifest = snap
    assert set(rec["release_id"]) >= {"SAS-2024A", "SAS-2024B", "SAS-2025A", "SAS-2026A", "SAS-2026B"}
    for rel, g in rec.groupby("release_id"):
        assert set(g["district"]) == set(DISTRICTS) | {"National"}, rel
    assert manifest["records_sha256"]


def test_raw_files_match_registry_checksums(snap):
    from src.services.snapshot_store import sha256_file
    _, manifest = snap
    for r in manifest["releases"]:
        assert sha256_file(DATA_DIR / r["raw_file"]) == r["sha256"]


def test_production_equals_yield_times_area(snap):
    rec, _ = snap
    p = crop_panel(rec)
    p = p.dropna(subset=["yield_kg_ha", "harvested_ha", "production_t"])
    ratio = p["production_t"] / (p["yield_kg_ha"] * p["harvested_ha"] / 1000)
    assert ((ratio - 1).abs() < 0.02).mean() > 0.99


def test_no_reported_zero_became_a_number(snap):
    rec, _ = snap
    assert rec.loc[rec["value_status"] != "observed", "value"].isna().all()


def test_standalone_2024_releases_match_annual_workbook(snap):
    rec, _ = snap
    ref = DATA_DIR / "raw" / "reference" / "SAS_2024_Annual_Tables.xlsx"
    if not ref.exists():
        pytest.skip("reference workbook not present")
    for season in ("A", "B"):
        ann = parse_workbook(ref, f"ANN-2024{season}", 2024, season).records
        a = ann[ann["metric"].isin(["yield_kg_ha", "harvested_ha"])].set_index(["district", "crop", "metric"])["value"]
        s = rec[(rec["release_id"] == f"SAS-2024{season}") & rec["metric"].isin(["yield_kg_ha", "harvested_ha"])]
        s = s.set_index(["district", "crop", "metric"])["value"]
        diff = (a - s.reindex(a.index)).abs()
        assert diff.fillna(0).max() < 1e-6


def test_known_values_trace_to_source(snap):
    """Spot-check against cells read directly from the 2026A workbook (Table 13 / Table 12)."""
    rec, _ = snap
    v = rec[(rec["release_id"] == "SAS-2026A") & (rec["crop"] == "maize") & (rec["metric"] == "yield_kg_ha")]
    v = v.set_index("district")["value"]
    assert abs(v["Nyagatare"] - 2886.6716251764697) < 1e-6
    assert abs(v["National"] - 1994.3650203946784) < 1e-6
    ev = evidence_table(rec, "maize", "A").set_index("district")
    assert abs(ev.loc["Nyagatare", "latest_ratio"] - 2886.6716251764697 / 1994.3650203946784) < 1e-9


def test_target_comparison_uses_both_seasons_only(snap):
    rec, _ = snap
    nvt = national_vs_target(rec, load_targets())
    both = {y for y, g in rec.groupby("season_year") if {"A", "B"} <= set(g["season"])}
    assert set(nvt["season_year"]) == both               # a year without both seasons is never computed
    m = nvt[(nvt["crop"] == "maize") & (nvt["season_year"] == 2026)].iloc[0]
    assert m["target_t_ha"] == 2.06


def test_brief_and_exports_match_evidence_table(snap):
    rec, manifest = snap
    ev = evidence_table(rec, "bean", "A")
    row = ev[ev["district"] == "Ruhango"].iloc[0]
    text = build_brief(row, manifest)
    assert row["category"] in text
    assert f"ratio {row['latest_ratio']:,.2f}" in text
    assert manifest["snapshot_id"] in text
    exported = pd.read_csv(pd.io.common.BytesIO(brief_csv(row)))
    assert exported.loc[0, "category"] == row["category"]
    assert np.isclose(exported.loc[0, "latest_ratio"], row["latest_ratio"])
