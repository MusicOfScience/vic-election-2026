# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/restore-source-freshness`
- Base commit: `2e092b7` (`main` / `origin/main` after PR #64 merged)
- Implementation commit: `d5c33f9` (`Refresh validated VEC enrolment inputs`)
- Outcome: the official VEC August 2026 district and region workbooks, extracted 4 September, are validated, reconciled and promoted through a review branch. The 88 districts and eight regions each total 4,683,403 electors; upstream and processed hashes are retained.
- Forecast effect: no favoured-party or likely-final-pair changes; maximum district win-probability movement is 0.12 percentage points; hung-parliament probability moves from 76.38% to 76.48%; Council major-party-no-control probability remains 100%.
- Safeguards: polling inputs and candidate promotion are unchanged. Production, complete-model backtest and calibration authorisation remain closed. The poll registry is now explicitly stale, so readiness is 5/9 gates rather than carrying forward the older 28 August assessment.
- Validation: deterministic refresh and source reconciliation passed; 122 JavaScript tests and 17 Python tests passed; lint, Vinext build, provenance, poll, candidate, psephology, validation-evidence and staged-shadow checks passed. Desktop and phone rendering passed, including the 50,488 Albert Park enrolment value. A non-blocking Recharts hidden-tab size warning remains; the SVG hydration mismatch found during review was fixed.
- Snapshot: `vec-enrolment-2026-09-04` fingerprints implementation commit `d5c33f9`.
- Pull request: [#65](https://github.com/MusicOfScience/vic-election-2026/pull/65), ready for project-owner review. GitHub-hosted checks may fail before running because of the account Actions billing/spending limit; local equivalents passed.

## Remaining work

- Poll freshness is blocked by missing newer model-eligible evidence: the Roy Morgan sources were healthy and unchanged on 15 September, discovery found no newer complete poll, and the DemosAU reader fallback did not yield a parseable new record. Do not advance the registry date without new evidence.
- Reconstruct first-party historical poll vintages with publication date, sample, method, observation source and reuse authority.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: project owner reviews and merges PR #65. A merge to `main` normally starts forecast validation, staged-shadow and GitHub Pages deployment workflows. After the merge, verify it, fast-forward local `main`, and begin the historical poll-vintage evidence batch unless a newer complete Victorian poll becomes available first.
