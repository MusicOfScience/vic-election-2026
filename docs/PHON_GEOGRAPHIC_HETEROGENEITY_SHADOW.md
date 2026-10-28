# PHON geographic heterogeneity — governed shadow workstream

Updated: 28 October 2026  
Status: completed shadow experiment; **no canonical parameter or forecast change**

## Purpose

This workstream tested whether the 2026 Assembly model's dedicated One Nation geography should be updated from its AEC 2022 federal ecological surface and whether the spatial signal's persistence is adequately calibrated.

The experiment is now adjudicated. Full results are in [`PHON_GEOGRAPHIC_HETEROGENEITY_RESULTS_2026-10-28.md`](PHON_GEOGRAPHIC_HETEROGENEITY_RESULTS_2026-10-28.md) and the machine-readable decision is in [`metadata/onp-geography-shadow-adjudication-2026-10-28.json`](../metadata/onp-geography-shadow-adjudication-2026-10-28.json).

**Decision: retain the 2025 surface as a governed shadow challenger; do not alter canonical PROD.**

## Code-audit correction: the current model already contains ONP geography

The original investigation began from a concern that current ONP support might be spread too uniformly across Assembly districts. Inspection of `model/src/vicforecast/forecast_2026.py` showed that this framing was wrong: the model already derives a dedicated `onp_local_log` from the AEC 2022 federal ecological surface and substitutes it into the Assembly simulation.

The live question therefore became whether the **2022-derived spatial surface is stale or mis-scaled for 2026**, not whether geography should be introduced from zero.

A second architectural issue emerged. The general AEC local pattern is configured with `aec_local_pattern_shrinkage: 0.62` and an ONP generic `local_logit_limit: 0.45`. The simulation applies the generic limits and then overwrites the ONP column with its dedicated `onp_local_log`, whose construction is separately clipped at `-1.20` / `+1.10`. The current ONP treatment is therefore a deliberate special case whose full spatial persistence requires validation.

## Shadow model

For district `i` the conceptual treatment is:

`logit(ONP_i) = alpha_state + lambda * delta_i + candidate_i + local_shock_i + residual_i`

where `alpha_state` is the unchanged statewide latent ONP level, `delta_i` is relative district geographic propensity and `lambda` controls persistence / shrinkage. No current seat polling is used to construct `delta_i`.

Because softmax transforms are nonlinear, every final treatment solves one common additive ONP logit intercept so its central enrolment-weighted ONP primary matches the current control. Geography therefore redistributes a fixed central statewide vote rather than silently changing the statewide vote level.

## Phase A — current 2022 surface

The current AEC-2022 ONP surface was run with common random numbers at `lambda = 0.00`, `0.50`, `0.62`, `0.75` and `1.00`. The `0.62` treatment is a config-consistency diagnostic because `0.62` is the AEC local-pattern shrinkage already declared for the general Assembly surface; it was not selected after seeing seat outputs.

The result is highly sensitive to `lambda`. At an effectively fixed statewide ONP vote, moving from `1.00` to `0.62` changes ONP expected Assembly seats from 16.28 to 11.26 and hung-parliament probability from 77.60% to 64.16%.

This does not establish `0.62` as the correct ONP value. It establishes that the current `1.00` exception is a material model parameter requiring calibration.

## Phase B — official 2025 challenger

`model/scripts/build_aec_2025_onp_geography.py` constructs an 88-district 2025 challenger from final official AEC 2025 House first preferences by polling place, AEC polling-place coordinates and the 88 current `STATE_ASSEMBLY_2022` polygons from Vicmap Admin. Non-geolocatable declaration votes are reported rather than guessed into districts.

### Crosswalk falsification test

The same physical polling-place assignment method was retrospectively applied to the 2022 federal election and compared with the repository's existing 2022 `allocated_ballots` surface:

- Pearson: **0.9882**
- Spearman: **0.9860**
- slope: **1.0188**
- R²: **0.9765**

The 2025 differences therefore cannot reasonably be dismissed as a simple spatial-join artefact.

### 2022 → 2025 change

Across all 88 districts:

- Pearson: **0.8364**
- Spearman: **0.7959**
- fitted 2025-on-2022 slope: **0.7749**
- R²: **0.6995**

