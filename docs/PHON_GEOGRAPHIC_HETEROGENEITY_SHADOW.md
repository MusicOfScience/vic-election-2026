# PHON geographic heterogeneity — governed shadow workstream

Updated: 2026-10-28
Status: shadow-only research and validation; no canonical parameter or forecast change

## Purpose

Recent Victorian polling places One Nation in the low-20s statewide, while independent electoral geography indicates that support is unlikely to be distributed uniformly across Assembly districts. This workstream tests whether updating and/or changing the persistence of PHON geography materially changes district final-pair composition or statewide government probabilities.

This document does **not** authorise a production change. The 8 October canonical forecast remains frozen. All tests described here are challenger/shadow analyses until they pass the repository's existing validation and owner-admission gates.

## Code-audit correction: the current model already contains PHON geography

Inspection of `model/src/vicforecast/forecast_2026.py` after opening this workstream found that the current Assembly model is **not geographically uniform for One Nation**. `build_assembly_seed()` derives `onp_local_log` from the AEC 2022 ecological surface with statewide contest coverage; the simulation then replaces the sparse 2022 Victorian state-ballot ONP pattern with that federal ecological propensity before applying regional and district shocks.

This materially narrows the original risk statement. The live question is not whether to add geographic heterogeneity from zero. It is whether the **2022-derived PHON spatial surface is stale or mis-scaled for 2026**, and whether a 2025 federal-derived surface improves the model prospectively.

The current model therefore becomes the control. It must not be described as a uniform-PHON model.

## Revised model-risk statement

Potential misspecification under investigation:

> The current 2026 Assembly model may use a stale or incorrectly persistent One Nation spatial propensity because its dedicated PHON geography is derived from the 2022 AEC ecological surface. A 2025 federal-derived district surface may alter relative PHON strength, final-two composition and seat conversion in rural, regional and outer-suburban seats.

A secondary sensitivity question is how strongly the existing spatial deviations should persist. This can be tested immediately on the existing 2022 surface, but that test is diagnostic only and cannot substitute for constructing the 2025 challenger.

## Independent evidence supporting investigation

The shadow hypothesis is motivated by evidence that predates or is independent of the current four-seat Morgan observation:

1. 2025 federal Victorian results show a strong rural / outer-suburban PHON gradient and very weak inner-Melbourne support.
2. Antony Green has independently mapped 2025 federal results onto current Victorian Assembly geography and identifies concentrated PHON propensity in rural/regional and selected outer-metropolitan districts.
3. Seats & Swings has published 88-seat electoral- and demographic-geography estimates whose relative ordering is broadly consistent with the same spatial pattern.
4. Roy Morgan's 21–26 October four-seat SMS poll is held out from fitting and treated as external validation-only evidence because of its small seat-level effective samples.

These sources are not all statistically independent: several derive from overlapping electoral geography. They must therefore not be counted as separate observations in a likelihood or used to inflate confidence.

## Shadow specification

For district `i`, represent the PHON latent primary conceptually as:

`logit(PHON_i) = alpha_state + lambda * delta_i + candidate_i + local_shock_i + residual_i`

where:

- `alpha_state` is the statewide latent PHON level from the admitted statewide polling scenario;
- `delta_i` is a pre-election district geographic propensity estimated independently of the validation targets;
- `lambda` controls persistence/shrinkage of the spatial signal;
- `candidate_i` is a separately governed candidate effect, centred at zero and not hand-tuned to current polling;
- `local_shock_i` captures electorate-specific campaign movement;
- `residual_i` captures remaining uncertainty.

The statewide level must be re-centred for each `lambda` so that introducing heterogeneity redistributes support rather than silently adding statewide PHON vote.

## Required shadow treatments

### Phase A — existing-surface sensitivity

Run the current AEC-2022 PHON surface with common random numbers at:

1. `lambda = 0.00` — uniform spatial counterfactual;
2. `lambda = 0.50` — strong shrinkage;
3. `lambda = 0.75` — intermediate shrinkage;
4. `lambda = 1.00` — current model treatment and therefore the control.

`model/scripts/run_onp_geography_shadow.py` implements this diagnostic without writing canonical forecast artefacts. It deliberately labels the source as the existing AEC-2022 ecological auxiliary. Results from Phase A can identify sensitivity to spatial persistence but cannot establish that the 2025 geography should replace the current surface.

### Phase B — 2025 challenger

`model/scripts/build_aec_2025_onp_geography.py` now defines the primary reproducible challenger construction. It uses final official AEC **2025 House first preferences by polling place**, AEC polling-place coordinates, and the 88 `STATE_ASSEMBLY_2022` polygons exposed by Vicmap Admin. The builder performs the point-in-polygon crosswalk without adding a GIS dependency and emits both an 88-seat relative surface and a provenance/audit JSON.

