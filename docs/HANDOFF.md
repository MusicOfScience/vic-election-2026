# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-first-complete-replay`
- Base commit: `627fd5f` (PR #97 merged; remote main synchronised). Focus cycle remains `vic_la_2018`.
- Completed: owner approval for uComms/ReachTEL is recorded and its structured facts are promoted beside the 3 Essential observations (4 observations, 2 independent families). The 2018 readiness contract is runnable; replay execution is explicitly separate from `productionCompatible: false`. A deterministic Assembly/Council prediction is frozen and hashed without loading outcomes.
- Safeguards: no current 2026 poll, candidate record, forecast output, scoring outcome or production gate changed. Runnable historical cycles remain 0/4.
- Validation: thresholds remain `preregistered-thresholds-fixed`; readiness, poll, local-input and Council-input validators are added. JavaScript/build/lint/provenance/psephology checks pass (134 tests); pure-stdlib Python category tests pass, while the existing pytest-based replay tests cannot import because pytest is absent in the documented interpreter.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; the approved replay input now contains 4 independently reconstructed observations from 2 families. The quarantined third-party dataset remains unused.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: recover or reconstruct a separately governed 2018 Assembly final-pair/winner scoring artefact. The prediction manifest exists, but scoring remains fail-closed until actual IRV outcomes are loaded after freeze.
