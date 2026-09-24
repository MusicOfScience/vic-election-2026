# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/freeze-2022-v2-prediction`
- Base commit: `1a6c07fe` (PR #103 merged; remote main synchronised). Focus cycle is frozen pre-score `vic_la_2022`.
- Current batch: Resolve approved/promoted and cycle-aware `historical_replay_v2` prediction sealed; no 2022 outcomes loaded.
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Resolve owner approval is recorded and the governed canonical input now has 3 approved 2022 observations from 2 independent families. The cycle-aware v2 runner uses a four-bucket observation state and only decomposes `OTH_RESIDUAL` with pre-cutoff local propensity at the ballot layer; ONP is zero where unavailable. Assembly simulations cover 87 districts and Council simulations cover 8 regions/40 seats. The immutable certifying prediction is `model/data/validation/historical-replays/vic_la_2022-v2-prediction.json`, SHA `f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0`; comparator bundle: `model/data/validation/historical-replays/vic_la_2022-v2-comparators.json`. No target outcomes were loaded.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 2/4 runnable, 2/4 predicted and 1/4 scored; certifying predicted cycles are 1 and certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: this batch will be published as one focused reviewable PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 6 observations overall, including 2 2022 Roy Morgan observations from 1 family. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: score the frozen 2022 v2 prediction in a separate batch using official outcomes only after verifying its hash. Do not regenerate it or tune the model from its score.
