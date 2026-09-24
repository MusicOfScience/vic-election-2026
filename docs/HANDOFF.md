# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/replay-preference-prior-integration`
- Base commit: `781c6b1` (PR #89 merged; remote main verified on 24 September). This batch passes the fail-closed walk-forward preference prior into a future runnable replay runner only.
- Completed: evidence-complete cycles will construct the prior before forecast execution and provide it to the explicit forecast runner; currently blocked cycles and the 2026 forecast remain unchanged. No transfer parameters were promoted.
- Previous batch retained: `vicforecast.historical_replay.run_historical_replay` remains fail-closed, enforces publication cutoffs and returns structured blockers for all four currently unrunnable cycles. No replay or gate is opened.
- Safeguards: RedBridge remains quarantined and model-ineligible pending explicit owner review; no poll rows, forecast outputs, candidate data, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: Python compilation and blocked replay CLI smoke passed; NumPy/pytest-dependent prior tests remain unavailable in the local interpreter. Forecast outputs and readiness gates are unchanged.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: run the full JavaScript checks, commit this replay integration batch, and publish one reviewable PR. Then supply independently reconstructed earlier-cycle preference evidence or retain the broad fallback and keep replay blocked; RedBridge owner acceptance remains separate.
