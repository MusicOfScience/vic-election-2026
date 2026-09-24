# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/prod-1-frozen-replay`
- Base commit: `c9f5916e40ec4683ae8ca1648d5cfddc92a961d8` (PR #75 merged; remote main verified on 24 September). This batch adds a fail-closed validator for the four historical replay specifications.
- Completed: the replay contract now checks canonical cycle IDs and cutoffs, deterministic seeds, scoring-only outcomes, publication-date leakage rules, required seat outputs and disclosed blockers. All four cycles remain explicitly unrunnable until residual poll, ballot and preference inputs are evidenced.
- Safeguards: no poll, candidate, outcome, forecast or authorisation file changed. The validator cannot open a replay or production gate; `productionCompatible` remains false and runnable cycles remain zero. Narracan remains separately governed by the historical evidence rules.
- Validation: 129 JavaScript tests passed; `npm run lint` passed after removing an unused constant; `npm run validation:replay-contract` passed; `git diff --check` passed. Python model tests remain unavailable because this Mac's Python runtimes lack `pytest`.
- Publication: this batch is uncommitted locally. The next operation is a reviewable commit and PR; no push or PR has been made. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: commit this replay-contract batch, push one reviewable PR, and inspect its checks once. After merge, verify it and continue the PROD ledger from the unresolved historical replay/backtest workstream without changing active forecasts.
