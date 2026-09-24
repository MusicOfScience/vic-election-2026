# PROD 1.0 completion ledger

Updated: 2026-09-24
Branch: `codex/redbridge-review-dossier`
Base: `77dbf42` (`origin/main`, PR #80 merged)

This ledger controls the finite PROD 1.0 backlog. Completed items stay closed unless a regression or new evidence invalidates them. Production authorisation remains closed until every required gate is supported by evidence.

| Workstream | Initial status | Blocking issue | Action required | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Source integrity and deterministic artefacts | Complete | None currently evidenced | Preserve fingerprints and generated-output checks | `npm run data:provenance:check`, `npm run release:readiness:check` | Complete — preserve |
| Assembly primary and Council evidence | Complete | None currently evidenced | Preserve official VEC evidence, rule versions and Narracan separation | `npm run validation:evidence`, `npm run psephology:validate` | Complete — preserve |
| Candidate coverage and quarantine | Complete | VEC nomination status remains separate | Use controlled review for changes | `npm run candidates:validate`, `npm run candidates:review:check` | Complete — preserve |
| Current critical-source freshness | Blocked | 15 September RedBridge/Accent report is captured and dossier-recommended for evidence acceptance, but remains quarantined pending project-owner review and separate model-eligibility checks | Record explicit owner decision; admit only if independence and comparability checks pass | `npm run release:readiness:check`, `node scripts/build-poll-promotion-audit.mjs --as-of 2026-09-24` | Open blocker — review decision required |
| Historical poll vintages | Partial | 64/200 matched; 136 residual; no reuse authority | Continue finite first-party reconstruction where it materially improves replay | `npm run validation:evidence` | Open blocker |
| Cutoff-safe ballot and incumbency | Partial | Official VEC 2022 handbooks now fix the nomination and post-draw publication timing framework, but candidate-specific acceptance, archived publication timing and aliases remain unresolved | Build cycle-scoped, leakage-safe slate evidence | `npm run validation:evidence` | Open blocker |
| Preference flows and final pairs | Partial | 39 indicative distributions lack complete replay evidence | Establish defensible cycle-specific final-pair and transfer inputs | `npm run validation:evidence` | Open blocker |
| Runnable frozen historical configurations | Partial | Four specifications exist but are deliberately unrunnable | Complete frozen inputs and scoring-only outcome separation; contract validator and Python runner now fail closed with structured blockers | `npm run validation:replay-contract`, `PYTHONPATH=model/src python3 -m vicforecast.historical_replay vic_la_2022` | Open blocker — runner guarded |
| Complete multi-party walk-forward backtest | Blocked | Existing validation is a two-party baseline, not the released probability model | Implement leakage-safe four-cycle replays and preregister acceptance criteria; scoring primitives now exist in `model/src/vicforecast/validation_metrics.py` | New replay/backtest checks | Open blocker — substrate started |
| Probability calibration | Blocked | No held-out complete-model reliability, slope/intercept or coverage evidence | Evaluate out-of-fold probabilities and intervals; reusable scoring primitives now exist | New calibration checks | Open blocker — substrate started |
| Production authorisation | Blocked | Depends on freshness, complete backtest, calibration and exact artefact identity | Authorise only after upstream gates pass | `npm run release:readiness:check` | Closed pending evidence |
| Public application and deployment | Complete but needs PROD verification | Production label remains correctly experimental | Run responsive/rendered checks after evidence gates are ready | `npm test`, `npm run lint`, deployment checks | Deferred until model gates |

## Current verified state

- Release readiness: `experimental-blocked`, 4/9 gates passing at the 24 September assessment; RedBridge freshness evidence is resolved into a dossier but not into model inputs.
- Blocking gates: critical source freshness, unresolved newer model evidence, complete forecast backtest, probability calibration and production authorisation.
- Forecast outputs and model configuration are unchanged by this ledger batch; runnable historical cycles remain 0/4.
- Demographic challenger remains rejected at central weight `0`.
- Preserved untracked user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json`.

Exact next action: obtain the explicit project-owner decision for the RedBridge dossier; if accepted, resolve sample-family independence before any separate model-eligibility decision. In parallel, locate archived candidate-list captures or other primary records proving 2022 candidate-specific availability, without importing outcomes into prediction inputs.
