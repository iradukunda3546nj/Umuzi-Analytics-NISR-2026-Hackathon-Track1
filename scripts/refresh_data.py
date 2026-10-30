"""Umuzi Analytics data refresh command.

Examples
--------
Ingest a new NISR SAS release as a candidate (not yet visible in the app):
    python -m scripts.refresh_data ingest --file "Tables_2027 Season A.xlsx" \
        --release-id SAS-2027A --season-year 2027 --season A --source-url <url>

Approve a candidate snapshot (makes it ACTIVE for the app):
    python -m scripts.refresh_data approve --snapshot snap-...

Roll back to an earlier approved snapshot:
    python -m scripts.refresh_data rollback --snapshot snap-...

Show the active snapshot, releases and warnings:
    python -m scripts.refresh_data status

Rebuild the store from data/sources.json (initial bootstrap):
    python -m scripts.refresh_data bootstrap --approve
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src import config
from src.services.snapshot_store import SnapshotStore


def _print_result(res) -> None:
    print(f"[{res.status}] {res.message}")
    if res.gate:
        for e in res.gate.errors:
            print(f"  ERROR   {e}")
        for w in res.gate.warnings:
            print(f"  WARNING {w}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="refresh_data", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", default=str(config.DATA_DIR))
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("ingest")
    i.add_argument("--source", default="sas", choices=["sas"])
    i.add_argument("--file", required=True)
    i.add_argument("--release-id", required=True)
    i.add_argument("--season-year", type=int, required=True)
    i.add_argument("--season", required=True, choices=["A", "B"])
    i.add_argument("--source-url", default="")
    i.add_argument("--publication-date", default="")
    i.add_argument("--approve", action="store_true",
                   help="publish immediately if all gates pass (analyst + approver in one step)")

    a = sub.add_parser("approve")
    a.add_argument("--snapshot", required=True)
    r = sub.add_parser("rollback")
    r.add_argument("--snapshot", required=True)
    sub.add_parser("status")
    b = sub.add_parser("bootstrap")
    b.add_argument("--approve", action="store_true")

    args = p.parse_args(argv)
    store = SnapshotStore(Path(args.data_dir))

    if args.cmd == "ingest":
        res = store.ingest(Path(args.file), args.release_id, args.season_year, args.season,
                           source_url=args.source_url, approve=args.approve,
                           publication_date=args.publication_date)
        _print_result(res)
        return 1 if res.status == "rejected" else 0
    if args.cmd == "approve":
        store.approve(args.snapshot)
        print(f"ACTIVE -> {args.snapshot}")
        return 0
    if args.cmd == "rollback":
        store.rollback(args.snapshot)
        print(f"ACTIVE rolled back -> {args.snapshot}")
        return 0
    if args.cmd == "status":
        sid = store.active_id()
        print(f"active snapshot: {sid}")
        if sid:
            _, m = store.load()
            for rel in m["releases"]:
                print(f"  {rel['release_id']}  sha256={rel['sha256'][:12]}  {rel['source_url']}")
            for w in m["gate"]["warnings"]:
                print(f"  warning: {w}")
        print(f"snapshots: {[s['snapshot_id'] for s in store.list_snapshots()]}")
        return 0
    if args.cmd == "bootstrap":
        sources = json.loads((Path(args.data_dir) / "sources.json").read_text(encoding="utf-8"))
        rc = 0
        for s in sources:
            res = store.ingest(Path(args.data_dir) / s["file"], s["release_id"], s["season_year"],
                               s["season"], source_url=s["source_url"], approve=args.approve,
                               publication_date=s.get("publication_date", ""))
            _print_result(res)
            rc |= res.status == "rejected"
        return rc
    return 2


if __name__ == "__main__":
    sys.exit(main())
