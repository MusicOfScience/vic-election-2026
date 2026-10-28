# PHON geographic heterogeneity shadow — results and adjudication

Updated: 28 October 2026  
Status: governed shadow result; **no canonical forecast or production parameter change**

## Executive decision

The Phase B investigation finds a real and material One Nation geographic update signal, but **does not support promotion into the canonical forecast**.

Three findings can coexist:

1. the 2025 federal geography is reproducible and is not an artefact of the new polling-place crosswalk;
2. the geography has changed materially since 2022 while preserving a strong rural / outer-suburban / inner-city structure;
3. Assembly seat conversion is highly sensitive to the unvalidated strength/persistence assigned to that geography, and held-out seat evidence does not validate the model's final-pair machinery.

The correct model-governance decision is therefore to retain the 8 October canonical forecast unchanged, preserve the new 2025 surface as a shadow challenger, and treat ONP geographic persistence as an explicit model-risk / calibration problem.

## Reproducible runs

Primary governed shadow run:

- GitHub Actions run: `40668909476`
- simulations: 5,000 per treatment
- common random numbers: yes
- central statewide ONP vote conservation: yes
- artifact: `onp-geography-shadow`
- artifact digest: `sha256:4a936bb29ca8bcbafbd3b09c0352d43cacdec54a44759856f32fb8a82c9e91ab`
- canonical forecast artefacts written: no

House-versus-Senate robustness run:

- GitHub Actions run: `40668427478`
- artifact: `onp-geography-house-senate-robustness`
- artifact digest: `sha256:bd85ceb2b23dd853e0c6bcbe73576c5158121189f7e019b01f02df2d1d0426aa`
- forecast weight: zero

Roy Morgan's 21–26 October four-seat poll and analyst seat calls were not read by the surface builders or simulation treatments.

## 1. Code audit changed the original question

The current model is not geographically uniform for One Nation. It already constructs a dedicated `onp_local_log` from the AEC 2022 federal ecological surface and substitutes that signal into the Assembly simulation.

The important architectural detail is that ONP is a special case. The general AEC local pattern is shrunk by `aec_local_pattern_shrinkage: 0.62`, and the configured generic ONP local-logit limit is `0.45`. The simulation first applies the generic local limits and then overwrites the ONP column with the dedicated `onp_local_log`, whose construction is clipped separately at `-1.20` / `+1.10`.

This means the live risk is not "missing ONP geography". It is whether the **dedicated full-strength ONP spatial exception is correctly sourced and calibrated**.

## 2. The 2025 crosswalk survives a direct falsification test

The 2025 House challenger is built from final official AEC polling-place first preferences, AEC polling-place coordinates and the 88 current Vicmap Assembly polygons.

Before interpreting its dramatic district changes, the same physical polling-place assignment method was applied retrospectively to the 2022 federal election and compared with the repository's existing 2022 `allocated_ballots` ecological surface.

Across all 88 districts:

| Diagnostic | Result |
| --- | ---: |
| Pearson spatial-signal correlation | **0.9882** |
| Spearman rank correlation | **0.9860** |
| fitted point-surface-on-existing slope | **1.0188** |
| R² | **0.9765** |
| mean absolute centred log-signal difference | **0.0663** |

That is strong method replication. The large 2025 changes in seats such as Greenvale, Kalkallo, Lara and Niddrie cannot reasonably be dismissed as a simple physical-polling-place crosswalk failure.

## 3. ONP geography changed materially from 2022 to 2025

Comparing the repository's 2022 House-derived spatial signal with the new 2025 House-derived signal:

| Diagnostic | Result |
| --- | ---: |
| Pearson spatial-signal correlation | **0.8364** |
| Spearman rank correlation | **0.7959** |
| fitted 2025-on-2022 slope | **0.7749** |
| R² | **0.6995** |
| mean absolute centred log-signal change | **0.2518** |

The result is neither instability nor stasis: there is strong persistence in broad geography, but enough structured movement that a four-year-old surface should not automatically be treated as current.

Examples from the official 2025 House mapping include:

- Morwell 15.24%
- Lara 11.87%
- Gippsland East 11.68%
- Murray Plains 10.37%
- Shepparton 10.01%
- Mildura 9.94%
- Eureka 9.80%
- Euroa 9.46%
- Greenvale 2.65%
- Kalkallo 3.21%
- Hawthorn 1.00%
- Kew 1.05%

These are federal-election shares used only as a *relative spatial signal*, not as state-election vote predictions.

Antony Green independently mapped 2025 House results to current Victorian state electorates and described the same broad pattern: stronger rural/regional and outer-suburban support and weak inner/eastern Melbourne support. See: https://antonygreen.com.au/vic2026-mapping-one-nations-2025-federal-result/

