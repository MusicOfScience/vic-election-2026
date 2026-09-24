# PROD 1.0 completion ledger

Updated: 2026-09-24
Branch: `codex/historical-first-runnable-cycle`
Base: `7297c55` (PR #95 merged)

This ledger controls the finite PROD 1.0 backlog. Completed items stay closed unless a regression or new evidence invalidates them. Production authorisation remains closed until every required gate is supported by evidence.

| Workstream | Initial status | Blocking issue | Action required | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Source integrity and deterministic artefacts | Complete | None currently evidenced | Preserve fingerprints and generated-output checks | `npm run data:provenance:check`, `npm run release:readiness:check` | Complete — preserve |
| Assembly primary and Council evidence | Complete | None currently evidenced | Preserve official VEC evidence, rule versions and Narracan separation | `npm run validation:evidence`, `npm run psephology:validate` | Complete — preserve |
| Candidate coverage and quarantine | Complete | VEC nomination status remains separate | Use controlled review for changes | `npm run candidates:validate`, `npm run candidates:review:check` | Complete — preserve |
| Current critical-source freshness | Blocked | 15 September RedBridge/Accent report is captured and dossier-recommended for evidence acceptance, but remains quarantined pending project-owner review and separate model-eligibility checks | Record explicit owner decision; admit only if independence and comparability checks pass | `npm run release:readiness:check`, `node scripts/build-poll-promotion-audit.mjs --as-of 2026-09-24` | Open blocker — review decision required |
| Historical poll vintages | Partial | 64/200 legacy leads matched; 3 independently reconstructed observations approved from 1 source family; sparse rule requires 2 families | Recover one targeted independent 2018 family; retain grouped categories and uncertainty | `node scripts/validate-historical-replay-input-readiness.mjs` | Open blocker |
| Cutoff-safe ballot and incumbency | Partial | 2018 ballot universe passes, but the boundary-aligned local artefact referenced by the existing validation report is absent | Restore or regenerate the fingerprinted pre-cutoff local input; do not substitute target outcomes | `node scripts/build-historical-local-inputs.mjs vic_la_2018` | Open blocker |
| Preference flows and final pairs | Partial | 39 indicative 2022 distributions remain outcome evidence; the walk-forward prior builder is now wired into future replay execution, but no source-party prior is forecast-ready | Establish walk-forward preference priors and separate final-pair scoring outcomes | `npm run validation:evidence`, guarded replay CLI, Python prior-builder tests | Open blocker |
| Runnable frozen historical configurations | Partial | Focus cycle 2018 selected by evidence completeness; poll diversity, local input and Council input remain blocked | Complete executable inputs, derive runnable state, then run prediction before loading outcomes | `metadata/historical-replay-input-readiness.json` | Open blocker — runner guarded |
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
- Focus cycle: `vic_la_2018`, selected by pre-score input completeness. Local blocker is the absent `model/data/processed/vec_2014_2018_same_boundary_tpp_swing.csv`; Council blocker is the absence of a pre-cutoff regional input, with the 2026 regional poll rejected.
- Verification: 134 JavaScript tests, build, lint, source provenance and psephology validation pass; Python replay tests remain environment-blocked by missing `pytest` and were not bypassed.

Exact next action: targeted Newspoll recovery remains blocked by missing safe primary-share fields; then restore the boundary-aligned local artefact and construct a pre-cutoff Council prior. No complete replay has yet executed.
