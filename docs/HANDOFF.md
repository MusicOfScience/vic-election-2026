# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/prepare-2014-holdout`
- Base commit: `602c7480` (PR #106 merged; remote main synchronised). The 2022 certifying prediction and score are immutable.
- Current batch: select and prepare the next certifying holdout using pre-score evidence completeness only.
- Batch state: `vic_la_2014` selected objectively; no 2014 prediction or target outcome was generated or loaded.
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; 2018 remains non-certifying, while the 2022 v2 score is the first certifying historical score.
- Resolve owner approval is recorded and the governed canonical input has 3 approved 2022 observations from 2 independent families. The sealed prediction remains SHA `f68f3bfba…`; the corrected comparator bundle remains SHA `cd04d597…`, while defective pre-score bundle SHA `1492dc93…` is preserved. Official VEC scoring outcomes are in `model/data/processed/vec_2022_assembly_final_pairs.csv` (87 districts; 77 final pairs available, 10 unavailable because only 2CP/early-majority evidence exists). Score: `model/data/validation/historical-replays/vic_la_2022-v2-score.json`, SHA `3bc3b150…`; manifest: `vic_la_2022-v2-score-manifest.json`.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 2/4 runnable, 2/4 predicted and 2/4 scored; certifying predicted cycles are 1 and certifying scored cycles are 1.
- Validation: winner accuracy 87.36%, district primary MAE 4.27pp, ALP-event Brier 0.09268, ALP-event log loss 0.68460, multiclass Brier 0.19075, multiclass log loss 1.76205 (misses the fixed 1.20 cycle threshold). Assembly mean-seat absolute error 2.86; frozen 80% chamber interval coverage 0.80. Council regional primary metric is unavailable because no regional primary estimates were frozen. Complete backtest, calibration and production authorisation remain closed.
- 2014 preparation: three archived first-party Roy Morgan observations (1 Oct, 27 Oct and 10 Nov) have complete structured categories, samples, fieldwork and TPP; automated gates pass but all await explicit owner approval. Bounded Essential/Newspoll checks remain methodologically incomplete and are recorded in `metadata/historical-poll-2014-second-family-assessment.json`; no second family is promoted. The 2010→2014 outcome-transition file remains scoring-only and forbidden in prediction.
- Local/Council state: the 2010 Assembly family baseline and 2010 Council evidence exist, but the 2014 crosswalk surface is absent from the clone, the notional 2010-on-2014 TPP provenance is not independently proven, and 2010→2014 Council region continuity is unaudited. 2014 remains blocked and no prediction was generated.
- Publication: PR #107 (https://github.com/MusicOfScience/vic-election-2026/pull/107) is open for review; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input contains 7 observations overall, including 3 2022 observations from 2 independent families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: obtain owner decisions for the three governed 2014 Roy Morgan cases, then recover one independent second poll family and prove a prediction-safe 2010-on-2014 baseline before wiring 2014 inputs. Do not generate a prediction until every gate passes.
