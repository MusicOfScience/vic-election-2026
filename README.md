# Victorian Election Forecast 2026

A responsive, experimental 2026 Victorian state election forecast and data atlas.

## Open in a browser

Once GitHub Pages is enabled for this repository, open:

https://musicofscience.github.io/vic-election-2026/

The site is also deployed at:

https://vic-election-forecast-2026.hxz.chatgpt.site

## What it shows

- A clearly labelled provisional Legislative Assembly forecast.
- Government-outcome probabilities and a full seat-count distribution.
- A live scenario slider for the statewide Labor two-party vote.
- Forecasts and uncertainty for all 88 districts.
- A region-by-region Legislative Council projection.
- Polling, historical validation, model limits and source links.

The default lower-house benchmark anchors to Roy Morgan's 5–7 August 2026 poll (ALP 49%, Coalition 51% two-party preferred), applies uniform swing to official 2022 district results, and uses the historical baseline RMSE as a conditional district-error envelope. It is deliberately labelled experimental and is not voting advice.

## Run locally

```bash
npm ci
npm run dev
```

## Build for Sites

```bash
npm run build
```

## Build the static GitHub Pages version

```bash
GITHUB_PAGES=true npx next build
```

The GitHub Actions workflow in `.github/workflows/deploy-pages.yml` builds and publishes the static site automatically after pushes to `main`.
