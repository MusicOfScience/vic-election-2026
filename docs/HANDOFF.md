# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/prepare-2022-certifying-replay`
- Base commit: `6753d07` (PR #100 merged; remote main synchronised). Focus cycle is now pre-score `vic_la_2022`.
- Current batch commit: `fbf9a5f`; PR #101 is open for review: https://github.com/MusicOfScience/vic-election-2026/pull/101
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Next-cycle selection is frozen to 2022 by pre-score evidence completeness. Two Roy Morgan cases and one RedBridge case are governed for review; no 2022 poll has been promoted. The official VEC 2018-on-2022-boundary TPP baseline is now recovered (87 November-election districts, published 2022-08-05); multi-party local inputs remain open. Council audit confirms Eastern Metropolitan (2018) cannot be joined directly to North-Eastern Metropolitan (2022), so a governed mapping/fallback is still required.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored; certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: this batch will be published as one focused reviewable PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 4 independently reconstructed observations from 2 families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: obtain project-owner decisions on the three 2022 poll cases, then complete the governed multi-party local-input and Council-region audits. Do not generate or score 2022 until those gates pass.
