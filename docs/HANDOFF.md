# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-slate-2010-timing`
- Base commit: `499aab0` (PR #86 merged; remote main verified on 24 September). This batch records the official VEC 2010 election report’s nomination timing and candidate-list limitation.
- Completed: the VEC 2010 report is fingerprinted and records party nominations closing 11 November 2010 and other candidates’ nominations closing 12 November 2010, with Appendix 14 candidate identities. Because it is a post-election report, it does not prove pre-cutoff availability.
- Previous batch retained: `vicforecast.historical_replay.run_historical_replay` remains fail-closed, enforces publication cutoffs and returns structured blockers for all four currently unrunnable cycles. No replay or gate is opened.
- Safeguards: RedBridge remains quarantined and model-ineligible pending explicit owner review; no poll rows, forecast outputs, candidate data, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: `npm run validation:evidence`, JSON parsing and `git diff --check` passed. Forecast outputs and readiness gates are unchanged.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: commit this focused evidence batch, run the required checks, and publish one reviewable PR. The timing-framework pass now covers all four cycles; next locate archived candidate-list captures or equivalent primary records proving candidate-specific timing, while RedBridge owner acceptance remains a separate decision-dependent blocker.
