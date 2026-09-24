# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/prod-1.0-completion`
- Base commit: `a32b1e972eff7e707c0afce55384fa7aeb4601ca` (PR #73 merged; remote main verified on 24 September). This batch stages a current primary poll and hardens freshness cutoff handling.
- Completed: two more Newspoll observations matched, bringing the total to 64/200 source matches and 41 cutoff-verified methods. Newspoll has seven matches, six verified methods and 32 unmatched leads. Queue and inventory hashes reconcile.
- Evidence: the Nov-Dec 2011 branded PDF survives in a contemporaneous third-party archive. The May-Jun 2015 publisher graphic is linked from a cutoff-safe archived article confirming its sample. That article does not preserve the graphic binary; its current method text is corroborating only and excluded from verified method coverage. Retrieval dates and fingerprints retain the 16 September inspection; the review and queue are dated 23 September.
- Safeguards: all 200 historical polling leads remain quarantined and none is replay-eligible. A 15 September 2026 RedBridge/Accent Victorian report is now staged for review, but it has not entered model inputs. Missing reuse authority and historical evidence still block promotion. Forecast code, inputs, outputs, candidate registry and authorisation files are unchanged. Readiness is `experimental-blocked`, 4/9 gates passing because the staged report is newer than the 8 August model poll and remains unresolved, alongside the existing backtest, calibration and authorisation blockers.
- Validation: build and all 128 JavaScript tests passed; lint passed; targeted evidence, readiness, provenance and candidate checks passed. Python model tests were not runnable because this Mac's Python lacks `pytest` (the bundled runtime also lacks it). Existing non-blocking build size, dependency deprecation, Recharts and sandbox WebSocket warnings remain. No forecast simulation or model input changed.
- Publication: this batch is uncommitted locally. The next operation is a reviewable commit and PR; no push or PR has been made. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: commit this staged-poll and cutoff-freshness batch, then review the PR checks once. After merge, verify it and continue the PROD ledger from the unresolved historical replay/backtest workstream without changing active forecasts.
