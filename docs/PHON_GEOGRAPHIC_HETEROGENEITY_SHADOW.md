# PHON geographic heterogeneity — governed shadow workstream

Updated: 2026-10-28
Status: shadow-only research and validation; no canonical parameter or forecast change

## Purpose

Recent Victorian polling places One Nation in the low-20s statewide, while independent electoral geography indicates that support is unlikely to be distributed uniformly across Assembly districts. This workstream tests whether the current model over-shrinks PHON geography and whether a geographically heterogeneous PHON component materially changes district final-pair composition or statewide government probabilities.

This document does **not** authorise a production change. The 8 October canonical forecast remains frozen. All tests described here are challenger/shadow analyses until they pass the repository's existing validation and owner-admission gates.

## Model-risk statement

Potential misspecification under investigation:

> The current 2026 Assembly model may over-shrink One Nation support geographically, producing district primaries that are too close to the statewide latent mean and therefore mis-stating final-two composition in rural, regional and outer-suburban seats.

The risk is primarily about **vote geography and elimination order**, not necessarily the statewide PHON primary itself.

## Independent evidence supporting investigation

The shadow hypothesis is motivated by evidence that predates or is independent of the current four-seat Morgan observation:

1. 2025 federal Victorian Senate and lower-house results show a strong rural / outer-suburban PHON gradient and very weak inner-Melbourne support.
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

Run at minimum:

1. **Control:** current production-compatible geography treatment with the same statewide evidence set.
2. **Fixed lambda = 0.50:** deliberately conservative persistence.
3. **Fixed lambda = 0.75:** intermediate challenger.
4. **Fixed lambda = 1.00:** full persistence stress case.
5. **Sampled lambda:** probabilistic persistence treatment over a pre-declared range/distribution; do not choose a posterior-favourable value after seeing election-target evidence.

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

High-priority diagnostics include:

- Pakenham
- Morwell
- Hastings
- Bass
- Shepparton
- Murray Plains
- Mildura
- Euroa
- Narre Warren North
- Narre Warren South
- Cranbourne
- Mill Park
- Thomastown
- Bayswater
- Box Hill
- Glen Waverley
- Ashwood
- Ringwood

These seats span expected high-PHON, three-way-contest and low-PHON/eastern-Melbourne environments.

## Promotion gate

No heterogeneous PHON component may enter the canonical forecast unless all of the following are satisfied:

1. the spatial feature is constructed from pre-election evidence with reproducible provenance;
2. statewide vote is conserved after geographic redistribution;
3. challenger results are stable across plausible `lambda` values rather than dependent on one selected value;
4. improvement is demonstrated on held-out or genuinely prospective evidence, not only in-sample plausibility;
5. results do not depend critically on a single statewide poll or pollster;
6. preference/final-pair behaviour remains coherent under the existing IRV engine;
7. uncertainty is not spuriously narrowed by treating derivative evidence as independent;
8. normal repository validation, readiness and owner-authorisation gates remain satisfied.

Until then, the heterogeneous model is shadow-only.

## Current interpretation

The present evidence is sufficient to reject a naive assumption that a statewide PHON primary in the low-20s should imply roughly low-20s support in every district. It is **not** sufficient to choose a production value of `lambda`, manually adjust individual seats, or convert small-sample seat polling into hard local priors.

The immediate technical objective is therefore controlled comparison of the existing model against the five treatments above, with Morgan and analyst commentary held out from fitting.
