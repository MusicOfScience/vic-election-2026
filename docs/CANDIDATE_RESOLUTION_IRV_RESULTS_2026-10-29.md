# Candidate-resolution IRV historical results

**Date:** 29 October 2026  
**Workstream:** Assembly IRV candidate/minor-party resolution  
**PR:** #140  
**Status:** historical architecture supported; production promotion rejected/deferred

## Executive finding

The preregistered `R1` challenger resolves `OTH_IND` into the actual minor-party and independent candidates while leaving Labor, Coalition, One Nation and Greens as the same family aggregates used by the current `R0/C0` model.

On the matched 2014–2022 historical final-pair universe, `R1` **passes every frozen architecture-screening criterion under both preregistered OTH destination-allocation rules**.

The dominant C0 failure diagnosed in PR #138 is therefore not merely descriptive. Treating the heterogeneous `OTH_IND` field as one synthetic contender is a material causal source of final-pair error in the historical benchmark.

The result does **not** justify production promotion. Candidate resolution improves final-pair inference very substantially but worsens winner-probability calibration under the still-narrow concentration-72 family preference uncertainty. Winner log loss increases from 0.294 to about 0.426. The next experiment must therefore combine the supported candidate-resolution architecture with a separately preregistered preference-uncertainty calibration rather than treating R1 as a finished model.

Canonical 2026 polling inputs, spatial priors, forecast outputs and production-authorisation state are unchanged. No 2026 R1 forecast or seat shadow was run in this workstream.

---

## 1. Frozen experimental design

The protocol and machine-readable support rule were committed before R1 fitting or historical outcome scoring.

### R0

The comparator is the PR #138 C0 benchmark:

- five collapsed model families: `ALP`, `LIB_NAT`, `ONP`, `GRN`, `OTH_IND`;
- current `PREFERENCE_PRIOR` mean structure;
- Dirichlet concentration 72;
- one family-level preference draw shared across all districts in a simulated election;
- deterministic lowest-tally IRV elimination;
- observed historical five-family first preferences as starting vote vectors.

### R1

R1 changes only the representation of the residual family:

- every actual VEC-listed Other/Independent candidate remains a separate contender;
- ALP, Coalition, One Nation and Greens remain collapsed family contenders;
- candidate-level first preferences reconcile exactly to the same district formal vote and C0 five-family totals;
- no cross-family preference mean is refitted;
- named-family transfer mass to OTH candidates is allocated **equally** across continuing OTH candidates in the primary specification;
- current-tally-proportional OTH allocation is a frozen sensitivity, not an alternative selected by score.

### Operational `q_oth`

R1 requires one quantity that C0 structurally cannot express: an eliminated OTH candidate can transfer to another continuing OTH candidate.

`q_oth` is therefore defined as the effective share of an eliminated OTH/Independent candidate's parcel transferred to continuing OTH/Independent candidates, conditional on at least one such candidate remaining.

It is an **operational elimination-stage quantity**, not an original voter-preference rate. Later VEC parcels can contain previously transferred ballots and are never relabelled as original preferences.

---

## 2. Pre-outcome evidence and freeze

The official VEC exclusion-parcel audit regenerated:

- **702** exclusion events;
- **163** clean original-parcel events;
- **539** later mixed-parcel events;
- **460** events with some same-family transfer;
- source-family events: ALP 8, Coalition 24, Greens 103, OTH/Independent 567, One Nation 0.

The effective-parcel evidence SHA-256 was frozen before R1 historical scoring:

`6180e2f699c28a7d3d458ae613b9e3a2f5e3cb6ba345f873ba1367134dd7e239`

Two 2010 district pages, Melton and Narre Warren South, remained fail-closed because the distribution-page candidate names could not be reconciled to the governed candidate registry. They were not manually repaired after seeing the calibration data.

### Walk-forward `q_oth`

The calibration unit is the district-election mean of eligible OTH exclusion-event retention shares. Uncertainty comes from a 5,000-draw block bootstrap over district-election units, not ballot-level pseudo-replication.

| Target | Training cycles | Eligible events | District-election units | Median | 5th pct | 95th pct |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2014 | 2010 | 93 | 40 | 0.3305 | 0.3047 | 0.3556 |
| 2018 | 2010, 2014 | 228 | 84 | 0.3656 | 0.3467 | 0.3847 |
| 2022 | 2010, 2014, 2018 | 332 | 118 | 0.3718 | 0.3549 | 0.3880 |

All three targets cleared the preregistered identification gate of at least 20 eligible events and at least 10 district-election units.

The exact pre-score `q_oth` fit SHA-256 was frozen as:

`d965b6c1447adfe69332f17e3ca03064cf317736073b0afbbe65e7f8fe60084e`

The historical scoring workflow regenerated both evidence products and verified these exact hashes **before** opening the historical outcome files.

---

## 3. Matched historical score, 2014–2022

The scorer first reproduced the published PR #138 C0 metrics to machine tolerance. That check passed before R1 was adjudicated.

### Family-level final-pair and winner metrics

| Metric | R0 / C0 | R1 equal allocation | R1 proportional sensitivity |
| --- | ---: | ---: | ---: |
| Winner districts | 263 | 263 | 263 |
| Winner modal accuracy | 0.9392 | 0.9316 | 0.9316 |
| Winner mean Brier | **0.1038** | 0.1194 | 0.1193 |
| Winner mean log loss | **0.2935** | 0.4263 | 0.4262 |
| Final-pair districts | 170 | 170 | 170 |
| Final-pair modal accuracy | 0.9059 | **0.9529** | **0.9529** |
| Final-pair mean Brier | 0.1762 | **0.0913** | **0.0905** |
| Final-pair mean log loss | 0.9977 | **0.4992** | **0.4597** |
| Observed pairs assigned zero probability | 11 | **5** | **4** |
| Phantom OTH modal-pair errors | 12 | **0** | **0** |

