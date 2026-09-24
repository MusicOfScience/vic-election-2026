# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/repair-2022-comparators`
- Base commit: `4acf3133` (PR #104 merged; remote main synchronised). Focus cycle remains frozen pre-score `vic_la_2022`.
- Current batch: repair and freeze the five preregistered v2 comparators before any 2022 outcome is loaded.
- Batch state: the old comparator bundle is preserved as a pre-score defect artefact; the replacement bundle is frozen and published in reviewable PR #105: https://github.com/MusicOfScience/vic-election-2026/pull/105
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Resolve owner approval is recorded and the governed canonical input now has 3 approved 2022 observations from 2 independent families. The immutable certifying prediction is `model/data/validation/historical-replays/vic_la_2022-v2-prediction.json`, SHA `f68f3bfba98a41205290aff7ef9fa151786d2407c1c764f09006b6b15757f0b0`. The old comparator bundle SHA `1492dc93…` is preserved and classified `pre-score-comparator-defect-discovered`; the new pre-outcome comparator contract is `metadata/historical-replay-v2-comparator-spec.json` and replacement bundle is `model/data/validation/historical-replays/vic_la_2022-v2-comparators-v2.json` (SHA `cd04d597…`). No target outcomes were loaded.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 2/4 runnable, 2/4 predicted and 1/4 scored; certifying predicted cycles are 1 and certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: PR #105 is ready for review; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 6 observations overall, including 2 2022 Roy Morgan observations from 1 family. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: review and publish this comparator repair, then score the immutable 2022 v2 prediction and frozen comparator bundle in a separate outcome-loading batch. Do not regenerate the prediction or tune from its score.
