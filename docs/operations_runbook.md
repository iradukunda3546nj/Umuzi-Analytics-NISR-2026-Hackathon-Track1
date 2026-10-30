# Operations Runbook

## Roles

| Role | Can do |
|---|---|
| Analyst | Download releases, run `ingest` (without `--approve`), review gate warnings |
| Approver (a second person where possible) | Run `approve` or `rollback`, commit the snapshot |
| Viewer | Use the app; no write access. The app has no upload or write functions. |

## Onboarding a new NISR release (for example SAS 2027 Season A)

1. Find the release page on statistics.gov.rw (Statistical publications > Agriculture and environment). Copy the URL of the "Tables" Excel file.
2. Add an entry to `data/sources.json` (`release_id`, `season_year`, `season`, `file`, `source_url`, `landing_page`).
3. `python -m scripts.download_sources`
4. `python -m scripts.refresh_data ingest --file data/incoming/nisr_sas/<file>.xlsx --release-id SAS-2027A --season-year 2027 --season A --source-url <url>`
5. Read the warnings. Compare the national maize yield with the figure in the NISR summary report.
6. `python -m scripts.run_analysis` against the candidate (temporarily approve, review, roll back if needed).
7. `python -m scripts.refresh_data approve --snapshot <id>`
8. `python -m pytest`. Real-data tests check invariants (coverage, checksums, consistency), so they should pass unchanged for a valid new release.
9. Commit `data/raw/`, `data/snapshots/`, `data/release_registry.json`, `reports/`. Push, which redeploys the app.

## Monitoring

- **Data and Methods** view: active snapshot, approval time, per-release gate status, warnings and missing releases.
- `python -m scripts.refresh_data status` gives the same from the command line.

## Failure recovery

| Symptom | Action |
|---|---|
| `ingest` reports `rejected at parse` | Open `data/quarantine/<...>/reason.json`. Usually a renamed table title or crop header: extend the pattern in `sas_adapter.py`, bump `ADAPTER_VERSION`, re-run. |
| `rejected by validation gates` | Read the listed errors. Do not loosen a gate to make a release pass without understanding why it failed. |
| A published snapshot is wrong | `python -m scripts.refresh_data rollback --snapshot <previous id>`, commit, investigate. |
| NISR corrects a published file | Ingest the corrected file under the same `release_id`; lineage is recorded automatically. |
| App shows "No approved data snapshot is active" | `ACTIVE.json` missing: run `status`, then `approve` the intended snapshot. |

## Provenance guarantees

Every record carries its source table; every snapshot carries its releases, checksums, adapter version, ruleset version, gates and approval record. Raw files are never edited.

## Access and privacy

Inputs are published aggregates (CC BY 4.0); there is no personal data. Student identity documents for the competition live only in the git-ignored `submission_private/` folder.
