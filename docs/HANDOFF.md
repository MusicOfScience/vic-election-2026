# Project handoff

Updated: 2026-09-24

## Current batch

- Branch: `codex/historical-replay-readiness`
- Base commit: `4d94195` (PR #94 merged; remote main verified on 24 September). This batch records the owner-approved Essential replay input, fixes acceptance thresholds before scoring, and defines per-cycle replay sufficiency.
- Completed: owner review `historical-poll-review-2018-essential-2026-09-24` approves only the structured Essential facts. Three observations are now governed replay inputs; the quarantined 200-row lead list remains untouched. The 2018 case passes provenance and ballot-aware methodology, but its one independent source family fails the common sparse-poll sufficiency rule.
- Safeguards: no current 2026 poll, candidate record, forecast output, scoring outcome or production gate changed. Runnable historical cycles remain 0/4.
- Validation: thresholds are now `preregistered-thresholds-fixed`; readiness and owner-review validators are added. Python replay remains fail-closed.
- Publication: this batch is local and uncommitted. The next operation is a reviewable commit and PR; do not merge or deploy manually.
- Preserved user files: `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` remain untracked and untouched.

## Remaining work and blockers

- Continue the finite historical polling queue with Galaxy and Newspoll2 after this batch; 32 Newspoll matches remain unresolved. Several publisher PDF retrieval attempts returned 403 and the tested archive alternatives were empty. Do not repeat unchanged requests or treat all discovered links as individually tested.
- Historical polling still has 64/200 legacy source-matched rows and 0 legacy queue rows; independently reconstructed replay inputs now total 3 observations from 1 source family under explicit owner approval. The common rule requires at least 3 observations from 2 independent families, so 2018 remains blocked without inventing precision.
- Newer model-eligible polling is still needed for freshness. Do not advance registry dates without complete evidence.
- Ballot availability, alias-aware incumbency, final-pair and preference evidence remain prerequisites for leakage-safe complete-model replay and calibration. Keep Narracan's January 2023 contest separate.

Exact next action: recover or reconstruct a second independent pre-cutoff 2018 poll family, then complete the cycle-specific local/contest and Council inputs. RedBridge owner acceptance and production authorisation remain separate.
