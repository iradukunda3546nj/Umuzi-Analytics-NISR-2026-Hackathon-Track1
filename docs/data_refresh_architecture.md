# Data Refresh Architecture

```
NISR release (xlsx)
   |  scripts/download_sources.py  or  analyst download
   v
data/incoming/                         (git-ignored staging area)
   |  python -m scripts.refresh_data ingest ...
   v
[1] checksum + idempotency check -----> same file, same adapter version -> "unchanged" (no-op)
   v
[2] source adapter (sas_adapter.py)    tables found by title; national-row labels normalised;
   |                                    0 and blank kept as "not reported"
   |-- parse error -------------------> data/quarantine/<time>_<release>/ + reason.json ; ACTIVE untouched
   v
[3] validation gates (gates.py)        districts, crops, metrics, national references, statuses,
   |                                    duplicates, production = yield x area, value ranges
   |-- any error ---------------------> quarantine ; ACTIVE untouched
   v
[4] candidate snapshot                 active records with this release added or replaced,
   |                                    records.csv + manifest.json (parent, ruleset, gates, lineage)
   v
[5] approval (explicit)                approve --snapshot <id>   (or --approve at ingest)
   v
data/snapshots/ACTIVE.json  -------->  app.py, scripts/run_analysis.py, briefs, exports
                                       (cache keyed by snapshot id, so a new approval invalidates caches)
```

## Properties (each covered by a test in `tests/test_pipeline.py`)

| Property | Mechanism | Test |
|---|---|---|
| New valid release flows to every view with no UI change | App derives releases, crops and latest release from the snapshot | `test_new_valid_release_updates_outputs_without_code_change` |
| Duplicate ingest is idempotent | Registry match on release, checksum and adapter version | `test_duplicate_ingest_is_idempotent` |
| Bad schema rejected; prior output survives | Parse and gate failures quarantine and return before any write | `test_bad_schema_is_rejected_and_active_snapshot_survives` |
| Late correction keeps lineage | Old registry entry marked `current: false`; new one records `supersedes`; both raw files kept | `test_late_correction_preserves_lineage_and_rollback` |
| Rollback | ACTIVE pointer moved to any earlier approved snapshot; nothing deleted | same |
| No silent publication | Candidates stay inactive until `approve` | `test_candidate_is_not_visible_until_approved` |
| Rule compatibility | Missing required metric blocks the release | `test_release_incompatible_with_decision_rules_is_blocked` |
| Views, tables and exports stay in sync | One snapshot, one set of functions; brief and CSV checked against the evidence table | `tests/test_real_data.py::test_brief_and_exports_match_evidence_table` |

## Re-processing after an adapter fix

The adapter carries a version (`ADAPTER_VERSION`). When parsing logic changes, re-running ingest on the same raw file produces a new snapshot marked `correction`, and the registry records which adapter version it superseded. This happened in practice on 2026-10-29: adapter 1.0 dropped national rows labelled "Total" or "S/Total"; 1.1 fixed this. The 1.0 snapshots are kept as history.

## What is automated, and what is not

| Step | Status |
|---|---|
| Download of known source URLs | Implemented as an analyst-run command (`download_sources`). Not scheduled. |
| Discovery of new NISR releases | **Not implemented.** NISR publishes on a page without a machine-readable feed; an analyst adds the new URL to `data/sources.json`. |
| Ingest, validation, quarantine | Implemented and tested. |
| Approval | Manual, by design. |
| Scheduled refresh | Not implemented. A scheduler (cron or CI) could run download, then ingest without `--approve`, then notify an approver. That is an extension point, not a delivered feature. |

## Deployment note

On Streamlit Community Cloud the file system is reset on redeploy, so the approved snapshot must be committed to the repository. The refresh workflow therefore runs on an analyst machine; committing the new snapshot and `ACTIVE.json` publishes it.
