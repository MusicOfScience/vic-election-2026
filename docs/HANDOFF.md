# Project handoff

Updated: 2026-10-08

## Current state

- Base main includes merged PR #124, HEAD `485421f69251809e849436a7e69211a3e42cf93f`. September Freshwater admission, deterministic refresh and shallow-CI baseline repair are merged. PR #121's community-resilience challenger remains deferred.
- Historical counters are runnable 4/4, predicted 4/4, scored 4/4, certifying predicted 3/4 and certifying scored 3/4.
- Certifying v2 cycles are `vic_la_2010`, `vic_la_2014` and `vic_la_2022`. `vic_la_2018` remains non-certifying: v1 implementation defect; v2 post-hoc diagnostic.
- The canonical aggregate is [`historical-certifying-v2-aggregate.json`](../model/data/validation/historical-replays/historical-certifying-v2-aggregate.json), SHA `7680fa6111c01665b24c6fe16bca6ab6d67f9aa4697c8294de1be33d0a4c972e`. Its unweighted three-cycle means are winner accuracy `0.8404301637`, multiclass Brier `0.2193372181`, multiclass log loss `1.0486418097` and district primary MAE `4.7557257435`.
- Complete backtest remains `closed-incomplete-certifying-four-cycle-protocol`; probability calibration remains `closed-incomplete-cycle-clustered-protocol`; production authorisation remains closed.

## Immutable scoring evidence

- 2010 score: [`vic_la_2010-v2-score.json`](../model/data/validation/historical-replays/vic_la_2010-v2-score.json), embedded score SHA `6503d74c2306f8bc08dae6e76f3b055a1c19f477e0b432119cbc820360d0e1b0`. Official VEC final-pair artefact SHA `00533f13f92713e28f30e173a12a786b7113cc02fb00301273e541ea4b74d9fd`; 88 districts, 44 final pairs available and 44 unavailable. Winner accuracy 86.36%, district primary MAE 3.91pp, Brier 0.16798, log loss 0.24398, final-pair accuracy 88.64%. Canonical Council regional MAE is `0.27911458333333333`.
- 2014 score SHA `e96125d51b4b85a365fb457148a0cee411f576c1d09f71b225fd7284175e4bae`; 2022 score SHA `3bc3b150a5a410bbda2c18e679ed0ae03c555a24d7f3b98a1b0e111c22abdb4e`.
- 2018 v1 remains an immutable negative implementation result, and its v2 output remains diagnostic only. No historical score was rewritten or tuned.

## Release-gate classification

The machine-readable classification is [`metadata/prod-1.0-closure-audit.json`](../metadata/prod-1.0-closure-audit.json). Generated readiness passes 6/9 gates: source integrity, critical-source freshness, model-input freshness, deterministic outputs, historical data readiness and candidate evidence. Complete backtest and probability calibration remain structurally blocked under the current protocol. Production authorisation remains downstream blocked.

Release readiness is assessed as of 2026-10-08. The owner-approved September Freshwater poll has a real fieldwork effective date of 28 September, ten days old against the unchanged 21-day policy. Poll and model effective dates advance because evidence was admitted and the forecast was regenerated.

## Current 2026 evidence decision

The owner accepts `redbridge-accent-vic-2026-09-14-primary` as evidence and explicitly holds model eligibility pending documented sample-family independence. Publication remains 15 September, fieldwork 1–14 September, full N=2,371, effective N=2,009 and voting-intention base N=2,160. It remains absent from canonical inputs; cross-tabs and alternative final pairs are supporting material within that one wave.

The original review packet is preserved in [`CURRENT_EVIDENCE_2026-10-08.md`](CURRENT_EVIDENCE_2026-10-08.md); its machine-readable packet now links the owner resolution. The owner accepts and admits exactly one September Freshwater observation, retaining exact workbook composition and full N=1,030, primary base N=977 and TPP base N=956. Poll publication is 1 October; first-party table release is 2 October. Freshwater remains the same pollster/source family. DemosAU and Resolve September remain explicit evidence/model holds with their existing blockers. Canonical events increase 13→14; eligible polls increase 12→13.

The deterministic refresh retains seed `20260826`, 5,000 simulations and every model coefficient, while advancing the assessment date from 26 August to 8 October. [`FORECAST_REFRESH_2026-10-08.md`](FORECAST_REFRESH_2026-10-08.md) and [`metadata/forecast-refresh-2026-10-08.json`](../metadata/forecast-refresh-2026-10-08.json) report every statewide/chamber change and all district deltas. No district crosses the declared five-percentage-point material-change threshold; no likely final pair changes. The August shadow remains pinned to 26 August and its original evidence IDs.

## Deferred research challenger

PR #121 records Kos Samaras' 1 October 2026 resilience argument as dependency-labelled analyst evidence and adds the specification [`COMMUNITY_RESILIENCE_CHALLENGER.md`](COMMUNITY_RESILIENCE_CHALLENGER.md) for the experimental `community_resilience_service_deficit` feature family.

This challenger is deliberately **outside the current critical path**. It is `reference_only`, has no quantitative model use, and must remain at zero central weight unless a later, separately governed, leakage-safe historical promotion test establishes incremental value. Do not begin the SA2 resilience feature build merely because the specification exists.

## Successor validation decision (proposed)

The [next-validation audit](NEXT_VALIDATION_PATH.md) traces consumed historical evidence, by-elections, cross-state limits and future 2026 snapshots. 2006 Assembly/Council outcomes supplied 2010 priors; 2002 district outcomes appear in the historical display; 1999 freshness and complete replay feasibility are unverified. No clean historical complete-election holdout is selected.

The [contamination inventory](../metadata/validation-evidence-contamination-audit.json) and [prospective protocol](../metadata/model-vnext-validation-protocol.json) recommend the exact current model, with no model clone, for one prospective 2026 election-level evaluation. Repeated freezes are dependent snapshots and simulations non-empirical. No pre-election complete-model production path is established by available evidence; all gates remain unchanged.

The protocol is `proposed-awaiting-owner-review`, not approved or activated. No new target entered the validation pipeline, no forecast refresh or snapshot sealing occurred in this batch.

Exact next action: owner review and explicit approval or rejection of `vic-2026-prospective-observational-v1`.

## Preserved audit history

The 2010 ballot gate was closed through the general contemporaneously-fixed-fact reconstruction policy, with direct PANDORA/NLA and Wayback capture attempts retained as failed routes. The 2014 crosswalk and ballot mask, 2022 Narracan separation, party-family mapping, and all prior score manifests remain governed. Untracked user files `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` were left untouched.

The previous forecast SHA is `70ed0b9b6abc45ed66dd4ac44ed727d8841d2b19358a473d0eb1c2574a9a1aab`. The authorized refreshed forecast SHA is `a1b9f98566931293edbcaf7edc320e90778feffff401d8fbc69e3abb2328eff2`. All 20 committed historical replay artefacts remain byte-identical, including frozen predictions, comparators and scores.
