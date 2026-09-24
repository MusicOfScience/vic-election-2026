# PROD 1.0 completion ledger

Updated: 2026-09-24
Branch: `codex/prod-1.0-completion`
Base: `a32b1e9` (`origin/main`, PR #73 merged)

This ledger controls the finite PROD 1.0 backlog. Completed items stay closed unless a regression or new evidence invalidates them. Production authorisation remains closed until every required gate is supported by evidence.

| Workstream | Initial status | Blocking issue | Action required | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| Source integrity and deterministic artefacts | Complete | None currently evidenced | Preserve fingerprints and generated-output checks | `npm run data:provenance:check`, `npm run release:readiness:check` | Complete — preserve |
| Assembly primary and Council evidence | Complete | None currently evidenced | Preserve official VEC evidence, rule versions and Narracan separation | `npm run validation:evidence`, `npm run psephology:validate` | Complete — preserve |
| Candidate coverage and quarantine | Complete | VEC nomination status remains separate | Use controlled review for changes | `npm run candidates:validate`, `npm run candidates:review:check` | Complete — preserve |
| Current critical-source freshness | Blocked | Model-eligible poll is stale; newer staged evidence is deliberately held | Obtain and review a legitimate current Victorian source, then run freshness gates | `npm run release:readiness:check`, `npm run sources:live` | Open blocker |
| Historical poll vintages | Partial | 64/200 matched; 136 residual; no reuse authority | Continue finite first-party reconstruction where it materially improves replay | `npm run validation:evidence` | Open blocker |
| Cutoff-safe ballot and incumbency | Partial | Pre-cutoff candidate timing and aliases unresolved | Build cycle-scoped, leakage-safe slate evidence | `npm run validation:evidence` | Open blocker |
| Preference flows and final pairs | Partial | 39 indicative distributions lack complete replay evidence | Establish defensible cycle-specific final-pair and transfer inputs | `npm run validation:evidence` | Open blocker |
| Runnable frozen historical configurations | Partial | Four specifications exist but are deliberately unrunnable | Complete frozen inputs and scoring-only outcome separation; the contract validator now checks cutoffs, seeds, output requirements and fail-closed blockers | `npm run validation:replay-contract` | Open blocker — contract guarded |
| Complete multi-party walk-forward backtest | Blocked | Existing validation is a two-party baseline, not the released probability model | Implement leakage-safe four-cycle replays and preregister acceptance criteria; scoring primitives now exist in `model/src/vicforecast/validation_metrics.py` | New replay/backtest checks | Open blocker — substrate started |
| Probability calibration | Blocked | No held-out complete-model reliability, slope/intercept or coverage evidence | Evaluate out-of-fold probabilities and intervals; reusable scoring primitives now exist | New calibration checks | Open blocker — substrate started |
| Production authorisation | Blocked | Depends on freshness, complete backtest, calibration and exact artefact identity | Authorise only after upstream gates pass | `npm run release:readiness:check` | Closed pending evidence |
| Public application and deployment | Complete but needs PROD verification | Production label remains correctly experimental | Run responsive/rendered checks after evidence gates are ready | `npm test`, `npm run lint`, deployment checks | Deferred until model gates |

## Current verified state

- Release readiness: `experimental-blocked`, 4/9 gates passing at the 15 September registry assessment.
- Blocking gates: critical source freshness, unresolved newer model evidence, complete forecast backtest, probability calibration and production authorisation.
- Forecast outputs and model configuration are unchanged by this ledger batch.
- Demographic challenger remains rejected at central weight `0`.
- Preserved untracked user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json`.

Exact next action: review the staged 15 September RedBridge report through the existing evidence workflow, then inspect the historical data/configuration modules and implement the smallest reproducible replay slice that can produce held-out complete-model metrics without importing outcome data into prediction inputs.
