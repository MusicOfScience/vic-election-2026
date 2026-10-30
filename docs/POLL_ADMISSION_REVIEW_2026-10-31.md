# Poll admission review — 31 October 2026

## Proposal history, subsequently approved

**Owner decision recorded:** the owner approved the exact two-wave bundle and experimental refresh. See [implemented refresh](FORECAST_REFRESH_2026-10-31.md) and `metadata/poll-admission-approval-2026-10-31.json`. The original unapproved proposal manifest remains unchanged as the reviewed object.

Original recommendation: accept the evidence and admit exactly **DemosAU September** and **Morgan 26–29 October** as current experimental Assembly polling inputs, with the limitations below. Retain the RedBridge October independence hold and Resolve/Newspoll methodology holds. No model parameter, preference prior, production gate, prospective seal or outcome score changes are proposed.

The review packet is `metadata/poll-admission-review-2026-10-31.json`. Exact proposed event and estimate rows are in `metadata/poll-admission-proposal-2026-10-31/`; `manifest.json` binds their hashes and records `approved:false`. Model-eligible flags in these proposed CSVs express the requested state, not a present authorisation. Canonical files remain unchanged.

## Source findings

| Wave | New finding | Recommendation |
|---|---|---|
| DemosAU 10–20 September | Primary report gives full N=1,020, **effective N=572**, internet-panel mode, rim-weighting variables, explicit named-party question and leaner, exclusion of remaining undecideds. Cross-wave respondent reuse is undisclosed. | Accept source facts; owner may admit this disjoint comparable wave acknowledging reuse uncertainty, with weight based on 572. This explicitly supersedes that September hold only. |
| Morgan 26–29 October | Preserved first-party PDF and release verify complete primary composition, SMS, full N=3,610. Effective N, exact questionnaire and undecided handling remain undisclosed. | Accept source facts; owner may admit as comparable normalised multi-party SMS observation, acknowledging those limitations and retaining the sample cap. Unknown prompt flag stays blank. Invalid 74–29 comparison stays excluded. |
| Newspoll 15–22 October | Primary publisher report found through indexed retrieval; headline primaries, full N=1,017 and online mode reconciled. Primary reporting available 25 October; earlier packet used secondary date 26 October. No October wave-specific method statement found. | Retain hold. Indexed primary evidence narrows the gap but does not disclose October weighting, effective N or undecideds. July 2025 method is a different wave and cannot supply these fields. An optional explicit reviewed exception is quantified separately. |
| RedBridge/Accent 2–8 October | Primary methodology reconfirms N=1,008, effective N=775 and excluded undecideds 7%; it does not establish respondent independence from earlier related material. | Retain existing owner independence requirement. Disjoint dates alone do not satisfy it. |
| Resolve 6–10 October | Located the primary publisher URL via Poll Bludger, but primary content/methodology could not be captured. | Retain primary-source reconciliation hold. A located URL is not a verified report. |

Sources:

- [DemosAU full methodology/report](https://demosau.com/wp-content/uploads/2026/10/DemosAU-Report-Victoria-Poll-September-2026.pdf), pages 1–3 and 11; [publisher release](https://demosau.com/news/coalition-lead-narrows-as-labor-rises-in-latest-victorian-poll/).
- [Morgan finding 10373](https://www.roymorgan.com/findings/10373-victorian-state-voting-intention-october-2026); preserved PDF in `metadata/current-evidence/2026-10-31/roy-morgan-10373.pdf`.
- [Newspoll primary publisher](https://www.theaustralian.com.au/nation/politics/newspoll-coalition-on-track-to-end-12-years-of-labor-rule-in-victoria/news-story/de80200643073b5304702a952a05b3ec); [publisher companion report](https://www.theaustralian.com.au/nation/daniel-andrews-won-three-elections-now-voters-have-turned-on-him/news-story/555b9e6dd559260625b4491c41eb604a); [official methodology index](https://www.pyxispolling.com/apc/).
- [RedBridge/Accent October methodology](https://www.accent-research.com/projects/afr-redbridge-group-and-accent-research-october-2026-victorian-state-poll).
- [Resolve publisher URL located](https://www.theage.com.au/politics/victoria/wilson-is-gaining-economic-traction-as-carroll-s-popularity-takes-a-further-dive-20261012-p614pi.html).

Retrieval boundaries: DemosAU PDF text was read through the search service. Direct file download returned HTML, so there is no invented PDF hash or claimed binary archive. Newspoll publisher facts came from indexed primary reporting; direct article retrieval failed. Resolve content was not verified. Undisclosed fields remain undisclosed.

## Conditional impact of the exact proposal

Assessment 31 October, 5,000 whole-election simulations, seed 20260826, unchanged model and existing canonical poll registry. DemosAU's disclosed effective N=572 is used. The new result is separately frozen; #144's output bytes/hashes remain intact.

| Inputs | Labor mean seats | Coalition mean seats | ONP mean seats | Hung | Coalition majority |
|---|---:|---:|---:|---:|---:|
| Existing registry re-aged | 38.23 | 30.99 | 16.37 | 77.42% | 3.00% |
| Proposed DemosAU + Morgan admission | 34.41 | 35.78 | 15.36 | 79.80% | 11.46% |
| Same + hypothetical Newspoll exception | 33.71 | 37.58 | 14.19 | 76.26% | 16.90% |

These are counterfactual input sensitivities, not approved canonical predictions or probabilities of forming government. The preference-model discrepancies identified in #144 remain unresolved. DemosAU’s published preference-flow assumptions are retained as reference evidence and are not fitted into the prior.

Full outputs: `metadata/poll-admission-sensitivity-2026-10-31.json`; run hashes: `metadata/poll-admission-run-record-2026-10-31.json`.

## Operational repair

The promotion-audit CLI still read only the older manual/primary/research registries after #144. It therefore omitted the five new campaign records despite those records appearing in the freshness monitor and public app.

The CLI now includes the same campaign waves, with later source reconciliation loaded separately from the immutable sensitivity packet. The audit reports 16 staged observations, zero authorised for promotion. The shared loader rejects unrecognised wave IDs, silently changed primaries or eligibility changes. Source reconciliation is not admission.

The public campaign cards now show disclosed effective sample sizes and the DemosAU methodology update. The original expanded sensitivity is explicitly labelled as preceding the effective-N capture; the new admission-review scenario is distinct.

## Owner approval required before canonical mutation

[Operations contract](AUTOMATION_SPEC.md), “Routine governed sequence between milestones”, step 4:

> Resolve eligibility through the existing owner/poll-review contracts, then update canonical inputs only for explicitly authorised observations.

The concrete requested bundle is:

1. Accept and admit DemosAU September with N=1,020/effective N=572; acknowledge undisclosed cross-wave reuse and supersede that wave's prior hold.
2. Accept and admit Morgan 26–29 October with N=3,610, existing sample cap, reported separate Independent/Other categories, and explicit missing-method caveats; exclude 74–29.
3. Retain RedBridge, Resolve and Newspoll holds; do not admit the early-October Morgan wave with unknown N.
4. After recording those decisions, perform the deterministic **experimental** forecast refresh and delta review. This does not open production authorisation or approve a preference-model challenger.

Before a subsequent canonical refresh, archive/re-anchor the historical staged-shadow and campaign-input integrity checks to their frozen source commits. Their hashes must not be rewritten to the new inputs; otherwise an authorised refresh would incorrectly be classified as corruption of the earlier run.
