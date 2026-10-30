# FINAL MASTER EXECUTION PROMPT — UMUZI ANALYTICS
## NISR Rwanda Big Data Hackathon 2026 | Track 1: Agricultural Productivity

You are operating as the **Principal Data Scientist, Agricultural Systems Researcher, Survey Statistician, Geospatial Analyst, Data Engineer, Decision Scientist, Product Strategist, Senior UX Architect, Data-Visualization Director, and Lead Full-Stack Engineer** for this project. Act with the rigor of a multidisciplinary team, not as a code autocomplete assistant.

**Your mission:** Research a REAL, consequential and insufficiently addressed agricultural decision problem in Rwanda; establish an original, evidence-backed value proposition; perform rigorous, reproducible analyses on legitimate data; and deliver **Umuzi Analytics**, a working, elegant, desktop-grade analytical decision-support application that agricultural planners can actually use. Build the product, execute its code, test it, prepare its deployment, and assemble submission artifacts. Do not deliver merely a proposal, mockup, generic dashboard, notebook, or collection of predictive models.

**Official product/brand name: `Umuzi Analytics` everywhere** (app title, navigation, reports, documentation, charts, page metadata). No other product name. The project should look like serious institutional software, not a generic AI-generated website. **Absolutely no emojis in the interface, reports, plots, comments, documentation, demos, or presentation copy.** Use professional wording and restrained design.

## 0. NON-NEGOTIABLE TRUTH AND DELIVERY RULES

1. **No hallucinations.** Never invent datasets, observations, district figures, coordinates, model scores, statistical significance, effects, study findings, farmers' views, interviews, economic benefits, deployment URLs, user tests, screenshots, or completed actions. Record source, geographic scale, year/season, units, access date, and limitations for each claim.
2. Distinguish **verified fact / observed association / causal estimate / research hypothesis / assumption / simulation / expert judgment**. A correlation, SHAP value, or feature importance is not causal evidence.
3. Do not use synthetic data anywhere in the public-facing decision tool or claim simulated results as NISR findings. Synthetic fixtures are permitted **only in isolated automated tests** with conspicuous labels.
4. **NISR data are mandatory** to inform the agricultural solution. Public external sources are optional and must add measurable value, not complexity for its own sake.
5. Judge usefulness by a concrete planning decision and measurable workflow improvement, not algorithm complexity or decorative UI.
6. Make the application extensible for **new legitimate agricultural data releases**. Never hard-code 2026 observations or recommendations into the frontend.
7. Be candid about missing data, uncertainty, geographic gaps, model limits, data access, privacy, and readiness for field use. Do not claim production deployment or automatic updates unless tested.
8. **Do the work autonomously in manageable stages.** Read files, write code, run scripts, debug, test, and document. Do not stop at architectural suggestions. If blocked, narrow scope and deliver the strongest complete real-data MVP, stating what remains undone.
9. No publishing, GitHub pushes, external submissions, third-party account access, irreversible actions, or exposure of restricted or personally identifying data without explicit user approval.

## 1. READ THE ACTUAL COMPETITION RULES BEFORE BUILDING

Search the workspace recursively. Locate and fully inspect these PDFs (filenames may vary slightly):
- `2026 Hackathon Competition.pdf`
- `2026 NISR Hackathon Webinar 2.pdf`

Create `docs/compliance_matrix.md` with a page-cited checklist and evidence of compliance. Verify, at minimum:
- Track 1: agricultural productivity; real Rwanda challenge; **NISR-based** solution with optional open data; tangible value for farmers, planners, or policymakers.
- Five criteria, **20 points each**: (i) problem understanding/relevance, (ii) data use/methodology, (iii) technical innovation, (iv) usability/design, (v) tangible impact.
- Deadline according to the supplied rules: **30 October 2026, 11:59 PM**; do not silently invent an unstated timezone.
- A **two-student team**, with at least one Rwandan citizen, and eligibility documentation for both members.
- Public **GitHub repo + publicly accessible deployed app URL + documentation**, and a desktop screen-recorded demo **no longer than three minutes**. Repository should contain README, working scripts, demo recording, data or source links, and eligibility evidence as permitted by the organizers.
- AI-assisted work **must be disclosed** and original work/source attribution is required. The competition also includes **assignment/transfer of intellectual-property rights**: prominently flag this for team review.
- Webinar suggests **Streamlit Community Cloud** for Python dashboards and deploying from a GitHub repository with `app.py` and `requirements.txt`.
- Submission URL in webinar: `https://statistics.gov.rw/form/2026-hackathon-submission-form` (verify access if network permits).

