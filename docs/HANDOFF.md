# Project handoff

Updated: 2026-09-14

## Current batch

- Branch: `codex/audit-narracan-cutoff`
- Base commit: `a746275` (`main` / `origin/main` at batch start)
- Outcome: Narracan's 28 January 2023 supplementary result is explicitly separated from the November 2022 validation cycle. It remains available only as a separately dated scoring outcome.
- Forecast effect: none. The approved experimental forecast inputs and outputs are unchanged.
- Authorisation: production remains closed; historical replay and probability-calibration gates remain closed.
- Validation: deterministic forecast refresh produced no forecast diff; 119 JavaScript tests and 15 Python tests passed; lint, build, provenance, poll, candidate, psephology, validation-evidence and staged-shadow checks passed.
- Pull request: pending one publication attempt after the batch commit.

## Remaining work

- Restore current critical-source freshness for VEC enrolment and the Victorian poll registry through the existing quarantine and review workflow.
- Reconstruct first-party historical poll vintages with publication date, sample, method, observation source and reuse authority.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: publish the tested branch and open the prepared pull request if GitHub accepts the operation; otherwise retain the local commit and record the precise blocker.
