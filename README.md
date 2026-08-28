# Victorian Election Forecasting Laboratory

A responsive public-interest forecasting application for the 2026 Victorian state election.

## What is implemented

- An empirical-Bayes, five-party poll of polls with recency weighting, effective-sample-size caps, partially pooled pollster effects and joint covariance.
- 5,000 reproducible correlated simulations across all 88 Legislative Assembly districts.
- Multi-party full-preferential counts with stochastic transfers and no forced Labor–Coalition final pair.
- Official VEC 2022 anchors combined with shrunk AEC-derived local patterns, current enrolment, direct district evidence and guarded by-election signals.
- A separate eight-region, five-member Council model under the enacted voter-directed 2026 rules, with guarded regional polling, exhausted preferences and region-level outcome uncertainty.
- Historical four-cycle validation, including the failed demographic challenger and its zero central model weight.
- Searchable district probabilities, likely final pairs, primary-vote estimates, chamber distributions and uncertainty intervals.
- Plain-English reading guidance and electorate profiles with current enrolment, 2022 baselines and five comparable historical swing cycles.
- An embedded explorer covering 1,729 ordinary voting centres from the VEC's official 2022 first-preference and final-two tables, with source links retained for verification. Federal polling places and non-geographic vote modes are not presented as state-election booths.
- A public Data & sources view separating official evidence, experimental model inputs, validation-only material and display-only evidence.
- A machine-readable source registry with canonical URLs, use status, data dates, criticality, local artefacts and material caveats.
- A generated provenance manifest recording SHA-256 checksums, byte counts and record counts for 14 important local artefacts.
- A public poll series generated directly from the canonical model registry, eliminating the former duplicate hand-written interface list.
- A 21/45/90-day polling sensitivity check showing how recency assumptions affect the statewide estimate.
- Electorate-level “Why this seat?” diagnostics comparing the official 2022-anchored starting point with the 2026 model average, including effective contenders and any guarded by-election signal.
- A single versioned forecast configuration controlling material polling and Assembly assumptions; its checksum is recorded in every forecast manifest.
- A statewide battleground board and five-cycle swing-history view with distributions, crossings, local extremes and boundary-method notes.
- Multi-party, unstable-final-two and recent-by-election hotspot lenses, plus Upper House regional volatility rankings.
- A plain-English four-cycle backtesting ledger showing average error, large-miss error and seat-winner accuracy while preserving the closed production gate.

The forecast is explicitly experimental. It is a research estimate, not voting advice or an authorised production forecast.

## Run the website

```bash
npm ci
npm run dev
```

## Refresh the embedded model output

```bash
PYTHONPATH=model/src python model/scripts/run_experimental_forecast.py --root model
node scripts/generate-model-output.mjs model
node scripts/generate-historical-data.mjs /path/to/reconstructed-model-repository
python3 scripts/generate-vec-booth-data.py
```

The generated TypeScript output is committed so the public static site does not need the large source-data archive at runtime. A minimal reproducible model bundle is included under `model/`.

## Verify source provenance

```bash
npm run data:provenance
npm run data:provenance:check
npm run data:polls
npm run data:polls:check
```

The production build runs the check automatically. A declared source artefact that is missing or has changed without regenerating the manifest fails the build. See `docs/DATA_SOURCES.md` for the source-status rules and update procedure.
