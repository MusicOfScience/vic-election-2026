# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/promote-2022-polls-and-local-surfaces`
- Base commit: `52df20c` (PR #101 merged; remote main synchronised). Focus cycle remains pre-score `vic_la_2022`.
- Current batch commit: `71b13ce`; PR #102 is open for review: https://github.com/MusicOfScience/vic-election-2026/pull/102
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Next-cycle selection is frozen to 2022 by pre-score evidence completeness. Both Roy Morgan cases are owner-approved and promoted; RedBridge remains incomplete and Freshwater was checked once but lacks an exhaustive primary table. The governed VEC TPP baseline and AEC relative district/region surfaces now pass pre-cutoff input checks; no 2022 prediction has been generated.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored; certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: this batch will be published as one focused reviewable PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 6 observations overall, including 2 2022 Roy Morgan observations from 1 family. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: recover one independently governed 2022 observation from a second source family (or obtain owner approval for a complete candidate), then rerun the fixed 3-observation/2-family sufficiency check. Do not generate or score 2022 until that gate passes.