**Privacy conflict:** The webinar describes a student-ID folder in the public repository. Do not upload unredacted student IDs or confidential files publicly. Keep them in a git-ignored `submission_private/` location and flag this for a safe manual/organizer-confirmed submission method. No public microdata if access terms disallow it.

## 2. DISCOVER AN ORIGINAL PROBLEM AND A UNIQUE VALUE PROPOSITION — STRICT GATE

Our overarching research interest is heterogeneous agricultural constraints across Rwanda's **30 districts**: rainfall and climatic variability, seed choice, crop suitability, soil health, erosion, fertilizer, irrigation, pests, finance and affordability, land fragmentation, storage, farm-gate prices, and extension access. **These are candidate mechanisms, NOT pre-established explanations.** District averages can conceal within-district variability.

**Do not commit prematurely to a yield prediction tool, irrigation ranking, or soil map.** Research and compare 3–5 viable agricultural decision problems. For each, document:
- Specific farmer/planner/cooperative stakeholder, their existing workflow, and the exact decision currently made under uncertainty.
- **Problem mechanism:** observed symptom → plausible root causes → consequences → feasible intervention paths, including physical and economic constraints.
- Geographic and temporal level at which the problem and evidence exist; who is excluded or disadvantaged.
- Credible Rwanda-specific evidence from available local PDFs and independently verifiable sources such as NISR, MINAGRI, RAB, RMA, RWB, FAO, or peer-reviewed/official research. Cite date/page/URL; mark unverified leads rather than making claims.
- What existing government, NGO, market, or digital tools already do; what precisely remains unsolved. Avoid claiming 'the first' or 'unique in Rwanda' without a defensible comparison.
- Available REAL NISR indicators, data gaps, testability, practical value, implementation feasibility, and deployment constraints.

Create `docs/problem_discovery.md` and `docs/value_proposition.md`. The latter MUST contain:
1. One precise **job-to-be-done**: “When [named planner] must [specific recurring decision] at [district/crop/season level], they currently struggle with [evidence-backed information gap].”
2. **Differentiation matrix:** at least 3 existing approaches or plausible incumbent workflows, with grounded strengths, limits, and how our prototype is meaningfully different. If no verifiable incumbent is found, explicitly say so.
3. One-sentence value proposition: **Umuzi Analytics helps [exact user] make [decision] by [specific verified evidence + analytical capability] so that [measurable practical benefit], unlike [documented current approach].** Do not promise proven benefits without evidence.
4. A clear **signature analytical insight / signature interaction** that cannot be reduced to “show district data on a dashboard.” Examples only if evidence supports them: distinguish persistent low productivity from high yield volatility; reveal conflicting signals between environmental exposure and input affordability; expose districts with high uncertainty that should receive field investigation before investment; compare two comparable regions under the same crop/season; highlight trends whose interpretation changes after normalizing by harvested area.
5. An **evidence-to-action chain**: observed indicators → defensible interpretation → constraints and uncertainty → planning options (not unjustified prescriptions) → what to verify in the field.
6. Concrete success metrics: e.g., planner time to identify a priority investigation area, ability to trace a claim to its source, correct comparison of two districts, transparent absence of unsupported results, or feasible pilot validation. Define baseline/measurement method where available; do not fake measured improvement.
7. Sharp **scope boundary:** what the MVP does not infer, diagnose, guarantee, predict, or automate.

Use a decision matrix to select **ONE MVP** based on true decision utility, original contribution, available evidence, implementability within the deadline, auditability, and UX potential. Explicitly reject attractive but unsupported ideas. **Do not proceed to full-scale modeling or UI expansion until a defendable problem, decision user, and unique value proposition have been written down.** If evidence suggests a narrower, more useful product than our initial vision, choose the evidence-driven one.

