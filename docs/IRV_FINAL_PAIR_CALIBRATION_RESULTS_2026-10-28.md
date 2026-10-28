# Assembly IRV preference and final-pair calibration — results

**Date:** 28 October 2026  
**Status:** historical research adjudication; no canonical 2026 forecast change  
**PR:** #138

## Executive finding

The current five-family Assembly IRV mechanism is **directionally useful but probabilistically overconfident and structurally limited by family aggregation**.

The preregistered historical transfer-evidence challenger (C1) could not identify a sharper source-family transfer matrix without violating the frozen evidence thresholds. Only seven clean events survived all semantic admissibility rules, all from Greens sources. Every C1 row therefore remained the preregistered broad fallback.

When scored conditionally on observed historical five-family first preferences:

- C0, the current production preference mechanism, retains high modal winner/final-pair accuracy;
- its final-pair probability scores deteriorate markedly in the more recent multi-party elections;
- C1's broad fallback does **not** improve modal final-pair accuracy, but its wider uncertainty materially improves final-pair Brier score and log loss;
- most C0 final-pair mistakes arise because `OTH_IND` is collapsed into one synthetic contender before IRV counting.

**Adjudication:** retain the research infrastructure; do not promote C1; do not alter PROD in this PR; do not proceed to C2/C3 source-family fitting because C1 is not identified. The next model-development question should be candidate/minor-party resolution and preference uncertainty, not another search for a five-family transfer coefficient.

## 1. Guardrails

The calibration protocol and Amendment 1 were committed before the relevant challenger fit/score stages. Historical fitting did not use:

- 2026 Assembly forecast outputs;
- PR #135/#136 geography-shadow outputs;
- October 2026 Roy Morgan seat polling;
- campaign or analyst seat calls;
- desired 2026 final pairs.

Historical winner/final-pair outcomes were loaded only for scoring after C1's evidence thresholds/model class had been fixed.

No 2026 challenger was executed in this workstream because no empirically fitted C1 row passed the preregistered identification gate.

## 2. Evidence reconstruction

Official VEC district distribution pages were audited across the four historical cycles. Candidate-level distribution tables were recoverable for:

| cycle | districts with candidate distribution table | districts without distribution link |
| --- | ---: | ---: |
| 2010 | 44 | 44 |
| 2014 | 45 | 43 |
| 2018 | 48 | 40 |
| 2022 | 28 | 59 |

The broader candidate-level audit recovered **702 exclusion events**:

- 163 first-exclusion/original-parcel events;
- 539 later mixed-parcel events;
- 460 events with some same-family transfer;
- source-family events: ALP 8, Coalition 24, Greens 103, OTH/Independent 567, One Nation **0**.

Later mixed parcels are not interpreted as original voter preferences. They are retained as operational elimination-stage evidence only.

### Clean original-parcel evidence

The original-parcel extractor produced 163 clean first-exclusion events before the semantic model rules were applied. Of these:

- 153 were `OTH_IND` source events and were excluded from empirical row fitting because `OTH_IND` is deliberately recognised as a heterogeneous residual family;
- three candidate events were excluded because multiple continuing candidates occupied one collapsed destination family;
- only **seven** events were admissible for C1 fitting, all from Greens sources.

Two 2010 source pages remained fail-closed because the historical governed candidate registry could not safely reconcile the named candidate. They cannot rescue the C1 identification threshold and were not manually guessed.

## 3. C1 identification result

Amendment 1 required, for any empirical source-family row:

- at least 12 admissible clean events;
- at least two earlier elections;
- an identifiable conditional destination-attractiveness graph;
- no sharp empirical `OTH_IND` row.

No source-family row passed those rules.

| target cycle | admissible training events | empirical rows | result |
| --- | ---: | ---: | --- |
| 2014 | 1 | 0 | all rows broad fallback |
| 2018 | 1 | 0 | all rows broad fallback |
| 2022 | 7 | 0 | all rows broad fallback |

