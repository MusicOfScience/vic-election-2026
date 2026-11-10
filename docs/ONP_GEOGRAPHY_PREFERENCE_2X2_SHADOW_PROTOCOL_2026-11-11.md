# 11 November 2026 — ONP geographical prior × preference uncertainty: controlled 2×2 sensitivity

**Status:** Pre-execution methodological specification, code and review-only workflow. This is a **mechanism sensitivity**, not model development, outcome-informed tuning, an empirically calibrated forecast, or authorisation to replace the 31 October reference.

## Central question

Does the implemented 2022 federal-auxiliary One Nation geographical propensity, and/or the tight concentration of the five-family preferential transfer distribution, materially cause the unusually high winning frequencies in Greenvale, Kororoit, Sydenham, Kalkallo, Mill Park and Morwell? Would a more conservative implementation materially change the party seat distribution and high-confidence claims?

PR #163 established: the 2026 forecast engine first clips all family logit deviations using `assembly.local_logit_limits.ONP=0.45`, then overwrites the ONP value with a federal-derived auxiliary independently bounded at **−1.20/+1.10**. The model also draws five-family Dirichlet preference rows at concentration **72**. Historical candidate-resolved work found concentration 4 promising for the candidate-resolved log-loss objective but **failed** its production winner-Brier gate against the established five-family model. Its selected value is therefore used **only as a stress value**, never a promoted choice for the current architecture.

## Frozen 2×2 specification

| Cell | ONP federal ecological locality | Assembly Dirichlet preference concentration |
|---|---|---:|
| **R / reference** | Original AEC auxiliary bounded −1.20/+1.10 | 72 |
| **G / geography bounded** | Clip the *existing* 88 AEC ONP auxiliary values to −0.45/+0.45, otherwise preserve all data | 72 |
| **P / wider preference stress** | Unchanged −1.20/+1.10 | 4 |
| **GP / both** | Clip to −0.45/+0.45 | 4 |

**All other inputs**: same original frozen **31 October 2026** state polls and eligibility decisions, no November polls, same official 2022 local baseline, same by-election evidence, same statewide polling model, same preference *mean matrix*, same shock distributions, same election date, simulation seed **20260826**. Run the **unmodified `vicforecast.forecast_2026.run_experimental_forecast`** through transient in-memory overrides for the scenario's `build_assembly_seed` output and `load_forecast_config` return value. Never write model outputs from this script.

Each cell uses **2,000 whole-election draws**. The existing published reference is **5,000 draws** and is not exactly identical to the new 2,000-draw control. All three numerical comparisons are made against the **same-size 2,000-draw R cell**, never against the different-size historical release. Random seed equality does **not** prove strict common-random-number coupling when the gamma/Dirichlet shape parameters change; interpret tiny probability deltas cautiously. Monte Carlo variation and the user's actual preference uncertainty are different sources of error.

All four scenarios run the original complete model engine but **only Assembly district/chamber results are interpreted**. The downstream Council RNG stream may differ as a side effect of an altered Assembly preference-draw sequence, despite identical Council assumptions: no claim is made that Council forecasts are sensitive to those parameters.

## Outputs and stopping rule

A single structured, source-fingerprinted JSON report should contain:

1. Exactly 88 named districts per cell, each family's modelled winning frequency, favoured family and modal final pair; party mean/median seats, majority and hung frequencies, and count of districts with ONP win frequency ≥80%.
2. Delta mean seats by family against control; exactly named changed modal winners and the twenty largest individual seat-probability changes for G, P and GP; count of districts with any winner-frequency shift ≥5 percentage points.
3. Fixed focus districts: Greenvale, Kororoit, Sydenham, Morwell, Kalkallo, Mill Park, Pakenham, Hawthorn, Kew, Benambra, Ripon; all four values and final-pair labels.
4. A simple **factorial interaction**, GP−G−P+R, by party mean seats. It is conditional model interaction, not empirical real-world effect.
5. Source file SHA-256 fingerprints, explicit as-of/seed/run count and a hard **no canonical-mutation** assertion.

**Descriptive materiality thresholds fixed before execution:** ≥0.05 change in one family's electoral win frequency in an individual seat; ≥1.0 change in expected Assembly seats by family; change of modal winning family in any seat. These thresholds screen practical relevance; they are not formal statistical significance tests. The proper interpretation of smaller differences is *indeterminate at this run size*, not **no effect**.

**Decision rule:** if G substantially changes high ONP probabilities, geography is an operative sensitivity, **not** a proven buggy assumption or validated correction. If P substantially changes them, the five-family transfer distribution is consequential, **not** evidence that concentration 4 is a calibrated alternative. The production gate remains closed without independent, walk-forward winner and final-pair calibration, including the known residual-candidate/independent aggregation failure.

If no large difference emerges, stop the geographical-only investigation. Do **not** extend the grid or retune parameters to manufacture a desired result. Instead prioritise individually resolved candidates, contemporaneous preference evidence and November primary poll admission, retaining all known limitations.

## Locked 2026 operational boundaries

- No admission of held DemosAU, Resolve, Lighthouse or Pakenham polls.
- No party-specific or candidate-specific incumbent, personal vote, how-to-vote or preference-transfer coefficient is inferred from 2026 announcements.
- No 2026 election outcomes are available or scored; no historical validation archive or previously registered prospective seal is opened.
- No model-input CSV, `model/config`, `model/src`, canonical output, owner approval, VEC candidate registry or `metadata/release-readiness.generated.json` is modified.
- No production status change from **6/9**.
- Data corruption, missing 88-electorate coverage, altered frozen config or source fingerprint, or failed tests are hard stops.

## Concurrent evidence correction

The Lighthouse poll-source entry in `metadata/november-poll-evidence-review-2026-11-11.json` is corrected to **Labor 22, Coalition 31, One Nation 23, Greens 14** based on contemporary News Corp publisher coverage, with the contradictory **Labor 23, ONP 22** Poll Bludger 6 November summary **retained explicitly**. A same-day reader of Poll Bludger itself pointed out the reversed figures. This poll remains held; no canonical forecast contained it. Links:

- <https://www.news.com.au/national/victoria/politics/new-victorian-poll-casts-more-doubt-for-labor-just-three-weeks-before-the-election/news-story/fb9f9df18a632a59d797a0a094a89c83>
- <https://www.pollbludger.net/2026/11/06/victorian-election-minus-three-weeks-2/>
- <https://www.pollbludger.net/2026/11/06/victorian-election-minus-three-weeks-2/comment-page-1/>

## Reproduction and CI

```bash
python -m pytest model/tests/test_onp_geography_preference_shadow.py -q
python model/scripts/shadow_onp_geography_preference_factorial.py \
  --simulations 2000 --seed 20260826 \
  --output artifacts/onp-factorial/onp-geography-preference-2026-11-11.json
```

GitHub's **ONP geography × preference uncertainty shadow** workflow runs these steps independently on the PR, checks source fingerprints and Git diff against canonical paths, displays concise numerical evidence and retains a **30-day review-only artifact**. A green workflow is execution evidence, not certification or an owner-model-change vote.

*When the run completes, its actual numerical findings should be appended in a separately identified post-execution results document, preserving this design unchanged.*
