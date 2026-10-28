# ONP spatial persistence calibration and 2026 shadow — results

Updated: 28 October 2026  
Status: governed shadow result; **no canonical forecast or production parameter change**

## Executive decision

Historical federal-election evidence strongly supports the existence of a persistent One Nation (ONP) spatial geography, but it also shows that the survival of newly revealed local deviations varies materially across eras.

A preregistered historical calibration was therefore frozen before any new 2026 Assembly output was generated. Its amended uncertainty model preserves between-era disagreement as an equal-weight empirical mixture rather than averaging that disagreement away.

When that frozen joint persistence distribution is propagated through the 2026 Assembly model:

- expected ONP seats move from **16.28 to 15.26**;
- Labor moves from **38.29 to 39.29**;
- Coalition moves only from **31.02 to 31.11**;
- Greens move from **2.40 to 2.33**;
- Labor majority probability rises from **19.3% to 24.54%**;
- Coalition majority probability rises from **3.1% to 3.86%**;
- hung-parliament probability falls from **77.6% to 71.6%**.

The aggregate chamber movement is moderate. The seat map is not: **15 modal winners and 21 modal final pairs change**, 38 districts move by at least five percentage points in ONP win probability, and 31 move by at least ten points.

**Adjudication: retain the calibrated persistence model as a governed shadow challenger. Do not alter PROD in this PR.** The geography workstream is now substantially better calibrated, but preference/elimination/final-pair uncertainty remains an independent production blocker and the current geography treatment still understates district-level spatial uncertainty because no additional residual `epsilon_i` distribution has been preregistered.

## 1. Calibration was frozen before the 2026 seat run

The calibration protocol was committed before any historical coefficient was observed:

- `docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_PROTOCOL.md`
- protocol commit `5e568b234372b3750c6a346da49be44b59ac3166`

Primary calibration evidence is final AEC **Senate** first preferences by physical polling place in Victoria at the 2016, 2019, 2022 and 2025 federal elections, mapped onto the same current 88 Assembly districts.

Senate is used as the historical calibration series because statewide party ballot coverage reduces House candidate-field and non-contestation contamination.

The two historical triplets are:

1. 2016 → 2019 → 2022
2. 2019 → 2022 → 2025

For each triplet, the middle election is decomposed into established geography plus a newly revealed spatial innovation, then the following election estimates retention of each component.

No new 2026 Assembly simulation, Roy Morgan seat poll, analyst seat call or campaign-source claim was read before the calibration freeze.

## 2. Historical Senate geography is highly persistent

Pairwise spatial diagnostics across all 88 current state districts:

| Federal cycles | Pearson | Spearman | weighted slope | weighted R² |
| --- | ---: | ---: | ---: | ---: |
| 2016 → 2019 | **0.9843** | **0.9857** | **0.8784** | **0.9678** |
| 2019 → 2022 | **0.9644** | **0.9562** | **0.7412** | **0.9270** |
| 2022 → 2025 | **0.9654** | **0.9545** | **0.9361** | **0.9293** |

This is strong evidence against treating ONP geography as ephemeral noise.

The result also clarifies why the fixed 2022 geography in PROD was not absurd: broad spatial structure is extremely persistent. The problem identified in PR #135 is that a fixed old surface can still put that strength in the wrong individual seats.

## 3. New local information does not have one stable retention coefficient

Projected from each historical triplet to the 574-day interval from 3 May 2025 to 28 November 2026:

| Historical triplet | established geography `a` | new innovation `kappa` |
| --- | ---: | ---: |
| 2016 → 2019 → 2022 | **0.8510** | **0.9729** |
| 2019 → 2022 → 2025 | **0.9854** | **0.6700** |

The two eras disagree in an important and structured way. The older triplet implies somewhat more decay in established geography but almost complete persistence of new local information. The newer triplet implies near-complete persistence of established geography but only about two-thirds persistence of the newly revealed innovation.

The initial bootstrap implementation averaged the two triplet values within every draw. That preserved the mean but suppressed genuine between-era model uncertainty. This was detected **before any new 2026 seat output was run** and corrected in:

- `docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_AMENDMENT_1.md`

The amended distribution is an equal-weight empirical mixture of the two complete 5,000-draw region-block bootstrap distributions, preserving every joint `(a, kappa)` pair.

## 4. Frozen persistence distribution

The final pre-2026 freeze is:

- `metadata/onp-spatial-persistence-freeze-v2-2026-10-28.json`
- historical calibration workflow: `40676227917`
- calibration artifact digest: `sha256:809a6d34ed4ee0732dd8db1bfab812d8b60eabdac801e82a70102d5acde87f57`
- frozen 10,000-draw mixture SHA-256: `14d6f36d593085a50369b5d7e51d3052afd075afaf0435a5b681773c866eeebd`