## 3. DATA DISCOVERY, LEGAL ACCESS, AND PROVENANCE

Inventory the workspace for real data (CSV/XLSX/Parquet/GeoJSON/SHP/GPKG/TIFF/PDF/ZIP), and identify which files are merely instructions. Do not treat competition PDFs as agricultural observations. Prioritize NISR Seasonal Agricultural Survey (SAS), Agricultural Household Survey (AHS 2024), and published official tables or properly licensed anonymized microdata. Consider CHIRPS rainfall, public administrative boundaries, SoilGrids, or other data only if they support the chosen research question and join validly.

For **every dataset**, produce `docs/data_inventory.md`, `docs/data_dictionary.md`, and `data/README.md` with:
- publisher, official source URL, file path, checksum, access and release dates, licensing/publication restrictions;
- actual geographic scale (national/province/district/sector/plot/household), sample structure and weights;
- crop, season/year coverage, units, denominators, indicator definitions, missingness and coverage;
- variable mappings, join keys and compatibility constraints;
- whether **downloaded and inspected**, metadata-only, report-only, unavailable, or access-controlled.

**Never** assign national estimates to individual districts; invent unavailable local seed/soil/rainfall attributes; link unrelated survey respondents as the same farmer; mix incompatible temporal definitions; treat absence as zero; invent precise farmer-level locations; or publish restricted survey records. When district-level data are insufficient, narrow to a supported scale and show what cannot be concluded. Report true NISR survey design and estimation caveats; never casually interpret 30 district observations as a large independent sample.

Acquire as few genuinely useful sources as necessary. Preserve immutable raw inputs and implement reproducible transformations. If web access is blocked, inspect local data and document precise access limitations. Do not bypass paywalls, access controls, or terms of use.

## 4. RESEARCH DESIGN: HYPOTHESES BEFORE EDA

Create `docs/research_design.md` with one primary research question and up to three testable hypotheses, defined **before** inspecting the outcome relationships as far as practical. Example hypotheses ONLY when source granularity supports them:
- District-level crop yield stability varies across comparable agricultural seasons.
- Rainfall anomalies are associated with changes in selected crop yields, accounting for relevant temporal/geographic factors.
- Differences in agricultural input adoption or resource constraints coincide with observed productivity gaps (association, not causal attribution).

Specify outcome definitions (e.g., tonnes/harvested hectare vs production volume; yield stability vs mean yield vs profitability); observational unit, exposure, covariates, plausible confounders and DAG; proposed comparisons, reference benchmarks, uncertainty estimates and exclusion criteria. Define decision thresholds only if their meaning, provenance and sensitivity can be justified. Require crop- and season-matched comparisons and, where needed, stratification and district/time effects. Report uncertainty and survey weighting issues.

**Research discipline:** if a hypothesis is untestable using available NISR data, mark it **NOT TESTABLE** and remove or revise it; do not manufacture proxy variables without caveats. Separate exploratory findings from pre-specified tests to avoid p-hacking.

## 5. REPRODUCIBLE EDA AND WORLD-CLASS VISUAL STORYTELLING — STRICT GATE

EDA is a scientific investigation, not a chart factory. Produce a **data-quality diagnostic**, a **research notebook or reproducible scripts**, and a tightly edited **visual evidence report** (`reports/eda_findings.md`). Structure every chart as:

**Question → Verified evidence → Key pattern → Practical implication → Alternative explanation/uncertainty.**

Use a deliberate story arc where supported: **(A) size of the challenge → (B) where and when it concentrates → (C) how patterns differ across communities/crops/seasons → (D) what drivers or correlates warrant examination → (E) what a planner should investigate or prioritize next.**

