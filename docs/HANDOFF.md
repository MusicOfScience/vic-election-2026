# Project handoff

Updated: 2026-09-16

## Current batch

- Branch: `codex/reconstruct-newspoll-archive`
- Base commit: `65cc47d` (`main` / `origin/main`, PR #71 merged)
- Implementation commit: `d14a501` (`Reconstruct cutoff-safe Newspoll evidence`)
- Outcome: five Newspoll leads are newly matched to timestamped, archived first-party PDFs with observation-specific samples and explicit telephone-survey methods. Across the evidence queue, 62 of 200 leads are now source-matched and 40 have explicit method evidence; 34 Newspoll gaps remain precisely recorded.
- Safeguards: only archive captures available before each historical cutoff were accepted. Cumulative tables without observation-specific samples and election-eve files first captured after their cutoff remain unresolved. The PDFs' attribution and copyright statements are not treated as a formal reusable-data licence. No quarantined vote values were copied, fully reconstructed/imported/replay-eligible counts remain zero, and all 200 leads stay quarantined.
- Forecast effect: none. The current forecast, candidate and poll registries, complete-model backtest/calibration gates, and production authorisation are unchanged. Release readiness remains `experimental-blocked` with 5/9 gates passing.
- Validation: Vinext build, lint, all 125 JavaScript tests, provenance, release-readiness, psephology and model-validation evidence checks passed. All ten pages of the five archived PDFs were also rendered and visually inspected. Existing non-blocking Recharts hidden-size and sandbox WebSocket warnings remain.
- Pull request: [#72](https://github.com/MusicOfScience/vic-election-2026/pull/72) is open and mergeable. The quality job was not started because GitHub reported failed account payments or a spending-limit restriction; this is an account-level Actions block, not a code failure.

## Remaining work

- Close the 34 remaining Newspoll observation gaps only if surviving original or contemporaneously archived publications establish cutoff-safe evidence; then continue with Galaxy and Newspoll2. Do not contact the secondary repository owner until material gaps remain after first-party reconstruction.
- Poll freshness remains blocked by missing newer model-eligible evidence; do not advance the registry date without a complete source.
- Establish cutoff-compliant ballot timing and incumbent/challenger status without inferring unmatched names.
- Extend defensible historical final-pair and preference evidence, then implement leakage-safe executable replays and calibration.

Exact next action: the project owner may review and merge PR #72 based on the complete local validation above. After merge, verify it, fast-forward local `main`, and continue the historical polling evidence queue without changing the forecast.
