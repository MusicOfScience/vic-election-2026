# Historical validation source acquisition

## Current instruction: no VEC primary request required

No action is required from the project owner. The project must first exhaust:

1. the supplied canonical checkpoints;
2. public first-party VEC pages, reports and spreadsheets; and
3. original pollster or publisher records.

The public VEC harvest has closed the Assembly primary-result gap. Other historical components remain under first-party reconstruction. The processed coverage figures below describe audit-ready model rows; they are not a claim that the project owner failed to supply official material.

The decision and source findings are recorded in `metadata/historical-public-source-audit.json`. Request state is tracked in `metadata/historical-source-acquisition-plan.json`.

## VEC acquisition order

The existing project already incorporates substantial official VEC evidence, including a complete 340-row four-cycle boundary-aligned TPP benchmark.

Candidate-level Assembly primaries are complete for all four frozen cycles. The supplied 2010 VEC Report to Parliament and the official public 2014, 2018 and 2022 district pages yield 2,296 candidate rows across all 352 district-cycle contests, plus 1,760 reconciled five-family target rows. The separate 2022 Narracan supplementary election is included and reconciled. All 323 rows retained from the 39 indicative preference-distribution workbooks match the new complete 2022 extraction exactly.

The acquisition order is therefore:

1. retain the completed audit of the supplied 2010 official report;
2. retain the fingerprinted 267-source public manifest and reconciled 2014-2022 extraction;
3. treat election results as scoring-only outcomes, never as pre-election inputs;
4. keep unknown party labels fail-closed; and
5. do not contact the VEC for Assembly primary results because no residual gap remains.

## Historical polling acquisition order

The pinned `d-j-hirst/aus-polling-analyser` file is a quarantined 200-row lead list, not a model input. The repository owner is the GitHub account `d-j-hirst`; no verified personal name is asserted.

The acquisition order is:

1. search original pollster and publisher records for publication dates, sample sizes, methods and observation URLs;
2. record a source and reuse basis for each observation;
3. keep every unresolved row quarantined;
4. produce a residual provenance and licensing report; and
5. use the repository's GitHub Issues route only if material gaps remain.

## Retired fallback request — Victorian Electoral Commission

**Do not send for 2010-2022 Assembly primary results: the public harvest is complete.**

**Subject:** Request for residual machine-readable Victorian Legislative Assembly candidate results

Hello VEC team,

I am maintaining a reproducible, non-commercial research project examining Victorian state-election forecasting and historical model validation.

After reviewing our supplied records and the VEC's public result pages and downloads, we identified the attached residual gaps in candidate-level Legislative Assembly first-preference results for the 2010, 2014, 2018 and 2022 elections.

Could you please provide, or direct me to, machine-readable records covering those specific gaps? CSV, XLSX or XLS would be ideal. Required fields are the election and district, candidate name, party or independent status, first-preference votes, district formal-vote total, source revision metadata and applicable reuse terms.

If a complete bulk export exists, a link would also be very welcome.

Many thanks for your assistance.

## Deferred fallback request — polling repository owner

**Do not send unless first-party reconstruction leaves material gaps.**

**Subject:** Victorian historical polling data: residual provenance fields and reuse terms

Hello,

I am auditing the Victorian polling file in `d-j-hirst/aus-polling-analyser` at commit `a244da459807a22284d569b0b7e95ce79dfc53ff`, path `analysis/Data/poll-data-vic.csv`, for a reproducible non-commercial election-model validation project.

We have attempted to reconstruct the observations from original pollster and publisher sources. For the remaining unresolved records, could you please clarify whether publication dates, sample sizes, collection methods or observation-level citations are available, and whether the file may be copied and reused under declared terms?

Until those points are resolved, our project treats the file only as a lead list and imports zero rows.

Many thanks for maintaining the resource.

