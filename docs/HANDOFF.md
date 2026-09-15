# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/reconstruct-midcycle-morgan-polls`
- Base commit: `60bdd65` (`main` / `origin/main`, PR #69 merged)
- Implementation commit: `c0498b6` (`Reconstruct mid-cycle Morgan poll evidence`)
- Outcome: ten 2015-2016 SMS Morgan leads are newly matched to timestamped, archived first-party pages with Victorian samples and explicit SMS method evidence. Together with Essential, 56 of 200 leads are source-matched and 34 have explicit method evidence.
- Safeguards: archive capture dates, rather than the pages' self-reported publication dates, determine evidence availability. Two matching 2015 pages remain unresolved because a cutoff-safe capture was not established. Conflicting February 2015 fieldwork and total-sample statements are preserved. No quarantined vote values were copied and no source declares reuse authority, so fully reconstructed, imported and replay-eligible counts remain zero and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: ready locally; publication is the next action. GitHub-hosted checks are expected to remain blocked before execution by the account Actions billing/spending restriction.

## Remaining work

- Close the ten remaining SMS Morgan and eight Essential observation gaps if surviving original or contemporaneously archived publications can be found; then continue with Newspoll, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: publish the tested branch once and create its review pull request. After the project owner merges it, verify the merge, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