The exact pre-outcome C1 freeze candidate is pinned by SHA-256 `056127783aebb1bea4ed0f5ab20b0685ece4c98d3e82b1ecacd620c0f8b6e78c` and copied into `metadata/irv-c1-walkforward-freeze-2026-10-28.json` with its source run/artifact identifiers.

This is a **negative identification result**, not permission to lower the thresholds after seeing the data.

## 4. C0 historical benchmark

C0 is the current Assembly preference mechanism under test:

- fixed statewide 5×5 `PREFERENCE_PRIOR`;
- Dirichlet concentration 72;
- one preference matrix draw shared across all districts in a simulated election;
- current deterministic `_count_irv` elimination logic.

The benchmark conditions on observed historical five-family first preferences. It therefore tests the preference/elimination/family-aggregation mechanism rather than the polling or primary-vote model.

True IRV final-pair scoring excludes 2018 two-candidate-preferred fallback pages.

### All four cycles

| metric | C0 |
| --- | ---: |
| winner districts | 351 |
| genuine final-pair districts | 214 |
| winner modal accuracy | **94.59%** |
| winner mean Brier | **0.0893** |
| winner mean log loss | **0.2360** |
| final-pair modal accuracy | **92.52%** |
| final-pair mean Brier | **0.1400** |
| final-pair mean log loss | **0.7925** |

C0 result SHA-256: `d77fd981c891f8d359b139a957eba0c2d12bfa86eb6a48600725c603e62e59d2`  
Actions run: `40692782605`  
Artifact ID: `12817408939`  
Artifact ZIP digest: `sha256:0c16ef0367f22729bc7fa56f94dfef950995009859d78c0059f8574b58fac3be`

### By cycle

| cycle | pair n | pair modal accuracy | pair Brier | pair log loss | winner modal accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2010 | 44 | 100.00% | ~0.0000 | ~0.0000 | 96.59% |
| 2014 | 45 | 95.56% | 0.0889 | 0.6140 | 96.59% |
| 2018 | 48 | 91.67% | 0.1667 | 1.0409 | 90.91% |
| 2022 | 77 | 87.01% | 0.2333 | 1.1949 | 94.25% |

The decline in final-pair probability performance as the electoral environment becomes more multi-party is material. The 2010 result should not be read as evidence that the same simplification is equally suitable in 2026.

## 5. Error anatomy

Across the 214 C0 final-pair observations, 16 modal final pairs are wrong.

- **12 of 16 (75%)** have `OTH_IND` in the model's modal final pair when the observed final pair contains no `OTH_IND` family.
- In 2022 this is **9 of the 10** modal final-pair errors.
- **11 of the 16** wrong observed final pairs receive zero probability in the 5,000 C0 simulations.
- The four wrong pairs not driven by a phantom `OTH_IND` contender are Greens elimination-order cases (Prahran/Preston/Pascoe Vale across the relevant cycles).

The dominant structural problem is therefore not simply a poorly chosen transfer percentage. Collapsing multiple independents/minor-party candidates into one `OTH_IND` primary pool can create a synthetic contender stronger than any actual candidate and changes the elimination order before preferences are even applied.

C0's 19 modal winner errors across all four cycles also concentrate in interpretable classes: seven observed Greens winners are modelled as Labor, three observed OTH/Independent winners are modelled as a major party, and the remaining errors are mostly close Labor–Coalition reversals.

## 6. Frozen C1 score

Because C1 identified no empirical row, its frozen consequence is the preregistered broad off-diagonal mean with concentration 2 for every source family. C1 is scored only on its walk-forward target cycles (2014, 2018, 2022).

C1 result SHA-256: `3bdd1c410888f00548c77876f3971965e3a9f8521d2f2e40df4e39f79ba638d7`  
Actions run: `40693404541`  
Artifact ID: `12817988630`  
Artifact ZIP digest: `sha256:107f755259081cb8d8ef5278f81b6f77fd9d0bd32257b3cecf1113a842b6d565`