### What changed

Under the primary equal-allocation R1:

- final-pair modal accuracy rises by about **4.7 percentage points**;
- final-pair Brier score nearly halves, 0.1762 → 0.0913;
- final-pair log loss roughly halves, 0.9977 → 0.4992;
- all **12** C0 phantom-OTH modal final-pair errors disappear;
- observed final pairs assigned zero probability fall from 11 to 5.

The proportional-allocation sensitivity tells the same qualitative story and is marginally better on pair Brier/log loss. Because the preregistration forbids selecting the allocation rule by score, the primary specification remains equal allocation. The sensitivity result is evidence that the architecture conclusion is not being driven by that allocation convention.

### Exact OTH candidate identity

There are 13 scored historical districts in which the observed family-level final pair contains `OTH_IND` and exact candidate identity is available for the R1 diagnostic.

Under both allocation rules:

- exact OTH-containing final-pair modal accuracy is **10/13 = 0.7692**;
- the primary equal-allocation run gives mean probability **0.7692** to the observed exact OTH-containing pair.

This is secondary evidence only. The frozen primary score remains the family-level final-pair comparison so R0 and R1 are evaluated on the same outcome space.

---

## 4. Frozen support rule

The preregistered architecture screen required all of:

1. final-pair log loss improvement ≥ 0.05;
2. final-pair Brier must not worsen;
3. winner Brier degradation ≤ 0.02 absolute;
4. phantom OTH modal-pair errors must fall;
5. the conclusion must be directionally stable under equal and proportional OTH destination allocation.

### Equal allocation

- pair log-loss improvement: **0.4985** — pass;
- pair Brier: 0.1762 → **0.0913** — pass;
- winner Brier change: **+0.01552** — pass within 0.02 tolerance;
- phantom OTH modal-pair errors: 12 → **0** — pass.

### Proportional sensitivity

- pair log-loss improvement: **0.5380** — pass;
- pair Brier: 0.1762 → **0.0905** — pass;
- winner Brier change: **+0.01549** — pass within tolerance;
- phantom OTH modal-pair errors: 12 → **0** — pass.

**Frozen adjudication:** `historically-supported-architecture-only`.

---

## 5. The important adverse result

R1 is not uniformly better.

Winner modal accuracy falls slightly, 93.92% → 93.16%, and winner Brier worsens by about 0.0155. That degradation was within the preregistered architecture-screening tolerance.

More importantly, **winner mean log loss worsens from 0.2935 to about 0.4263**. Winner log loss was a reported primary metric but was not a pass/fail threshold in the frozen architecture rule. It must therefore be treated as a genuine adverse result, not ignored because R1 passed the screen.

The most defensible interpretation is:

- candidate resolution fixes a real elimination-order/final-pair pathology;
- concentration 72 and/or the remaining family-level transfer uncertainty is still too restrictive for calibrated winner probabilities once candidate-level elimination paths are exposed;
- the supported architecture correction and preference-uncertainty calibration are separate problems and should remain separate experiments.

This is consistent with PR #138, where broader C1 uncertainty materially improved final-pair probability scores even though a sharper empirical five-family transfer matrix could not be identified.

---

## 6. Decisions

### Retain

- the candidate-resolved OTH/Independent research architecture;
- the official VEC effective-parcel audit;
- district-election block-bootstrap `q_oth` calibration;
- exact candidate reconciliation and R0 reproduction checks;
- equal-allocation primary rule plus proportional sensitivity.

### Do not promote

This workstream does **not** authorise:

- replacing the current production Assembly IRV mechanism;
- changing `PREFERENCE_PRIOR` means;
- changing concentration 72;
- changing any canonical 2026 forecast output;
- running a 2026 R1 seat shadow inside PR #140;
- claiming candidate resolution alone improves all probability calibration.

### Next experiment

The next clean workstream should preregister a **candidate-resolved preference-uncertainty calibration**. Its purpose is to test whether retaining the supported R1 candidate architecture while broadening/calibrating preference uncertainty can preserve the large final-pair gains without the observed winner-log-loss penalty.

That protocol should be committed before any new historical score and before any 2026 candidate-resolved shadow is generated.

Only after the combined architecture + uncertainty model passes its historical calibration gates should a separate, explicitly governed 2026 shadow be considered.

---

## 7. Reproducibility

Pre-score fit workflow:

- run: `40710083717`
- artifact: `12825532350`
- artifact zip SHA-256: `f9715fc05fad20a10ab11249bb079b2f4fabcab52e4fe94e2f1bb45521e4b403`

Historical scoring workflow:

- run: `40710790066`
- artifact: `12825967575`
- artifact zip SHA-256: `cda0cb042d0279cac44fa13a6414f939300400d535c17d5f3eda18c35ab98595`
- score JSON SHA-256: `269b7f518705d7d2072e508e5f6ab194b8b4b98c8cf631786c6d690a21a2f98e`

The scoring workflow verified the exact frozen effective-transfer evidence and `q_oth` fit hashes before reading historical outcomes, reproduced the C0 matched benchmark to machine tolerance, and passed the explicit no-2026/no-production boundary checks.