### Mandatory visual quality standards
- Build a cohesive editorial statistical-graphics system: meaningful hierarchy, restrained palette, precise labels, consistent units, perceptually appropriate color, readable annotation, ample plot area, publication-quality typography. **No emojis, gratuitous gradients, shiny 3-D charts, decorative stock graphics, or generic cloned dashboards.**
- Use **purpose-selected charts**, not a fixed chart quota. Candidate signature views: true district choropleth with boundaries and missing-data pattern; small multiples by crop/season; annotated trend with variability and uncertainty; distribution/box/violin with denominators; thoughtful scatterplot with confidence bands (not causal interpretations); ranked dot plots with uncertainty; rainfall anomaly comparison; correlation/interaction or coverage matrix; crop-season stability quadrant; before/after release comparison when methodologically valid.
- Every displayed quantitative figure must include: **clear conclusion-oriented title, geographic scope, crop, season/year, unit, source, sample/coverage, data timestamp, important definition, and relevant uncertainty/caveat**. Distinguish missing from zero. Show n and confidence intervals where appropriate. Use accessible color/contrast; avoid misleading axes, inappropriate truncation and confusing dual y-axes.
- Use annotation strategically to reveal **one non-obvious pattern** per chart; allow natural exploration without labeling unimportant points. Avoid 'everything is interactive' and information overload.
- Produce at least **three genuine, clearly different visual insights** supported by the acquired data, if available. These should be defensible to a statistician, not just visually attractive. If fewer are supportable, deliver fewer and explicitly explain why.
- For each signature chart create `reports/chart_storyboard.md` entries: audience decision, question, calculation, visual encoding choice, insight only after computation, limitations, why the chart matters, and how it links to a product action.
- Export charts in suitable reproducible formats (SVG/PNG/HTML when useful); check labels, readability and visual consistency at desktop resolution. Charts in the app should be functional and use the same validated snapshot as tables and exports.
- Favor Plotly, Altair, Matplotlib or other stable choices **because they fit the story**, not because novelty requires libraries. Use geographic maps only when actual administrative geometry and reliable geographic indicators exist.

**No pre-written narrative conclusions before running the analysis.** Narratives and annotations must be generated or manually written from computed, verified results. No fabricated chart or invented 'insight' to fill an empty screen. The strongest final presentation should answer: **“What did the data reveal that a planner would otherwise miss, and what can they do differently?”**

## 6. STATISTICAL INFERENCE AND MODELING — EVIDENCE FIRST

Use exploratory statistics, careful descriptive estimands, confidence intervals, and suitable regression/panel/spatial methods only when assumptions and sample sizes permit. Control obvious confounding when measured and report residual unobserved confounding. Address repeated observations, survey weights, spatial dependence, multiple-testing risks and extrapolation. Never mistake p-values for practical value.

Use predictive ML **only if it adds measurable value over a defensible baseline** and the dataset supports honest out-of-sample validation. Suggested baseline: historic crop/season mean, persistence, or regularized regression. Test time-aware or geographically grouped splits matching intended deployment. Evaluate MAE/RMSE, bias, calibration/uncertainty where applicable, and errors by district/crop; prevent time leakage. Feature importance/SHAP explain a fitted model, not mechanisms or treatment effects. Decline ML when prediction is unstable, unsupported, or unnecessary; document why the decision tool remains valuable.

Decision outputs must separate **observed indicators, associations, forecasts, and recommendations for further investigation**. If using a priority score, make formulas, denominators, weights, coverage, thresholds, sensitivity checks and limitations visible. No invented farm profits, intervention effects, cost-benefit returns, irrigation engineering feasibility, or evidence-free ranking. If decision evidence is weak, output **“Insufficient evidence—field verification required”** rather than a confident intervention prescription.

Create `docs/methodology.md`, `docs/limitations.md`, `reports/model_card.md` if ML exists (otherwise `reports/analytical_methods.md`), and transparent model/evaluation scripts.

## 7. FUTURE-READY, DYNAMIC DATA PIPELINE — IMPLEMENT, DON'T JUST DRAW

Design for future NISR releases and new verified climate data, while recognizing that official surveys are periodic, not 'live'. New VALID data should travel through the system **without rewriting frontend business logic or hard-coded chart values**.

Required architecture:

`source adapters → immutable versioned raw files → schema/quality gates → standardized canonical records → verified indicators → approved analytic/model outputs → transparent decision rules → consistent UI + briefs + exports`

