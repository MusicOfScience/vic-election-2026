# PROD 1.0 validation conclusion

Updated 2026-09-25 from merged PR #118 (`ad5d1b5d`).

## Historical conclusion

The historical programme has reached its valid endpoint under the registered protocol. Three cycles are certifying `historical_replay_v2` holdouts: 2010, 2014 and 2022. The 2018 replay remains a genuine score of the code that ran, but is permanently non-certifying because its v1 implementation defect collapsed local party-family structure; its v2 run was post-hoc diagnostic evidence and cannot be made fresh again.

The immutable three-cycle descriptive means are winner accuracy `0.8404301637`, multiclass Brier `0.2193372181`, multiclass log loss `1.0486418097`, and district primary MAE `4.7557257435`. The Brier numerical mean is below `0.22`, while log loss is above `1.00`; neither is a protocol gate result because the preregistered rule requires four certifying cycles. The aggregate is an unweighted mean of cycle-level metrics, not a pooled district-level replication.

Known weaknesses remain recorded rather than repaired: 2010 missed the seat-count maximum-family-error and frozen interval-coverage thresholds; 2014 missed seat count, multiclass Brier and interval coverage; 2022 missed multiclass log loss. Final-pair calibration, regional-primary probability/error metrics and the contest-type metric are unavailable under the frozen output contracts. The complete backtest and probability-calibration gates therefore remain `closed-incomplete-certifying-four-cycle-protocol` and `closed-incomplete-cycle-clustered-protocol`.

No prediction, comparator, threshold, preference rule, uncertainty parameter, or Council rule was changed in this close-out. A future revised model must have a new version identity and a prospective validation protocol; consumed holdouts cannot be reused as fresh tests.

## Current release gates

The nine-gate classification is recorded in [`metadata/prod-1.0-closure-audit.json`](../metadata/prod-1.0-closure-audit.json): source integrity, deterministic outputs, historical data readiness and candidate evidence pass. Critical source freshness and model-input freshness are resolvable current-evidence blockers. Complete backtest and probability calibration are structurally blocked under the current PROD 1.0 protocol. Production authorisation is downstream blocked and remains closed.

The release report was refreshed as of 2026-09-25 without advancing any source effective date. The model-eligible poll registry remains outside the fixed 21-day freshness window. The captured September RedBridge/Accent report is evidence-accepted in principle but remains staged pending an explicit independence review against the earlier RedBridge family. Its full sample (`N=2,371`) and published vote-intention base (`N=2,160`) remain distinct; no model input was changed.

## Future path

For the current model and release, retain the last valid experimental forecast, resolve current evidence freshness through explicit review, and keep production authorisation closed. If further modelling is desired, create a separately versioned model and preregister a new walk-forward protocol using genuinely unconsumed future elections, prospective datasets or simulation studies. Do not create a synthetic fourth holdout or retune `historical_replay_v2` from these results.

The deterministic 2026 forecast remains unchanged at SHA `70ed0b9b6abc45ed66dd4ac44ed727d8841d2b19358a473d0eb1c2574a9a1aab`.