## 4. House-versus-Senate robustness supports a genuine 2025 spatial signal

House candidate fields can create local artefacts. A zero-weight robustness test therefore mapped final 2025 Senate polling-place first preferences onto the same 88 Assembly districts.

House versus Senate 2025 spatial geography:

| Diagnostic | Result |
| --- | ---: |
| Pearson correlation | **0.9110** |
| Spearman correlation | **0.9059** |
| fitted Senate-on-House slope | **0.9102** |
| R² | **0.8300** |
| mean absolute centred log-signal difference | **0.2012** |

The broad 2025 geography is therefore not merely a House-candidate artefact. However, the ballots are overlapping evidence from the same election and are not statistically independent.

Some districts remain candidate/context-sensitive and require caution. Large House/Senate differences include South-West Coast, Niddrie, Northcote, Richmond, Preston, Greenvale, Essendon and Lara. The Senate check should widen uncertainty in those seats rather than be counted as a second independent confirmation.

## 5. Central-vote conservation

Initial shadow runs exposed an important confound: scaling spatial heterogeneity changed the simulated statewide mean ONP primary through the nonlinear softmax transformation.

The final governed runs therefore solve one common additive ONP logit intercept per treatment at the frozen canonical latent statewide mean. This holds the central enrolment-weighted ONP primary equal to the current control while changing only geographic dispersion.

The workflow requires calibration residual below `1e-8` percentage points and simulated weighted-district drift no greater than 0.25 percentage points. All final treatments passed.

This is essential: differences below are geography/persistence effects, not covert statewide vote changes.

## 6. Phase A — sensitivity of the current 2022 geography

The current model is `lambda = 1.00`. The `0.62` row is especially informative because `0.62` is the AEC local-pattern shrinkage already declared in the forecast configuration for the general Assembly surface.

| 2022 surface lambda | Labor mean | Coalition mean | ONP mean | Greens mean | P(Labor majority) | P(Coalition majority) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.00 | 40.50 | 40.40 | 4.52 | 2.57 | 33.18% | 28.86% | 37.96% |
| 0.50 | 39.52 | 36.51 | 9.66 | 2.29 | 27.74% | 13.84% | 58.42% |
| **0.62** | **39.13** | **35.28** | **11.26** | **2.32** | **25.26%** | **10.58%** | **64.16%** |
| 0.75 | 38.77 | 33.85 | 13.03 | 2.34 | 23.34% | 7.02% | 69.64% |
| **1.00 current** | **38.29** | **31.02** | **16.28** | **2.40** | **19.30%** | **3.10%** | **77.60%** |

Holding the statewide ONP level constant, changing only the current ONP spatial persistence from 1.00 to the configured generic AEC value of 0.62 removes **5.02 expected ONP seats**, adds **4.26 Coalition seats** and **0.84 Labor seats**, and lowers hung-parliament probability by **13.44 percentage points**.

This is a material architecture sensitivity. The canonical ONP seat expectation is strongly dependent on the decision to use the dedicated full-strength ONP geography rather than the general AEC shrinkage treatment.

This does not prove that `0.62` is correct for ONP. It proves that `lambda = 1.00` needs calibration rather than assumption.

## 7. Phase B — 2025 House geography under fixed persistence

The 2025 challenger uses the same statewide polling, preference machinery, candidate files, random seed and central statewide ONP vote level as the current model.

| 2025 surface lambda | Labor mean | Coalition mean | ONP mean | Greens mean | P(Labor majority) | P(Coalition majority) | P(hung) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.50 | 40.08 | 36.14 | 9.47 | 2.30 | 30.40% | 12.98% | 56.62% |
| **0.62** | **39.78** | **34.68** | **11.25** | **2.29** | **28.48%** | **9.56%** | **61.96%** |
| 0.75 | 39.48 | 32.98 | 13.23 | 2.30 | 26.42% | 6.38% | 67.20% |
| **1.00** | **39.12** | **29.64** | **16.89** | **2.34** | **22.94%** | **2.60%** | **74.46%** |

The full-persistence 2025 surface leaves aggregate ONP seats superficially close to the current model: **16.89 versus 16.28**. That similarity is misleading. It is produced by substantial seat migration across the map.

At `lambda = 1.00` the 2025 surface changes the modal winner in 15 districts and the modal final pair in 24 districts. Forty districts move by at least five percentage points in ONP win probability and 34 by at least ten points.

Examples at full persistence:

