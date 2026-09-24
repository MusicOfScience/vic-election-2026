# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-poll-reuse-basis`
- Base commit: `3962559` (PR #92 merged; remote main verified on 24 September). This batch separates historical poll provenance, methodological adequacy and reuse basis without importing the quarantined candidate dataset.
- Completed: added a machine-readable seven-class reuse policy, a conservative 2018 Essential case adjudication, and validators/tests. The case is independently reconstructed from a first-party PDF, public before the 2018 cutoff, and stores only required structured facts; it remains blocked because the complete five-family model requires an explicit ONP share.
- Safeguards: the legacy 200-row candidate queue remains quarantined and replay-ineligible; no poll rows, forecast outputs, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: policy validator and focused JavaScript evidence tests are added; broader checks are pending this batch. Python replay remains fail-closed.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 source-matched rows and 0 replay-eligible legacy rows. The new policy means null `declaredReuseLicence` is not, by itself, a universal finding against an independently reconstructed factual observation; provenance, model fields and manual reuse review remain separate gates.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: run the full JavaScript checks, then identify a contemporaneous five-family poll or preregister a sparse-poll uncertainty rule before admitting any historical poll to replay. RedBridge owner acceptance and production authorisation remain separate.
