# Approved experimental forecast refresh — 31 October 2026

## Owner decision implemented

The project owner explicitly replied “Approve” to the exact two-wave bundle in the admission review. The durable decision is `metadata/poll-admission-approval-2026-10-31.json`, bound to the original proposal manifest and its event/estimate checksums.

Admitted:

- DemosAU / PremierNational, fieldwork 10–20 September: full N=1,020, **effective N=572**. The original method, questionnaire, weighting and undecided handling were reconciled. Unknown respondent reuse is an acknowledged limitation.
- Roy Morgan, fieldwork 26–29 October: full N=3,610, effective N undisclosed; existing sample cap retained. The published six-category primary composition is preserved, including Independent 7.5 and Other 6 separately. Unknown exact questionnaire/undecided handling/overlap are acknowledged. The 74–29 alternate matchup remains excluded.

RedBridge October, Resolve October and Newspoll October remain held. Early-October Morgan remains reference-only with unknown N. No held wave was admitted by implication.

The original 8 October owner approval and the unapproved proposal packet remain historical records. The new approval supplements them, rather than retrospectively rewriting them. The application scripts verify the admitted rows and are idempotent.

## Result

| Assembly measure | 8 October snapshot | 31 October refresh |
|---|---:|---:|
| Labor mean seats | 38.29 | 34.41 |
| Coalition mean seats | 31.02 | 35.78 |
| One Nation mean seats | 16.28 | 15.36 |
| Greens mean seats | 2.40 | 2.44 |
| Labor majority frequency | 19.30% | 8.74% |
| Coalition majority frequency | 3.10% | 11.46% |
| Hung parliament frequency | 77.60% | 79.80% |

These are experimental simulation frequencies, not calibrated production probabilities or a forecast of minority-government negotiations. The current canonical output reproduces the earlier approved-bundle sensitivity to machine precision. Differences against the old published snapshot combine input addition and assessment-date advance; they are not causal estimates of one poll.

The public headline uses **medians** (Labor 34, Coalition 35, ONP 15); the table above uses **means**. Independent medians and modal electorate winners are different summaries and must not be conflated.

## District changes

All 88 district deltas and all eight Council-region deltas are in `metadata/forecast-refresh-2026-10-31.json`.

- 50 districts have at least one party's win frequency change by at least five percentage points.
- Four modal winners change: Bass ONP→Coalition; Bendigo East Labor→ONP; Bentleigh Labor→Coalition; Ripon ONP→Coalition. These are modal changes, not declarations that a seat is safe.
- Three final-pair **compositions** change: Bundoora and Laverton from Labor–ONP to Labor–Coalition; Richmond from Greens–Labor to Greens–Coalition.
- Bendigo East and Bentleigh reverse ordering within the same pair. The audit reports those separately through the five ordered-pair changes, rather than counting them as new compositions.

## Council boundary

The existing voter-directed approximation is regenerated because statewide polling changes affect it. Mean seats are Labor 11.19, Coalition 12.90, ONP 9.31, Greens 2.94 and Other/Independent 3.67. The regional input remains the August Morgan table. No missing newer regional cell is inferred, no new Council-specific poll is injected and no candidate-level STV claim is made.

## Readiness and preservation

- 15 eligible polls, up from 13; 16 registry events including the retained non-comparable record.
- Poll effective date advances to 29 October; assessment date advances to 31 October.
- Current readiness returns from 4/9 to **6/9**: source freshness and model-input resolution now pass. Complete-model backtest, probability calibration and production authorisation remain closed.
- Fixed seed 20260826; 5,000 simulations; all model coefficients and engine source bytes unchanged. Only `as_of` changes in the configuration.
- All 105 existing validation-archive files, including historical predictions/scores and the first prospective package, remain byte-identical. No new prospective snapshot, historical outcome score or 2026 outcome score was created.
- The original September/Freshwater refresh audit, staged August shadow, October campaign sensitivity and admission-review sensitivity remain frozen. Their checks now read immutable original Git input trees. CI explicitly fetches those trees and runs old sensitivities in isolated worktrees. Recorded hashes are not rewritten to the new inputs.

## Validation

Passed locally: 209 JavaScript tests, 92 Python tests, lint, static Pages export, owner-admission idempotence, the new refresh-delta audit and original snapshot verification. A second deterministic regeneration produced zero additional drift. The release remains experimental. New model research or preference-prior promotion is outside this approval.
