# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/redbridge-review-dossier`
- Base commit: `77dbf42bcba24c2495e6a822a460f204e0b73f49` (PR #80 merged; remote main verified on 24 September). This batch moves the captured 15 September RedBridge/Accent report into the existing poll review dossier without admitting it to model inputs.
- Completed: the report is now `quarantined-awaiting-review`, the dossier covers 8 staged polls, and its recommendation is evidence `accept` with model `conditional_review`. The promotion audit still reports `human-evidence-acceptance-required`; no canonical poll rows were written.
- Safeguards: the report fingerprint, fieldwork/publication dates, sample distinction and five-way toplines are unchanged. Forecast outputs, model configuration, candidate data, historical outcomes and authorisation gates are unchanged. Readiness remains `experimental-blocked`, 4/9; runnable historical cycles remain 0/4.
- Validation: focused primary-source, dossier, freshness and release-readiness tests passed; the promotion audit reported 8 staged and 0 promotable; release readiness regenerated at 24 September and remained 4/9 blocked. Full build/lint remain to be run before publication. Python model tests remain unavailable because this Mac's Python runtimes lack `pytest`.
- Publication: this batch is uncommitted locally. The next operation is a reviewable commit and PR; no push or PR has been made. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: commit this dossier batch, run the full required checks, push one reviewable PR, and inspect its checks once. After merge, verify it; the next decision-dependent blocker is explicit project-owner acceptance and separate RedBridge model-eligibility review.
