# Victorian Election Forecasting Laboratory — browser dashboard

A responsive public-interest research dashboard built from the sealed 14 August 2026 Victorian Election Forecasting Laboratory checkpoint.

## What it shows

- A nine-poll, multi-party benchmark with recency and sample-size weighting.
- Sensitivity to 21-, 45- and 90-day poll half-lives, plus the complete eligible-poll registry.
- The evidence stack: polling, official results, boundary lineage, demographics, preference distributions and historical validation.
- A searchable conditional-scenario explorer for all 88 Legislative Assembly districts.
- Council-region external benchmarks, kept distinct from model outputs.
- The four-cycle preregistered held-out validation result and current model gate.

Roy Morgan is one polling input and one external Council benchmark; it is not presented as the forecasting model. Historical results, external commentary, polling benchmarks, scenario diagnostics and authorised model outputs are kept visually and methodologically distinct. The production forecast gate remains closed because the frozen demographic residual candidate failed its held-out promotion test.

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
