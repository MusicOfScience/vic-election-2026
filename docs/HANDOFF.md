# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/repair-historical-adapter-v2`
- Base commit: `5cdd8dd` (PR #99 merged; remote main synchronised). Focus cycle remains `vic_la_2018`.
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored; certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: PR #99 is open at https://github.com/MusicOfScience/vic-election-2026/pull/99; checks are queued. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 4 independently reconstructed observations from 2 families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: recover the smallest finite polling/local/Council evidence set for the next certifying cycle; no remaining cycle is currently evidence-complete. Preserve v1 and do not tune or regenerate 2018.