- Hastings: ONP win probability 9.7% → 53.5%
- Shepparton: 39.1% → 67.4%
- Narre Warren North: 46.3% → 79.5%
- Cranbourne: 56.2% → 85.0%
- Lara: 12.2% → 93.5%
- Eureka: 24.0% → 90.1%
- Niddrie: 2.4% → 71.2%
- Greenvale: 97.1% → effectively 0%
- Kalkallo: 81.7% → 0.1%
- Thomastown: 67.6% → 11.1%
- Mill Park: 80.9% → 32.1%

The aggregate seat total can therefore look stable while the underlying district model is materially different. The old and new surfaces cannot be treated as interchangeable merely because both yield roughly 16–17 ONP seats under full persistence.

## 8. Lambda dominates the production conclusion

The central scientific failure is stability across plausible persistence treatments.

On the 2025 surface, ONP expected seats move from **9.47 at lambda 0.50** to **11.25 at 0.62**, **13.23 at 0.75** and **16.89 at 1.00**, despite an effectively fixed statewide ONP vote.

The corresponding hung-parliament probability moves from **56.62% to 61.96%, 67.20% and 74.46%**.

This is not Monte Carlo noise. It is structural sensitivity.

The original promotion gate required challenger results to be stable across plausible lambda values. They are not. That criterion therefore fails.

## 9. Held-out Roy Morgan seat evidence does not rescue promotion

Roy Morgan's 21–26 October SMS poll interviewed only 283 electors across Bass, Hastings, Morwell and Pakenham and is held out from fitting. The published likely final contests are:

- Bass: Liberal vs Labor
- Hastings: One Nation vs Liberal
- Morwell: One Nation vs Labor
- Pakenham: One Nation vs Labor

Source: https://www.roymorgan.com/findings/10371-victorian-state-voting-intention-eastern-victoria-seats-october-2026

The 2025 shadow improves the directional ONP primary story in several of these seats, but the full-persistence treatment does not reproduce those four modal final-pair claims. Morgan's tiny combined sample is not a reliable hard target, but it provides no basis for declaring the model's elimination/preference structure validated.

This matters because the repository already records preference flows / final pairs and complete probability calibration as open production blockers.

## 10. Why no sampled-lambda result is being manufactured now

The workstream called for a pre-declared probabilistic lambda treatment. A numerical prior distribution was **not sealed before the fixed-lambda outputs were inspected**.

Choosing one now to produce a convenient central answer would be post-hoc model selection and would violate the purpose of this exercise. Therefore no sampled-lambda forecast is reported here.

A future probabilistic lambda treatment should be derived from external pre-election evidence — for example cross-election spatial persistence across official federal cycles — and its distribution must be frozen before examining its 2026 Assembly seat output.

## 11. Adjudication against the promotion gate

| Gate | Result |
| --- | --- |
| reproducible pre-election spatial construction | **PASS** |
| statewide-vote conservation | **PASS** |
| crosswalk method replication | **PASS** |
| independent House/Senate spatial robustness | **PASS, with dependence caveat** |
| stable across plausible lambda | **FAIL** |
| held-out/prospective seat improvement | **INCONCLUSIVE / final-pair mismatch** |
| not dependent on one statewide poll | **PASS for geography construction** |
| preference/final-pair behaviour validated | **FAIL / existing blocker** |
| uncertainty appropriately represented | **OPEN** |
| normal production validation/authorisation | **BLOCKED** |

### Decision

**Do not promote the 2025 geography or alter canonical PROD in this PR.**

The 2025 surface should be retained as a governed challenger because it contains genuine new spatial information. The more urgent modelling task is to calibrate ONP spatial persistence and final-pair/preference behaviour before any production replacement is considered.

## 12. Practical interpretation

The investigation changes the way the existing headline forecast should be read.

The canonical expectation of roughly 16 ONP Assembly seats is not simply a consequence of polling One Nation in the low-20s. It is strongly mediated by a full-strength geographic-persistence choice. Under otherwise identical statewide evidence, plausible shrinkage treatments produce materially fewer ONP seats and materially more Coalition seats.

Conversely, updating from 2022 to 2025 geography at full persistence does not greatly alter ONP's aggregate seat expectation, but it substantially changes *which seats* the model thinks One Nation can win.

That is a classic "right total for potentially wrong reasons" risk. It is exactly why the canonical forecast should remain frozen while the challenger is validated.

## Next research step

Estimate or pre-register a defensible persistence distribution using only pre-election evidence, then rerun the 2025 challenger prospectively. Do not tune lambda to Morgan, analyst seat calls or desired chamber outcomes.

A useful empirical clue, not yet a production parameter, is that the observed 2025-on-2022 House spatial slope is 0.7749 over roughly three years. Any conversion of that descriptive slope into a 2026 persistence prior requires an explicit temporal model and should be a separate governed exercise.
