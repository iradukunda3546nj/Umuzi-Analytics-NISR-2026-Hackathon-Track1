"""Versioned, transactional snapshot store.

Flow: stage raw file -> parse (source adapter) -> gates -> candidate snapshot ->
explicit approval -> ACTIVE pointer. The app reads only the ACTIVE snapshot.

- Raw inputs are immutable: a file whose name exists with a different checksum is
  rejected; the same checksum is an idempotent no-op.
- A failed release is quarantined with its gate report; ACTIVE is untouched.
- Re-publishing a release_id (correction or late backfill) creates a new snapshot
  and the manifest records which raw file superseded which, so lineage survives.
- Rollback moves the ACTIVE pointer to any earlier snapshot; nothing is deleted.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src import config
from src.ingestion.sas_adapter import ADAPTER_VERSION, SchemaError, parse_workbook
from src.validation.gates import GateReport, validate_release

RULESET_VERSION = "evidence-rules-1.0"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def records_hash(df: pd.DataFrame) -> str:
    cols = ["release_id", "district", "crop", "metric", "value", "value_status"]
    canon = df[cols].sort_values(cols[:4]).to_csv(index=False, float_format="%.6f")
    return hashlib.sha256(canon.encode()).hexdigest()


@dataclass
class RefreshResult:
    status: str                      # published | candidate | unchanged | rejected
    snapshot_id: str | None
    message: str
    gate: GateReport | None = None


class SnapshotStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or config.DATA_DIR)
        self.raw_dir = self.data_dir / "raw" / "nisr_sas"
        self.snap_dir = self.data_dir / "snapshots"
        self.quarantine_dir = self.data_dir / "quarantine"
        self.registry_path = self.data_dir / "release_registry.json"
        self.active_path = self.snap_dir / "ACTIVE.json"
        for d in (self.raw_dir, self.snap_dir, self.quarantine_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---------- registry ----------
    def registry(self) -> list[dict]:
        if self.registry_path.exists():
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        return []

    def _save_registry(self, reg: list[dict]) -> None:
        self.registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    # ---------- active snapshot ----------
    def active_id(self) -> str | None:
        if not self.active_path.exists():
            return None
        return json.loads(self.active_path.read_text(encoding="utf-8"))["snapshot_id"]

    def load(self, snapshot_id: str | None = None) -> tuple[pd.DataFrame, dict]:
        sid = snapshot_id or self.active_id()
        if sid is None:
            raise FileNotFoundError("no approved snapshot is active")
        d = self.snap_dir / sid
        records = pd.read_csv(d / "records.csv")
        manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        return records, manifest

    def list_snapshots(self) -> list[dict]:
        out = []
        for d in sorted(self.snap_dir.glob("snap-*")):
            m = d / "manifest.json"
            if m.exists():
                out.append(json.loads(m.read_text(encoding="utf-8")))
        return out

    def _set_active(self, snapshot_id: str, reason: str) -> None:
        self.active_path.write_text(json.dumps(
            {"snapshot_id": snapshot_id, "activated_utc": _now(), "reason": reason}, indent=2),
            encoding="utf-8")
        m_path = self.snap_dir / snapshot_id / "manifest.json"
        m = json.loads(m_path.read_text(encoding="utf-8"))
        m["approval"] = {"status": "approved", "approved_utc": _now(), "reason": reason}
        m_path.write_text(json.dumps(m, indent=2), encoding="utf-8")

    def approve(self, snapshot_id: str, reason: str = "analyst approval") -> None:
        if not (self.snap_dir / snapshot_id / "manifest.json").exists():
            raise FileNotFoundError(snapshot_id)
        _, m = self.load(snapshot_id)
        if not m["gate"]["passed"]:
            raise ValueError("cannot approve a snapshot that failed validation")
        self._set_active(snapshot_id, reason)

    def rollback(self, snapshot_id: str) -> None:
        self.approve(snapshot_id, reason="rollback")

    # ---------- ingest ----------
    def _quarantine(self, src: Path, release_id: str, reason: dict) -> Path:
        q = self.quarantine_dir / f"{_now().replace(':', '')}_{release_id}"
        q.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, q / src.name)
        (q / "reason.json").write_text(json.dumps(reason, indent=2), encoding="utf-8")
        return q

    def ingest(self, file: Path, release_id: str, season_year: int, season: str,
               source_url: str = "", publisher: str = "National Institute of Statistics of Rwanda",
               approve: bool = False, publication_date: str = "") -> RefreshResult:
        file = Path(file)
        checksum = sha256_file(file)
        raw_name = f"{release_id}__{checksum[:12]}{file.suffix}"
        raw_path = self.raw_dir / raw_name

        reg = self.registry()
        same = [r for r in reg if r["release_id"] == release_id and r["sha256"] == checksum
                and r.get("adapter_version", "sas-adapter-1.0") == ADAPTER_VERSION]
        if same:
            return RefreshResult("unchanged", self.active_id(),
                                 f"{release_id} with checksum {checksum[:12]} already ingested")

        # Stage + parse + gates. Nothing touches registry, raw store or ACTIVE until all pass.
        try:
            parsed = parse_workbook(file, release_id, season_year, season)
        except (SchemaError, KeyError, ValueError, OSError) as exc:
            q = self._quarantine(file, release_id, {"stage": "parse", "error": str(exc)})
            gate = GateReport(errors=[f"parse failed: {exc}"])
            return RefreshResult("rejected", self.active_id(),
                                 f"rejected at parse; quarantined in {q.name}", gate)
        gate = validate_release(parsed.records)
        gate.warnings = parsed.warnings + gate.warnings
        if not gate.passed:
            q = self._quarantine(file, release_id, {"stage": "validate", **gate.as_dict()})
            return RefreshResult("rejected", self.active_id(),
                                 f"rejected by validation gates; quarantined in {q.name}", gate)

        # Candidate = active records with this release replaced (correction/backfill) or added.
        base = pd.DataFrame()
        prev_entry = None
        if self.active_id():
            base, _ = self.load()
            base = base[base["release_id"] != release_id]
        prev = [r for r in reg if r["release_id"] == release_id and r.get("current", True)]
        if prev:
            prev_entry = prev[-1]
        candidate = pd.concat([base, parsed.records], ignore_index=True)
        candidate = candidate.sort_values(["season", "season_year", "district", "crop", "metric"])
        rhash = records_hash(candidate)
        if self.active_id():
            _, am = self.load()
            if am["records_sha256"] == rhash:
                return RefreshResult("unchanged", self.active_id(), "content identical to active")

        if not raw_path.exists():
            shutil.copy2(file, raw_path)
        for r in reg:
            if r["release_id"] == release_id:
                r["current"] = False
                r["superseded_utc"] = _now()
        entry = dict(release_id=release_id, season_year=season_year, season=season,
                     publisher=publisher, source_url=source_url, publication_date=publication_date,
                     raw_file=str(raw_path.relative_to(self.data_dir)).replace("\\", "/"),
                     sha256=checksum, retrieved_or_imported_utc=_now(), tables_used=parsed.tables_used,
                     adapter_version=ADAPTER_VERSION, current=True,
                     supersedes=(f"{prev_entry['sha256'][:12]}/"
                                 f"{prev_entry.get('adapter_version', 'sas-adapter-1.0')}"
                                 if prev_entry else None))
        reg.append(entry)

        sid = f"snap-{_now().replace(':', '').replace('-', '')}-{rhash[:8]}"
        sdir = self.snap_dir / sid
        sdir.mkdir(parents=True, exist_ok=False)
        candidate.to_csv(sdir / "records.csv", index=False)
        manifest = dict(
            snapshot_id=sid, created_utc=_now(), parent_snapshot=self.active_id(),
            ruleset_version=RULESET_VERSION, records_sha256=rhash, n_records=len(candidate),
            releases=[r for r in reg if r.get("current", True)
                      and r["release_id"] in set(candidate["release_id"])],
            change=dict(release_id=release_id, kind="correction" if prev_entry else "new_release"),
            gate=gate.as_dict(), approval={"status": "pending"})
        (sdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self._save_registry(reg)
        if approve:
            self._set_active(sid, f"approved at ingest of {release_id}")
            return RefreshResult("published", sid, f"{release_id} published as {sid}", gate)
        return RefreshResult("candidate", sid,
                             f"{release_id} staged as candidate {sid}; approve to publish", gate)
