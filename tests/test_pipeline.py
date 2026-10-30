"""Refresh pipeline tests on SYNTHETIC fixtures (see tests/fixtures/synthetic_sas.py)."""
import json

import pandas as pd
import pytest

from src.analytics.indicators import evidence_table
from src.ingestion.sas_adapter import parse_workbook
from src.services.snapshot_store import SnapshotStore
from tests.fixtures.synthetic_sas import make_workbook


@pytest.fixture
def store(tmp_path):
    s = SnapshotStore(tmp_path / "data")
    for y in (2024, 2025):
        f = make_workbook(tmp_path / f"fx_{y}A.xlsx", y, "A", start_table=8 + y - 2024)
        res = s.ingest(f, f"SAS-{y}A", y, "A", approve=True)
        assert res.status == "published", res.gate.as_dict() if res.gate else res.message
    return s


def test_adapter_finds_renumbered_tables_and_national_labels(tmp_path):
    f = make_workbook(tmp_path / "a.xlsx", 2026, "A", start_table=21)
    r = parse_workbook(f, "X", 2026, "A")
    d = r.records
    assert r.tables_used["yield_kg_ha"] == "Table 23"
    nat = d[d["district"] == "National"]
    # 'Total' (fertilizer) and 'S/Total' (production) are recognised as the national row.
    assert nat[nat["metric"] == "inorganic_fert_farmers_pct"]["value"].iloc[0] == 60.0
    assert nat[(nat["metric"] == "production_t") & (nat["crop"] == "maize")]["value"].notna().all()


def test_published_zero_is_not_a_zero_yield(tmp_path):
    f = make_workbook(tmp_path / "a.xlsx", 2026, "A")
    d = parse_workbook(f, "X", 2026, "A").records
    sorghum = d[(d["crop"] == "sorghum") & (d["metric"] == "yield_kg_ha") & (d["district"] != "National")]
    assert (sorghum["value_status"] == "reported_zero").all()
    assert sorghum["value"].isna().all()


def test_new_valid_release_updates_outputs_without_code_change(store, tmp_path):
    rec_before, _ = store.load()
    ev_before = evidence_table(rec_before, "maize", "A")
    assert ev_before["latest_release"].iloc[0] == "SAS-2025A"
    f = make_workbook(tmp_path / "fx_2026A.xlsx", 2026, "A", start_table=14)
    res = store.ingest(f, "SAS-2026A", 2026, "A", approve=True)
    assert res.status == "published"
    rec_after, manifest = store.load()
    ev_after = evidence_table(rec_after, "maize", "A")
    assert ev_after["latest_release"].iloc[0] == "SAS-2026A"
    assert "ratio_SAS-2026A" in ev_after.columns
    assert ev_after.set_index("district").loc["Ruhango", "matched_seasons_adequate"] == 3
    assert manifest["parent_snapshot"] is not None


def test_duplicate_ingest_is_idempotent(store, tmp_path):
    active = store.active_id()
    n_snap = len(store.list_snapshots())
    f = make_workbook(tmp_path / "fx_2025A.xlsx", 2025, "A", start_table=9)
    res = store.ingest(f, "SAS-2025A", 2025, "A", approve=True)
    assert res.status == "unchanged"
    assert store.active_id() == active
    assert len(store.list_snapshots()) == n_snap


def test_bad_schema_is_rejected_and_active_snapshot_survives(store, tmp_path):
    active = store.active_id()
    rec_before, _ = store.load()
    for kwargs, rid in [(dict(drop_input=True), "SAS-2026A"), (dict(bad_district=True), "SAS-2027A")]:
        f = make_workbook(tmp_path / f"bad_{rid}.xlsx", int(rid[4:8]), "A", **kwargs)
        res = store.ingest(f, rid, int(rid[4:8]), "A", approve=True)
        assert res.status == "rejected"
        assert store.active_id() == active
    rec_after, _ = store.load()
    pd.testing.assert_frame_equal(rec_before, rec_after)
    quarantined = list((store.data_dir / "quarantine").iterdir())
    assert len(quarantined) == 2
    reason = json.loads((quarantined[0] / "reason.json").read_text())
    assert reason.get("errors") or reason.get("error")


def test_late_correction_preserves_lineage_and_rollback(store, tmp_path):
    first_active = store.active_id()
    f = make_workbook(tmp_path / "fx_2024A_v2.xlsx", 2024, "A", yield_scale=1.05)
    res = store.ingest(f, "SAS-2024A", 2024, "A", approve=True)
    assert res.status == "published"
    reg = store.registry()
    versions = [r for r in reg if r["release_id"] == "SAS-2024A"]
    assert len(versions) == 2
    assert versions[0]["current"] is False and versions[1]["current"] is True
    assert versions[1]["supersedes"].startswith(versions[0]["sha256"][:12])
    _, m = store.load()
    assert m["change"]["kind"] == "correction"
    # Both raw files are kept immutably.
    assert len(list((store.data_dir / "raw" / "nisr_sas").iterdir())) == 3
    store.rollback(first_active)
    assert store.active_id() == first_active


def test_candidate_is_not_visible_until_approved(store, tmp_path):
    active = store.active_id()
    f = make_workbook(tmp_path / "fx_2026A.xlsx", 2026, "A")
    res = store.ingest(f, "SAS-2026A", 2026, "A", approve=False)
    assert res.status == "candidate"
    assert store.active_id() == active
    store.approve(res.snapshot_id)
    assert store.active_id() == res.snapshot_id


def test_release_incompatible_with_decision_rules_is_blocked(store, tmp_path):
    """No ML model is used. The analogue of feature-drift blocking: a release that lacks
    an input the decision rules require is rejected before it can reach the app."""
    f = make_workbook(tmp_path / "fx_2026A.xlsx", 2026, "A", drop_input=True)
    res = store.ingest(f, "SAS-2026A", 2026, "A", approve=True)
    assert res.status == "rejected"
    assert any("inorganic" in e for e in res.gate.errors)