Mixture summaries:

| coefficient | mean | median | 5th pct | 25th pct | 75th pct | 95th pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| established geography `a` | 0.9158 | 0.9210 | 0.8235 | 0.8495 | 0.9860 | 1.0000 |
| new innovation `kappa` | 0.8082 | 0.7746 | 0.5997 | 0.6678 | 0.9749 | 1.0000 |

The joint correlation is **−0.9217**. Sampling the coefficients independently would therefore destroy a central feature of the historical evidence and is prohibited.

## 5. 2026 shadow coupling

The 2026 coupling was preregistered after the freeze but before the new seat run:

- `docs/ONP_SPATIAL_PERSISTENCE_2026_SHADOW_PROTOCOL.md`

For each simulation:

`delta_2026,s = a_s * persistent_2025 + kappa_s * residual_2025`

where the 2025 House spatial signal is decomposed using the same methodology established in merged PR #135.

The current House decomposition is:

- weighted 2025-on-2022 slope: **0.8730**;
- weighted R²: **0.6823**;
- weighted SD of 2022 signal: **0.5579**;
- weighted SD of 2025 residual: **0.3324**.

The persistence selection uses a separate fixed seed `20261028`; the election model retains its canonical seed `20260826`.

Control and challenger share exactly the same statewide poll draw, regional shock, district shock, by-election signal and preference matrix in every simulation.

A common ONP logit intercept is solved separately for every persistence draw so the central enrolment-weighted statewide ONP primary equals the control. Maximum residual after calibration was approximately **5.6×10⁻15 percentage points**.

## 6. Frozen-persistence 2026 Assembly result

Governed run:

- GitHub Actions run: `40677049969`
- simulations: **5,000**
- shadow artifact digest: `sha256:1650439bdf5bdd98fac2f9fe67e54b391f2b2357fc6693db80d2745edc9dbbbf`
- shadow JSON SHA-256: `0e1bf9d860859eaea7ce2d17230b071df64d359ccdafcf56a8e61b0ae0fe6353`
- control reproduced canonical Assembly results to machine precision

| Outcome | current PROD geography | frozen historical-persistence shadow | change |
| --- | ---: | ---: | ---: |
| Labor mean seats | 38.29 | **39.29** | +1.01 |
| Coalition mean seats | 31.02 | **31.11** | +0.09 |
| ONP mean seats | 16.28 | **15.26** | −1.02 |
| Greens mean seats | 2.40 | **2.33** | −0.07 |
| Other/independent mean seats | 0.01 | **0.01** | ~0 |
| P(Labor majority) | 19.30% | **24.54%** | +5.24pp |
| P(Coalition majority) | 3.10% | **3.86%** | +0.76pp |
| P(hung) | 77.60% | **71.60%** | −6.00pp |

The ONP chamber distribution remains broad: the challenger's central 80% interval is approximately **8–23 seats**, versus **10–23** under the fixed current geography.

The correct interpretation is not that calibrated geography neatly removes one ONP seat. It is that introducing empirically calibrated spatial uncertainty shifts some probability mass away from ONP while widening the lower tail and materially changing individual contests.

## 7. Chamber robustness across historical regimes

The fixed persistence mixture deliberately retains two distinct historical regimes. Their conditional chamber results are strikingly similar:

| source regime | simulations | Labor mean | Coalition mean | ONP mean | P(hung) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2016–2019–2022 | 2,548 | 39.22 | 31.17 | **15.30** | 72.37% |
| 2019–2022–2025 | 2,452 | 39.37 | 31.04 | **15.23** | 70.80% |

That is useful evidence that the chamber-level ONP total is not being driven by which historical persistence regime happens to be selected. The uncertainty remains much more consequential geographically than aggregately.

## 8. Seat identity remains unstable

Compared with the current geography:

- **15 modal winners change**;
- **21 modal final pairs change**;
- **38 districts** move by at least 5pp in ONP win probability;
- **31 districts** move by at least 10pp.

Largest ONP win-probability changes include:

| District | primary change | ONP win-P change | interpretation |
| --- | ---: | ---: | --- |
| Greenvale | −20.65pp | **−93.94pp** | very large downgrade |
| Kalkallo | −17.12pp | **−79.62pp** | very large downgrade |
| Kororoit | −13.60pp | **−71.30pp** | very large downgrade |
| Lara | +11.14pp | **+67.82pp** | very large upgrade |
| Eureka | +7.93pp | **+56.72pp** | large upgrade |
| Niddrie | +9.38pp | **+53.56pp** | large upgrade |
| Thomastown | −8.26pp | **−51.66pp** | large downgrade |
| Mill Park | −6.98pp | **−45.80pp** | large downgrade |
| Narracan | −7.00pp | **−41.52pp** | large downgrade |
| Hastings | +6.97pp | **+36.18pp** | large upgrade |

