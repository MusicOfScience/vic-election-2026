# PHON geographic heterogeneity — residual-retention supplement

Updated: 28 October 2026  
Status: governed shadow diagnostic; **no canonical forecast or production parameter change**

## Why this supplement exists

The fixed-`lambda` work in `PHON_GEOGRAPHIC_HETEROGENEITY_RESULTS_2026-10-28.md` establishes that the model is structurally sensitive to the overall strength of ONP geography. It does not cleanly distinguish persistent geography from genuinely new 2025 local information.

This supplementary experiment decomposes the centred spatial field as:

`delta_2025 = beta * delta_2022 + residual_2025`

and varies only how much of `residual_2025` is retained. This is a better diagnostic for the question: **does new 2025 information mainly change the chamber total, or mainly which seats make up that total?**

Every treatment uses 5,000 simulations, common random numbers and the same central-vote conservation solve used by the main shadow. Roy Morgan, analyst seat calls, candidate adjustments and post-8-October statewide polling are not used to fit the treatment.

Workflow run: `40670889750`  
Artifact digest: `sha256:a2045109f64dea7dd5a4e7db6ee017a3977cce556a746647cec0846c17f50554`

## Decomposition

The enrolment-weighted 2025-on-2022 spatial decomposition gives:

| Diagnostic | Result |
| --- | ---: |
| weighted persistence slope (`beta`) | **0.8730** |
| weighted R² | **0.6823** |
| SD of centred 2022 signal | **0.5579** |
| SD of centred 2025 signal | **0.5897** |
| SD of new 2025 residual | **0.3324** |

The broad spatial structure therefore persists strongly, while the new 2025 residual is large enough to matter.

## Chamber results

| New 2025 residual retained | ALP mean | Coalition mean | ONP mean | Greens mean | P(ALP maj.) | P(Coalition maj.) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Current PROD geography | **38.29** | **31.02** | **16.28** | **2.40** | **19.3%** | **3.1%** | **77.6%** |
| 0% | 38.50 | 32.44 | 14.70 | 2.36 | 21.3% | 4.7% | 74.0% |
| 25% | 39.04 | 31.81 | 14.79 | 2.36 | 24.1% | 4.3% | 71.6% |
| 50% | 39.43 | 31.21 | 15.00 | 2.36 | 25.3% | 4.0% | 70.6% |
| 75% | 39.37 | 30.45 | 15.81 | 2.35 | 24.6% | 3.2% | 72.2% |
| 100% | 39.12 | 29.64 | 16.89 | 2.34 | 22.9% | 2.6% | 74.5% |

The key result is that, **conditional on retaining the persistent 2022→2025 component**, ONP remains around 15–17 expected seats across the residual-retention range. The initial fixed-`lambda` experiment therefore overstated the uncertainty in the *aggregate* ONP seat total by conflating overall geographic strength with new local information.

This does not validate current PROD. The chamber total can be similar for very different underlying seat maps.

## Seat identity remains highly unstable

Compared with current geography:

| New residual retained | modal winner changes | ONP win-P shifts ≥5pp | ONP win-P shifts ≥10pp |
| ---: | ---: | ---: | ---: |
| 0% | 2 | 16 | 3 |
| 25% | 4 | 23 | 13 |
| 50% | 7 | 30 | 21 |
| 75% | 13 | 37 | 27 |
| 100% | 15 | 40 | 34 |

At 50% retention, illustrative ONP primary / win-probability changes are:

- Greenvale: 37.5% / 97.1% → 23.4% / 23.4%
- Kalkallo: 36.1% / 81.7% → 24.7% / 12.5%
- Lara: 26.6% / 12.2% → 33.3% / 54.6%
- Eureka: 26.1% / 24.0% → 30.9% / 62.2%
- Hastings: 23.4% / 9.7% → 27.7% / 31.7%
- Niddrie: 20.9% / 2.4% → 26.5% / 26.1%
- Morwell: 46.5% / 89.5% → 45.3% / 85.0%
- Pakenham: 28.4% / 24.2% → 29.4% / 28.8%

The principal live risk is therefore **seat identity and final-pair composition**, not simply the headline number of ONP seats.

## Held-out directional check

Roy Morgan's 21–26 October four-seat SMS poll remains held out. Its pooled ONP primary across Hastings, Morwell and Pakenham was reported at 39% from a very small overall sample. As more 2025 residual information is admitted, the shadow's simple mean ONP primary across those three seats rises from roughly 31.5% to 36.6% and ONP enters more likely final pairs.

That is directionally supportive of some updating, but the sample is far too small and seat-level sample sizes are undisclosed, so it cannot calibrate the retention coefficient.

## Adjudication

This experiment **refines but does not reverse** the main promotion decision.

- A fixed 2025 geography should **not** replace PROD.
- The 2025 surface contains genuine new local information.
- Once stable persistence is separated from new residual information, the chamber-level ONP expectation is considerably more robust than the crude global-`lambda` sensitivity implied.
- Seat identities and final pairs remain materially unstable.
- A future production candidate should represent geography as an uncertain latent field, for example:

`delta_2026,i = beta * delta_2022,i + kappa * residual_2025,i + epsilon_i`

`kappa` must be calibrated or preregistered from external pre-election evidence rather than chosen from the 2026 seat outputs. The appropriate next target is repeated official federal/Senate spatial persistence, with candidate-sensitive seats receiving wider residual uncertainty.
