# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-ballot-aware-polling`
- Base commit: `17cd38b` (PR #93 merged; remote main verified on 24 September). This batch tests whether historical poll adequacy must use the 2026 five-family ballot schema.
- Completed: added a machine-readable seven-class reuse policy, a cycle-aware ballot-family contract, and validators/tests. Candidate evidence shows no One Nation Assembly candidates in 2010, 2014 or 2018 and four in 2022. The 2018 Essential case is independently reconstructed from a first-party PDF, public before the cutoff, and stores only required structured facts; its grouped residual is methodologically adequate for the active four-family ballot universe but still awaits manual reuse review.
- Safeguards: the legacy 200-row candidate queue remains quarantined and replay-ineligible; no poll rows, forecast outputs, historical outcomes or authorisation gates changed. Runnable historical cycles remain 0/4.
- Validation: policy validator and focused JavaScript evidence tests are added; broader checks are pending this batch. Python replay remains fail-closed.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 source-matched rows and 0 replay-eligible legacy rows. The new policy means null `declaredReuseLicence` is not, by itself, a universal finding against an independently reconstructed factual observation; provenance, cycle-aware model fields and manual reuse review remain separate gates.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: complete the governed manual review decision for the 2018 Essential case; meanwhile finish ballot/slate and preference evidence needed for an end-to-end replay. RedBridge owner acceptance and production authorisation remain separate.
