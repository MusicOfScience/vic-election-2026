# Project handoff

Updated: 2026-09-25

## Current batch

- Branch: `codex/score-frozen-2018-replay`
- Base commit: `b9b4e46` (PR #98 merged; remote main synchronised). Focus cycle remains `vic_la_2018`.
- Completed: official VEC final-pair/winner scoring artefact now covers all 88 districts. The committed prediction hash remains `424552f6…`; it was not regenerated. A separate score artefact and manifest now score the frozen prediction.
- Safeguards: no current 2026 poll, candidate record, forecast output or production gate changed. Historical progress is 1/4 runnable, 1/4 predicted and 1/4 scored.
- Validation: thresholds remain `preregistered-thresholds-fixed`; JavaScript/build/lint/provenance/psephology and isolated Python tests pass. The score is single-cycle evidence; complete backtest and calibration remain closed.
- Publication: PR #99 is open at https://github.com/MusicOfScience/vic-election-2026/pull/99; checks are queued. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 4 independently reconstructed observations from 2 families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: review the first single-cycle score, especially the frozen Assembly seat-scale defect and deferred Council seat scoring. Preserve this score; do not tune or regenerate 2018.
