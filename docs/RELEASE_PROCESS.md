# Forecast update and release process

The project follows a fail-closed, pull-request-based release process. Automation may detect a change, regenerate outputs and report readiness, but it never promotes an experimental forecast to production by itself.

## Normal update

1. Update the canonical source registry and its local source artefacts. Preserve the original source URL, effective date, verification status and caveats.
2. Run `npm run forecast:refresh`. This reruns the seeded model and rebuilds the website-facing poll, model, provenance and readiness artefacts.
3. Review the Git diff. A timestamp-only or no-op update is not a material release.
4. Run `python -m pytest model/tests`, `npm test` and `npm run lint`.
5. Submit the change through a pull request. Publish only the reviewed commit that passed all checks.

## Automated checks

- **Forecast quality gates** run on pull requests and `main`. They regenerate every deterministic artefact and fail if the committed outputs differ.
- **Source freshness monitor** runs twice weekly and can also be started manually. It assesses each critical source against its explicit staleness threshold and uploads a machine-readable report.
- For a targeted update, `npm run forecast:refresh:changed -- BASE_REF` uses content changes—not file timestamps—to rerun only affected forecast, public-data and provenance stages.
- Source monitoring does not scrape or silently replace canonical inputs. Acquisition remains guarded until a source-specific parser and validation contract exist.

## Production gate

A release requires current source fingerprints, fresh critical inputs, matching model output and configuration hashes, the historical validation ledger, and explicit production authorisation for the complete probability model. The last gate is currently closed. If any required gate fails, retain the last valid forecast and do not publish new probabilities as production-ready.
