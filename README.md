# Victorian Election Forecasting Laboratory

A responsive public-interest forecasting application for the 2026 Victorian state election.

## What is implemented

- An empirical-Bayes, five-party poll of polls with recency weighting, effective-sample-size caps, partially pooled pollster effects and joint covariance.
- 5,000 reproducible correlated simulations across all 88 Legislative Assembly districts.
- Multi-party full-preferential counts with stochastic transfers and no forced Labor–Coalition final pair.
- Official VEC 2022 anchors combined with shrunk AEC-derived local patterns, current enrolment, direct district evidence and guarded by-election signals.
- A separate eight-region, five-member Council model under the enacted voter-directed 2026 rules.
- Historical four-cycle validation, including the failed demographic challenger and its zero central model weight.
- Searchable district probabilities, likely final pairs, primary-vote estimates, chamber distributions and uncertainty intervals.

The forecast is explicitly experimental. It is a research estimate, not voting advice or an authorised production forecast.

## Run the website

```bash
npm ci
npm run dev
```

## Refresh the embedded model output

```bash
python scripts/run_experimental_forecast.py --simulations 5000 --seed 20260826
node scripts/generate-model-output.mjs /path/to/model-repository
```

The generated TypeScript output is committed so the public static site does not need the large source-data archive at runtime. A minimal reproducible model bundle is included under `model/`.
