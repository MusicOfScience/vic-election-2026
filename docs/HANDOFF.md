# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/freeze-2014-crosswalk`
- Base commit: `8bc89cc2` (PR #110 merged; remote main synchronised). The 2022 certifying prediction and score are immutable.
- Current batch: rebuild and freeze the prediction-safe 2014 multi-party geographic crosswalk and v2 holdout.
- Batch state: `vic_la_2014` is input-complete and its certifying prediction/comparator bundle are frozen; no 2014 target outcome was generated, loaded or scored.
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; 2018 remains non-certifying, while the 2022 v2 score is the first certifying historical score.
- Resolve owner approval is recorded and the governed canonical input has 3 approved 2022 observations from 2 independent families. The sealed prediction remains SHA `f68f3bfba…`; the corrected comparator bundle remains SHA `cd04d597…`, while defective pre-score bundle SHA `1492dc93…` is preserved. Official VEC scoring outcomes are in `model/data/processed/vec_2022_assembly_final_pairs.csv` (87 districts; 77 final pairs available, 10 unavailable because only 2CP/early-majority evidence exists). Score: `model/data/validation/historical-replays/vic_la_2022-v2-score.json`, SHA `3bc3b150…`; manifest: `vic_la_2022-v2-score-manifest.json`.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 3/4 runnable, 3/4 predicted and 2/4 scored; certifying predicted cycles are 2 and certifying scored cycles are 1.
- Validation: winner accuracy 87.36%, district primary MAE 4.27pp, ALP-event Brier 0.09268, ALP-event log loss 0.68460, multiclass Brier 0.19075, multiclass log loss 1.76205 (misses the fixed 1.20 cycle threshold). Assembly mean-seat absolute error 2.86; frozen 80% chamber interval coverage 0.80. Council regional primary metric is unavailable because no regional primary estimates were frozen. Complete backtest, calibration and production authorisation remain closed.
- 2014 preparation: the three archived first-party Roy Morgan observations and May Essential observation are explicitly owner-approved and promoted through the cycle-scoped governed input (`model/data/validation/historical-replay-2014-poll-observations.json`); polling is 4 observations from 2 independent families and passes the fixed rule. The 2010→2014 outcome-transition file remains scoring-only and forbidden in prediction.
- Local/Council state: the 88-row ABC/Antony Green notional-margin baseline, all eight new-boundary Council priors and the cutoff-safe ballot mask remain governed. The four restored payloads are hash-verified in `metadata/historical-replay-2014-crosswalk-build-manifest.json`; the rebuilt 616-cell crosswalk is `model/data/processed/historical_2014_crosswalk_core_features_long.csv` (SHA `2b2a1612c631eba1a7a782f9147e90745d1d8fdf1c3a13bd8ebd7e276a4f0398`), and the 88-row local input is `model/data/validation/historical-replay-2014-local-inputs.csv` (SHA `5aab7e9d8998674770845b41720f7b4219967d194cf99eaf8c012aba01b20f64`). Council no longer needs a region-name continuity join.
- Publication: PR #110 is merged at `8bc89cc2`; this batch is prepared on `codex/freeze-2014-crosswalk`. The sealed 2014 prediction is `model/data/validation/historical-replays/vic_la_2014-v2-prediction.json` (internal prediction SHA `7621cd120c9efdd7f891d0d69fbd711b8d5316af632547df6035e3ea096b38b0`) and the pre-outcome comparator bundle is `model/data/validation/historical-replays/vic_la_2014-v2-comparators.json` (SHA `d0178652ddcd922ae8b61cadac40ff6bab296c27f9bcc4be97cd5e34f43e3efd`). Local checks are green; GitHub Actions may remain externally blocked by the account billing/spending-limit restriction. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- The approved 2014 replay input now has four observations from two independent families, and the fixed poll gate passes. Do not reopen the historical polling sweep for this cycle.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input contains 7 observations overall, including 3 2022 observations from 2 independent families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- The 2014 input blocker is closed by a deterministic rebuild from the four restored pre-cutoff source payloads. The old report SHA was not recovered; the new output is explicitly versioned and does not claim byte identity. Ballot availability is closed with the cutoff-safe 88-row family mask; Council and preference inputs retain their governed broad fallbacks.

Exact next action: preserve the sealed 2014 prediction and comparator bundle and conduct the separate outcome-scoring batch. Do not load 2014 outcomes in this batch; complete backtest, calibration and production authorisation remain closed.
