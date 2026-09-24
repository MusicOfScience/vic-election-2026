# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-slate-timing`
- Base commit: `93467fc` (PR #82 merged; remote main verified on 24 September). This batch records a verified official VEC nomination-timing source for the 2022 cycle.
- Completed: the VEC 2022 candidate handbook is fingerprinted and recorded as timing-framework evidence: party nominations closed 10 November 2022 and independent nominations 11 November 2022. This narrows the slate-timing gap but does not prove candidate-specific acceptance/publication timing.
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

Exact next action: commit this focused evidence batch, run the required checks, and publish one reviewable PR. Then continue candidate-specific 2022 slate timing and alias evidence; RedBridge owner acceptance remains a separate decision-dependent blocker.
