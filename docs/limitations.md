# What the app cannot tell you

1. **Yields are what farmers report.** NISR measures plot areas with GPS but takes harvest amounts from
   the farmer (SAS Season B 2026 main report, p.20). Some district differences may come from how people
   report, not from what they harvested.
2. **No margin of error for districts.** NISR publishes margins of error only for national crop areas
   (report Table 5, p.17), not for yields and not for districts. The 500 ha rule and the "2 of the last 3
   surveys" rule are safeguards, not confidence intervals. Small differences, a few percent, should not be
   read as real.
3. **Small crops rest on few farmers.** A crop grown on a few hundred hectares in a district may appear on
   only a handful of sampled plots (see `docs/methodology.md`, section 4). The app labels these "too
   uncertain to judge" instead of hiding them.
4. **The same land may be surveyed again.** The reports do not say whether the same sample squares are
   revisited each season. If they are, the strong season-to-season consistency partly reflects the same
   plots being measured again.
5. **Usable history starts in 2018, and the early years compare poorly.** The 2015-2017 tables give no district
   yields, and for 2014 only a PDF report was found. District rankings in 2018 and 2019 agree only weakly with later years, so labels use the last 3
   surveys. Season B 2025 is missing, so the Season B window is 2023, 2024 and 2026. Input figures for 2018
   are counted per plot instead of per farmer and are not used.
6. **Seed and fertilizer use cover all crops.** The district figure is the share of farmers using the input
   on any crop. A district can use plenty of fertilizer overall and little on maize.
7. **Patterns, not causes.** Low input use alongside low yields does not prove that more inputs would help.
   Altitude, rainfall, soils and where programmes were targeted all play a part. Nothing here estimates
   what an intervention would change.
8. **"Below the national average" is not "below what is possible".** A crop grown outside its best zone
   (for example Irish potato in the eastern lowlands) can look short every season without being fixable
   or worth fixing.
9. **District averages hide differences inside the district.** Sectors, households, women and men, and
   small and large farms are not visible. NISR's district yields combine small and large farms, so a few
   large commercial farms can raise a district's average.
10. **The 90% line matters.** Moving it to 80% or 95% changes 17% to 23% of maize Season A labels and up
    to 30% of maize Season B labels. The 500 ha line matters less for maize and beans, but for Irish potato
    lowering it to 200 ha changes 23% of labels (`reports/analysis_results.json`, "sensitivity").
11. **The goal comparison is approximate.** PSTA 5 does not state exactly how it combines seasons, and
    Season C is left out.
12. **Map boundaries are for display.** They come from geoBoundaries (2012, from NISR data). District names
    match the survey tables exactly.
13. **Not yet tested with users or experts.** No planner, agronomist or farmer has used the app yet, and no
    agronomist has reviewed the thresholds or the field checklists.
14. **Updates are manual.** A new survey must be downloaded and approved by an analyst; nothing runs on a
    schedule.
