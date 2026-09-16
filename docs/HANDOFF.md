# Project handoff

Updated: 2026-09-16

## Current batch

- Branch: `codex/close-morgan-poll-audit`
- Base commit: `77a92c0` (`main` / `origin/main`, PR #70 merged)
- Implementation commit: `c062490` (`Close cutoff-safe Morgan polling evidence gap`)
- Outcome: the 1 August 2015 SMS Morgan lead is newly matched to a timestamped, archived first-party page with a 1,089-elector Victorian sample and explicit SMS method evidence. Together with Essential, 57 of 200 leads are source-matched and 35 have explicit method evidence.
- Safeguards: the archived 2018 election-eve page was deliberately rejected because its `2018-11-23T17:22:56Z` capture was already 24 November in Melbourne, after the 23 November local cutoff. Nine Morgan gaps remain precisely recorded. No quarantined vote values were copied and no source declares reuse authority, so fully reconstructed, imported and replay-eligible counts remain zero and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: [#71](https://github.com/MusicOfScience/vic-election-2026/pull/71) is open and mergeable. The quality job was not started because GitHub reported failed account payments or a spending-limit restriction; this is an account-level Actions block, not a code failure.

## Remaining work

- Close the nine remaining SMS Morgan and eight Essential observation gaps only if surviving original or contemporaneously archived publications can establish cutoff-safe evidence; otherwise continue with Newspoll, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: the project owner may merge PR #71 based on the complete local validation above. After merge, verify it, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
