# PROD 1.0 completion ledger

Updated: 2026-09-25
Branch: `codex/historical-first-complete-replay`
Base: `627fd5f` (PR #97 merged)

This ledger controls the finite PROD 1.0 backlog. Completed items stay closed unless a regression or new evidence invalidates them. Production authorisation remains closed until every required gate is supported by evidence.

| Workstream | Initial status | Blocking issue | Action required | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Source integrity and deterministic artefacts | Complete | None currently evidenced | Preserve fingerprints and generated-output checks | `npm run data:provenance:check`, `npm run release:readiness:check` | Complete — preserve |
| Assembly primary and Council evidence | Complete | None currently evidenced | Preserve official VEC evidence, rule versions and Narracan separation | `npm run validation:evidence`, `npm run psephology:validate` | Complete — preserve |
| Candidate coverage and quarantine | Complete | VEC nomination status remains separate | Use controlled review for changes | `npm run candidates:validate`, `npm run candidates:review:check` | Complete — preserve |
| Current critical-source freshness | Blocked | 15 September RedBridge/Accent report is captured and dossier-recommended for evidence acceptance, but remains quarantined pending project-owner review and separate model-eligibility checks | Record explicit owner decision; admit only if independence and comparability checks pass | `npm run release:readiness:check`, `node scripts/build-poll-promotion-audit.mjs --as-of 2026-09-24` | Open blocker — review decision required |
| Historical poll vintages | Partial | 4 approved observations from 2 independent families; 64/200 legacy leads remain archive-only | Preserve governed input and uncertainty; do not import lead dataset | `node scripts/validate-historical-replay-input-readiness.mjs` | Input gate passing for 2018 |
| Cutoff-safe ballot and incumbency | Partial | 2018 uses 2014 Assembly primaries as a pre-cutoff baseline; the 2014→2018 outcome-transition file is scoring-only | Wire baseline into the real historical runner and retain the dependency audit | `node scripts/build-historical-local-inputs.mjs vic_la_2018` | Open blocker |
| Preference flows and final pairs | Partial | 39 indicative 2022 distributions remain outcome evidence; the walk-forward prior builder is now wired into future replay execution, but no source-party prior is forecast-ready | Establish walk-forward preference priors and separate final-pair scoring outcomes | `npm run validation:evidence`, guarded replay CLI, Python prior-builder tests | Open blocker |
| Runnable frozen historical configurations | Partial | 2018 readiness components pass and prediction execution is separated from production compatibility; scoring outcome artefact remains absent | Load separately governed final-pair/winner outcomes only after prediction freeze | `metadata/historical-replay-input-readiness.json` and frozen prediction manifest | Open blocker — scoring evidence |
| Complete multi-party walk-forward backtest | Blocked | Existing validation is a two-party baseline, not the released probability model | Run leakage-safe four-cycle replays against the fixed comparator/metric protocol | `metadata/historical-validation-acceptance-criteria.json` | Open blocker — evidence |
| Probability calibration | Blocked | No held-out complete-model reliability, slope/intercept or coverage evidence | Evaluate out-of-fold probabilities and intervals under the fixed cycle-clustered protocol | `metadata/historical-validation-acceptance-criteria.json` | Open blocker — evidence |
| Production authorisation | Blocked | Depends on freshness, complete backtest, calibration and exact artefact identity | Authorise only after upstream gates pass | `npm run release:readiness:check` | Closed pending evidence |
| Public application and deployment | Complete but needs PROD verification | Production label remains correctly experimental | Run responsive/rendered checks after evidence gates are ready | `npm test`, `npm run lint`, deployment checks | Deferred until model gates |

## Current verified state

- Release readiness: `experimental-blocked`, 4/9 gates passing at the 24 September assessment; RedBridge freshness evidence is resolved into a dossier but not into model inputs.
- Blocking gates: critical source freshness, unresolved newer model evidence, complete forecast backtest, probability calibration and production authorisation.
- Forecast outputs and model configuration are unchanged by this ledger batch; runnable historical cycles remain 0/4.
- Demographic challenger remains rejected at central weight `0`.
- Preserved untracked user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json`.
- Historical poll reuse policy: `metadata/historical-poll-reuse-policy.json`. The prior queue rule treated null declared licence as a universal replay blocker; the new policy keeps the quarantined third-party dataset blocked but allows independently reconstructed factual observations to be assessed separately.
- Cycle-aware ballot review: 2010, 2014 and 2018 have no One Nation Assembly candidates; 2022 has four. The 2018 Essential case passes provenance and methodological adequacy because its grouped Other residual is sufficient for the active four-family ballot universe, and owner approval has promoted only its structured replay input.
- Owner decision recorded: `metadata/historical-poll-reuse-review.json`; the approved replay input contains 3 structured observations from 1 independent source family. Legacy queue replay-eligible rows remain 0; total approved replay observations are 3.
- Fixed validation thresholds are recorded in `metadata/historical-validation-acceptance-criteria.json` before any complete replay score. Replay-input readiness remains 0/4 runnable and release readiness remains unchanged.
- Focus cycle: `vic_la_2018`, selected by pre-score input completeness. Poll, local, Council and preference contracts pass; the prediction path is executable while production compatibility remains false.
- Verification: 134 JavaScript tests, build, lint, source provenance and psephology validation pass; Python replay tests remain environment-blocked by missing `pytest` and were not bypassed.

Exact next action: obtain a governed 2018 Assembly final-pair/winner scoring artefact. A frozen prediction is generated at `model/data/validation/historical-replays/vic_la_2018-prediction.json`; no target outcomes were loaded before freeze. Complete backtest, calibration and production gates remain closed.