There is strong broad persistence but material structured change.

### House-versus-Senate robustness

A zero-weight 2025 Senate mapping tests whether the House surface is merely a candidate-field artefact:

- Pearson House/Senate: **0.9110**
- Spearman: **0.9059**
- slope: **0.9102**
- R²: **0.8300**

The broad 2025 geography survives the chamber change. House and Senate are overlapping evidence from the same election and are not treated as statistically independent.

## Final fixed-lambda results

### Current 2022 surface

| lambda | Labor | Coalition | ONP | Greens | P(Labor maj.) | P(Coalition maj.) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 40.50 | 40.40 | 4.52 | 2.57 | 33.18% | 28.86% | 37.96% |
| 0.50 | 39.52 | 36.51 | 9.66 | 2.29 | 27.74% | 13.84% | 58.42% |
| **0.62** | **39.13** | **35.28** | **11.26** | **2.32** | **25.26%** | **10.58%** | **64.16%** |
| 0.75 | 38.77 | 33.85 | 13.03 | 2.34 | 23.34% | 7.02% | 69.64% |
| **1.00 current** | **38.29** | **31.02** | **16.28** | **2.40** | **19.30%** | **3.10%** | **77.60%** |

### 2025 House challenger

| lambda | Labor | Coalition | ONP | Greens | P(Labor maj.) | P(Coalition maj.) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.50 | 40.08 | 36.14 | 9.47 | 2.30 | 30.40% | 12.98% | 56.62% |
| **0.62** | **39.78** | **34.68** | **11.25** | **2.29** | **28.48%** | **9.56%** | **61.96%** |
| 0.75 | 39.48 | 32.98 | 13.23 | 2.30 | 26.42% | 6.38% | 67.20% |
| **1.00** | **39.12** | **29.64** | **16.89** | **2.34** | **22.94%** | **2.60%** | **74.46%** |

At full persistence the aggregate ONP seat total looks deceptively stable — 16.89 versus the current 16.28 — while the modal winner changes in 15 districts and the modal final pair changes in 24. Forty districts move by at least five percentage points in ONP win probability and 34 move by at least ten points.

The 2022 and 2025 surfaces can therefore yield similar ONP totals for substantially different geographic reasons.

## Held-out evidence

Roy Morgan's 21–26 October Bass/Hastings/Morwell/Pakenham SMS poll remains validation-only and was never read by construction or simulation code. The 2025 challenger improves the directional ONP primary story in several of those seats but does not reproduce Morgan's published modal final-pair claims. Given Morgan's combined four-seat sample of only 283, this is not a hard failure target; equally, it provides no basis for declaring the preference/elimination machinery validated.

## Promotion gate

| Gate | Result |
| --- | --- |
| reproducible pre-election spatial construction | **PASS** |
| statewide-vote conservation | **PASS** |
| crosswalk method replication | **PASS** |
| House/Senate spatial robustness | **PASS, dependence caveat** |
| stable across plausible `lambda` | **FAIL** |
| held-out/prospective seat improvement | **INCONCLUSIVE** |
| preference/final-pair behaviour validated | **FAIL / existing blocker** |
| uncertainty adequately represented | **OPEN** |
| normal production authorisation | **BLOCKED** |

No revised ONP geography may enter the canonical forecast on the evidence in this PR.

## Why no sampled-lambda output is reported

The protocol required a probabilistic persistence treatment whose distribution was pre-declared. A numerical distribution was not sealed before the fixed-lambda outputs were inspected. Selecting one now would be post-hoc parameter choice.

The sampled treatment is therefore deliberately not manufactured. A future persistence distribution must be derived from external pre-election evidence and frozen before its 2026 Assembly output is examined.

## Final interpretation

The experiment produces two robust conclusions:

1. **The 2025 geography is worth keeping.** It survives crosswalk replication and same-election House/Senate robustness and contains material information not present in the 2022 surface.
2. **The current seat forecast is too sensitive to unvalidated ONP spatial persistence for the challenger to be promoted.** The more urgent task is calibration of `lambda` and preference/final-pair behaviour, not choosing whichever geographic treatment produces the most plausible headline seats.

Canonical PROD remains frozen. The 2025 surface is retained as a shadow challenger and prospective calibration asset.
