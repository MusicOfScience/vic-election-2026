# ONP spatial persistence — frozen-calibration 2026 shadow protocol

Date: 28 October 2026  
Status: preregistered after persistence freeze, **before new 2026 Assembly output**

## Frozen input

The only permitted persistence input is:

`metadata/onp-spatial-persistence-freeze-v2-2026-10-28.json`

and specifically the checksummed 10,000-draw equal-era joint empirical mixture described there.

The earlier pooled-average freeze is explicitly prohibited as a simulation input.

## 2025 spatial decomposition

Use the same official AEC 2025 House → current Assembly spatial surface and the same weighted decomposition established in merged PR #135:

`delta_2025 = beta_25_22 * delta_2022 + residual_2025`

where `beta_25_22` is re-estimated reproducibly from the current model's 2022 ONP surface and the official 2025 House surface using fixed 2026 district enrolment weights.

No Morgan, campaign-source, candidate-specific, analyst or 2026 seat-result information enters this decomposition.

## 2026 latent geography

For simulation `s`, draw one *joint* persistence pair `(a_s, kappa_s)` and construct:

`delta_2026,s = a_s * persistent_2025 + kappa_s * residual_2025`

where:

`persistent_2025 = beta_25_22 * delta_2022`.

The two persistence coefficients must never be sampled independently because the historical calibration contains strong negative joint dependence.

No additional spatial error term `epsilon_i` is added in this workstream because no distribution for it was preregistered. The resulting geography uncertainty is therefore a lower-bound treatment of spatial uncertainty and must be described as such.

## Persistence draw selection

- simulations: **5,000**
- persistence selection seed: **20261028**
- selection rule: NumPy `default_rng(20261028).integers(0, 10000, size=5000)`; sampling with replacement from the frozen mixture in its committed/generated row order
- election simulation seed: the canonical model seed from `experimental_forecast.yml` (currently `20260826`)

The separate persistence seed prevents the geography-distribution draw from consuming or shifting the canonical election-shock RNG stream.

## Vote-level isolation

For each selected geography draw, solve one common additive ONP logit intercept at the frozen canonical statewide latent mean so the enrolment-weighted central ONP primary equals the current geography control.

This calibration may alter only the common ONP intercept. It must not alter district ordering or relative spatial deviations.

## Common random numbers

For every simulation, the control and frozen-persistence challenger use exactly the same:

- statewide latent poll draw;
- regional shocks;
- district shocks;
- by-election signal;
- preference-flow draw;
- IRV counting logic.

The only Assembly difference is the ONP local geographic field.

## Required outputs

Report for control and challenger:

- expected seats by party;
- P(ALP ≥45), P(Coalition ≥45), P(hung);
- district ONP mean primary and win probability;
- modal winner and modal final pair;
- number of districts with ONP win-probability movement ≥5pp and ≥10pp;
- modal winner and modal final-pair changes;
- largest district changes;
- outcome splits by historical mixture regime (`2016-2019-2022` vs `2019-2022-2025`) as a model-uncertainty diagnostic, not separate forecasts;
- persistence-draw realised quantiles/correlation;
- central-vote calibration residual diagnostics.

## Held-out validation

Only after the shadow output is generated and hashed may held-out evidence be inspected, including Roy Morgan's October 2026 four-seat mini-poll and analyst/campaign seat calls. Held-out evidence may evaluate the frozen challenger but cannot alter the frozen calibration, persistence mixture, draw seed or simulation coupling.

## Production rule

This remains a shadow experiment. No canonical input, coefficient or forecast artefact may be written. Any production change requires a separate explicit PR and must clear the repository's normal production gates, including preference/final-pair and probability-calibration blockers.
