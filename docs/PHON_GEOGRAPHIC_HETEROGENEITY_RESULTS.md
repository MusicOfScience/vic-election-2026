# PHON geographic heterogeneity shadow — Phase B adjudication

**Status:** validated shadow finding; **production promotion deferred / failed**  
**Canonical forecast:** unchanged  
**Canonical model date:** 8 October 2026  
**Shadow workflow run:** `40670889750`  
**Artifact:** `onp-geography-shadow`, SHA-256 digest `a2045109f64dea7dd5a4e7db6ee017a3977cce556a746647cec0846c17f50554`

## Executive finding

The production model already contains a geographically heterogeneous One Nation (ONP) local propensity derived from the AEC 2022 federal ecological surface. Phase B tested whether that geography is stale enough to warrant a 2025 update.

The answer is **yes at seat level, but not yet in a form that should be promoted to production**.

The official AEC-2025 House polling-place surface contains substantial new geographic information. However, treating the full 2025 surface as known truth changes too many individual seat and final-two outcomes to satisfy the preregistered stability requirement. A decomposition that separates the persistent 2022→2025 component from genuinely new 2025 residual information produces a much more stable chamber result while still revealing large seat-identity changes.

The model risk is therefore best described as:

> **PROD's aggregate ONP seat count is not obviously badly miscalibrated, but the identity of those ONP seats and several final-two compositions are materially exposed to stale local geography.**

That finding is strong enough to retain as model-risk evidence. It is not strong enough to replace the production surface with a single fixed 2025 treatment.

## 1. Crosswalk falsification test

Before interpreting any 2025 movement, the physical polling-place → Victorian Assembly mapping method was tested against 2022.

Using the same point-location method on AEC 2022 House ordinary polling-place votes and comparing it with the existing production `allocated_ballots` ecological surface gives:

| Diagnostic | Result |
| --- | ---: |
| Districts | 88 |
| Pearson spatial-signal correlation | **0.9882** |
| Spearman rank correlation | **0.9860** |
| Fitted point-on-existing slope | **1.0188** |
| R² | **0.9766** |
| Mean absolute centred signal difference | **0.0787 log units** |

**Adjudication:** the point-location method is a sufficiently close reconstruction of the existing ecological allocation for Phase B. The large 2025 changes cannot reasonably be dismissed as a generic crosswalk failure.

## 2. 2022 → 2025 geographic persistence

The 2025 House surface was built from final official AEC first preferences at physical ordinary polling places, AEC polling-place coordinates and all 88 current Assembly polygons from Vicmap. Declaration votes without a defensible home-seat location were not spatially invented.

Across all 88 districts:

| Diagnostic | Unweighted comparison |
| --- | ---: |
| Pearson correlation | **0.8364** |
| Spearman correlation | **0.7959** |
| 2025-on-2022 slope | **0.7749** |
| R² | **0.6995** |

The model-consistent enrolment-weighted decomposition used by the residual-retention experiment gives:

| Diagnostic | Weighted result |
| --- | ---: |
| 2025-on-2022 slope | **0.8730** |
| R² | **0.6823** |
| SD of centred 2022 signal | **0.5579** |
| SD of centred 2025 signal | **0.5897** |
| SD of new 2025 residual | **0.3324** |

About 68% of the weighted 2025 spatial variance is explained by the persistent 2022 pattern. The remainder is large enough to matter and too structured to ignore, but may contain a mixture of genuine geographic change, federal-candidate effects and election-specific noise.

Largest raw spatial changes include sharp 2025 weakening relative to 2022 in Greenvale, Kalkallo and Kororoit, and strengthening in Lara, Niddrie and Eureka. Those are exactly the kinds of movements that require uncertainty treatment rather than manual acceptance or rejection.

## 3. Why the original global-lambda experiment is not the preferred adjudicator

Scaling an entire spatial surface by a single λ confounds two questions:

1. how much of the old geographic structure persists; and
2. how much genuinely new 2025 local information should be retained.

The crude λ experiments therefore produced very large chamber swings. They remain useful sensitivity diagnostics, but they are not the best candidate architecture.

The cleaner experiment decomposes the centred signals as:

`delta_2025 = beta * delta_2022 + residual_2025`

and varies only the retention of `residual_2025` from 0% to 100%. Every treatment receives a single common additive ONP-logit calibration so the central enrolment-weighted statewide ONP primary exactly matches the control. Common random numbers are used throughout.

No Roy Morgan seat poll, candidate adjustment or post-8-October statewide polling is used to fit these treatments.

## 4. Residual-retention simulation results

5,000 simulations were run per treatment with the canonical random seed.

| New 2025 residual retained | ALP mean seats | Coalition mean seats | ONP mean seats | Greens mean seats | P(ALP maj.) | P(Coalition maj.) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Current PROD geography | **38.29** | **31.02** | **16.28** | **2.40** | **19.3%** | **3.1%** | **77.6%** |
| 0% | 38.50 | 32.44 | 14.70 | 2.36 | 21.3% | 4.7% | 74.0% |
| 25% | 39.04 | 31.81 | 14.79 | 2.36 | 24.1% | 4.3% | 71.6% |
| 50% | 39.43 | 31.21 | 15.00 | 2.36 | 25.3% | 4.0% | 70.6% |
| 75% | 39.37 | 30.45 | 15.81 | 2.35 | 24.6% | 3.2% | 72.2% |
| 100% | 39.12 | 29.64 | 16.89 | 2.34 | 22.9% | 2.6% | 74.5% |

This is the central Phase-B result.