This reinforces the main conclusion from PR #135: a headline ONP seat total can remain relatively stable while the model's seat map changes radically.

## 9. Held-out Roy Morgan check

Only after the frozen challenger had been generated and hashed was Roy Morgan's 21–26 October 2026 four-seat SMS poll inspected as held-out evidence.

Roy Morgan interviewed **283 electors across Bass, Hastings, Morwell and Pakenham** and reported:

- Bass: Liberal vs Labor, Liberal ahead;
- Hastings: ONP vs Liberal, ONP ahead;
- Morwell: ONP vs Labor, ONP ahead;
- Pakenham: ONP vs Labor, ONP ahead;
- pooled ONP primary across Hastings/Morwell/Pakenham: **39%**.

Source: https://www.roymorgan.com/findings/10371-victorian-state-voting-intention-eastern-victoria-seats-october-2026

The frozen challenger moves the simple mean modelled ONP primary across Hastings/Morwell/Pakenham from **32.79% to 34.87%**, directionally toward Morgan.

Seat-level comparison:

- **Bass:** challenger favours Coalition/Liberal (53.4%), matching Morgan's winner direction, but its modal final pair remains ONP–Labor rather than Liberal–Labor.
- **Hastings:** ONP win probability rises from 9.7% to **45.9%**, but the modal pair is ONP–Labor rather than Morgan's ONP–Liberal.
- **Morwell:** ONP remains strongly favoured at **81.2%**, but the modal opponent is Coalition rather than Morgan's Labor.
- **Pakenham:** ONP rises from 24.2% to **31.2%** win probability, but Coalition remains favoured and the modal final pair remains Coalition–Labor.

This is **directionally supportive of the geography update but not validating of the model's final-pair machinery**. The Morgan sample is far too small and seat-level sample sizes are undisclosed, so these differences must not be tuned away.

## 10. Promotion-gate adjudication

| Gate | Result |
| --- | --- |
| historical pre-election persistence calibration | **PASS** |
| calibration frozen before 2026 seat output | **PASS** |
| between-era uncertainty retained | **PASS** |
| joint `(a,kappa)` dependence preserved | **PASS** |
| official 2016/2019/2022/2025 source provenance | **PASS** |
| statewide-vote isolation | **PASS** |
| common-random-number control reproduction | **PASS** |
| chamber result robust across historical persistence regimes | **PASS, caveat** |
| seat identity robust | **FAIL** |
| held-out seat-direction evidence | **PARTIAL / SUPPORTIVE** |
| preference/final-pair validation | **FAIL / existing blocker** |
| full district-level spatial uncertainty (`epsilon_i`) represented | **NO / lower-bound uncertainty** |
| normal production probability calibration / authorisation | **BLOCKED** |

### Decision

**Do not alter canonical PROD in PR #136.**

The historical calibration is worth retaining and merging as research infrastructure. It materially improves the scientific treatment of ONP geography and provides a frozen challenger that can be reproduced without post-hoc tuning.

It does not clear the downstream production gate. The next highest-value modelling work is no longer another geography coefficient search. It is validation/improvement of multi-party elimination order, preference flows and final-pair probabilities, while retaining the new geography challenger as a shadow comparator.

## 11. Remaining limitations

1. **Only two historical triplets.** The equal-era mixture is deliberately conservative but coarse.
2. **Senate-to-House transportability.** Persistence is calibrated on Senate geography but applied to a House-derived 2025 innovation decomposition. PR #135's House/Senate correlation of ~0.91 supports this, but does not make the chambers identical.
3. **No additional `epsilon_i`.** The shadow captures uncertainty in retention of established and new spatial components, not all possible district-specific geographic error. Seat-level uncertainty is therefore a lower bound.
4. **Preference model unchanged.** Geographic improvements can expose rather than solve elimination-order and preference-flow deficiencies.
5. **Canonical evidence date remains 8 October 2026.** This work changes geography treatment only in shadow; it does not admit later statewide polling into PROD.

## 12. Recommended next workstream

Close the geography-calibration loop after PR #136 and move to a separate governed **final-pair / preference calibration** workstream.

The key question should be:

> Given multi-party primaries and realistic local geography, does the IRV elimination and transfer model produce calibrated probabilities for who reaches the final two and who ultimately wins?

That work should use historical Victorian full-preference evidence and held-out replay where possible, and should remain separate from any decision to promote the ONP geography challenger.
