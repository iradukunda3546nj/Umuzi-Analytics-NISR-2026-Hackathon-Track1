# Submission Checklist

Deadline: **30 October 2026, 11:59 PM** ([C] p.3; no timezone stated).
[C] = `2026 Hackathon Competition.pdf`, [W] = `2026 NISR Hackathon Webinar 2.pdf` (organiser documents, kept locally in `residuals/`, not published).

## Evaluation criteria ([C] p.4, 20 points each)

| Criterion | Proof in this repository | Status |
|---|---|---|
| 1. Problem understanding and relevance (NST2 / Vision 2050) | PSTA 5 / NST2 50% productivity target and SAS-measured yield targets (cited pages); `docs/problem_discovery.md`, `docs/value_proposition.md` | Done |
| 2. Data use and methodology | 5 NISR releases harvested and validated; title-based adapter; zero vs missing handling; pre-specified tests with permutation p-values and Holm correction; sensitivity analysis; `docs/methodology.md`, `reports/eda_findings.md` | Done |
| 3. Tech innovation | Versioned, gated, rollback-capable refresh pipeline; evidence-category engine; reproducible charts; ML deliberately not used, with reasons (`reports/analytical_methods.md`) | Done |
| 4. Usability and design | 8 views, evidence panel, exportable brief, validated palette; `docs/ux_acceptance.md` (one open narrow-width issue) | Done (developer-tested only) |
| 5. Tangible impact | Planner workflow and brief; field validation plan. **Impact not yet measured.** | Plan ready |

## Repository requirements ([W] p.17-18)

| Item | Status | Action |
|---|---|---|
| README | Done | Add the deployed URL after deployment |
| Scripts that work on any machine | Done locally (38 tests pass) | Optional: repeat install on a second machine |
| Video (.webm/.gif, at most 3 min, not a phone) | **TEAM** | Record from `demo/demo_script.md`; save as `demo/demo.webm` |
| Data and link | Done | - |
| Student cards for both members | **TEAM / FLAG** | Keep in `submission_private/` (git-ignored). Ask organisers before publishing ID documents publicly |

## Submission steps (all need the team's accounts and authorisation)

| Step | Status |
|---|---|
| Review `docs/AI_USE_DISCLOSURE.md` and complete the TEAM sections | USER ACTION |
| Both members read the IP assignment clause ([C] p.3) | USER ACTION |
| Confirm eligibility: 2 students, at least one Rwandan citizen, registered by 20 October | USER ACTION |
| Create public GitHub repo and push (`docs/deployment.md`) | USER ACTION (needs authorisation) |
| Deploy on Streamlit Community Cloud; test in a private window | USER ACTION |
| Record and add the demo video | USER ACTION |
| Submit at https://statistics.gov.rw/form/2026-hackathon-submission-form | USER ACTION |
| Open the app shortly before the deadline so it is awake | USER ACTION |

## Quality gate ([spec] section 11)

| # | Question | Answer |
|---|---|---|
| 1 | One clear Rwanda-specific planning decision? | Yes: which district-crop gaps to diagnose first, and for which constraint |
| 2 | Value proposition substantiated? | Evidence-backed insight (persistence, input context); user value not yet tested |
| 3 | Every number traceable? | Yes: snapshot, release, table; spot-checked by tests |
| 4 | Non-obvious, defensible pattern? | Yes: persistent maize shortfalls mostly not input-poor |
| 5 | Comparisons valid for crop, time, geography, unit, coverage? | Same crop, season type and release; coverage flag; seasons never pooled |
| 6 | Uncertainty and missingness visible; causal claims limited? | Yes |
| 7 | Working planner journey? | Yes: scope, map, persistence, input context, brief, export |
| 8 | Serious desktop software look? | Developer judgement: yes; needs external review |
| 9 | Future data without UI edits? | Yes (tested with synthetic release) |
| 10 | Bad refresh fails safely? | Yes (tested) |
| 11 | Local tests pass; deployed app works? | Local: 38/38. Deployment: not done |
| 12 | Submission, AI, privacy, team, IP obligations addressed? | Documented; team actions outstanding |