### Matched 2014/2018/2022 comparison

| metric | C0 current prior | C1 broad fallback | change |
| --- | ---: | ---: | ---: |
| winner modal accuracy | **93.92%** | 90.49% | −3.42pp |
| winner mean Brier | **0.1038** | 0.1611 | worse |
| winner mean log loss | 0.2935 | **0.2631** | better |
| final-pair modal accuracy | 90.59% | **90.59%** | unchanged |
| final-pair mean Brier | 0.1762 | **0.1309** | better |
| final-pair mean log loss | 0.9977 | **0.5718** | substantially better |

C1 does not discover a better transfer mean. It mainly widens uncertainty.

The unchanged modal final-pair accuracy is especially informative: the current mean structure/primary ordering continues to determine the most common pair, while the broader distribution stops expressing unjustified certainty about alternative elimination paths.

The trade-off is real. Broad C1 is less decisive and worsens winner Brier/modal accuracy, even as it materially reduces catastrophic final-pair log-loss errors.

## 7. Scientific interpretation

The evidence supports four conclusions.

### 7.1 The production mean prior is not falsified

C0's modal accuracy is high enough that replacing its transfer means with uniform transfers would discard useful information. C1 provides no empirical historical estimate capable of improving those means under the frozen rules.

### 7.2 The production uncertainty is too sharp for final-pair inference

Concentration 72 produces increasingly poor final-pair probability scores in modern cycles and assigns effectively zero probability to several outcomes that actually occurred. C1's broad uncertainty improves final-pair Brier/log loss without changing modal pair accuracy on the matched cycles.

This is evidence for an **uncertainty-calibration problem**, not evidence that concentration 2 should automatically replace 72 in PROD.

### 7.3 `OTH_IND` aggregation is a first-order architecture problem

Most final-pair errors are generated before a defensible source-party transfer coefficient could fix them. The model combines candidates who compete against and transfer to one another into one synthetic family primary.

A future challenger should resolve candidate/minor-party fragmentation rather than attempting to tune a single `OTH_IND` transfer row.

### 7.4 C2/C3 source-family models are not identified

A hierarchical or district-specific source-family model cannot be justified when the pooled empirical row itself does not meet the preregistered evidence threshold. Proceeding to C2/C3 would convert sparsity into pseudo-precision.

## 8. Adjudication

### Pass / retain

- four-cycle official final-pair/winner scoring infrastructure;
- corrected genuine-IRV final-pair universe;
- historical VEC distribution-page audit;
- clean original-parcel and effective-parcel evidence audits;
- frozen C1 evidence/parameter gate;
- C0 and C1 reproducible historical scoring workflows;
- the finding that final-pair uncertainty is under-dispersed under C0;
- the structural diagnosis of `OTH_IND` aggregation.

### Reject / do not promote

- C1 as a production preference matrix;
- any post-hoc lowering of the 12-event/two-election identification threshold;
- C2/C3 five-family source-party fitting on the current evidence;
- a 2026 shadow based on an unidentifiable fitted transfer model;
- any canonical forecast change in PR #138.

## 9. Recommended next workstream

Open a separate, preregistered workstream rather than extending #138 indefinitely. It should test two separable issues:

1. **Candidate/minor-party resolution:** use the complete historical candidate-primary evidence to model how `OTH_IND` vote is fragmented across actual candidates instead of treating the residual family as one contender.
2. **Preference uncertainty calibration:** retain informative mean structure where defensible, but test wider uncertainty using a validation design fixed before examining any new 2026 shadow.

The 702 effective elimination-stage parcels can inform whether a candidate-level operational transfer model is feasible, but later mixed parcels must not be relabelled as original voter source-party preferences.

Any resulting 2026 challenger should be a new explicit PR after historical architecture and scoring rules are frozen.
