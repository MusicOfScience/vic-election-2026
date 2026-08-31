# Forecast update and release process

The project follows a fail-closed, pull-request-based release process. Automation may detect a change, regenerate outputs and report readiness, but it never promotes an experimental forecast to production by itself.

## Normal update

1. Update the canonical source registry and its local source artefacts. Preserve the original source URL, effective date, verification status and caveats.
2. Run `npm run forecast:refresh`. This reruns the seeded model and rebuilds the website-facing poll, model, provenance and readiness artefacts.
3. Review the Git diff. A timestamp-only or no-op update is not a material release.
4. Run `python -m pytest model/tests`, `npm test` and `npm run lint`.
5. Submit the change through a pull request. Publish only the reviewed commit that passed all checks.
6. If the material forecast changed, append an immutable snapshot with `npm run snapshot:create` before release.

## Automated checks

- **Forecast quality gates** run on pull requests and `main`. They regenerate every deterministic artefact and fail if the committed outputs differ.
- **Source freshness and live-source monitor** runs twice weekly and can also be started manually. It assesses critical-source staleness, validates live source contracts and uploads machine-readable reports.
- **Live-source quarantine** fingerprints canonical upstream responses. Changed or invalid sources are retained for review and never silently promoted into model inputs.
- **Candidate validation** enforces provisional versus VEC-official candidate states and rejects invalid official status claims.
- For a targeted update, `npm run forecast:refresh:changed -- BASE_REF` uses content changes—not file timestamps—to rerun only affected forecast, public-data and provenance stages.

## Live-source promotion

A valid changed source is not automatically accepted. Review `live-source-report.json`, confirm that the publisher, date, semantics and parsed values are what the model expects, then run `npm run sources:promote -- --id <adapter-id> --report live-source-report.json`. Commit the resulting state change through a pull request before adapting any canonical model input.

## Production gates

The readiness report deliberately separates historical **data availability** from predictive **model validation**. A four-cycle ledger proves that the historical substrate exists; it does not certify the complete 2026 probability model.

A production release requires all of the following:

- current source fingerprints and critical-source age checks;
- no newer reviewed evidence left unresolved outside the canonical model input;
- matching model output and configuration hashes;
- the four-cycle historical dataset;
- walk-forward backtesting of the complete multi-party seat model;
- probability calibration and interval-coverage tests;
- sufficient 2026 candidate evidence across all 88 Assembly districts; and
- explicit production authorisation.

Feature experiments are recorded separately. The demographic challenger failed its sealed promotion test and remains at zero central weight. That rejection is an honest modelling result, not a failed requirement that prevents a simpler validated model from eventually reaching production.

`metadata/model-validation-evidence-contract.json` records the evidence required to test the complete system. The existing four-cycle TPP residual ledger satisfies the two-party benchmark component only. Leakage-safe specifications are now frozen for 2010, 2014, 2018 and 2022, but they are deliberately unrunnable: historical polling vintages are missing and party-primary/ballot, preference/final-pair and Council evidence remains partial.

`metadata/model-validation-evidence-inventory.json` is the fingerprinted, machine-audited account of progress against that contract. It currently records one complete component, five partial components and one missing component. The partial evidence includes 2022 district-primary and ballot records, 39 indicative Assembly preference distributions, high-level anchors for all eight 2022 Council regions and four deterministic historical cycle specifications. The specifications enforce election-eve cutoffs, scoring-only outcomes and zero weight for the rejected demographic challenger. These artefacts improve the validation substrate but do not open either complete-model gate.

If any required gate fails, retain the last valid forecast and do not publish new probabilities as production-ready.
