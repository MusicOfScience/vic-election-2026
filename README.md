# Victorian Election Forecast 2026 — browser dashboard

A responsive public-interest data dashboard built from the sealed 14 August 2026 Victorian Election Forecasting Laboratory checkpoint.

## What it shows

- The current model gate and the reason no 2026 seat probabilities are published yet.
- Searchable reference data for all 88 Legislative Assembly districts.
- Official 2022 ALP two-party-preferred measures and June 2026 enrolment.
- The four-cycle preregistered historical validation result.
- Methodology, integrity and source-provenance status.

Historical results are clearly separated from forecasts. The production forecast gate remains closed because the frozen demographic residual candidate failed its held-out promotion test.

## Run locally

```bash
npm ci
npm run dev
```

## Build

```bash
npm run build
```

## Refresh generated dashboard data

With a reconstructed modelling repository available locally:

```bash
node scripts/generate-dashboard-data.mjs /path/to/vic-election-model
```

The generated TypeScript file is committed so the deployed dashboard does not need the large private/raw source archive at runtime.
