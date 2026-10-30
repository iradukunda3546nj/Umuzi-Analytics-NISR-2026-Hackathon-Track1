"""Download the NISR SAS workbooks listed in data/sources.json into data/incoming/.

Each file is checked against the SHA-256 recorded in data/release_registry.json
when one exists, so a silently changed upstream file is reported, not ingested.

Run:  python -m scripts.download_sources
"""
from __future__ import annotations

import json
import sys
import urllib.request

from src.config import DATA_DIR
from src.services.snapshot_store import sha256_file


def main() -> int:
    sources = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    reg_path = DATA_DIR / "release_registry.json"
    registry = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else []
    known = {r["release_id"]: r["sha256"] for r in registry if r.get("current")}
    rc = 0
    for s in sources:
        dest = DATA_DIR / s["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {s['release_id']} ...")
        urllib.request.urlretrieve(s["source_url"], dest)
        digest = sha256_file(dest)
        expected = known.get(s["release_id"])
        if expected and digest != expected:
            print(f"  CHANGED upstream: {digest[:12]} != registered {expected[:12]}; "
                  "ingest it as a correction only after review")
            rc = 1
        else:
            print(f"  ok {digest[:12]}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
