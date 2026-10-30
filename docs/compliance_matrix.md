# Compliance Matrix - NISR 2026 Big Data Hackathon

Sources read in full on 2026-10-29:
- **[C]** `2026 Hackathon Competition.pdf` (5 pages, a web-page print of the competition announcement)
- **[W]** `2026 NISR Hackathon Webinar 2.pdf` (20 slides, "NISR 2026 Big Data Hackathon Submission Webinar")

Status key: **MET** (evidence in repository), **READY** (prepared; needs a team action), **TEAM** (only the team can do it), **FLAG** (needs a team decision).

| # | Requirement | Source | Status | Evidence / remaining action |
|---|---|---|---|---|
| 1 | Track 1, Agricultural Productivity: solution addressing a real agricultural challenge in Rwanda | [C] p.1 | MET | Persistent district yield shortfalls against PSTA 5 / NST2 productivity targets; `docs/problem_discovery.md` |
| 2 | Solution informed by NISR data, optionally with other open data on agriculture, food security or climate | [C] p.1 | MET | Five NISR SAS releases (2024A to 2026B); MINAGRI PSTA 5 targets; NISR-derived boundaries. `docs/data_inventory.md` |
| 3 | Tangible practical impact for farmers, planners or policymakers encouraged | [C] p.1 | MET (potential) | Planner workflow and exportable Evidence Brief; impact is **not yet measured** with users. `docs/field_validation_plan.md` |
| 4 | Undergraduate or master's students; student card or official document | [C] p.2 | TEAM | Both members must hold valid documents. Not verifiable by the software. |
| 5 | Team of 2 students, at least one Rwandan citizen | [C] p.2 | TEAM | Team composition is not recorded in this repository. Confirm before submission. |
| 6 | Any programming language | [C] p.3 | MET | Python 3, Streamlit |
| 7 | Submission: public GitHub link, deployed app link, documentation | [C] p.3; [W] p.16 | READY | Repository prepared locally (git initialised, not pushed). Deployment config ready; **no public URL exists yet**. Pushing and deploying need the team's accounts and explicit authorisation. |
| 8 | **IP assignment**: by entering, participants assign and transfer all IP rights in the submitted work to NISR, which may use, reproduce, modify, publish and distribute it for any purpose | [C] p.3 | **FLAG** | Both team members should read this clause before submitting. It covers the code, documents and demo in this repository. |
| 9 | Previous 1st to 3rd place winners not eligible | [C] p.3 | TEAM | Team to confirm. |
| 10 | Original work, not submitted elsewhere; all sources acknowledged in full | [C] p.3 | MET / TEAM | Sources cited in README, `data/README.md`, `docs/data_inventory.md`; the team must confirm originality and that the work was not submitted elsewhere. |
| 11 | AI tools allowed as assistants but **must be disclosed**; failure means disqualification | [C] p.3 | MET (draft) | `docs/AI_USE_DISCLOSURE.md`. The team must review, complete and keep it in the submission. |
| 12 | Registration deadline 20 October 2026, 11:59 PM | [C] p.3 | TEAM | Registration status unknown to this project. If the team did not register, it may be ineligible. |
| 13 | **Submission deadline 30 October 2026, 11:59 PM** | [C] p.3; [W] p.16 | READY | No timezone is stated in either PDF. Rwanda time (CAT, UTC+2) is the likely reading but is **not confirmed**; plan to submit well before then. |
| 14 | Evaluation: five criteria, 20 points each (problem relevance with NST2/Vision 2050; data use and methodology; tech innovation; usability and design; tangible impact) | [C] p.4 | MET | Mapping in `reports/submission_checklist.md` |
| 15 | Streamlit apps: deploy on Streamlit Community Cloud from a public GitHub repo with `app.py` and `requirements.txt` | [W] p.3-5 | READY | `app.py`, `requirements.txt`, `.streamlit/config.toml` present; `docs/deployment.md` |
| 16 | Free tier: about 2.7 GB memory; sleeps after 12 h idle | [W] p.4 | MET | App loads a 12,400-row snapshot and a 289 KB boundary file; memory use is small. Open the link shortly before the deadline ([W] p.15). |
| 17 | Test the link in a private window; open it shortly before the deadline | [W] p.15 | TEAM | After deployment. |
| 18 | Deployed app publicly accessible; if login is required, provide credentials | [W] p.16 | MET | No login. |
| 19 | Repo file 1: README explaining data used, what it communicates, how to interact | [W] p.17 | MET | `README.md` |
| 20 | Repo file 2: scripts that work on any machine | [W] p.17 | MET | `app.py`, `src/`, `scripts/`; tests pass locally (`pytest`: 38 passed). Clean-machine install not yet repeated on a second machine. |
| 21 | Repo file 3: video (.webm or .gif) demonstrating the UI, **3 minutes maximum**, not filmed with a phone | [W] p.17 | **TEAM** | Script in `demo/demo_script.md`. No recording exists yet; the team must record it. |
| 22 | Repo file 4: the data used and a link to it | [W] p.17 | MET | `data/raw/` (CC BY 4.0 permits redistribution) and source URLs in `data/sources.json`, `data/README.md` |
| 23 | Repo file 5: student cards or official documents for both members | [W] p.17-18 | **FLAG** | The webinar's example puts student cards in the public repository. Identity documents in a public repo are a privacy risk. They belong in the git-ignored `submission_private/`. Ask the organisers (prosper.ayinebyona@statistics.gov.rw, [C] p.5) whether redacted cards or a private channel are acceptable before publishing them. |
| 24 | Submission form | [W] p.16 | TEAM | `https://statistics.gov.rw/form/2026-hackathon-submission-form`. Not opened or submitted by this project. |

## Data licence compliance

NISR terms of use (https://statistics.gov.rw/terms-use, read 2026-10-29): NISR data and analysis are released under **CC BY 4.0** and may be copied, distributed and adapted provided integrity is respected and NISR is acknowledged. The app and README credit "National Institute of Statistics of Rwanda". Raw files are kept byte-identical (SHA-256 recorded).
