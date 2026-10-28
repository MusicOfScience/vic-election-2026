# ONP spatial-persistence calibration protocol

Updated: 28 October 2026
Status: preregistered calibration design; **no 2026 Assembly output may be inspected by this workstream until the persistence model is frozen**

## Purpose

PR #135 established that the current model's One Nation (ONP) geography is not missing, but that the dedicated full-strength 2022-derived spatial surface is stale enough to create material seat-identity and final-pair risk. It did not identify a defensible production persistence coefficient.

This workstream estimates persistence from official historical evidence that predates the 2026 Victorian election and freezes a forward model before applying it to the 2026 Assembly simulator.

## Primary calibration evidence

Use final Australian Electoral Commission (AEC) **Senate first preferences by physical polling place in Victoria** for the federal elections of:

- 2 July 2016 (`20499`)
- 18 May 2019 (`24310`)
- 21 May 2022 (`27966`)
- 3 May 2025 (`31496`)

Senate geography is the primary series because ONP receives statewide ballot coverage in each cycle, reducing the House candidate-field / non-contestation problem. House results may be used only as a same-election measurement-error or chamber diagnostic and receive zero direct calibration weight unless a later protocol amendment is committed before any 2026 Assembly run.

Each cycle is mapped to the same current 88 Victorian Assembly districts using that election's AEC polling-place coordinates and the current Vicmap Assembly polygons. Declaration votes without defensible physical location are excluded rather than geographically invented.

## Spatial signal

For district `i` and election `t`:

`raw_t,i = log(max(ONP_share_t,i, 0.0005) / located_state_ONP_share_t)`

The signal is then centred using fixed 2026 district enrolment weights:

`delta_t,i = raw_t,i - sum_i(w_i * raw_t,i)`

The same 2026 weights are used in every cycle so changes in centring weights cannot masquerade as temporal persistence.

## Triplet decomposition

Two fully historical triplets are available:

1. 2016 → 2019 → 2022
2. 2019 → 2022 → 2025

For each triplet `(t0, t1, t2)`:

1. Estimate the middle-cycle persistent component with weighted least squares through the origin:
   `beta01 = argmin sum_i w_i (delta_t1,i - beta * delta_t0,i)^2`.
2. Define:
   `persistent_t1 = beta01 * delta_t0`
   `innovation_t1 = delta_t1 - persistent_t1`.
3. Estimate how much of those two components survives into `t2`:
   `delta_t2 = a * persistent_t1 + kappa * innovation_t1 + error`.
4. Fit `a` and `kappa` by weighted least squares constrained to `[0, 1]` because they are interpreted as retention fractions rather than amplification coefficients.

`a` measures persistence of already-established geography. `kappa` measures persistence of *new local information* revealed in the middle election. This directly matches the architecture suggested by PR #135 and avoids selecting a global lambda from 2026 seat outputs.

## Time conversion

Retention estimates are observed over unequal election intervals. For positive retention `r` measured over `D` days, convert to the target horizon by continuous compounding:

`r_target = exp(log(r) * target_days / D)`.

The target horizon is from the 2025 federal election (3 May 2025) to the 2026 Victorian election (28 November 2026).

If a fitted retention is exactly zero, its target-horizon value remains zero.

## Uncertainty

The point estimate alone is insufficient.

Use a **5,000-draw block bootstrap by the eight Victorian Legislative Council regions**. For each draw, sample eight regions with replacement and include all Assembly districts belonging to each sampled region. Refit the complete triplet decomposition.

For each bootstrap draw:

- estimate `a` and `kappa` for both historical triplets;
- convert each to the 2025→2026 target horizon;
- pool the two triplet target-horizon values with equal triplet weight;
- record the pooled `a_target` and `kappa_target`.

The frozen persistence distribution is the empirical joint bootstrap distribution of `(a_target, kappa_target)`, not a hand-chosen named distribution.

Because only two historical triplets exist, between-triplet disagreement is substantive model uncertainty and must be reported rather than averaged away. Leave-one-region-out estimates and unweighted estimates are required diagnostics.

## Measurement-error diagnostics

The calibration report must include:

- district coverage and located-vote share by cycle;
- cross-cycle Pearson and Spearman correlations;
- pairwise weighted slopes and R²;
- same-election House/Senate diagnostics where House coverage is usable;
- the existing 2022 point-crosswalk replication result as a mapping-method benchmark;
- largest district innovations and residuals;
- bootstrap distribution summaries and region influence diagnostics.

House and Senate ballots from the same election are overlapping evidence and must never be counted as independent replications.

## Freeze rule

Before any new 2026 Assembly simulations are run, commit a machine-readable calibration artefact containing:

- source hashes and URLs;
- all cycle surfaces;
- fitted triplet coefficients;
- bootstrap seed and draw count;
- empirical joint `(a_target, kappa_target)` draws or a checksummed deterministic representation;
- summary quantiles;
- explicit status `frozen-pre-2026-seat-run`.

Only after that commit may a separate simulation runner consume the frozen distribution.

## Prohibited fitting targets

The following remain held out and receive zero calibration weight:

- Roy Morgan's October 2026 Bass/Hastings/Morwell/Pakenham poll;
- 2026 campaign-source seat claims;
- analyst seat calls;
- any 2026 Assembly output from PR #135;
- desired chamber totals, majority probabilities or hung-parliament probabilities.

They may be used only after the calibration distribution is frozen, for prospective/held-out validation.

## Promotion rule

This workstream does not itself change PROD. A later production proposal must separately show that the frozen persistence distribution improves or appropriately widens seat-level calibration without degrading preference/final-pair behaviour or violating the repository's existing production gates.