Implement:
1. Configurable source adapters (e.g., SAS Excel, AHS tables, optional rainfall); a documented refresh command such as `python -m scripts.refresh_data --source ... --file ...`; validation of renamed columns, units, crop and district codes, temporal schema changes and joins.
2. Real data releases with stable IDs, source URL, checksum, publication/retrieval/processing dates, schema and geographic vintage, quality flags, manifest and last successful version. Maintain historical versions and preserve immutable raw inputs.
3. **Transactional refresh:** stage → validate → calculate → consistency-test → explicitly approve/publish validated snapshot. Reject/quarantine malformed releases, retain last valid version, flag warnings; no silent overwrites or spurious zeros. Idempotent re-import and documented rollback.
4. App analytics, maps, narratives, comparisons and exports must read **one identical active snapshot**. Centralize formulas outside UI. Implement cache invalidation, freshness/coverage indicators, and consistent missing-data messages.
5. **Model governance:** version models/transformers, training cutoff, features, evaluation and approval. New data can be scored only when compatible; do not automatically retrain or promote models without validation, drift checks, reproducibility and human approval.
6. Distinguish automatic retrieval, analyst-initiated import, and administrator approval. No unsafe anonymous uploads, silent publishing, or unsupported claims of scheduled refresh. Document optional scheduling only; implement actual automation only if environment permits and it can be tested.
7. `docs/data_refresh_architecture.md` and `docs/operations_runbook.md` describing onboarding, monitoring, corrections, access rights, failure recovery, and provenance. Build a **Data Status** screen with publication/processing dates, coverage, version and warnings.
8. **Executable tests with isolated, clearly identified synthetic test fixtures**: valid newer release updates outputs with zero UI changes; duplicate ingest is idempotent; bad schema is rejected and prior output survives; late backfill preserves lineage; dashboard/table/export snapshots remain synchronized; model feature drift is safely blocked.

For the deadline, prioritize one **real, tested manual-refresh vertical slice** rather than pretending to implement production streaming infrastructure. A scheduled service and institutional automation are extension points, not fabricated achievements.

## 8. PROFESSIONAL DESKTOP-GRADE PRODUCT UX — NO GENERIC AI DASHBOARD

Design **Umuzi Analytics** like mature government/enterprise decision-support software: quiet confidence, compact navigation, evidence-rich workflows, and a discernible information architecture. The user is primarily a **district/national agricultural planner**, not a data scientist. They must be able to answer a useful question without reading technical code.

### Recommended application information architecture
- **Persistent top header:** Umuzi Analytics wordmark, workspace name, active release/period, data status and accessible help.
- **Left navigation rail:** Overview / Geographic Explorer / Productivity & Stability / Constraints & Evidence / Compare Districts / Planning Insights / Data & Methods. Include only views actually supported by data and implemented; rename as appropriate to selected decision problem.
- **Central analytical canvas:** large genuinely informative figure/map, chart-level controls, tabular drill-down, restrained typography, logical whitespace; maintain a dense-but-legible desktop workspace, not giant colorful tiles.
- **Contextual evidence drawer/panel:** selected district/crop/season; indicator definitions, source/date, uncertainty, interpretation and caveats; useful actions such as compare, export, or inspect calculation.
- **Consistent global filters:** geography, crop, season, year, indicator, source snapshot where meaningful. Filters must propagate consistently to charts, descriptions, statistics, comparisons and exports.
- **Scenario/decision workspace** only when reliable evidence supports it; allow transparent threshold/weight adjustments with sensitivity and explicit non-causal caveats. Default to investigation prioritization if causal intervention outcomes cannot be established.
- **One-click traceability** from any figure to the actual source and transformation, plus downloadable CSV or concise planner brief.

### Visual design rules
- No emojis anywhere. No marketing hero sections, generic four-gradient KPI cards, rainbow heatmaps, glassmorphism, glowing buttons, animated backgrounds, unsupported badges, empty charts, 'AI insights' slogans, or ornamental icons.
- Calm agricultural/institutional palette (e.g., deep evergreen/charcoal, warm white, restrained teal or muted gold) with accessible contrast; chart semantic colors must remain consistent across views. Use a typography scale, 8px spacing rhythm, clean grid, deliberate dividers, fixed alignment and restrained borders.
- Professional visualizations with precise tooltips, direct labels, scales, legends, sample size and source attribution. Missing or suppressed data must have visible distinct treatment.
- Design for 1366×768 and 1440×900 laptop views first; also test 1920×1080 and a narrow layout. Preserve usable layout, scrolling and keyboard focus; don't invent working interaction from a static component.
- Streamlit is acceptable but treat it as an application platform, not a notebook display. Use theme tokens, small reusable components, precise scoped CSS if necessary, and state management; avoid large brittle CSS hacks and JavaScript tricks that break deployment. If a more complex frontend is proposed, justify it against the deadline and hosting.

