# Project handoff

Updated: 2026-09-15

## Current batch

- Branch: `codex/reconstruct-essential-polls`
- Base commit: `68e659e` (`main` / `origin/main`, PR #66 merged)
- Implementation commit: `1b42974` (`Reconstruct Essential historical poll evidence`)
- Outcome: 33 of 41 Essential leads are matched to 10 dated first-party pollster or commissioning-publisher sources with observation URLs and samples. Twelve have observation-specific method evidence; eight remain unresolved.
- Safeguards: no quarantined vote values were copied. A source date records only when that source proves the observation was public and is checked against the frozen cycle cutoff; it is not relabelled as the original release date. No source declares reuse authority, so fully reconstructed, imported and replay-eligible counts remain zero and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: ready locally; publication is the next action. GitHub-hosted checks are expected to fail before execution while the account Actions billing/spending limit remains in effect.

## Remaining work

- Close the eight Essential observation gaps if surviving original publications can be found; otherwise continue with Newspoll, SMS Morgan, Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: commit this handoff, publish the tested branch once and create its review pull request. After the project owner merges it, verify the merge, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
