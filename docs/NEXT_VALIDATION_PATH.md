# Next validation path: prospective 2026 evidence

Audit date: 8 October 2026. Base: merged PR #124, main commit
`485421f69251809e849436a7e69211a3e42cf93f`.

## Decision proposed for review

Register **the exact current experimental model** under validation protocol
`vic-2026-prospective-observational-v1`. Preserve witnessed, self-contained 2026
forecast freezes. Select only the future Victorian general election as an
empirical unit. No older holdout is selected or scored in this batch. This draft
is not owner approval and does not authorise scoring or model changes.

**No defensible route to complete-model production validation before 28 November
was established by the available evidence.** Keep the forecast experimental
through the election. Component checks can precede election day, but target-outcome
accuracy cannot. One future election still cannot establish multi-election chamber
calibration. No release gate opens from descriptive scores, simulations or protocol
integrity checks. This conclusion concerns audited evidence, not a proof that no
external archive could ever exist.

The [contamination inventory](../metadata/validation-evidence-contamination-audit.json)
records lineage, exposure dimensions and uncertainty. The
[prospective protocol](../metadata/model-vnext-validation-protocol.json) fixes units,
cutoffs, comparators, metrics, missingness, aggregation and stopping rules before
new targets enter the pipeline. `node scripts/validate-next-validation-protocol.mjs`
checks the draft and frozen fingerprints; it is not a release-gate adapter.

## Confirmed state and immutable boundary

PRs #119–#124 close the historical programme, park resilience, resolve current
evidence and admit exactly one owner-approved September Freshwater observation.
PR #124 also repairs shallow-CI access to the exact pre-refresh Git baseline.
Readiness remains **6/9**: complete backtest, probability calibration and production
authorisation remain closed. There are 13 eligible polls; September RedBridge,
DemosAU and Resolve remain held. Seed is 20260826 and simulations are 5,000.
Forecast SHA256 is
`a1b9f98566931293edbcaf7edc320e90778feffff401d8fbc69e3abb2328eff2`.

2010/2014/2022 are consumed certifying v2 evidence. 2018's v1 defect and post-hoc
v2 status are permanent negative/diagnostic evidence. Version renaming cannot make
results unseen. All 20 frozen replay prediction/comparator/score artefacts are
fingerprinted and untouched. No historical replay is tuned/rerun, no old threshold
changes, no current forecast refresh, no resilience build or model-weight change.

## Contamination and historical feasibility

| Evidence | Classification | Finding and legitimate use |
| --- | --- | --- |
| 2010 / 2014 / 2022 | CONSUMED_AS_VALIDATION | Scored and used for governance; successor design/descriptive regression only. |
| 2018 | POST_HOC_DIAGNOSTIC_ONLY | Permanently non-certifying; original defect and exposed diagnostic preserved. |
| 2006 | CONSUMED_AS_MODEL_INPUT | Assembly/Council outcomes supply 2010 priors; not pristine. |
| 2002 | PARTIALLY_CONSUMED | District TPP/swing outcomes in committed historical display; no complete cutoff-safe replay bundle. |
| 1999 | FRESHNESS_UNVERIFIED | Official report exists; freshness and replay feasibility unproved; incidental aggregate search-result exposure recorded. |
| Earlier cycles | NOT_FEASIBLE in this programme | No justified complete-model bundle or additional target acquisition. |
| Five recent by-elections | CONSUMED_AS_MODEL_INPUT | Winner-family boost in current model; full stored results exposed. |
| Narracan supplementary | PARTIALLY_CONSUMED | Outcome extraction captured primaries; November 2022 exclusion does not erase exposure. |
| Other by-elections | FRESHNESS_UNVERIFIED | Contest/report existence, not positive freshness certification; component potential only. |
| Other jurisdictions | EXTERNAL_VALIDITY_ONLY | No fresh target selected; rule/transport/exposure audit required. |
| Victorian 2026 | UNCONSUMED_CANDIDATE | Future target conditional on registration/sealing; one election. |
| Simulation | NON_EMPIRICAL | Controlled numerical evidence, not empirical electoral replication. |

