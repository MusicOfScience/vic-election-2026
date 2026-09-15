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

Published August 2026 Upper House regional estimates are retained as a separate processed poll table. They are partially verified and receive guarded model weight because regional sample sizes were not published; they do not override the official VEC baseline.

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

## VEC enrolment refresh

The active enrolment inputs come from the VEC district and region workbooks listed on the canonical electoral-roll statistics page. The repository does not need Excel or a third-party workbook package to validate them: `model/scripts/extract_vec_enrolment.py` reads the XLSX container directly, checks the VEC area type and column contract, requires 88 districts and eight regions, preserves the extraction date, and fails unless district and region elector totals reconcile.

Download both official workbooks outside the repository, then run:

```bash
npm run data:enrolment:extract -- \
  --district-workbook <district.xlsx> \
  --region-workbook <region.xlsx> \
  --output-dir model/data/processed \
  --baseline-district model/data/processed/vec_enrolment_district_2026-06.csv \
  --baseline-region model/data/processed/vec_enrolment_region_2026-06.csv \
  --report metadata/vec-enrolment-validation-2026-09-04.json
npm run data:enrolment:dashboard
```

The 4 September 2026 extract reconciles at 4,683,403 electors in both workbooks. Its validation record retains the official URLs, upstream hashes, output hashes, coverage and comparison with the June inputs. Extraction never promotes a workbook automatically; active paths, provenance, forecasts and the live-source fingerprint still require review together.

## Current limitations

- GitHub-native source-freshness monitoring now runs twice weekly. Acquisition remains guarded and source-specific rather than silently scraping or replacing canonical inputs.
- The public forecast remains experimental and has not cleared the production forecast gate.
- Narracan's January 2023 supplementary-election result is modelled separately, but its physical voting-centre explorer remains a tracked source gap.