House results are used deliberately rather than Senate results for the primary challenger: the current 2022 ecological auxiliary is a federal local-pattern surface, Antony Green's independent 2025 mapping also uses House results, and House results avoid introducing a chamber change into the year-on-year comparison. Senate geography remains a useful robustness check, not the primary replacement surface.

The builder excludes non-geolocatable declaration votes from the district surface and reports them rather than allocating them heuristically. This avoids false precision but means the surface is an ecological polling-place approximation, not a reconstruction of every elector's home district.

Before any simulation, Phase B must pass these checks:

1. exactly 88 unique Assembly polygons and 88 output districts;
2. AEC/Vicmap source payload hashes recorded;
3. no Morgan, 2026 seat polling or candidate-effect input used in construction;
4. statewide located-vote ONP share reconciled against the corresponding AEC ordinary-vote universe, with any denominator difference explained;
5. district ranking and broad rural/outer/inner gradient compared against Antony Green as an **independent diagnostic**, not fitted to his map;
6. 2022-vs-2025 district log-ratio correlation, regression slope, rank correlation and largest residual/change seats reported;
7. anomalous seats reviewed for known federal candidate-field effects before any production interpretation.

Only after these checks should the 2025 surface enter the shadow simulator. The final challenger set should include fixed `lambda = 0.50`, `0.75`, `1.00` and a pre-declared sampled-lambda treatment. Do not choose a posterior-favourable lambda after seeing validation evidence.

All variants must use common random numbers where practical and identical non-PHON coefficients, polling evidence, preference machinery and candidate files.

## Evidence governance

### Fit / construction data

Permitted:

- pre-election 2025 federal electoral geography;
- official AEC/VEC spatial crosswalks;
- pre-declared demographic predictors if tested as a separate challenger;
- admitted statewide Victorian polling according to existing project rules.

### Validation-only data

Do not fit to:

- Roy Morgan 21–26 October Bass/Hastings/Morwell/Pakenham claims;
- campaign-source seat commentary;
- post-hoc analyst seat calls;
- election outcomes.

These may be used only for prospective validation or qualitative diagnostic comparison.

## Evaluation metrics

Compare every challenger with the control on:

- district primary MAE where independent seat evidence is available;
- final-pair composition probabilities;
- winner probabilities;
- expected seats by ALP / Coalition / PHON / Greens / Other;
- `P(ALP >= 45)`, `P(Coalition >= 45)`, `P(hung Assembly)`;
- number and identity of seats whose modal final pair changes;
- number and identity of seats whose winner probability moves >=5pp and >=10pp;
- sensitivity to `lambda`;
- leave-one-pollster-out statewide polling sensitivity;
- calibration / scoring results once admissible held-out evidence becomes available.

A geographically richer model is not preferred merely because it produces more dramatic seat variation.

## Specific diagnostic seats

High-priority diagnostics include Pakenham, Morwell, Hastings, Bass, Shepparton, Murray Plains, Mildura, Euroa, Narre Warren North, Narre Warren South, Cranbourne, Mill Park, Thomastown, Bayswater, Box Hill, Glen Waverley, Ashwood and Ringwood.

These seats span expected high-PHON, three-way-contest and low-PHON/eastern-Melbourne environments.

## Promotion gate

No revised PHON geographic component may enter the canonical forecast unless all of the following are satisfied:

1. the spatial feature is constructed from pre-election evidence with reproducible provenance;
2. statewide vote is conserved after geographic redistribution;
3. challenger results are stable across plausible `lambda` values rather than dependent on one selected value;
4. improvement is demonstrated on held-out or genuinely prospective evidence, not only in-sample plausibility;
5. results do not depend critically on a single statewide poll or pollster;
6. preference/final-pair behaviour remains coherent under the existing IRV engine;
7. uncertainty is not spuriously narrowed by treating derivative evidence as independent;
8. normal repository validation, readiness and owner-authorisation gates remain satisfied.

Until then, the revised geographic model is shadow-only.

## Current interpretation

The code audit changes the scientific interpretation of this workstream. The current model already encodes substantial PHON geographic heterogeneity, so the earlier framing of PROD as effectively uniform was wrong. The immediate task is now a **surface-update and persistence-validation problem**, not a geography-versus-no-geography problem.

Phase A can establish how sensitive current outputs are to the strength of the existing 2022 spatial pattern. Phase B is now specified as a reproducible official-data build rather than an analyst-derived seat table. Morgan remains held out. Independent analyst mappings are diagnostics only. No production change is authorised by this workstream.
