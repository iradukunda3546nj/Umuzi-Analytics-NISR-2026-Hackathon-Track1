# Problem Discovery

Date: 2026-10-29. Evidence levels: **[F]** verified fact from a cited document, **[O]** observation computed from NISR data in this repository, **[H]** hypothesis, **[U]** unverified lead.

## Policy context

- **[F]** NST2 (2024-2029) and PSTA 5 aim for "a 50% increase in productivity and more than 6% annual growth in agricultural GDP" (MINAGRI, *PSTA 5 Abridged version*, p.14).
- **[F]** The PSTA 5 results framework sets national yield targets for priority food crops, **measured by the NISR Seasonal Agricultural Survey (SAS)**. Examples: maize 1.7 MT/ha (baseline 2023) to 2.06 (2025/26) to 2.74 (2028/29); beans 0.6 to 0.9 to 1.1; Irish potato 8.2 to 10.1 to 14.7 (p.21). Smallholder improved-seed use: 35.9% to 50% (p.22).
- **[F]** PSTA 5 plans delivery through AgriHubs and Farm Service Centres (p.14 and following).
- **[F]** NISR publishes SAS district tables per season (Season A, Season B) as Excel files with about 27 crop columns by 30 districts per indicator (inspected releases 2024A, 2024B, 2025A, 2026A, 2026B).

## Candidate decision problems compared

### 1. Persistent district yield shortfalls: where to send field diagnosis first (SELECTED)
- **Stakeholder and decision.** District agronomists and Directors of Agriculture, with MINAGRI/RAB planning staff, decide each season which district-crop combinations get field diagnosis, extension attention or input-programme scrutiny.
- **Mechanism.** Symptom: a district yield below national. Possible causes: input access, soil acidity or fertility, erosion, unsuited varieties, water, agro-ecological marginality, survey noise. A persistent gap points to structural causes; a one-off dip points to a season shock. Misreading one as the other misdirects scarce agronomist time.
- **Scale.** District by crop by season, which is exactly the published SAS grain.
- **Evidence.** [O] National A+B yields for all 8 PSTA 5 priority crops were below their 2025/26 targets (52% to 97% of target). [O] 60 district-crop pairs sit below 0.9 x national in all three Season A releases, against 16.9 expected by chance (p = 0.0005).
- **Existing tools.** SAS PDF reports and Excel tables (one season per file). [F] Smart Nkunganire System (SNS) registers farmers for subsidised inputs and recommends quantities by land size and location ([MINAGRI news item](https://www.minagri.gov.rw/updates/news-details/smart-nkunganire-system-to-enhance-access-to-agriculture-inputs)). Neither compares district performance across seasons.
- **Gap.** No verified tool was found that classifies district-crop shortfalls by persistence and input context with source traceability. [U] Internal MINAGRI dashboards may exist; none was publicly verifiable.
- **Testability.** High: all inputs are published at district level.

### 2. Small-scale irrigation targeting
- SAS tables give irrigation technique shares **among irrigated plots** and water-source shares, not irrigable area, water availability or cost. A ranking would rest on proxies. **Rejected**: the evidence cannot support siting decisions.

### 3. Soil conservation and erosion prioritisation
- SAS gives the share of farmers protecting land against erosion (about 90% nationally in every release, [O]) and erosion severity shares. The near-universal adoption figure leaves little district variation to act on, and severity is plot-reported. **Kept as context**, not the core product.

### 4. Post-harvest storage and use of production
- "Use of production" is published nationally by crop, not by district ([O] 2026A Table 16). **Rejected**: wrong geographic grain for district planning.

### 5. District yield forecasting (ML)
- Three Season A and two Season B releases per district give too few time points for honest out-of-sample validation, and there are no validated rainfall covariates. **Rejected**: it would look sophisticated without being defensible.

## Decision matrix (1 = weak, 5 = strong)

| Criterion | 1 Persistent shortfall triage | 2 Irrigation | 3 Erosion | 4 Post-harvest | 5 Forecast |
|---|---|---|---|---|---|
| Decision utility | 5 | 4 | 3 | 3 | 3 |
| Original contribution | 4 | 3 | 2 | 2 | 3 |
| Evidence available at the right grain | 5 | 2 | 3 | 1 | 2 |
| Implementable by the deadline | 5 | 3 | 4 | 3 | 2 |
| Auditability | 5 | 2 | 4 | 3 | 2 |
| UX potential | 5 | 3 | 3 | 2 | 3 |
| **Total** | **29** | 17 | 19 | 14 | 15 |

## Who is excluded or disadvantaged

District averages hide sector and household variation. Crops grown on small areas (wheat, paddy rice outside marshland schemes) often fall under the coverage threshold and are reported as "insufficient evidence" rather than classified. Large-scale farms (LSF) are included in district totals; the app does not separate smallholder yields.
