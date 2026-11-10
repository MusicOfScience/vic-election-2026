# 11 November 2026 — November polling and seat-level model mechanics

**Outcome:** completed review of all newly accessible published poll evidence, documented exact poll-status barriers, and produced a reproducible **88-seat model-mechanics audit** against the verified 1,037-candidate VEC ballot. No canonical forecasting input, model coefficient, simulation output, election-score file or prospective record was changed.

## Question and decision

Can the existing 31 October experimental forecast be responsibly refreshed with the newest November polling, and can its extreme One Nation and independent-seat predictions be defended before the 28 November election?

**Poll decision:** no November wave presently reaches the existing first-party methodology and owner-admission gate. Source records are **staged for review**, not rejected as invalid measurements. Not admitting them yet means the reference forecast remains stale. A refresh cannot be made by merely repeating its own deterministic outputs; it needs approved new inputs.

**Mechanism decision:** all 88 Assembly districts contain official candidates from all five forecast party families. Therefore **absence of a One Nation candidate is falsified as an explanation** for extreme One Nation win frequencies. The model nevertheless treats the modelled residual **OTH_IND as one candidate**, despite multiple separate candidates, and treats any Liberal–National coalition candidates as a single family. This is a **demonstrated representation limitation**, not evidence that any particular named candidate should receive a specified probability.

## Poll evidence examined

The machine-readable review is `metadata/november-poll-evidence-review-2026-11-11.json`. Its figures are source observations, not canonical input rows. Four distinct waves need **three different treatments**.

| Wave | What can be established | What cannot be established | Admission |
| --- | --- | --- | --- |
| DemosAU / PremierNational, 30 Oct–5 Nov, **N=1,562** | Contemporary independent reporting gives Labor **18**, Coalition **33**, ONP **21**, Greens **17**, Coalition TPP **56–44** | Original wave-specific published methodology, effective N, weighting, undecided treatment, overlapping panel respondents. The **11% Others is a mathematical residual** from four quoted categories, not a separately inspected reported category | **Hold** |
| Resolve / The Age, early Nov, **Victorian N≈1,000** | Primary publisher/media reporting corroborates Labor **22**, Coalition **30**, ONP **23**, Greens **13** | Fieldwork end date conflicting across sources (**5 vs 7 Nov**), full Victorian table, effective N and undecided treatment. State subset is part of concurrent federal survey, not a second independent national observation. **12% Others is derived residual**, not primary-verified | **Hold** |
| Lighthouse / Growth Intelligence Centre, 19 Oct–1 Nov, **N=1,289** | Publisher-linked contemporary News Corp reporting quotes Labor **22**, Coalition **31**, ONP **23**, Greens **14**; an initial Poll Bludger report transposed Labor/ONP as 23/22, explicitly challenged in its contemporaneous comments | Company/sponsor method and effective base; rolling two-week tracker prevents assuming future waves independent. Some third-party ledgers invert the 23/22 minor-party columns | **Hold** |
| TKW Research / DemosAU, **Pakenham 4–8 Nov**, N=484, **effective N=289** | **First-party interactive report** gives Pickering (ONP) **40%**, Dyson (Liberal) **24%**, Soliven (Labor) **14%**, Yawari (Greens) **13%**. Rim weighting and undecided treatment described; effective margin of error ±5.8% | Independent respondent overlap with statewide DemosAU; two-candidate preferred **50–50 is explicitly modelled using assumed preferences**, not a directly polled 2CP. One electorate cannot be admitted as statewide voting-intention observation | **Hold as model input; useful external local diagnostic** |

Source hierarchy:
- Primary DemosAU **Pakenham local evidence**: <https://demosau.com/wp-content/uploads/DemosAU/pakenham-electorate-poll.html>.
- Resolve publisher/media article (indexed): <https://www.brisbanetimes.com.au/politics/victoria/half-of-victorians-open-to-a-one-nation-coalition-as-carroll-faces-labor-wipeout-20261109-p61cjv.html>.
- DemosAU latest state reported by the independent Poll Bludger: <https://www.pollbludger.net/2026/11/09/demosau-labor-18-coalition-33-one-nation-21-in-victoria/>.
- Resolve state reported by Poll Bludger: <https://www.pollbludger.net/2026/11/10/victorian-election-resolve-strategic-and-pakenham-seat-poll/>.
- Lighthouse rolling-wave report: <https://www.pollbludger.net/2026/11/06/victorian-election-minus-three-weeks-2/>.
- DemosAU's **published methodology index** <https://demosau.com/methodology-statements/> had not yet listed the November Victorian statewide wave at this review. September methodology is not substituted for November without direct evidence.

No new political figure, pollster statement or third-party polling *average* is used to retune the frozen forecast. The publisher of an article is not always the pollster conducting fieldwork; differentiate those authorities.

## Reproducible model audit

`node scripts/audit-2026-model-mechanics.mjs --output seat-integrity-review.json` runs against the **actual committed model outputs, source code and VEC roster**, checks 88 probability vectors, extracts the five-family Dirichlet preference-mean matrix directly from `model/src/vicforecast/forecast_2026.py`, verifies 88 official candidate slates and returns all 88 seat records and flagged examples. It writes **only** the nominated output file and never mutates canonical inputs.