The machine-readable inventory traces priors, baselines, geography, feature design,
party mappings, preferences, uncertainty, architecture, thresholds, model selection,
reconstruction, diagnostics and human exposure. `not-established` means unknown,
not proof of no influence. Searches covered committed documentation, metadata,
configuration, model scripts and generated displays; contributor memory is not
exhaustively certified. Known score misses remain consumed negative evidence.

### 2006 circularity

`vec-2006-assembly-source-manifest.json` and
`build_historical_2010_local_inputs.py` identify official five-family primary
compositions for all 88 same-boundary districts, used in 2010 local priors with its
cutoff-safe baseline. `extract_vec_2006_council_prior.py` aggregates eight official
regional first-preference tables into ALP, LIB_NAT, GRN and OTH_IND: the 32-row 2010
Council prior. The next-cycle selection explicitly relied on these sources.
`targetOutcomeDependency:false` concerns **2010** outcomes, not 2006 freshness.

Using earlier priors in a hypothetical 2006 replay removes direct self-input but
not project outcome exposure or outcome-informed reconstruction choices. Fine
transfer dimensions may remain uninspected, but none is certified fresh here;
these require an independent component exposure audit/protocol. They cannot make
the complete election pristine. From 2006 Council changed from 22 provinces/44
members and staggered contests to eight regions electing five members each.

### 2002 and 1999

The historical display generator consumes 2002 ALP TPP starts and 2002–06 swings;
`app/historical-data.generated.ts` embeds district values. Direct central fitting
on 2002 is not established; project/human outcome exposure is. AEC 2022 ecological
surfaces, prior-election anchors, census surfaces and failed demographic feature
promotion also contribute input/design lineage: zero current weight does not
erase selection/diagnostic exposure. Historical preference logic is separately
walk-forward; the live engine's documented fixed preference matrix does not prove
that all human design choices were blind to older outcomes.

VEC lists 1999/2002/2006 reports. Only source existence was checked: no target report
PDF or detailed old district table was acquired. A feasibility search incidentally
displayed secondary aggregate 1999/2002 results; exposure is recorded. No structured
1999 target input was found, which is insufficient to declare it pristine.

Neither 1999 nor 2002 has an established complete pre-election polling bundle with
sample/mode/categories/undecided metadata, cutoff-safe ballot availability,
prior-only boundary crosswalk or local surface in the present architecture. 2002
requires pre-target redistribution records; 1999 requires earlier baselines and
geography. Historical party-family mappings need a separately versioned rule.
Pre-reform Council geography, staggered terms and election rules cannot be replayed
by the unchanged current joint model. Report existence does not establish adequate
contemporaneous polling. Further target browsing would consume evidence without
first establishing a useful test. These cycles are not selected.

### By-elections and supplementary elections

Warrandyte (26 August 2023), Mulgrave (18 November 2023), Prahran/Werribee
(8 February 2025) and Nepean (2 May 2026) appear in `recent_state_by_elections.json`.
The live engine uses winner family as a local logit boost with 0.030 maximum and
1,100-day decay. Nepean also informs reference-only analyst evidence. All are
consumed, even though only winner identity enters the boost.

Narracan (28 January 2023) primaries were extracted and excluded from the November
2022 score universe. Its known results are not fresh. The inventory separately
lists VEC source existence for Northcote 2017; Polwarth, South-West Coast and
Gippsland South 2015; Lyndhurst 2013; Melbourne/Niddrie 2012; Broadmeadows 2011;
Altona/Benalla 2010; Kororoit 2008; Albert Park/Williamstown 2007; Burwood 1999.
No result links or tables for these older contests were opened in this audit.
No dedicated current signal was found, but unknown design/human exposure remains.

A separately audited future/unconsumed contest could validate local primary
response, candidate/retirement effects, preference mechanics and conditional
uncertainty. Declare non-contestation, turnout and selection bias. Contests on the
same date are correlated; multiple seats are not general-election replications.
Such tests cannot certify statewide aggregation, 88-seat probabilities, hung
parliament or Council.