Once stable geography and new residual information are separated, **the chamber-level ONP estimate remains roughly 15–17 seats across the full residual-retention range**. The large uncertainty is primarily *which* seats ONP wins, not whether the party has approximately two versus approximately seventeen seats.

The corresponding hung-parliament probability remains high in every treatment (about 71–78%). The production chamber picture is therefore much more robust than the first crude global-λ experiment implied.

## 5. Seat identity is not robust

The apparent chamber robustness must not be mistaken for seat-level robustness.

At 50% new-residual retention, compared with current geography:

- **7 modal seat winners change**;
- **30 seats** move by at least 5 percentage points in ONP win probability;
- **21 seats** move by at least 10 percentage points.

At 100% retention:

- **15 modal seat winners change**;
- **40 seats** move by at least 5 points in ONP win probability;
- **34 seats** move by at least 10 points.

Illustrative 50%-retention changes include:

| District | Current ONP primary / win P | 50% residual retention | Direction |
| --- | ---: | ---: | --- |
| Greenvale | 37.5% / 97.1% | 23.4% / 23.4% | large downgrade |
| Kalkallo | 36.1% / 81.7% | 24.7% / 12.5% | large downgrade |
| Lara | 26.6% / 12.2% | 33.3% / 54.6% | large upgrade |
| Eureka | 26.1% / 24.0% | 30.9% / 62.2% | large upgrade |
| Hastings | 23.4% / 9.7% | 27.7% / 31.7% | upgrade |
| Niddrie | 20.9% / 2.4% | 26.5% / 26.1% | upgrade |
| Morwell | 46.5% / 89.5% | 45.3% / 85.0% | remains very strong |
| Pakenham | 28.4% / 24.2% | 29.4% / 28.8% | modest upgrade |

No single retention value is promoted by this table. It demonstrates why a fixed deterministic seat geography is currently too strong an assumption.

## 6. Held-out checks

### Roy Morgan Eastern Victoria mini-poll

Roy Morgan's 21–26 October 2026 SMS poll interviewed **283 electors across Bass, Hastings, Morwell and Pakenham**. It reported a combined ONP primary of **39% across Hastings, Morwell and Pakenham**, and placed ONP in the likely final two in all three. This evidence was held out from construction and fitting.

As new 2025 residual information is admitted, the shadow model moves toward that direction: the simple unweighted mean modelled ONP primary across Hastings/Morwell/Pakenham rises from roughly 31.5% at 0% residual retention to roughly 36.6% at 100% retention, and ONP appears in more likely final pairs.

This is supportive of retaining some new 2025 information, but it **does not select a retention value**. The Morgan sample is tiny, seat-level sample sizes are undisclosed, the reported 39% is pooled across three seats, and the model still disagrees with Morgan on some opponent/final-pair identities.

Source: https://www.roymorgan.com/findings/10371-victorian-state-voting-intention-eastern-victoria-seats-october-2026

### Independent modelling

Seats & Swings' separate electoral and demographic approaches also find strong but imperfect agreement in ONP geography and explicitly identify large model disagreements/candidate anomalies in seats including Mill Park, Pakenham, Shepparton and other northern/eastern seats. That supports treating the new local component as uncertain rather than accepting a single federal mapping literally.

Source: https://seatsandswings.com/articles/how-can-we-predict-one-nation-first-preferences-9ecef754

Antony Green's independent 2025 federal→Victorian mapping likewise identifies a strong rural/regional and outer-suburban geographic structure, supporting the existence of a persistent local signal but not establishing a production coefficient for 2026.

Source: https://antonygreen.com.au/vic2026-mapping-one-nations-2025-federal-result/

## 7. Production promotion gate

### Passed

- official 2025 data acquisition and provenance;
- 88-seat coverage;
- 2022 method-reconstruction / crosswalk falsification test;
- deterministic/common-random-number simulation machinery;
- central statewide ONP vote conservation;
- evidence that 2025 contains new geographic information beyond 2022;
- held-out evidence points in the direction of at least some 2025 updating.

### Not passed

- seat-level stability across plausible treatments;
- a defensible empirical calibration for how much 2025 residual information should be retained for a 2026 state election;
- demonstrated out-of-sample improvement against an appropriate historical analogue;
- sufficient evidence to distinguish persistent geographic change from 2025 House candidate/election-specific residuals seat by seat.

**Decision: do not promote a fixed 2025 geography into PROD.**

## 8. Recommended model architecture from here

If geography is promoted later, it should be a **latent / uncertain spatial field**, not a hard replacement table.

A defensible candidate architecture is:

`delta_2026,i = beta * delta_2022,i + kappa * residual_2025,i + epsilon_i`

where:

- `beta` represents persistent geographic structure;
- `residual_2025` represents new information revealed in 2025;
- `kappa` is estimated or assigned a governed uncertainty distribution rather than chosen by visual preference;
- `epsilon_i` is larger where independent predictors disagree or where federal candidate effects are known to contaminate the signal.

The next calibration target should be independent historical evidence (preferably repeated Senate/federal geography, where statewide party coverage reduces House-candidate contamination), not Morgan or the 2026 seat outcomes we are trying to predict.

## 9. Governance conclusion

PR #135 now contains a successful and reproducible shadow experiment, not a proposed production forecast change.

It is scientifically reasonable to merge the **research infrastructure and documented negative/deferred promotion result** while leaving canonical PROD numerically and architecturally unchanged. Any future promotion of a latent 2025-informed geography must be a separate explicit model-change decision with its own validation evidence.
