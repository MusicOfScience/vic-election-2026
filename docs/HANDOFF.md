# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-replay-no-leakage`
- Base commit: `5aec3b4` (PR #96 merged; remote main synchronised). Focus cycle remains `vic_la_2018`, selected without viewing replay scores.
- Completed: the 3 approved Essential observations remain governed replay inputs; the local builder now uses only the pre-cutoff 2014 Assembly baseline and rejects the 2014→2018 outcome-transition file. Council has a governed broad prior from 2014 regional structure. Verified uComms/ReachTEL facts are staged for owner approval.
- Safeguards: no current 2026 poll, candidate record, forecast output, scoring outcome or production gate changed. Runnable historical cycles remain 0/4.
- Validation: thresholds remain `preregistered-thresholds-fixed`; readiness, poll, local-input and Council-input validators are added. JavaScript/build/lint/provenance/psephology checks pass (134 tests); pure-stdlib Python category tests pass, while the existing pytest-based replay tests cannot import because pytest is absent in the documented interpreter.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; independently reconstructed replay inputs total 3 approved Essential observations from 1 family. uComms/ReachTEL is admissible but remains `awaiting-project-owner-approval`.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: obtain owner approval for the uComms/ReachTEL structured-facts case, then promote it through the governed path and connect the separated inputs to the guarded replay runner. Production authorisation remains closed.