| Diagnostic | Observed from 31 October reference |
| --- | --- |
| Distinct official nominee availability by five broad families | **All five families represented in all 88 districts** |
| ONP-winning frequency ≥80% | **6 districts**: Greenvale 96.30%, Kororoit 95.94%, Sydenham 92.36%, Morwell 85.40%, Kalkallo 84.88%, Mill Park 84.28% |
| OTH family modelled primary ≥20% but winning frequency below 1% | **3**: Hawthorn 27.13% / 0.92%; Kew 26.43% / 0.06%; Benambra 23.24% / 0.02% |
| Separate Liberal and National nominees but a single model family | **Ripon** (two coalition-family nominees) |
| One Nation Pakenham first preferences: local poll vs model primary | **40.0% vs 27.588%**, difference **12.41 percentage points** (different dates/methodologies, not a direct sampling residual) |
| Pakenham model frequencies | Coalition winner **82.92%**, ONP **14.94%**; model modal pair Coalition–Labor **51.9%** |
| Conditional transfer mean when only ONP and Labor survive and Coalition is eliminated | **0.51/(0.51+0.26) = 66.23% ONP** |
| Conditional transfer mean when only Coalition and OTH survive and Labor is eliminated | **0.39/(0.39+0.13) = 75.0% Coalition** |
| Preference prior concentration | **72**; only random fluctuations *within this assumed prior* are represented in simulations |
| Effective ONP locality limit | Configured generic bound **±0.45**, but the code overrides the clipped ONP value with AEC federal auxiliary signal separately capped **−1.20 to +1.10**. Thus the **effective** positive relative-odds multiplier can reach **exp(1.10)=3.004** rather than **exp(0.45)=1.568**. Could be intentional but must be documented and tested as a distinct source-level structural assumption. |

The 2022 One Nation **model baseline** in Greenvale, Kororoit, Sydenham and Kalkallo is ~0.15%, but the registered 2022 state election ONP ballot was very sparse. Subtracting that from 2026 modelled primary and labelling the difference a measured *candidate swing* would be invalid. The geographic ONP pattern uses the **2022 federal AEC ecological allocation**, moderated by fixed limits and local shocks; it is not observed local 2026 polling.

The model's current preference priors redistribute a five-family *aggregate* through `_count_irv`. The hypothetical conditional ratios above do **not** establish actual 2026 second preferences, actual two-candidate outcomes or causation of all six extreme frequencies. Full joint simulation includes uncertain statewide polls, regional and district shocks and stochastic preference rows.

### Falsification and limitations

- **Rejected candidate-absence hypothesis:** One Nation does have a verified Assembly nominee in every district, including the six near-certain model ONP seats. No missing-nominee mask explains their predictions.
- **Confirmed representation problem:** some electorates have several different minor/independent candidates, but model `OTH_IND` is a single simulated candidate. The model can therefore produce artificial elimination paths and final pairs. This aligns with the candidate-resolved historical research, which improved final-pair accuracy but failed the stronger winner-Brier production gate.
- **Preference concentration concern supported, not resolved:** Historical walk-forward challenger selected a much wider prior (concentration **4**, boundary of the prespecified grid); it greatly improved some final-pair scores but worsened winner Brier from 0.13096 to 0.14747. A single favourable metric is insufficient for promotion.
- **Pakenham potential miss:** later local data report a substantially higher ONP primary, but effective N is only 289, poll mode and geography differ from the statewide reference, and the local 2CP is modelled from assumptions. It is *not* proof that the exact 31 Oct win frequency is wrong or that the 2026 election outcome is known.
- **Source-level bound mismatch established:** `assembly.local_logit_limits.ONP: 0.45` is used in the generic `np.clip`, but the subsequent `local_pattern[:, 2] = districts.onp_local_log` replaces the clipped column. The auxiliary is capped separately at −1.20/+1.10 in `build_assembly_seed`. This is a *confirmed implementation precedence*, not a confirmed unintended bug. Any attempt to make ±0.45 operative would create a **new model identity and new probability distribution**, so it cannot be silently patched into a prospective forecast.
- **Alternative explanations:** real local opinion differences, sponsor/mode effects, time variation, denominator definitions, geography mismatch, candidate effects and model priors. These must be distinguished rather than choosing whichever explanation fits a political narrative.

## What the app gains

- A **November evidence review** in the Polls tab, with exact fieldwork/sample caveats and links.
- A **Seat model integrity** view in the Forecast tab, filtering high ONP, collapsed Others and Pakenham. Each row shows modelled primary, simulation win frequency and actual count of nominated party-family candidates.
- Explanatory preference arithmetic and explicit 2026-vs-2022 baseline warning.
- No new calibration or live reference probabilities are implied. The existing experimental model date is shown beside the new evidence date.

## Decisions that remain owner-governed

1. Obtain and independently fingerprint the **DemosAU November primary report**, with methodology and effective N. If unavailable, create an explicit secondary-source exception packet and quantify its weight sensitivity before requesting approval; do **not** assume N=1,562 is effective N.
2. Reconcile Resolve's fieldwork period and how its Victorian subsample was drawn; seek the complete publisher/pollster tables. Avoid accidental double counting with federal data or overlapping survey waves.
3. Require sample independence and rolling-wave de-duplication evidence before considering any Lighthouse inclusion.
4. Keep Pakenham as **non-canonical local validation signal** unless a separately preregistered local evidence model handles it. The current model has no per-district poll-admission contract.
5. Once exact inputs are genuinely eligible and the owner explicitly approves them, **only then** rerun the deterministic registered model, verify changed model outputs and 88-seat/8-region deltas, and preserve any prospective freeze windows. No simultaneous preference-prior refit.
6. There is **no path to immediate statistical 9/9** through this work; the historical 2018 and probability-calibration gates remain closed.

**Stopping rule:** if primary wave methodology cannot be obtained before the 17 November pre-early-voting cutoff, report the still-held waves as an evidence limitation and preserve the existing model. Do not silently treat media summaries as first-party source proof or backdate a forecast.
