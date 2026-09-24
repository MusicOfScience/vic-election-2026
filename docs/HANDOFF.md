# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-first-runnable-cycle`
- Base commit: `7297c55` (PR #95 merged; remote main verified on 24 September). Focus cycle selected by input completeness: `vic_la_2018`, without viewing replay scores.
- Completed: the 3 approved Essential observations remain governed replay inputs; fail-closed local and Council builders now point to the exact missing artefacts. The modern 2026 Council poll is explicitly rejected as post-cutoff. No broad archival search was started.
- Safeguards: no current 2026 poll, candidate record, forecast output, scoring outcome or production gate changed. Runnable historical cycles remain 0/4.
- Validation: thresholds remain `preregistered-thresholds-fixed`; readiness, poll, local-input and Council-input validators are added. JavaScript/build/lint/provenance/psephology checks pass (134 tests); pure-stdlib Python category tests pass, while the existing pytest-based replay tests cannot import because pytest is absent in the documented interpreter.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; independently reconstructed replay inputs total 3 observations from 1 source family under explicit owner approval. The common rule requires at least 3 observations from 2 independent families, so 2018 remains blocked without inventing precision.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: the targeted Newspoll family remains blocked because the archived asset lacks safe structured primary shares; recover an equivalent first-party record only if available. Then restore the missing boundary-aligned local artefact and construct a pre-cutoff Council prior. RedBridge owner acceptance and production authorisation remain separate.
