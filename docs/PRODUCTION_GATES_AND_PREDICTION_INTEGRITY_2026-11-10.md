# 10 November 2026 — production gates and prediction-instrument decision

**Scope:** methodological and operational decision following merged PR #153, before early voting. **Decision status:** audit / execution plan, not release authorisation, protocol amendment, or model promotion.

## Finding

**The current PROD 1.0 model cannot earn 9/9 under its registered four-cycle acceptance protocol.** As at the 31 October assessed release, **6/9** gates pass; the three blocked gates are complete historical backtest, probability calibration and their downstream production authorisation.

The distinction matters: the experimental forecast can be made materially better as an information product **without** claiming it has achieved statistical certification. Do not relabel an operational checklist as a substitute for the preregistered 9/9 criteria.

## Evidence and disconfirmation

1. `metadata/historical-validation-acceptance-criteria.json` explicitly demands **four** cycle-level leakage-safe replications: 2010, 2014, 2018 and 2022. It prohibits opening the complete backtest with a missing cycle, changing thresholds after seeing scores, or treating within-cycle districts as independent elections.
2. `model/data/validation/historical-replays/historical-four-cycle-validation-status.json` records **three** certifying cycles: 2010, 2014, 2022. **2018 v1** scored with an implementation defect. Its corrected v2 output is diagnostic **after target exposure** and permanently non-certifying. Re-running or renaming cannot reverse that exposure.
3. `docs/PROD_1_0_VALIDATION_CONCLUSION.md` records unweighted three-cycle descriptive means: district winner accuracy **0.8404301637**, multiclass Brier **0.2193372181**, multiclass log loss **1.0486418097**, district primary MAE **4.7557257435 percentage points**. Failures include seat-count and 80% interval coverage thresholds (2010/2014), 2014 Brier, and 2022 log loss. Final-pair calibration, regional probabilities and contest-type criteria are incomplete. The aggregate is not a certifying result.
4. `metadata/model-vnext-validation-protocol.json` registers the existing exact model prospectively for **one 2026 general election**. It explicitly says one election cannot replace a missing historical four-cycle replication or establish multi-election calibration. The sealed 8 October package must be preserved. All future evaluation uses the predeclared primary pre-election snapshot and outcome embargo.
5. `docs/CANDIDATE_RESOLUTION_PREFERENCE_UNCERTAINTY_RESULTS_2026-10-29.md` provides unusually useful research **and negative evidence**. The U1 challenger improved pooled 2018/2022 final-pair accuracy from **88.80% to 95.20%**, reduced final-pair Brier from **0.20768 to 0.06629** and winner log loss from **0.34009 to 0.24776**, but worsened winner Brier **0.13096 to 0.14747** and winner modal accuracy **92.57% to 87.43%**. Its concentration parameter was selected at the tested **lower boundary of four**. The strong production-candidate gate failed. These historical comparisons are *component/architecture research*, **not** new unexposed election-cycle replications or authority to overwrite the live model.
6. Official VEC, **10 November**: **1,037 candidates** — **734 Assembly**, **303 Council**, across **88 districts and eight regions**. Source: <https://vec.vic.gov.au/about-us/media/media-releases/1037-candidates-will-contest-the-2026-state-election>. The VEC's ballot roster is authoritative, but the existing 2026 engine does **not** consume a candidate-level ballot mask. Factually complete candidate displays cannot by themselves improve or certify forecast accuracy.

### Feasibility of other historical holdouts

`docs/NEXT_VALIDATION_PATH.md` / `metadata/validation-evidence-contamination-audit.json` already examined the obvious alternatives: 2006 is a model prior, 2002 has outcome exposure and missing pre-target evidence, 1999 freshness is unproved and required cutoff-safe priors/poll/ballot/Council comparability are unavailable. Cross-jurisdiction cases pose structural transfer problems. Searches for another cycle are not justified merely to fill a quota. Reopen this only on **new, externally independently verified**, provenance-preserved pre-target forecasts and complete inputs, not an unspecified hope of discovery.

## Decision: two separate release tracks

### Track A — election-ready experimental instrument (work now)

The following is a **nine-item operational acceptance checklist**, not the original 9/9 production certificate. Each item must have inspectable evidence and a reported state; a date or software build is not sufficient evidence.

