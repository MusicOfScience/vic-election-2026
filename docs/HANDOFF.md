# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/reconstruct-older-morgan-polls`
- Base commit: `a6dca1c` (`main` / `origin/main`, PR #68 merged)
- Implementation commit: `7ebfa8a` (`Reconstruct pre-cutoff 2014 Morgan evidence`)
- Outcome: three older SMS Morgan leads are newly matched to timestamped, archived first-party pages with samples and explicit SMS method evidence. Together with Essential, 46 of 200 leads are source-matched and 24 have explicit method evidence.
- Safeguards: archive capture dates, rather than the pages' self-reported publication dates, determine evidence availability. Three later-November 2014 pages remain unresolved because availability by the cutoff is unproved. The September commissioning discrepancy and the existing fieldwork/table discrepancies remain explicit. No quarantined vote values were copied and no source declares reuse authority, so fully reconstructed, imported and replay-eligible counts remain zero and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: ready locally; publication is the next action. GitHub-hosted checks are expected to fail before execution while the account Actions billing/spending limit remains in effect.

## Remaining work

- Close the 20 remaining SMS Morgan and eight Essential observation gaps if surviving original or contemporaneously archived publications can be found; then continue with Newspoll, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: publish the tested branch once and create its review pull request. After the project owner merges it, verify the merge, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
