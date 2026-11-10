# ONP geography × Assembly preference dispersion — completed controlled sensitivity

**Completed:** Wednesday 11 November 2026 AEDT. **Evidence:** [GitHub Actions run #42843996903](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42843996903), successfully finished, all **four** source-locked shadow cells (2,000 whole-election simulations per cell). **Status: research-only; NOT an authorised forecast or model update.**

The experiment protocol was committed *before* its first numerical execution: [ONP_GEOGRAPHY_PREFERENCE_2X2_SHADOW_PROTOCOL_2026-11-11.md](ONP_GEOGRAPHY_PREFERENCE_2X2_SHADOW_PROTOCOL_2026-11-11.md). The original registered model and all canonical polling/election artefacts remained byte-unchanged, verified by workflow source checks and `git diff --exit-code`.

## Exact source and computation evidence

- Source input-bundle SHA-256: **`9ace8c2c41247ce1c44983aa9ace9d9e4079c7549fe3fa90a37d21231d5a4483`** (17 files including original Python engine, pinned configuration and numerical constraints, polling data, historical surfaces, and this experiment code/protocol).
- Complete machine-readable results (all 88 districts × four cases, individual-family win frequencies and pairings, scenario effects, all 88 risk deltas, focus districts, input hashes): [GitHub Actions run #42843996903](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42843996903), artifact **`onp-geography-preference-factorial-shadow-2026-11-11`**, ID **13775839505**. Artifact expires **10 December 2026**.
- Uncompressed numerical JSON SHA-256: **`c3a474a492eb9497a971f926a2c8e42cb97f52a65921f695eafb3c83e6cc9365`**; GitHub ZIP archive SHA-256 **`09f3b04b535e22280a0a843720da59ce3dcb1b928102d2ae494c93be86d604de`**.
- Fixed published reference, 5,000 draws: Labor **34.4074**, Coalition **35.7782**, ONP **15.3608** expected seats. Identical-input 2,000-draw shadow control reproduced those to +0.0981, −0.1782 and +0.0952 seats respectively. All experimental deltas below use **the common 2,000-draw shadow control**, not the differently sized 5,000-draw release.
- Seed **20260826**, model as-of **31 October 2026**, no November polls, no changed baselines, no changed preference means, no recorded 2026 outcomes.

## Direct experiment results

| Assembly metric | Reference (R) | Bounded ONP geography (G) | Wider preference stress (P) | Both (GP) |
| --- | ---: | ---: | ---: | ---: |
| Labor mean seats | **34.51** | 33.73 | 33.70 | 33.16 |
| Coalition mean seats | **35.60** | **38.70** | 35.88 | 38.46 |
| One Nation mean seats | **15.46** | **13.25** | **15.49** | 13.72 |
| Greens mean seats | 2.43 | 2.32 | 2.66 | 2.37 |
| Other family mean seats | 0.01 | 0.01 | 0.27 | 0.30 |
| Hung frequency across shadow elections | **79.65%** | 69.85% | **42.95%** | **36.30%** |
| Labor majority frequency | 8.85% | 8.50% | 27.60% | 27.60% |
| Coalition majority frequency | 11.50% | 21.65% | 28.85% | 35.40% |
| ONP-winning frequency ≥80% in N seats | **6** | **3** | **0** | **0** |
| 80% simulation range: Labor | 25–44 | 23.9–44 | **12–55** | **11–57.1** |
| 80% simulation range: Coalition | 26–45 | 29–48 | **16–59** | **17–62** |
| 80% simulation range: ONP | 10–21 | 8–19 | **4–29** | **2–27** |

**Important:** Under P and GP, ALP + Coalition majority frequencies + hung frequencies sum to 99.4% and 99.3%, respectively. The balance comprises simulations in which one of the other model families reaches a majority; those are not separately classified in this table. Never present the two major-party majorities as if exhaustive. These are *model frequencies* under deliberately stress-tested assumptions, NOT calibrated electoral probabilities.

### Effects versus R (same 2,000 draws)

| Comparison | Δ Labor mean seats | Δ Coalition | Δ ONP | Modal winner changes | Districts with ≥5 pp family win-frequency change |
| --- | ---: | ---: | ---: | ---: | ---: |
| G − R | −0.776 | **+3.096** | **−2.205** | **4** | **22** |
| P − R | −0.803 | +0.281 | +0.038 | **1** | **80** |
| GP − R | −1.349 | **+2.856** | **−1.734** | **7** | **78** |

Mean-seat factorial interaction **GP−G−P+R** is **−0.521 seats Coalition** and **+0.434 One Nation**, indicating these interventions are not perfectly additive in this finite Monte Carlo simulation.

### Six originally ≥80%-winning One Nation districts

Each percentage is **One Nation's model winning frequency**, not primary vote or survey share.

| District | R | G | P | GP |
| --- | ---: | ---: | ---: | ---: |
| Greenvale | 96.4% | 88.8% | 78.2% | 66.3% |
| Kororoit | 96.3% | 86.8% | 78.4% | 66.9% |
| Sydenham | 92.0% | 83.2% | 75.1% | 62.3% |
| Kalkallo | 85.7% | 71.4% | 72.4% | 62.3% |
| Mill Park | 84.0% | 73.0% | 69.9% | 61.6% |
| Morwell | **86.2%** | **16.7%** | 76.7% | **24.5%** |

The *geography-only* scenario switches four modal winners: **Morwell and Narracan ONP→Coalition**, plus **Box Hill and Glen Waverley Labor→Coalition**. The *preference-only* scenario changes just **Bendigo East Labor→ONP**, with a relatively small 2.4 pp leading-frequency shift in that near-competitive district. The *both* scenario switches seven modal winners (Morwell, Narracan, Box Hill, Caulfield, Glen Waverley, Ringwood and Bendigo East).

## Interpretation, rival explanations and consequence

**Finding 1 — geographical ONP assumption is consequential.** The live model effectively uses a federal auxiliary ONP log-odds band −1.20/+1.10 because the post-clipping ONP override supersedes the generic `±0.45` bound. Reapplying `±0.45` shifts **about 2.2 One Nation expected seats to other parties** and **about 3.1 Coalition expected seats upwards**, while materially changing individual seats such as Morwell (86.2%→16.7% ONP winning frequency). This makes geographical ONP heterogeneity a **first-order sensitivity**. It does *not* prove that ±0.45 is better: a genuine locally concentrated ONP vote could justify part of the federal auxiliary.

**Finding 2 — a shared statewide preference matrix dominates chamber uncertainty when made broader.** The engine draws one Dirichlet five-family preference matrix **per simulated election**, then applies that same matrix across **all 88 Assembly districts**. Changing concentration **72→4** does not materially affect ONP's *mean seat count* (15.46→15.49), but expands 80% seat distributions very substantially and reduces hung frequency **79.65%→42.95%**. That means the published probabilities of *government type* and the six apparently near-certain ONP seats depend strongly on this tight prior/whole-state coupling. **The real electorate did not acquire a new 43% hung-parliament probability**; this is a deliberately extreme model stress.

**Finding 3 — the two assumptions interact but do not resolve independent candidates.** Both changes still use the **five-party family count**, aggregating separate minor-party and independent candidates as if `OTH_IND` were one actual contestant. Hence neither controls known artificial final-pair elimination and personal-vote risks; the historical candidate-resolved challenger has not cleared its stronger winner-Brier gate.

**Disconfirming evidence / boundaries:** The old concentration-4 preference uncertainty was selected in a *different* candidate-resolved architecture and **failed production winner-Brier** against the reference. There is no evidence it optimises the present five-family model. Nor does this sensitivity identify the causal influence of November polls, which are held. Same seed does not guarantee *strict paired common random numbers* for different Dirichlet shapes. Two-thousand draws make small shifts, near-tied modal changes and lower-tail mass less stable than a full precision study. The 80% ranges are under separate **different assumed models**, not a credible interval spanning model uncertainty, and must not be averaged.

## Stopping judgement and next decision

**Do not promote G, P or GP.** The narrow geographical-parameter question has delivered a meaningful finding, so further unsupervised grid extension or rerouting is not justified. The immediate improvements warranted are:

1. Display **model-robustness warnings** alongside extreme seat and hung-parliament results. These can reference this reproducible audit, without swapping the actual released forecast probabilities or claiming that four runs bracket reality.
2. Independently validate whether the AEC 2022 geographic ONP propensity predicts *actual* local candidate outcomes in past elections with complete candidate availability, **without training against 2026 results**. If historical information is insufficient, explicitly record the irreducible uncertainty.
3. Prioritise verified **individual independent/minor-party candidate resolution** and actual 2026 preference/HTV evidence (recognising how-to-vote recommendations are not observed voter transfers). A successor model needs a separate preregistered historical winner/final-pair calibration gate.
4. Recover first-party wave-level methodology for November DemosAU and Resolve, then submit a *separate* governed polling admission proposal. Do not use these unadmitted waves to retrofit today's sensitivity.

Production-readiness remains **6/9**; no prospective registration, historical replay, model engine, official candidate directory, accepted poll or canonical forecast changed. This research creates inspectable evidence, **not a certificate of forecast accuracy**.
