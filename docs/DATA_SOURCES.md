# Data sources and provenance

The source registry at `metadata/sources.json` is the canonical inventory of the external evidence currently represented by the application and model bundle.

It records, for every source group:

- the publisher and canonical URL;
- the type and effective date of the data;
- when the source was last checked;
- whether it is accepted, experimental, display-only or validation-only;
- how the model uses it;
- whether it is critical to the forecast;
- the local artefacts derived from it; and
- material caveats or unresolved gaps.

## Trust and model use are separate

`confidence` describes the source, while `useStatus` describes what the project currently does with it.

An official source may be display-only or experimental. For example, AEC federal-election geography is official data, but it remains a secondary contextual predictor rather than a substitute for VEC state-election results.

Finding or retrieving a source does not automatically authorise it for the central model.

## Generated provenance manifest

Run:

```bash
npm run data:provenance
```

This validates the registry and generates:

- `metadata/source-provenance.generated.json` for machine-readable auditing; and
- `app/source-provenance.generated.ts` for the public Data & sources view.

Every declared local artefact receives a SHA-256 checksum, byte count and—where practical—a record count. The production build runs `npm run data:provenance:check` so stale or missing provenance fails before deployment.

## Adding or changing a source

1. Add or update the source in `metadata/sources.json`.
2. Preserve the raw upstream file outside generated frontend code where licensing and repository size permit.
3. Add a deterministic parser or transformation.
4. Declare every processed or generated artefact in `localArtifacts`.
5. Run `npm run data:provenance`.
6. Run the complete tests and model checks.
7. Submit code, parser or schema changes through a reviewed pull request.

Routine validated data refreshes may later be automated. Parser changes, schema migrations and uncertain corrections must not silently rewrite production data.

## Current limitations

- GitHub-native scheduled acquisition and change detection belong to the later automation phase and are not yet active.
- The public forecast remains experimental and has not cleared the production forecast gate.
- Narracan's January 2023 supplementary-election result is modelled separately, but its physical voting-centre explorer remains a tracked source gap.
