# IRV and final-pair calibration protocol

Status: preregistered research protocol. No canonical 2026 forecast change is authorised by this document.

## Question

Can the Assembly preference-transfer and elimination machinery be calibrated from historical Victorian evidence well enough to improve final-pair and winner probabilities relative to the current global transfer prior, without tuning to 2026 forecast outputs or held-out 2026 seat commentary/polls?

## Current model under test

The 2026 Assembly model currently:

1. generates district primary-vote vectors;
2. draws one whole-election 5x5 preference matrix from row-wise Dirichlet distributions centred on the fixed `PREFERENCE_PRIOR` matrix;
3. uses `assembly.preference_prior_concentration = 72`;
4. applies the same sampled preference matrix to every Assembly district in that simulation;
5. deterministically eliminates the lowest continuing party family until two remain;
6. records the resulting final pair and winner.

The current matrix and concentration are controls, not targets to be defended.

The five modelled families are `ALP`, `LIB_NAT`, `ONP`, `GRN` and `OTH_IND`. This family aggregation is itself part of the mechanism under test. In particular, multiple unrelated independent/minor candidates can collapse into a single `OTH_IND` family even though actual IRV eliminates candidates, not party-family aggregates.

## Governance firewall

Parameter fitting and model selection must use historical election evidence only.

The following may not be used to select transfer means, concentration, stratification or model class:

- 2026 Assembly forecast seat probabilities or chamber outputs;
- the 2026 ONP geography shadow outputs from PRs #135/#136;
- Roy Morgan's October 2026 four-seat poll;
- campaign-source seat claims, analyst calls or desired 2026 final pairs;
- any post-election 2026 evidence.

The research team has already seen existing 2026 model outputs. Therefore this is not a blinded exercise. The safeguard is procedural: the challenger specification and historical scoring rule must be frozen before any challenger is propagated through the 2026 model.

## Historical evidence hierarchy

### Tier 1: direct official transfer evidence

Use official VEC distribution-of-preferences / count evidence where it identifies actual transfer parcels and destinations. Candidate parties must be mapped through the repository's frozen fail-closed historical party-family crosswalk.

Existing audited evidence includes 1,204 transfer rows from 39 2022 indicative distributions. Those rows are admissible for describing 2022 transfer behaviour but are not by themselves sufficient to make every source-party parameter forecast-ready.

For transfer-parameter fitting, a transfer event is admissible as a clean source-party observation only when the excluded candidate's distributed parcel can be interpreted without silently attributing previously transferred votes to that candidate's original party. The default admissible set is therefore pure/original-parcel events unless a later-count decomposition is explicitly demonstrated from official data.

### Tier 2: official final-pair and winner outcomes

Use separately loaded official final-pair identities and winners only for scoring a forecast generated without target-cycle outcomes. Final-pair outcomes may not be reverse-engineered into a transfer matrix and then scored on the same contests.

### Tier 3: broad prior

Where an earlier-cycle source-party transfer parameter is unsupported, retain a broad preregistered prior and wider uncertainty. Missing evidence must not be replaced with a sharp point estimate.

## Module-isolation scoring design

The first adjudication is conditional on **observed historical five-family first preferences**. This intentionally removes polling, geography and primary-vote forecast error from the test and asks whether the preference/elimination module can recover observed winners and final pairs when its first-preference input is effectively perfect.

This conditional test is diagnostic, not a substitute for the complete walk-forward forecast replay. A mechanism that fails conditional scoring cannot be rescued by upstream forecast improvements; a mechanism that passes conditional scoring still requires full-model validation later.

Winner outcomes are scored wherever an official winner is available. Final-pair outcomes are scored only where the governed outcome artefact contains two official finalists.

Final-pair scoring uses unordered family pairs with replacement. This deliberately allows observed categories such as `OTH_IND`–`OTH_IND` or `LIB_NAT`–`LIB_NAT` if two distinct candidates from the same model family reach the actual final two. The current five-family IRV engine cannot generate a same-family pair, so such outcomes receive zero model probability rather than being silently remapped. Their frequency is reported separately as a structural family-aggregation diagnostic.

## Walk-forward design

Target cycles are 2014, 2018 and 2022 where the required scoring outcomes can be reconstructed cleanly. 2010 may contribute training evidence but cannot train itself. C0 may additionally be scored descriptively on 2010 because it does not fit any historical parameters.

For each target cycle:

- fit preference information only from earlier elections;
- freeze the target-cycle preference distribution before loading that cycle's final-pair/winner outcomes;
- generate district final-pair and winner probabilities from the target cycle's pre-election primary-vote replay inputs, or from observed historical primaries for the module-isolation diagnostic;
- only then load the official scoring outcomes.

No target-cycle transfer observation may train the same target cycle.

## Challenger ladder

All challengers retain the existing IRV elimination rule initially. This separates preference calibration from a simultaneous count-rule rewrite.

### C0 — current control

Fixed current `PREFERENCE_PRIOR`, concentration 72, one statewide matrix draw per simulation.

The first C0 score is conditional on observed five-family historical primaries and uses the production `_count_irv` implementation unchanged.

### C1 — leakage-safe pooled historical mean

Source-party transfer means estimated only from admissible earlier-cycle direct transfer evidence. Unsupported rows retain the broad prior. Dispersion must be estimated from historical variability rather than copied from 72.

`OTH_IND` is not permitted to become a sharp pooled source-party parameter merely because numerical fit appears strong: the family contains heterogeneous independents and minor parties. Any pooled `OTH_IND` treatment must remain broad or be represented by a defensible hierarchy that acknowledges that heterogeneity.

### C2 — hierarchical partial pooling

If evidence volume permits, estimate source-party transfer vectors with partial pooling across elections and districts. The model may include election-level variation and seat-level variation, but no district-specific coefficient may be fitted unless supported by repeated historical evidence.

### C3 — district-level preference heterogeneity

Only test this if C2 demonstrates identifiable between-district variance beyond sampling noise. A district-specific draw must be hierarchical and shrink strongly toward the election-level source-party vector. Do not hand-tune named seats.

The challenger ladder stops at the simplest model that improves held-out historical scoring without materially degrading calibration or becoming weakly identified.

## Dispersion and dependence

The current model's single whole-election preference draw induces perfect cross-seat dependence in transfer behaviour within a simulation. The calibration must separately test:

- election-level/common transfer uncertainty;
- district-level residual transfer uncertainty;
- source-party-specific uncertainty.

If the evidence cannot identify these components, retain broader uncertainty rather than forcing a decomposition.

## Scoring metrics

Primary metrics:

- final-pair multiclass Brier score;
- final-pair log loss;
- winner multiclass Brier score;
- winner log loss;
- final-pair top-1 accuracy;
- winner accuracy;
- calibration intercept/slope where sample size permits.

Diagnostics:

- frequency and score impact of same-family observed final pairs that the five-family engine cannot represent;
- error by source party eliminated;
- error in three-party / multi-party contests;
- error where ONP or Greens enter the final pair;
- error by metropolitan / regional grouping where available;
- sensitivity to concentration / variance assumptions;
- leave-one-election-out stability.

A challenger is not promoted because it improves raw accuracy alone. It must improve or preserve proper scoring rules and avoid false confidence.

## Promotion gate

A challenger may be proposed for a later 2026 shadow only if all of the following hold:

1. no target-cycle leakage;
2. reproducible official-source evidence and hashes;
3. at least two genuinely held-out historical target cycles contribute to adjudication;
4. final-pair Brier/log loss improve versus C0 without material winner-calibration deterioration;
5. improvement is not driven by one election or a handful of named seats;
6. uncertainty is at least as wide as justified by observed historical transfer variability;
7. unsupported source-party rows remain broad rather than fabricated;
8. the challenger remains coherent with Australian full-preferential IRV counting;
9. family aggregation does not create an unacknowledged structural impossibility large enough to invalidate final-pair probability claims;
10. normal repository quality gates pass.

Passing this gate authorises only a separate 2026 shadow experiment. It does not alter canonical PROD.

## Held-out 2026 evidence

Only after the historical model class and parameters are frozen may a separate 2026 shadow be generated. Only after that shadow is hashed may October 2026 seat polling or analyst seat evidence be inspected as external validation.

## Immediate implementation order

1. inventory the existing 2010/2014/2018/2022 official transfer and final-pair evidence;
2. score C0 conditionally on observed historical five-family primaries;
3. reconstruct admissible pure/original-parcel source-party transfer observations with the frozen family crosswalk;
4. identify which target cycles can support leakage-safe C1 scoring;
5. fit C1 and, only if supported, C2/C3;
6. execute walk-forward historical scoring;
7. freeze the adjudicated historical preference model;
8. only then build a common-random-number 2026 shadow runner.