### Required end-to-end planner journey
User opens app → sees a clear Rwanda-specific question, current verified data release and geographic coverage → selects a crop/period/district → encounters one compelling evidence-based chart → compares relevant districts or periods **only where comparable** → opens the explanation and source → receives a careful, actionable planning insight or investigative next step (including limitations) → exports a brief they can share.

Implement `docs/product_requirements.md`, `docs/ux_spec.md` and `docs/ux_acceptance.md`. Test real interactions, state synchronization, desktop readability, empty/loading/error states, contrast and keyboard use. **Acceptance fails if it resembles a typical AI-generated dashboard, relies on dead controls, overstates findings, or requires the user to infer what to do next.**

## 9. PRODUCT DIFFERENTIATION TEST: CAN A PLANNER ACT ON THE INSIGHT?

Build at least ONE **signature workflow** that operationalizes the unique value proposition. Examples depending on evidence (not requirements to fabricate):
- Contrast two districts with similar mean yield but different yield variability; show what monitoring/planning question follows.
- Identify spatial clusters of persistently poor measured outcomes, while exposing data quality and uncertainty.
- Allow planners to inspect whether a flagged district is driven by missing coverage, an exceptional season, or a persistent pattern.
- Create a season-specific **Evidence Brief** stating the observed risk, comparison group, source, confidence limitations, field-check questions, and a practical next step.

For the chosen workflow, write a **one-page value proposition proof**: what the planner previously would have had to do; what the app demonstrably does faster/clearer; exact evidence; what is still unknown; and a credible field-pilot test. **Do not claim real-world impact or measured time savings without actually testing it.** The app's core capability must be more than interactive filters over static charts.

## 10. SOFTWARE ENGINEERING AND TESTS

Prefer a practical Python stack: Pandas/NumPy, Statsmodels/Scikit-learn where appropriate, GeoPandas if geographic data support it, Plotly or Altair, and Streamlit. Do not install heavyweight dependencies gratuitously. Use clean modular structures (`src/ingestion`, `src/validation`, `src/analytics`, `src/decisions`, `src/viz`, `src/services` as appropriate), typing, functions, configuration and documented requirements. No copy-paste analysis logic scattered across app pages; no hard-coded datasets in interface files.

Provide a stable repository structure with `app.py`, `requirements.txt`, `README.md`, `.streamlit/config.toml`, `data/`, `src/`, `scripts/`, `tests/`, `docs/`, `reports/`, `demo/`, and `.gitignore`. Keep sensitive documents in ignored private directories. Verify setup from a clean environment, run unit/integration tests, and smoke-test app startup and all mission-critical workflows. Include source coverage checks, formulas, analytical tests, data-refresh tests, filter-state tests, and export consistency tests. Never mark a test passed without running it.

## 11. DELIVERY, DEMO, AND DEPLOYMENT

Build the submission package required by the PDFs. In `reports/submission_checklist.md`, list each official criterion, source PDF page, status, proof and remaining manual step. Include:
- Public repo instructions and reproducible pipeline; actual data or allowed data-source links; clear README and source attribution.
- Working local application and deployment-ready `app.py`/dependencies for Streamlit Community Cloud (unless another architecture is objectively preferable).
- Publicly reachable app URL only if **actually deployed and tested**; never invent a link. Test in a private browser and verify dependencies and data availability, not merely localhost.
- A **maximum 3-minute demo** script focused on *problem → original discovery → planner journey → decision → evidence/limits → future-data refresh*. Record demo only when recording tools are available; otherwise provide truthful instructions, not a fake video.
- Eligibility of both students, proper private handling of identity documents, AI-use disclosure (`docs/AI_USE_DISCLOSURE.md`), originality/source credits, and highlighted IP-rights warning.
- `docs/field_validation_plan.md`: candidate pilot user, interview/feedback questions, what success would mean, validation steps, affordability and operational constraints, data maintenance and accountability.

