# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/historical-poll-reconstruction-queue`
- Base commit: `d6ee426` (`main` / `origin/main`, PR #65 merged)
- Implementation commit: `8723893` (`Define historical poll reconstruction queue`)
- Outcome: the fingerprinted 200-row historical polling lead list is now represented by a reproducible aggregate reconstruction queue covering 18 source families. The five largest families account for 142 leads, providing a finite first-party research order without committing observation rows.
- Safeguards: all 200 leads remain quarantined; reconstructed, imported and replay-eligible counts remain zero. Fieldwork midpoint is not treated as publication date. Explicit publication date, sample, method, observation URL and reuse authority remain mandatory.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: deterministic regeneration matched byte-for-byte; Vinext build, lint, all 124 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: ready locally; publication is the next action. GitHub-hosted checks are expected to fail before execution while the account Actions billing/spending limit remains in effect.

## Remaining work

- Work the historical poll queue against original pollster or publisher records, starting with Essential, Newspoll, SMS Morgan, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after that reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: publish the tested branch and create its review pull request. After the project owner merges it, verify the merge, fast-forward local `main`, and begin first-party reconstruction for the highest-priority historical poll source family.
