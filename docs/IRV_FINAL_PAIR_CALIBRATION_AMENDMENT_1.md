# IRV final-pair calibration — Amendment 1

Status: preregistered before inspection of the reconstructed historical source-family event counts or any C1 target-cycle score.

Date: 28 October 2026

## Why this amendment exists

The initial evidence audit established two structural facts before C1 fitting:

1. the 2018 scoring artefact contains a documented fallback from true distribution-derived final pairs to published two-candidate-preferred (2CP) pairs in seats without a distribution result;
2. historical VEC distribution pages have a stable count structure in which the first exclusion is a clean original-parcel transfer, while later exclusions contain mixed parcels from earlier transfers.

Neither fact is a 2026 forecast result. This amendment fixes the scoring target and the C1 estimator before the reconstructed source-family event counts are inspected.

## Final-pair scoring correction

A historical final pair is admissible for IRV scoring only when its `outcome_table_kind` is one of:

- `results-after-distribution`;
- `distribution-page-final-total`.

The 2018 `two-candidate-preferred-final-page` fallback is excluded from IRV final-pair scoring. Early-majority seats with no official final distribution remain unscored for final-pair identity. Official elected-member outcomes remain valid for winner scoring.

The corrected C0 benchmark is therefore the control for every later C1/C2 comparison. C1 and C0 must be compared on the exact same admissible target seats within each cycle.

## C1 clean-event universe

A training event may enter C1 only when all of the following are true:

1. it is the first candidate exclusion in an official VEC distribution;
2. the transfer parcel reconciles exactly to that candidate's first-preference vote total;
3. destination transfer votes reconcile exactly to the parcel total;
4. the source candidate and every continuing destination candidate map through the governed historical party-family crosswalk;
5. no transfer remains inside the same collapsed model family as the source candidate;
6. no continuing destination model family contains more than one candidate in that event.

Rules 5–6 deliberately remove observations whose candidate-level structure the five-family IRV engine cannot represent. They remain structural diagnostics and are not silently discarded from the research record.

Later mixed-parcel exclusions are not C1 training observations unless a future separately preregistered decomposition can recover original preference origins from official evidence.

## C1 row eligibility

A source-family row may receive an empirical C1 parameter only when, using elections strictly earlier than the target cycle:

- at least **12** admissible clean events exist;
- those events span at least **two distinct earlier elections**;
- the conditional destination-attractiveness model is identifiable from the observed continuing-family choice sets.

The 12-event threshold is fixed before inspecting the reconstructed family counts and is consistent with the repository's earlier conditional-preference numerical gate.

`OTH_IND` is never eligible for a sharp C1 source row. It is a heterogeneous aggregation of unrelated independents and minor parties and therefore remains on the broad fallback in C1 regardless of sample size.

A row that fails any criterion uses the broad fallback rather than borrowing a sharp point estimate from another source family.

## C1 mean model

For each eligible source family, C1 estimates destination **attractiveness** rather than naïvely averaging observed shares across seats with different available parties.

For event `e`, let `A_e` be the continuing destination families. For source family `s`, each destination family `j` has positive attraction `theta[s,j]`, with the source diagonal fixed at zero. The event probability is:

`p[e,j] = theta[s,j] / sum(theta[s,k] for k in A_e)` for `j in A_e`.

`theta` is estimated by conditional multinomial maximum likelihood using only admissible earlier-cycle events. One log-attraction is fixed as the reference for identification. If the observed choice-set graph does not identify all required destination contrasts, the row is declared unsupported and uses the broad fallback; no ridge term is introduced merely to force identifiability.

The fitted attractions are normalised to a full off-diagonal mean row after estimation. When the production IRV restricts the row to currently continuing families, it recovers the same conditional-attractiveness form.

## C1 dispersion

Dispersion is estimated separately for each eligible source-family row from the same earlier-cycle training events.

The candidate concentration grid is fixed at:

`[2, 4, 8, 12, 18, 24, 36, 48, 72, 108, 144]`.

For each value, event transfer counts are scored under a Dirichlet-multinomial model centred on the fitted conditional destination probabilities. The training-only concentration with the greatest summed log likelihood is selected. If values are tied to numerical tolerance, choose the **lower** concentration, preserving more uncertainty.

No target-cycle final-pair or winner outcome enters concentration selection.

## Broad fallback

Unsupported source rows use a uniform off-diagonal mean over the four other model families and concentration **2.0**, matching the existing leakage-safe historical replay fallback. When some destination families have already been eliminated or were absent, the IRV counter renormalises that broad row across the continuing families.

## Dependence held fixed in C1

C1 changes preference means and row dispersion only. It retains the current model's one whole-election preference-matrix draw per simulation, shared across districts. Cross-seat preference dependence is therefore held fixed for the C0-v-C1 test.

Election-level versus district-level residual dependence belongs to C2 and may be tested only if C1 passes held-out scoring strongly enough to justify extra complexity.

## Walk-forward targets

- 2014 is reported as a diagnostic C1 broad-fallback case because only one earlier election exists and no empirical row can satisfy the two-election rule.
- 2018 may fit empirical rows from 2010 + 2014 only.
- 2022 may fit empirical rows from 2010 + 2014 + 2018 only.
- A later 2026 shadow, if authorised, may fit from 2010 + 2014 + 2018 + 2022 only after the historical model class is frozen.

Promotion still requires improvement on at least two genuinely held-out historical target cycles. A 2014 broad-fallback diagnostic does not count as an empirical-row validation cycle.

## Still forbidden

This amendment does not authorise inspection of 2026 challenger outputs. C1 model selection must remain independent of:

- 2026 Assembly seat/chamber probabilities;
- PR #135/#136 shadow results;
- October 2026 seat polling;
- named-seat analyst or campaign claims;
- desired 2026 final-pair identities.

Canonical PROD remains unchanged.
