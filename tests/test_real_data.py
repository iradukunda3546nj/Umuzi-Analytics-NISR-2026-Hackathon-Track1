"""Integrity tests on the ACTIVE snapshot built from real NISR SAS releases."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.indicators import crop_panel, evidence_table, load_targets, national_vs_target
from src.config import DATA_DIR, DISTRICTS
from src.decisions.brief import brief_csv, build_brief
from src.decisions.finding import build_finding
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
    ok = ((p["production_t"] / (p["yield_kg_ha"] * p["harvested_ha"] / 1000) - 1).abs() < 0.02)
    share = ok.groupby(p["release_id"]).mean()
    # Current releases are internally exact; older annual workbooks are published with small
    # rounding differences (2018B: 93% of cells within 2%), which the gates report as warnings.
    assert share[[r for r in share.index if r >= "SAS-2024"]].min() > 0.99
    assert share.min() > 0.90


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
    f = build_finding(ev, crop_panel(rec), "Ruhango")
    text = build_brief(f, manifest)
    assert row["category"] in text and f.headline in text
    assert f"({row['latest_ratio']:.0%} of national)" in text
    assert manifest["snapshot_id"] in text
    exported = pd.read_csv(pd.io.common.BytesIO(brief_csv(f)))
    assert exported.loc[0, "category"] == row["category"]
    assert np.isclose(exported.loc[0, "latest_ratio"], row["latest_ratio"])


def test_historical_releases_present_and_2018_inputs_excluded(snap):
    rec, manifest = snap
    rels = set(rec["release_id"])
    assert {f"SAS-{y}{s}" for y in range(2018, 2024) for s in "AB"} <= rels
    assert "SAS-2025B" not in rels                      # not published: never imputed
    inputs_2018 = rec[(rec["release_id"].str.startswith("SAS-2018")) & (rec["crop"] == "all")]
    assert inputs_2018.empty                             # per-plot basis, not comparable
    meta = {r["release_id"]: r for r in manifest["releases"]}
    assert meta["SAS-2018B"]["sheet_overrides"] == {"harvested_ha": "Appendix 5"}


def test_historical_values_trace_to_source(snap):
    """Cells read directly from the annual workbooks (yield tables, kg/ha)."""
    rec, _ = snap
    y = rec[(rec["crop"] == "maize") & (rec["metric"] == "yield_kg_ha")].set_index(["release_id", "district"])["value"]
    assert abs(y[("SAS-2018A", "Nyarugenge")] - 942.1188) < 1e-6      # 2018 Appendix 9 (transposed)
    assert abs(y[("SAS-2018A", "National")] - 1524.757683757732) < 1e-6  # "Overall Yield 2018 A" column
    assert abs(y[("SAS-2019A", "Nyarugenge")] - 733) < 1e-9            # 2019 Table 13
    assert abs(y[("SAS-2019A", "National")] - 1539) < 1e-9
    assert abs(y[("SAS-2020A", "National")] - 1598.0345770309802) < 1e-6  # "National", not "National 2019 A"
