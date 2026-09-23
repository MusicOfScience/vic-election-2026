# Project handoff

Updated: 2026-09-23

## Current batch

- Branch: `codex/continue-newspoll-archive`
- Base commit: `3886a44381009d973a1ad94a8c25440290857af5` (PR #72 merged; remote main verified unchanged on 23 September). Implementation: the commit containing this handoff, titled `Extend Newspoll evidence with explicit archive limitations`.
- Completed: two more Newspoll observations matched, bringing the total to 64/200 source matches and 41 cutoff-verified methods. Newspoll has seven matches, six verified methods and 32 unmatched leads. Queue and inventory hashes reconcile.
- Evidence: the Nov-Dec 2011 branded PDF survives in a contemporaneous third-party archive. The May-Jun 2015 publisher graphic is linked from a cutoff-safe archived article confirming its sample. That article does not preserve the graphic binary; its current method text is corroborating only and excluded from verified method coverage. Retrieval dates and fingerprints retain the 16 September inspection; the review and queue are dated 23 September.
- Safeguards: all 200 polling leads remain quarantined and none is replay-eligible. Missing reuse authority and historical evidence still block promotion. Forecast code, inputs, outputs, candidate/poll registries and authorisation files are unchanged. Readiness remains `experimental-blocked`, 5/9 gates passing.
- Validation: build, all 126 JavaScript tests, lint, candidate and psephology checks passed. The build also verified model output, poll/provenance/readiness artefacts, historical evidence, candidate review and staged-poll safeguards. The queue was regenerated from the hash-verified pinned lead file. Diff check passed with no generated forecast drift. Model simulations were not rerun because model code and inputs did not change. Existing non-blocking build size, dependency deprecation, Recharts and sandbox WebSocket warnings remain. No interface changes.
- Publication: locally ready; push and PR creation are the next operation. No PR exists at the time of this commit. Previous PR #72 had an Actions account payments/spending-limit failure; do not assume the new run will share it. Branch push has no matching workflow trigger; PR creation runs quality checks. Merging to main normally triggers Pages deployment and source monitoring. Do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling reuse authority is unestablished. No owner contact is required yet; complete the existing first-party reconstruction before escalating residual gaps.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: publish this tested branch and create its PR, then inspect the actual check result once. The owner merges. After verified merge, fast-forward main safely and work on the existing Galaxy/Newspoll2 queue without changing active forecasts.