## Cross-jurisdiction limits

All six candidates have compulsory voting. That does not equalise polling houses,
modes/response, turnout, party systems, candidate information, redistributions,
district geography or ecological features. No cross-state target outcome or replay
was selected/acquired. A component selection first needs an exposure ledger,
contemporary polls/ballots, law-version pinning and prior-only boundary mapping.

| Jurisdiction | Material differences | Legitimate potential scope |
| --- | --- | --- |
| NSW | Optional-preference Assembly, statewide 21-of-42 Council; different exhaustion/minor-party geography. | IRV exhaustion/transfer components, not Victorian 8x5 joint validation. |
| Queensland | Current full-preference 93-seat unicameral Assembly; older optional-preference era, LNP/KAP party system. | Shared lower-house counting/probability components, no Council test. |
| South Australia | 47-seat Assembly, statewide 11-of-22 Council, distinct minor/local parties and Council preferences. | Shared lower-house components/external validity after audit. |
| Western Australia | 59-seat Assembly; from 2025 statewide 37-seat optional-preference Council replaces regions; Nationals geography. | Versioned counting/uncertainty stress tests, not unchanged joint replay. |
| Tasmania | Five seven-member Hare-Clark Assembly districts, partial preferences/Robson rotation; 15 rotating single-member Council seats. | Adapted quota/transfer mechanics, not Victorian IRV Assembly. |
| ACT | Five five-member Hare-Clark districts, Robson rotation, urban geography, unicameral. | Transfer mechanics/external validity, not joint chambers. |

A portable component might eventually have its own certifying cross-state protocol.
That certifies that component under explicit conditions, not the Victorian complete
model. Porting/tuning against a target consumes its outcomes. Primary rule-source
URLs and reviewed findings are recorded per jurisdiction; source retrieval failures
are not filled with invented methodology.

## Exact model under a new validation identity

Choose arrangement A: `vic_2026_experimental_joint_v1`, fingerprinted at PR #124,
under a new validation protocol. A behaviourally identical model clone adds no new
evidence. A structural revision requires new model identity and fresh prospective
registration, and is not needed in this batch.

Register engine/runner/dependency hashes, baseline full configuration and structural
configuration hash. Only `as_of` may change in config. Governed polls and candidate/
ballot facts used by this exact engine are versioned input snapshots; no coefficient,
feature, party-mapping, uncertainty, seed, simulation or counting change is allowed.
Prediction-changing bug fixes require new model/protocol while preserving negative
evidence. Output-neutral documentation/tooling corrections may append audited
amendments. Changed units, metrics, comparators, aggregation, cutoffs or stopping
rules require a prospective version before exposure. Once 2026 results are known,
this target cannot be refreshed for a revision.

## Prospective freezes and prerequisites

VEC primary pages checked 8 October establish writ/roll close 3 November (8pm),
nominations noon 9 November, early voting 18–27 November, election Saturday
28 November (8am–6pm), writ return 19 December. Melbourne times below use UTC+11.
Reverify before sealing; schedule corrections require prospective amendment.

| Snapshot | Exact trigger/cutoff (Melbourne) | Role |
| --- | --- | --- |
| Post-Freshwater | Approved protocol merge and witnessed archival seal of existing 8 October forecast | Secondary; no claim original generation was preregistered |
| Writ / roll close | 3 November, 20:00 | Secondary |
| Nominations | 9 November, 12:00 | Secondary; later official publications enter later freezes |
| Before early voting | 17 November, 23:59:59 | Secondary |
| Final pre-election | 27 November, 23:59:59 | **Primary** |

No snapshot is sealed here. Missing a cutoff means unavailable, not reconstructed.
Evidence must be published, captured and explicitly admitted by cutoff. Earlier
fieldwork cannot excuse late publication/admission. No later data revision, target
result, leak or target-derived crosswalk enters a sealed prediction. Live updates
remain experimental and never overwrite freezes.

