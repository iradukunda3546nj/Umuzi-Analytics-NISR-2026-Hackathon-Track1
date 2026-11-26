# AI Use Disclosure and Team Contributions

**Project:** Umuzi Analytics — NISR 2026 Big Data Hackathon, Agricultural Productivity Track  
**Purpose:** Transparent disclosure of AI assistance and the research, design, and engineering work directed by the team.

**In short:** the team designed the logic of the pipeline and the labelling rules. Claude Code (Anthropic) wrote the code, tests and draft documents following that logic. The team evaluated that the code follows the logic, refined the program files, and is accountable for everything the application claims.

## 1. How the project was conceived and directed by the team

The Umuzi Analytics team initiated the project by examining the practical challenges of agricultural productivity in Rwanda. Our reasoning focused on how conditions can differ across the country's 30 districts and how crop outcomes may be affected by seed and fertilizer use. We deliberately avoided assuming that a single input or intervention explains low yields everywhere.

Based on this problem framing, the team established the intended direction of the work:

- **Problem relevance:** Investigate geographically uneven or persistently low crop productivity, and distinguish observed shortfalls from their *unproven* causes.
- **Research objectives and hypotheses:** Examine district, crop, and season-level differences; investigate persistence and input-related patterns when supported by available data; and avoid interpreting correlation as causation.
- **Intended users and decisions:** Design a tool primarily for agricultural planners and district-level stakeholders to locate evidence-backed shortfalls, compare districts, understand data limitations, and identify questions to verify with agronomists or farmers before intervening.
- **Pipeline logic:** Define how the data should flow, from NISR workbooks to the app: find each table by its title, check every survey before it is used, store each version of the data, compare each district with the national average of the same survey, judge a pattern from the most recent surveys, and look at seed and fertilizer use only after a shortfall is found.
- **Engineering requirements:** Specify a reproducible data-to-decision workflow, a future-compatible process for incorporating newly published data, clear source traceability, and a usable desktop-style analytical interface.
- **Product and visual direction:** Define the Umuzi Analytics identity and request professional, restrained UI/UX, interactive geographic exploration, meaningful visual storytelling, transparent indicators, and no decorative or unsupported conclusions.

These contributions are **problem formulation, research direction, pipeline and rule design, product requirements, systems design, and prompt/specification engineering**.

## 2. AI tools used

- Claude Code (Anthropic)

## 3. What Claude Code contributed

Working from the team's logic and specifications, Claude Code:

- wrote the program code that implements the team's pipeline and rules (reading the NISR workbooks, quality checks, data versions, the labelling rules, the app and the Umuzi Assistant);
- wrote the automated tests;
- drafted the documentation (README, methodology, limitations, data inventory) and the slides;
- ran the analyses and checks the team asked for, such as the backtest and the recomputation of every quoted figure from the NISR source files.

The application itself uses no AI model. The Umuzi Assistant answers from fixed rules and the same data as the map, so it cannot invent a number.

## 4. Human review and project accountability

The team evaluated that the code follows the logic we gave, refined the program files, and decided what to keep. Each change is checked by the automated tests, and every figure we quote can be traced to its NISR table.

Our contribution is not measured only by the number of lines of code written manually. It includes identifying a relevant Rwandan agricultural decision problem, directing the research, designing the pipeline logic, translating that problem into technical and user requirements, reviewing the usefulness of the analytical outputs, and accepting responsibility for what the application claims.

## 5. Data and related documentation

Data and documentary sources are referenced in `README.md`, `data/README.md`, and `docs/data_inventory.md`. The research design, analysis scripts, tests, and the detailed team specification provide additional provenance for how the application was built.
