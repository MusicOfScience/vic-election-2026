# Operational readiness

Batch 7 adds a guarded live-data operating layer without changing the experimental forecast or opening the production-authorisation gate.

## Live-source contract

Every monitored upstream source has an adapter in `metadata/live-source-adapters.json` with a canonical HTTPS URL, expected semantic markers, a minimum payload size, criticality and a promotion policy.

`scripts/monitor-live-sources.mjs` fetches each source, removes volatile script/style content, validates the contract and fingerprints the canonical response. A changed or invalid source is quarantined; it is never promoted into the forecast automatically.

The state file `metadata/live-source-state.json` stores only fingerprints that have been reviewed and accepted. After reviewing a valid monitor report, promote one source explicitly with:

```bash
npm run sources:promote -- --id <adapter-id> --report live-source-report.json
```

Commit that state change through a pull request. This makes source acquisition fail closed: a layout change, correction or unexpected payload cannot silently alter published probabilities.

## Candidate lifecycle

`metadata/candidates-2026.json` is the canonical 2026 candidate register. Before nominations close, public declarations and party endorsements may be recorded as `announced` or `endorsed` with a primary source URL. Only VEC evidence may promote a candidate to an official nomination/result state.

The VEC nomination window is encoded as 4–9 November 2026. `npm run candidates:validate` rejects duplicate/incomplete records and official statuses without VEC authority.

## Forecast snapshots

`metadata/forecast-snapshots.json` is append-only for material forecast releases. Create a snapshot only after reviewed inputs change the forecast:

```bash
npm run snapshot:create -- --id <snapshot-id> --captured-at <ISO-time> --commit-sha <sha>
```

Each generated snapshot records the forecast/config/source/candidate fingerprints and release-gate status, allowing later reconstruction of what the model said and why.

## Monitoring cadence

The GitHub Actions source monitor runs twice weekly and uploads both release-readiness and live-source reports for 90 days. It validates the candidate registry on the same run. Closer to nomination week and election day the cadence can be increased deliberately after the VEC publishes stable candidate/results endpoints.

## What Batch 7 does not do

It does not scrape unreviewed numbers into the model, infer official candidates from media reports, auto-open the production gate, or consume election-night results before a separately tested VEC results adapter exists. Those are explicit promotion decisions, not missing safeguards.
