# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/snapshot-history-ui`
- Base commit: `cd6f95b72782d99db2bbb31b59055854f2dbfd69` (PR #77 merged; remote main verified on 24 September). This batch exposes the existing immutable forecast snapshot ledger in the app's Data & Sources view.
- Completed: users can now see each recorded snapshot's forecast date, gate count, capture date, status and short commit fingerprint. The panel is read-only and uses the existing append-only metadata; no snapshot or forecast values changed.
- Safeguards: no poll, candidate, outcome, forecast or authorisation file changed. The UI wording change cannot open a replay or production gate; `productionCompatible` remains false and runnable cycles remain zero. Narracan remains separately governed by the historical evidence rules.
- Validation: bounded build passed; focused UI tests passed (14); `npm run lint` passed; `git diff --check` passed. Existing non-blocking Recharts zero-size and Vite WebSocket warnings remain under server-side rendering. Python model tests remain unavailable because this Mac's Python runtimes lack `pytest`.
- Publication: this batch is uncommitted locally. The next operation is a reviewable commit and PR; no push or PR has been made. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: commit this snapshot-history UI batch, push one reviewable PR, and inspect its checks once. After merge, verify it and continue responsive QA only where a concrete defect is found; keep historical reconstruction bounded and production gates closed.
