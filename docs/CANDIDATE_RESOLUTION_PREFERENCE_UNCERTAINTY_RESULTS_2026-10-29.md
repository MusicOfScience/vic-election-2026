# Candidate-resolved preference uncertainty — historical results

Updated: 29 October 2026

## Question

PR #140 established that resolving actual Other/Independent candidates materially improves historical final-pair inference, but the candidate-resolved model using the current Dirichlet concentration of 72 worsens winner probability calibration.

This workstream asked one deliberately narrow question:

> Can the candidate-resolved architecture be retained while changing only preference-draw dispersion, with the existing preference means held fixed?

No 2026 Assembly forecast output, 2026 seat polling, preference-mean refit, or production forecast mutation was permitted during calibration or adjudication.

## Frozen design

The protocol was committed before new scoring in `docs/CANDIDATE_RESOLUTION_PREFERENCE_UNCERTAINTY_PROTOCOL.md`.

The concentration grid was fixed at:

`4, 8, 12, 18, 24, 36, 48, 72, 108, 144`

Walk-forward selection used:

- 2014 evidence only to select the concentration applied to 2018;
- pooled 2014+2018 evidence to select the concentration applied to 2022;
- an equal-weight average of winner and final-pair mean log loss as the selection objective;
- the higher concentration for ties within `1e-6`;
- equal OTH allocation as the primary rule;
- current-tally-proportional OTH allocation as the frozen sensitivity.

The existing PR #140 candidate-resolution architecture, preference means, `q_oth` definition, simulation count and election seed were held fixed.

## Gate A — training-only concentration selection

Workflow run: `40756820783`

Selection artefact SHA-256:

`2a63a1eaadc29dd46f5e6afb8046ce2e22eab3e7bf1df2b6e73333294a9ea5a1`

All four preregistered selections landed on concentration **4**, the lower edge of the frozen grid:

| Allocation | Held-out target | Training evidence | Selected concentration | Training objective |
| --- | ---: | --- | ---: | ---: |
| Equal | 2018 | 2014 | 4 | 0.120245 |
| Equal | 2022 | 2014+2018 | 4 | 0.171802 |
| Proportional | 2018 | 2014 | 4 | 0.118874 |
| Proportional | 2022 | 2014+2018 | 4 | 0.163951 |

This is strong evidence that the current concentration of 72 is too tight for the historical training objective. It is **not** evidence that 4 is the globally optimal concentration. Because every selection hit the lower grid boundary, the protocol forbids extending the grid after seeing held-out outcomes.

The selection was frozen in `metadata/candidate-resolution-preference-concentration-freeze-2026-10-29.json` before Gate B opened the held-out targets.

## Gate B — held-out 2018 and 2022

Workflow run: `40759176362`

Held-out score SHA-256:

`00ae0c61344a08f76e9f31be398ae5ad34279c3d62e174a600a31ea271fc6f62`

The tables below compare:

- **R0 / C0** — current five-family architecture, concentration 72;
- **R1 / 72** — candidate-resolved OTH architecture from PR #140, concentration 72;
- **U1 / 4** — the same candidate-resolved architecture and preference means, but with the walk-forward-selected concentration 4.

### Pooled 2018+2022 — primary equal-allocation rule

| Metric | R0 / C0 | R1 / 72 | U1 / 4 |
| --- | ---: | ---: | ---: |
| Winner modal accuracy | 92.57% | 91.43% | 87.43% |
| Winner mean Brier | 0.13096 | 0.15038 | 0.14747 |
| Winner mean log loss | 0.34009 | 0.50080 | **0.24776** |
| Final-pair modal accuracy | 88.80% | 95.20% | **95.20%** |
| Final-pair mean Brier | 0.20768 | 0.09220 | **0.06629** |
| Final-pair mean log loss | 1.13578 | 0.45784 | **0.09592** |
| Phantom OTH modal-pair errors | 12 | 0 | **0** |
| Observed final pairs assigned zero probability | 9 | 3 | **0** |

The proportional-allocation sensitivity tells the same qualitative story. Under proportional OTH allocation U1 has winner log loss `0.24018`, pair Brier `0.06286`, pair log loss `0.09090`, pair modal accuracy `95.20%`, and zero observed final pairs assigned zero probability.

## Per-cycle result

### 2018

