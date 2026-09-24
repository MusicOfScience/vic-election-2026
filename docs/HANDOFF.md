# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/preregister-validation-criteria`
- Base commit: `c4e8922` (PR #91 merged; remote main verified on 24 September). This batch adds a version-controlled historical validation acceptance protocol.
- Completed: the protocol fixes the four-cycle unit of replication, cycle-clustered dependence treatment, required baselines and metrics, and forbids score-driven thresholds or automatic production opening. No replay scores exist yet and the 2026 forecast remains unchanged.
- Previous batch retained: `vicforecast.historical_replay.run_historical_replay` remains fail-closed, enforces publication cutoffs and returns structured blockers for all four currently unrunnable cycles. No replay or gate is opened.
- Safeguards: RedBridge remains quarantined and model-ineligible pending explicit owner review; no poll rows, forecast outputs, candidate data, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: JSON/acceptance validation and release checks pass; no replay scores were examined. Forecast outputs and readiness gates are unchanged.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: run the full JavaScript checks, commit this acceptance-protocol batch, and publish one reviewable PR. Before the first complete replay score is interpreted, register performance thresholds; RedBridge owner acceptance remains separate.
