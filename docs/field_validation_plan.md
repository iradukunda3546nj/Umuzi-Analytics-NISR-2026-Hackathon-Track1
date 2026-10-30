# Field Validation Plan

## Candidate pilot users
- Agronomists or Directors of Agriculture in 3 districts with different evidence profiles in Season A: one "persistent, low inputs" (for example Ruhango, maize and bean), one "persistent, inputs not low" (for example Ngororero, maize), one mostly "not below national" (for example Musanze). Contact through MINAGRI/RAB. Not yet contacted.
- One NISR agricultural statistics officer to review the use of district estimates.

## Questions for planners (30-minute session each)
1. How do you currently decide where to send field staff before a season? Which documents do you use?
2. Task (timed, with the NISR Excel files first, then the app): "List districts where maize Season A yield has been below national in every season since 2024."
3. Does the category for your district match your experience? Which part is wrong?
4. Is the "next step" something you could act on? What is missing?
5. Would you share the Evidence Brief with anyone? Who, and what would they need?
6. What would make you distrust this tool?

## Questions for field verification (per flagged district-crop pair)
Use the brief's field-check questions, plus: actual area and location of the crop; input availability and timing last season; soil test results if any; variety grown; any shock in the latest season.

## What success would mean
- Planners complete task 2 correctly and faster with the app than with the files (time both; report the actual numbers).
- In at least 3 of 5 field-checked pairs, agronomists judge the category plausible.
- No statement in 10 audited briefs fails to trace to a source cell.
- At least one planner says the brief would change where they look first. If none do, the value proposition is not supported and the product should change.

## Steps
1. Ethics and permission: confirm with MINAGRI/district whether a short staff interview needs approval. No farmer data is collected.
2. Two-week pilot after the next SAS release, ingesting it through the refresh pipeline in front of an NISR or MINAGRI data officer.
3. Record task times, errors and comments; publish a short results note, including negative results.

## Affordability and operations
- Hosting: free tier is enough for a pilot; an institutional deployment would need a government server or paid hosting.
- Maintenance: about half a day per SAS release (download, ingest, review, approve, commit). Requires a named data officer.
- Accountability: approver named in the runbook; every published snapshot records its approval time.