| Metric | R0 / C0 | R1 / 72 | U1 / 4 |
| --- | ---: | ---: | ---: |
| Winner modal accuracy | 90.91% | 89.77% | 82.95% |
| Winner Brier | 0.1637 | 0.1942 | 0.1877 |
| Winner log loss | 0.4673 | 0.7870 | **0.3228** |
| Pair modal accuracy | 91.67% | 93.75% | **93.75%** |
| Pair Brier | 0.1667 | 0.1250 | **0.0907** |
| Pair log loss | 1.0409 | 0.7531 | **0.1234** |
| Zero-probability observed pairs | 3 | 2 | **0** |

### 2022

| Metric | R0 / C0 | R1 / 72 | U1 / 4 |
| --- | ---: | ---: | ---: |
| Winner modal accuracy | 94.25% | 93.10% | 91.95% |
| Winner Brier | 0.0979 | 0.1060 | 0.1068 |
| Winner log loss | 0.2114 | 0.2113 | **0.1718** |
| Pair modal accuracy | 87.01% | 96.10% | **96.10%** |
| Pair Brier | 0.2333 | 0.0718 | **0.0511** |
| Pair log loss | 1.1949 | 0.2738 | **0.0788** |
| Zero-probability observed pairs | 6 | 1 | **0** |

No held-out target suffered the preregistered catastrophic log-loss reversal under either OTH allocation rule.

## Preregistered adjudication

### Research-support gate: **PASS**

Under the primary equal-allocation rule:

- winner log-loss improvement vs R1/72: **+0.25305** required `>=0.03`;
- final-pair log-loss advantage vs R0/C0: **+1.03986** required `>=0.05`;
- final-pair Brier change vs R1/72: **-0.02590**, therefore improved rather than worsened;
- winner Brier change vs R1/72: **-0.00291**, therefore improved;
- final-pair modal accuracy drop vs R1/72: **0.0 pp**;
- no target-cycle catastrophic reversal;
- proportional-allocation sensitivity independently passes the same qualitative gate.

The correct research conclusion is therefore:

> **Historically supported uncertainty correction.** Candidate resolution should not be paired with the current concentration-72 preference uncertainty as though elimination paths were that precise. Much wider uncertainty materially improves held-out probability scoring without sacrificing the candidate-resolution final-pair accuracy gain.

### Strong production-candidate gate: **FAIL**

The stronger gate fails one consequential condition:

- U1 pooled winner Brier = `0.14747`;
- R0/C0 pooled winner Brier = `0.13096`;
- U1 is therefore **0.01651 worse** than R0/C0;
- the frozen production tolerance was at most `+0.01`.

Winner modal accuracy also falls from `92.57%` under R0/C0 and `91.43%` under R1/72 to `87.43%` under U1/4. Winner modal accuracy was not itself a frozen research gate, but it is an important diagnostic and must not be hidden by the excellent log-loss result.

Consequently:

- concentration 72 is historically too confident for the candidate-resolved architecture;
- concentration 4 is historically supported as an **uncertainty correction for research**, not as a universal production parameter;
- the lower-bound selection is a material calibration warning;
- **a separate 2026 shadow is not authorised by this workstream**;
- canonical PROD remains unchanged.

## Interpretation

The result resolves the main tension from PR #140 but exposes a more specific one.

Candidate resolution fixes a structural elimination-order problem. Widening preference uncertainty then fixes much of the probability overconfidence: it removes zero-probability observed final pairs and sharply improves both final-pair Brier and log loss. It also repairs the severe winner log-loss penalty seen under R1/72.

However, a single global concentration of 4 is too blunt to be considered production-ready. It protects against catastrophic misses by spreading probability more widely, but on some seats — particularly in 2018 — that diffusion changes modal winner calls and leaves winner Brier materially worse than the simpler R0/C0 benchmark.

The evidence therefore points away from the question “is the right global concentration 72 or 4?” and toward a richer uncertainty structure. A future preregistered workstream could test whether preference uncertainty should differ by source family, elimination stage, contest structure, or another historically identifiable dimension. Any such work must be specified before inspecting its 2026 Assembly effect.

The current workstream must **not** extend the concentration grid below 4 post hoc, choose an intermediate value because it looks attractive after the held-out result, or tune against 2026 seat outcomes.

## Decision

**Merge the historical research result when repository checks are green. Do not promote U1/4 into PROD and do not run a 2026 challenger under #142.**

This PR records a successful calibration diagnosis and a failed production-candidate gate. Both are useful results.