Each archive must contain inputs, outputs, code/config/runtime dependencies, source
IDs/receipts/admission states, geographic/ballot mappings, probability vectors,
seat distributions and interval definitions; include SHA256, actual UTC witness
time, cutoff, immutable commit and protocol/model identity. Comparator outputs and
scorer hashes must be sealed before activation. The existing snapshot script indexes
hashes but is not a self-contained archive or cutoff witness. A subsequent bounded
sealing implementation is required after approval; no receipt is invented here.

These are **one dependent election-level unit**, not five independent elections,
not a fourth historical PROD 1.0 replication. Earlier snapshots describe information
accumulation; only the final snapshot is primary. If registration is delayed until
a scheduled cutoff passes, that snapshot remains missing and execution cannot claim
full integrity PASS by backfilling it.

## Fixed scoring and interpretation

Required comparators are prior-result and uniform-swing, using the same cutoff-safe
family/ballot universe and fixed preference-counting prior. JSON fixes definitions;
exact implementations and outputs must be hashed before first evaluation sealing.
No comparator is run here. Metrics: multiclass Brier/log loss, winner accuracy,
district/statewide primary MAE, mean/median family-seat errors, central 80% interval
coverage/widths, Council regional errors and pre-exported hung probabilities.
Log loss uses epsilon `1e-12`, disclosing zero/clipped events. Family order and
interval quantiles are fixed. Missing metrics retain reason/denominator, never zero
imputation or post-target reconstruction. OTH_IND grouping evaluates families,
not individual independent candidates or Council candidate order.

Ten equal-width district-family reliability bins are descriptive within one
correlated election. No district/family bootstrap as independent election-level
calibration, no same-target fitted correction and no full chamber calibration PASS
threshold. A later calibration programme needs independent cycles and its own
training/evaluation separation.

Before election day: conservation/counting invariants, reproducibility, governance
and seal integrity can be checked. After official certified results: votes, winners,
seat errors, hung-event outcome and reliability can be scored. The target universe
is contests held on 28 November; deferred/supplementary contests are separate.
Incomplete results stay unavailable with scoring-only receipt versions; writ return
is a schedule reference, not automatic permission to score missing targets.

Integrity PASS means preregistration/sealing/hashes/universe/missingness and all
negative-result retention were honoured. It is **not performance or production
PASS**. Leakage, backdating, undeclared changes, missing primary/comparator or
discarded negatives mean execution FAIL. Publish all fixed scores/comparator losses
descriptively. Stop affected evaluations on contamination/cutoff/manifest uncertainty;
preserve originals and never swap a losing target. Production cannot open
without separate explicit governance and adequate evidence.

## Simulation and rejected alternatives

Future simulations may test bias, uncertainty propagation, known-DGP coverage
with Monte Carlo error, preference conservation/exhaustion and correlated chamber
aggregation. Preregister DGP assumptions, misspecification stresses, seeds, sample
sizes and numerical rules before execution. If the simulator assumes the model is
true, success is self-consistency, not real electoral calibration. Simulation adds
zero independent elections and cannot repair the empirical historical gate.

Reopening 2018 or declaring 2006 fresh violates lineage. Older report existence
cannot overcome exposure/missing cutoff-safe joint inputs. By-elections test local
components, cross-state adaptation tests transport under different laws, and
simulation tests mechanics; none supplies complete-model pre-election calibration.
Prospective 2026 sealing best preserves current work and protects future learning
against post-hoc tuning without inventing a model variant or weakening production.

## Primary checks and review boundary

- [VEC calendar](https://www.vec.vic.gov.au/voting/types-of-elections/state-elections)
  and [2026 election page](https://www.vec.vic.gov.au/voting/2026-state-election).
- [VEC reports](https://www.vec.vic.gov.au/about-us/publications/state-election-reports-and-plans)
  and [contest timeline](https://www.vec.vic.gov.au/results/state-election-results/state-by-elections-timeline): existence only.
- Jurisdiction rule-source URLs are attached to the inventory entries. No historical
  target dataset was acquired or scored in this run.

Exact next action: owner review and explicit approval or rejection of
`vic-2026-prospective-observational-v1`.
