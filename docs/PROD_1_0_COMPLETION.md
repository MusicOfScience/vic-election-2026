# PROD 1.0 completion ledger

Updated: 2026-09-25
Branch: `codex/promote-2022-polls-and-local-surfaces`
Base: `52df20c` (PR #101 merged)
Current batch: 2022 pre-score input substrate after PR #101; v1 remains immutable and non-certifying. PR #102 is open for review.

This ledger controls the finite PROD 1.0 backlog. Completed items stay closed unless a regression or new evidence invalidates them. Production authorisation remains closed until every required gate is supported by evidence.

| Workstream | Initial status | Blocking issue | Action required | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Source integrity and deterministic artefacts | Complete | None currently evidenced | Preserve fingerprints and generated-output checks | `npm run data:provenance:check`, `npm run release:readiness:check` | Complete — preserve |
| Assembly primary and Council evidence | Complete | None currently evidenced | Preserve official VEC evidence, rule versions and Narracan separation | `npm run validation:evidence`, `npm run psephology:validate` | Complete — preserve |
| Candidate coverage and quarantine | Complete | VEC nomination status remains separate | Use controlled review for changes | `npm run candidates:validate`, `npm run candidates:review:check` | Complete — preserve |
| Current critical-source freshness | Blocked | 15 September RedBridge/Accent report is captured and dossier-recommended for evidence acceptance, but remains quarantined pending project-owner review and separate model-eligibility checks | Record explicit owner decision; admit only if independence and comparability checks pass | `npm run release:readiness:check`, `node scripts/build-poll-promotion-audit.mjs --as-of 2026-09-24` | Open blocker — review decision required |
| Historical poll vintages | Partial | 2018 has 4 approved observations from 2 families; 2022 has 2 approved Roy Morgan observations from 1 family; RedBridge/Freshwater remain incomplete | Recover one independently governed second-family observation; do not import lead dataset | `node scripts/validate-historical-replay-input-readiness.mjs` | 2022 poll gate blocked |
| Cutoff-safe ballot and incumbency | Partial | 2018 uses 2014 Assembly primaries as a pre-cutoff baseline; the 2014→2018 outcome-transition file is scoring-only | Wire baseline into the real historical runner and retain the dependency audit | `node scripts/build-historical-local-inputs.mjs vic_la_2018` | Open blocker |
| Preference flows and final pairs | Partial | 39 indicative 2022 distributions remain outcome evidence; the walk-forward prior builder is now wired into future replay execution, but no source-party prior is forecast-ready | Establish walk-forward preference priors and separate final-pair scoring outcomes | `npm run validation:evidence`, guarded replay CLI, Python prior-builder tests | Open blocker |
| Runnable frozen historical configurations | Partial | 2018 prediction is frozen and scored against 88 official VEC outcome rows; three cycles remain blocked | Preserve immutable prediction/score pair; extend walk-forward coverage | `model/data/validation/historical-replays/vic_la_2018-score-manifest.json` | One cycle scored |
| Complete multi-party walk-forward backtest | Blocked | Existing validation is a two-party baseline, not the released probability model | Run leakage-safe four-cycle replays against the fixed comparator/metric protocol | `metadata/historical-validation-acceptance-criteria.json` | Open blocker — evidence |
| Probability calibration | Blocked | No held-out complete-model reliability, slope/intercept or coverage evidence | Evaluate out-of-fold probabilities and intervals under the fixed cycle-clustered protocol | `metadata/historical-validation-acceptance-criteria.json` | Open blocker — evidence |
| Production authorisation | Blocked | Depends on freshness, complete backtest, calibration and exact artefact identity | Authorise only after upstream gates pass | `npm run release:readiness:check` | Closed pending evidence |
| Public application and deployment | Complete but needs PROD verification | Production label remains correctly experimental | Run responsive/rendered checks after evidence gates are ready | `npm test`, `npm run lint`, deployment checks | Deferred until model gates |

## Current verified state

- Release readiness: `experimental-blocked`, 4/9 gates passing at the 24 September assessment; RedBridge freshness evidence is resolved into a dossier but not into model inputs.
- Blocking gates: critical source freshness, unresolved newer model evidence, complete forecast backtest, probability calibration and production authorisation.
- Forecast outputs and model configuration are unchanged by this ledger batch; historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored, with 0/4 certifying scored cycles because v1 contains confirmed adapter defects.
- Demographic challenger remains rejected at central weight `0`.
- Preserved untracked user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json`.
- Historical poll reuse policy: `metadata/historical-poll-reuse-policy.json`. The prior queue rule treated null declared licence as a universal replay blocker; the new policy keeps the quarantined third-party dataset blocked but allows independently reconstructed factual observations to be assessed separately.
- Cycle-aware ballot review: 2010, 2014 and 2018 have no One Nation Assembly candidates; 2022 has four. The 2018 Essential case passes provenance and methodological adequacy because its grouped Other residual is sufficient for the active four-family ballot universe, and owner approval has promoted only its structured replay input.
- Owner decisions recorded: Essential and uComms/ReachTEL reviews; the approved replay input contains 4 structured observations from 2 independent source families. Legacy queue replay-eligible rows remain 0.
- Fixed validation thresholds are recorded in `metadata/historical-validation-acceptance-criteria.json` before scoring. Replay progress is 1/4 runnable, 1/4 predicted and 1/4 scored; release readiness remains unchanged.
- Focus cycle: `vic_la_2018`. V1 local-family mapping, Assembly seat aggregation and Council top-two defects are preserved as a negative implementation result. V2 uses `metadata/historical-party-family-mapping.json`, per-simulation chamber draws and a non-certifying diagnostic output.
- V2 diagnostic artefact: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json` (SHA `3aa4ce84…`); comparator limitations are recorded in `metadata/historical-replay-v1-comparator-audit.json`.
- Next certifying cycle selected before scoring: `vic_la_2022`. Both Roy Morgan cases are owner-approved and promoted; RedBridge remains incomplete and Freshwater lacks an exhaustive primary table. The official VEC TPP baseline plus AEC relative district/region surfaces pass pre-cutoff checks; ballot, local and Council components are ready, but poll sufficiency remains blocked.
- Verification: JavaScript, build, lint, source provenance, psephology and isolated Python validation pass; the official 2018 outcome extractor validates 88/88 districts.

Exact next action: recover one clean second-family 2022 observation and obtain its explicit owner approval before freezing a 2022 v2 prediction.
