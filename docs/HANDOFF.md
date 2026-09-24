# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/recover-2022-second-family-poll`
- Base commit: `2b063b7c` (PR #102 merged; remote main synchronised). Focus cycle remains pre-score `vic_la_2022`.
- Current batch: bounded second-family poll recovery; no 2022 prediction or score generated.
- V1 evidence is immutable: prediction `424552f6…`, score `fe6734e2…`; winner accuracy 62.5%, final-pair accuracy 85.23%, primary MAE 8.33pp, complete-ensemble ALP-event Brier/log loss 0.23819/0.67015 versus uniform-swing 0.18139/0.54935. Assembly seat scoring was invalid and Council scoring deferred.
- Confirmed v1 defects: historical `Coalition/Greens/Other/Independent` labels were zero-filled against internal names, collapsing local baselines; chamber seats were aggregated across simulations; Council used a deterministic top-two 3/2 shortcut.
- V2 adds a governed family mapping, varied local vectors, per-simulation Assembly/Council seat draws and explicit parity/version manifests. The 2018 v2 output is post-hoc diagnostic/non-certifying and does not replace v1.
- V2 diagnostic: `model/data/validation/historical-replays/vic_la_2018-v2-diagnostic.json`, SHA `3aa4ce84…`; v1 remains the only historical score and is excluded from certification.
- Next-cycle selection is frozen to 2022 by pre-score evidence completeness. Both Roy Morgan cases are owner-approved and promoted. Freshwater was checked once systematically (first-party article, WordPress API, Datawrapper and media references) but still lacks an exhaustive primary table; no arithmetic residual was fabricated. Resolve/The Age (fieldwork recorded as 16–20 November, n=1,000, ALP 36, Coalition 36, Greens 10, Independent 6, Other 12, TPP 53–47) is independently reconstructed with contemporaneous numerical corroboration and awaits owner approval. The governed VEC TPP baseline and AEC relative district/region surfaces pass pre-cutoff input checks; no 2022 prediction has been generated.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored; certifying scored cycles remain 0.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: this batch will be published as one focused reviewable PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 6 observations overall, including 2 2022 Roy Morgan observations from 1 family. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: obtain explicit owner approval for `historical-poll-2022-resolve-2022-11-16-20`, then rerun the fixed 3-observation/2-family sufficiency check. Do not generate or score 2022 before approval.
