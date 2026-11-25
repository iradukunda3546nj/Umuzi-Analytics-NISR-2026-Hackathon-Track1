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

RULESET_VERSION = "evidence-rules-2.0"


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

    def _raw_path_for(self, file: Path, release_id: str, checksum: str) -> Path:
        # Both seasons of an annual workbook share one raw copy: reuse any stored
        # file with the same checksum instead of storing the bytes twice.
        existing = sorted(self.raw_dir.glob(f"*__{checksum[:12]}{file.suffix}"))
        return existing[0] if existing else self.raw_dir / f"{release_id}__{checksum[:12]}{file.suffix}"

    def _parse_and_gate(self, file: Path, release_id: str, season_year: int, season: str,
                        sheet_overrides: dict | None, inputs_comparable: bool):
        """Parse and validate one release. Returns (parsed, gate) or a rejected RefreshResult.
        Nothing touches the registry, raw store or ACTIVE pointer here."""
        try:
            parsed = parse_workbook(file, release_id, season_year, season,
                                    sheet_overrides=sheet_overrides, inputs_comparable=inputs_comparable)
        except (SchemaError, KeyError, ValueError, OSError) as exc:
            q = self._quarantine(file, release_id, {"stage": "parse", "error": str(exc)})
            return RefreshResult("rejected", self.active_id(), f"{release_id} rejected at parse; "
                                 f"quarantined in {q.name}", GateReport(errors=[f"parse failed: {exc}"]))
        gate = validate_release(parsed.records, inputs_expected=inputs_comparable)
        gate.warnings = parsed.warnings + gate.warnings
        if not gate.passed:
            q = self._quarantine(file, release_id, {"stage": "validate", **gate.as_dict()})
            return RefreshResult("rejected", self.active_id(), f"{release_id} rejected by validation "
                                 f"gates; quarantined in {q.name}", gate)
        return parsed, gate

    def ingest(self, file: Path, release_id: str, season_year: int, season: str,
               source_url: str = "", publisher: str = "National Institute of Statistics of Rwanda",
               approve: bool = False, publication_date: str = "",
               sheet_overrides: dict | None = None, inputs_comparable: bool = True) -> RefreshResult:
        return self.ingest_batch([dict(file=file, release_id=release_id, season_year=season_year,
                                       season=season, source_url=source_url, publisher=publisher,
                                       publication_date=publication_date, sheet_overrides=sheet_overrides,
                                       inputs_comparable=inputs_comparable)], approve=approve)

    def ingest_batch(self, entries: list[dict], approve: bool = False) -> RefreshResult:
        """Ingest one or more releases as a single candidate snapshot.

        All-or-nothing: if any release fails parsing or a gate, it is quarantined
        and no snapshot is created, so a backfill can never be half-published.
        """
        reg = self.registry()
        staged = []
        for e in entries:
            file = Path(e["file"])
            checksum = sha256_file(file)
            same = [r for r in reg if r["release_id"] == e["release_id"] and r["sha256"] == checksum
                    and r.get("current", True)
                    and r.get("adapter_version", "sas-adapter-1.0") == ADAPTER_VERSION]
            if same:
                continue
            out = self._parse_and_gate(file, e["release_id"], e["season_year"], e["season"],
                                       e.get("sheet_overrides"), e.get("inputs_comparable", True))
            if isinstance(out, RefreshResult):
                return out
            staged.append((e, file, checksum, *out))
        if not staged:
            ids = ", ".join(e["release_id"] for e in entries)
            return RefreshResult("unchanged", self.active_id(), f"{ids} already ingested")

        # Candidate = active records with these releases replaced (correction/backfill) or added.
        new_ids = {e["release_id"] for e, *_ in staged}
        base = pd.DataFrame()
        if self.active_id():
            base, _ = self.load()
            base = base[~base["release_id"].isin(new_ids)]
        candidate = pd.concat([base] + [p.records for *_, p, _g in staged], ignore_index=True)
        candidate = candidate.sort_values(["season", "season_year", "district", "crop", "metric"])
        rhash = records_hash(candidate)
        if self.active_id():
            _, am = self.load()
            if am["records_sha256"] == rhash:
                return RefreshResult("unchanged", self.active_id(), "content identical to active")

        kinds = {}
        gate = GateReport()
        for e, file, checksum, parsed, g in staged:
            rid = e["release_id"]
            prev = [r for r in reg if r["release_id"] == rid and r.get("current", True)]
            prev_entry = prev[-1] if prev else None
            kinds[rid] = "correction" if prev_entry else "new_release"
            raw_path = self._raw_path_for(file, rid, checksum)
            if not raw_path.exists():
                shutil.copy2(file, raw_path)
            for r in reg:
                if r["release_id"] == rid:
                    r["current"] = False
                    r["superseded_utc"] = _now()
            reg.append(dict(
                release_id=rid, season_year=e["season_year"], season=e["season"],
                publisher=e.get("publisher", "National Institute of Statistics of Rwanda"),
                source_url=e.get("source_url", ""), publication_date=e.get("publication_date", ""),
                landing_page=e.get("landing_page", ""), notes=e.get("notes", ""),
                raw_file=str(raw_path.relative_to(self.data_dir)).replace("\\", "/"),
                sha256=checksum, retrieved_or_imported_utc=_now(), tables_used=parsed.tables_used,
                sheet_overrides=e.get("sheet_overrides") or {},
                inputs_comparable=e.get("inputs_comparable", True),
                adapter_version=ADAPTER_VERSION, current=True,
                supersedes=(f"{prev_entry['sha256'][:12]}/"
                            f"{prev_entry.get('adapter_version', 'sas-adapter-1.0')}"
                            if prev_entry else None)))
            gate.warnings += [f"{rid}: {w}" for w in g.warnings]

        sid = f"snap-{_now().replace(':', '').replace('-', '')}-{rhash[:8]}"
        sdir = self.snap_dir / sid
        sdir.mkdir(parents=True, exist_ok=False)
        candidate.to_csv(sdir / "records.csv", index=False)
        label = ", ".join(sorted(new_ids)) if len(new_ids) <= 3 else f"{len(new_ids)} releases"
        manifest = dict(
            snapshot_id=sid, created_utc=_now(), parent_snapshot=self.active_id(),
            ruleset_version=RULESET_VERSION, records_sha256=rhash, n_records=len(candidate),
            releases=[r for r in reg if r.get("current", True)
                      and r["release_id"] in set(candidate["release_id"])],
            change=dict(release_ids=sorted(new_ids), kinds=kinds),
            gate=gate.as_dict(), approval={"status": "pending"})
        (sdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self._save_registry(reg)
        if approve:
            self._set_active(sid, f"approved at ingest of {label}")
            return RefreshResult("published", sid, f"{label} published as {sid}", gate)
        return RefreshResult("candidate", sid, f"{label} staged as candidate {sid}; approve to publish", gate)
