# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/reconstruct-sms-morgan-polls`
- Base commit: `7a2aa92` (`main` / `origin/main`, PR #67 merged)
- Implementation commit: `6196cbc` (`Reconstruct SMS Morgan historical poll evidence`)
- Outcome: ten of 33 SMS Morgan leads are matched to dated first-party Roy Morgan pages with observation URLs and samples; nine have explicit SMS method evidence. Together with Essential, 43 of 200 leads are source-matched and 21 have explicit method evidence.
- Safeguards: no quarantined vote values were copied. The approval-only September 2020 lead remains unresolved, and four source fieldwork/table-label discrepancies remain explicit. Every availability date is tied to its cited source and checked against the frozen cycle cutoff. No source declares reuse authority, so fully reconstructed, imported and replay-eligible counts remain zero and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: ready locally; publication is the next action. GitHub-hosted checks are expected to fail before execution while the account Actions billing/spending limit remains in effect.

## Remaining work

- Close the 23 older SMS Morgan and eight Essential observation gaps if surviving original or contemporaneously archived publications can be found; then continue with Newspoll, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: commit this handoff, publish the tested branch once and create its review pull request. After the project owner merges it, verify the merge, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