| Priority | Deliverable | Evidence-based acceptance test |
| --- | --- | --- |
| 1 | Verified official ballot | Capture actual VEC raw workbook and SHA256; independently reconcile **734 Assembly + 303 Council** candidates, 88 + 8 contests, candidate names, party/independent designation and ballot/group order. Resolve aliases and changes against the 305-entry provisional registry. |
| 2 | Governed November polling | Obtain first-party polling tables, exact dates, base/effective N, sponsor/mode, source-family independence; retain holds/rejections. Explicit owner approval for each model-eligible wave. Track #154. |
| 3 | Reproducible updated reference forecast | If model-eligible evidence is admitted, rerun deterministic **existing** model and reconcile outputs, seed, model/config hashes, chamber and 88-seat probabilities; publish a new dated experimental snapshot and material-change ledger. |
| 4 | Scenario sensitivity *without misrepresentation* | Show how specified independent input assumptions change indicative outputs in a **separate, clearly hypothetical** scenario product; do not present synthetic probabilities as validated forecasts or alter the registered reference engine. Prefer predeclared stress bounds over chosen headlines. |
| 5 | Candidate and preference fidelity | Identify precisely which seats have implausible five-family collapsed-ballot assumptions; present observed final ballot beside model assumptions. New candidate-resolved challenger requires separate model identity, preregistration and a decision rule that includes **both winner and final-pair scores**. |
| 6 | Council realism | Integrate verified regional evidence where available and identify structural uncertainty under 2026 abolition of group voting tickets. Do not infer new transfer distributions from old party tickets or stale August regional polls. |
| 7 | Interpretability and internal consistency | Provide seat-level attribution, poll versions and source lineage, party-family win probabilities, final-pair instability, modelled seat contribution vs chamber mean, missingness, and clear explanation of correlated seat outcomes. An arithmetic check is not calibration. |
| 8 | Usability / source QA | Actual mobile-device review of search, profile, tables, dark/print output, accessibility, download, source links and refresh notices; verify the deployed artifact matches merged `main`. |
| 9 | Prospective snapshot and election-night discipline | Prepare frozen pre-early-voting **17 Nov 23:59:59 AEDT** and primary final pre-election **27 Nov 23:59:59 AEDT** in their original witnessed windows. Missing windows remain missed. Do not ingest actual outcomes into the forecast before the approved freeze. Treat VEC results-feed test data as simulation, never observed votes. |

The one new app surface created in this batch is the **Prediction audit**, which computes expected party seats as the sum of district win probabilities and compares these with already simulated chamber means, allows filtering across the eight Council geographies for Assembly seats, lists the least-settled seats, and distinguishes this numerical audit from empirical calibration. It does not mutate the canonical forecast.

### Track B — eventual validated production model (gate-locked)

1. **No post-hoc PROD 1.0 resurrection.** Keep its current gates 6/9 and close that validation programme honestly.
2. **Version a successor**, if evidence justifies it, with explicit engine identity, prior-only inputs, all outcome-exposure dependencies, candidate-level rules, uncertainty components, baselines, score units and stopping rules.
3. **Pre-register the successor before any unconsumed targets are observed**, including real data provenance, calibration metrics, election-cycle clustering and missingness handling. An existing historical outcome used in model/feature selection remains consumed for final confirmation; historical tests of a successor can establish plausibility but not be called fresh.
4. Preserve the **2026 prospective** election as an independent evaluation of the registered model; it supplies one new whole-election test, not a multi-election calibration distribution. Distinguish any election-cycle descriptive scores from individual seat-level diagnostics.
5. Require enough genuinely independent future target elections, or externally verified unaffected prediction archives and comparable electoral rules, to satisfy the new protocol's prespecified validation criteria. **No evidence-backed near-term date for 9/9 is established.** Production authorisation requires a documented evaluation of both passing gates and unresolved tail risks.

## Risk ranking for forecasts presented before 28 November

1. **Highest immediate avoidable risk: stale or absent accepted evidence.** Reference model still as-of **31 October**, official ballot not in its engine, candidate roster partial. Fix provenance and governance before changing numbers.
2. **Highest demonstrated structural risk: OTH/independent aggregation and preference-count uncertainty.** Candidate-level architecture research is promising on final pair but loses winner Brier. Neither side of that trade-off may be concealed.
3. **Council risk: regional polling vintage and 2026 GVT abolition.** Any overly precise regional probabilities require particularly conspicuous uncertainty labels.
4. **Institutional reliability risk: apparent precision from 5,000 simulations.** Monte Carlo draws quantify the *specified* model only; they do not multiply empirical validation units. Avoid saying a 60% forecast has a measured 60% real-world frequency.
5. **Political interpretation risk: majority and final-pair tails.** Marginal district probabilities cannot be multiplied as if independent to infer parliament outcomes. Publish the actual joint seat-draw result where exported; label unsupported joint/conditional quantities unavailable.

## Stop rules

- If official VEC source capture is not reproducible or 734/303 rows do not reconcile, do **not** accept a complete ballot. Record the discrepancy and retain the previous reference.
- If poll-source independence, denominators or original publication cannot be verified, **hold** the wave; do not choose between competing secondary summaries ad hoc.
- If a challenger improves one metric but breaches a prespecified primary guardrail, **do not promote**, regardless of attractiveness of its Assembly seat story.
- If a prospective cutoff is missed, record it as unavailable; never reconstruct a pre-election seal from later data.
- If no genuinely new independent validation unit is available, **stop claiming progress towards PROD 9/9 from additional tests of consumed outcomes**. Move effort to truthful app usability, data freshness and the registered prospective election.

**Decision:** Do not change production authorisation or forecast inputs in this PR. Deliver verifiable, public-facing depth without pretending the historic validation problem has disappeared.