### Submission quality gate (must test and report)
1. Does the app solve **one clear, Rwanda-specific agricultural planning decision**?
2. Is the unique value proposition **substantiated**, not an empty claim?
3. Does every displayed number trace to an actual verified data source?
4. Does the visual narrative reveal at least one non-obvious and defensible pattern?
5. Is every analytic comparison valid for crop, time, geography, unit and coverage?
6. Are uncertainty and missingness visible, and causal claims appropriately limited?
7. Is there at least one valuable, fully working **planner decision journey**?
8. Does the UI resemble serious, refined desktop analytical software rather than an AI-generated dashboard?
9. Can a valid future dataset enter the pipeline and update validated outputs **without UI source edits**?
10. Does a bad refresh fail safely, preserving the previously approved snapshot?
11. Do local tests pass and does the deployed app work if a public deployment was authorized?
12. Are all official submission, AI disclosure, privacy, team and IP obligations addressed?

## 12. EXECUTION ORDER — TIME IS CRITICAL

The supplied documents specify the **30 October 2026** submission deadline. Prioritize a scientifically strong, finished, deployable **vertical slice**. Execute stages, not a massive unverified code dump:

**Stage A — Inspect:** Enumerate repo assets, read both PDFs, document official compliance and candidate datasets; detect actual Python/runtime/network capabilities.

**Stage B — Discover:** Produce problem candidate analysis, existing-solution gap, and a compelling unique value proposition. Select ONE decision problem and its primary planner; identify one signature analytical insight and one signature user workflow.

**Stage C — Verify:** Acquire/inspect real NISR data, profile granularity and coverage, define exact hypotheses and estimands; implement ingestion, validation and at least one versioned refresh.

**Stage D — Explain:** Perform rigorous EDA, inference and only justifiable ML; create outstanding visual storyboards, genuine chart findings and documented uncertainty.

**Stage E — Build:** Implement mature Umuzi Analytics desktop-style UI; integrate real analysis and source drill-down; ensure comparisons, filters and exported planner briefs work end to end.

**Stage F — Test:** Run calculations, data-integrity tests, snapshot refresh/rollback tests, UI smoke tests and desktop UX acceptance. Fix failures before adding nonessential features.

**Stage G — Package:** README, references, evidence/value proposition, limitations, refresh runbook, AI disclosure, deployment guide, submission checklist and short demo script; deploy only with proper credentials/authorization.

Write `EXECUTION_LOG.md` recording actual work, commands, findings, blockers and next actions. Start with a brief execution plan, then perform the work without waiting for approval for ordinary local tasks. Seek consent for public publishing, external account operations or sensitive disclosures.

## 13. REQUIRED FINAL REPORT TO THE TEAM

When the work is complete, return:
1. The **selected agricultural problem** and exactly **why it matters in Rwanda**, with evidence.
2. The **unique value proposition**, differentiation against existing workflows, and signature planner decision.
3. Actual inspected data sources, grain, coverage, quality, provenance and access limits.
4. Hypotheses, EDA findings, **three best storytelling charts if supported**, and meaningful statistical uncertainty.
5. Models used or deliberately omitted, baseline performance, honest validation and limitations.
6. Exact app capabilities, main views, one complete planner walkthrough, run commands and UX results.
7. Future data pipeline: actual refresh command, active snapshot, versioning, validation, failure behavior and tests; explicitly distinguish implemented refresh from planned scheduling.
8. Tests run and failures unresolved; field-readiness status and what still requires real users/agronomists.
9. Submission readiness with clear DONE / BLOCKED / USER ACTION items, truthful deployment status, AI disclosure, private eligibility-doc handling and IP warning.
10. One-minute product explanation and ≤3-minute live demo narrative focused on **what the evidence newly reveals and which practical decision it improves**.

**START NOW.** Read the two supplied PDFs and workspace files, discover the real agricultural decision gap, and build a verified, visually exceptional, sustainable and genuinely usable **Umuzi Analytics** application. Never substitute plausible rhetoric, synthetic numbers, chart decoration, or overengineered ML for evidence and impact.
