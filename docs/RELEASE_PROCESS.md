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

## Production gate

A release requires current source fingerprints, fresh critical inputs, matching model output and configuration hashes, the historical validation ledger, and explicit production authorisation for the complete probability model. The last gate is currently closed. If any required gate fails, retain the last valid forecast and do not publish new probabilities as production-ready.
