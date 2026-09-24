# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-replay-runner`
- Base commit: `4dc4ae56b4a48fe540c0a2dcd67ecfc88877534f` (PR #81 merged; remote main verified on 24 September). This batch adds a reusable fail-closed Python replay orchestrator.
- Completed: `vicforecast.historical_replay.run_historical_replay` loads a frozen cycle, enforces publication cutoffs, rejects undated/later prediction evidence, refuses outcomes before prediction is frozen, and returns structured blockers for all four currently unrunnable cycles. No replay or gate is opened.
- Safeguards: RedBridge remains quarantined and model-ineligible pending explicit owner review; no poll rows, forecast outputs, candidate data, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: Python compile and CLI smoke test passed; later/undated evidence and premature outcome checks passed in direct smoke tests. Full JavaScript/build checks remain to be run before publication. Python `pytest` remains unavailable because it is not installed in the local runtimes.
- Publication: this batch is uncommitted locally. The next operation is a reviewable commit and PR; no push or PR has been made. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: run the full required checks, commit this replay-runner batch, push one reviewable PR, and inspect its checks once. After merge, verify it; the next decision-dependent blocker is explicit project-owner acceptance and separate RedBridge model-eligibility review.
