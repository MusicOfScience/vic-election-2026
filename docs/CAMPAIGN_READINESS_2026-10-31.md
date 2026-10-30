# Campaign readiness — 31 October 2026

## Decision and scope

The owner authorised implementation of the campaign-readiness review. This batch makes the public app explicit about stale predictions, reviews current source facts, runs updated sensitivities with the unchanged canonical engine, and prepares official-nomination reconciliation. It does not reinterpret that instruction as an explicit admission of waves already subject to owner holds, authorise a failed research challenger, seal a prospective milestone or score 2026 outcomes.

## Public behaviour

- A forecast-currency notice precedes every tab. Included fieldwork (28 September), latest campaign publication reviewed (30 October), five campaign waves awaiting admission and current assessed readiness are separate.
- The retained 8 October prediction is labelled as a retained snapshot. “Where support sits now” becomes “Support in the retained snapshot”.
- The Campaign update tab shows source links, admission caveats, the new sensitivities, Council limitations and verified Melbourne election dates.
- The Data & sources readiness ledger uses a separately generated current assessment (4/9 on 31 October, including the newly registered unresolved campaign evidence), while the immutable historical 8 October assessment remains unchanged.
- Pages recalculates campaign currency using the Melbourne build date after deterministic checks. A successful daily rebuild does not update the forecast or imply fresh polling. The core readiness and evidence-freshness monitors also include the new campaign ledger, using publication cutoffs so historical assessments remain unchanged. The earlier monitor reported 5/9 before this evidence was registered; the pending admission gate now reduces it to 4/9.
- Council control percentages are described as simulation frequencies under retained assumptions. The August regional input and non-injection of newer regional evidence are explicit.

## Evidence adjudication

`metadata/current-evidence-shadow-2026-10-31.json` preserves the earlier DemosAU/RedBridge/Resolve holds and adds:

1. **Morgan, 26–29 October, n=3,610:** direct HTML and linked PDF captured and cross-checked. Six reported primary categories sum to 100; Independent 7.5 and Other 6 remain distinct in the evidence. The unchanged model maps both into its existing OTH_IND family. Effective N, weighting detail, undecided treatment and respondent overlap are not disclosed in the captured release. Pending explicit canonical admission.
2. **Newspoll, 15–22 October, n=1,017:** reported primaries and 55–45 corroborated; full primary wave capture is unresolved. Secondary-captured sensitivity use only.
3. **Morgan, 8–9 October:** latest PDF reproduces its primaries but supplies no wave sample size. Reference-only; not injected.
4. **Morgan alternative pair:** both HTML and PDF prose report Coalition–ONP 74–29. Excluded from numerical comparison; no 74–26 correction inferred. Three-party and pairwise results are dependent outputs of one survey, not independent observations or an identified transfer matrix.
5. **Council:** 20 October minimum seat allocation remains reference-only. No missing regional primary cells are filled and no new regional Council input is manufactured.

HTML/PDF source hashes, PDF link and checked pages are recorded in the evidence ledger. The captured [Morgan press release PDF](../metadata/current-evidence/2026-10-31/roy-morgan-10373.pdf) is preserved with its matching hash. Source facts are reviewed for this sensitivity packet; that is separate from canonical evidence acceptance and model eligibility.

## Updated unchanged-engine sensitivities

Assessment 31 October; 5,000 simulations per scenario; seed 20260826; shared random-number construction; all model coefficients and canonical files unchanged. Effective sample N=775 is honoured for the RedBridge observation in the expanded scenario; the runner previously discarded disclosed effective N during temporary registry construction. This is a shadow-input handling correction, not a new model parameter. The October 25 report remains historical; rerunning its script now honours disclosed effective N.

| Inputs | Labor mean | Coalition mean | ONP mean | Hung | Coalition majority |
|---|---:|---:|---:|---:|---:|
| Existing registry re-aged | 38.23 | 30.99 | 16.37 | 77.42% | 3.00% |
| Add latest Morgan | 33.99 | 35.62 | 15.94 | 81.10% | 10.98% |
| Add Newspoll + Morgan | 33.34 | 37.58 | 14.57 | 76.58% | 17.22% |
| Expanded current evidence | 34.43 | 36.78 | 14.12 | 78.52% | 13.44% |

Expanded adds DemosAU September, RedBridge October, Resolve October, Newspoll October and Morgan October. The latter two secondary captures remain labelled. The latest primary and secondary waves are not falsely combined into a primary-only scenario.

The Coalition strengthens materially within the model. Hung parliament remains dominant. These outputs do not support replacing the headline with a calibrated Coalition-government probability: the engine does not model minority-government negotiations, and its preference architecture has unresolved defects. No uniform swing conversion is used.

Full district/chamber results: `metadata/current-evidence-results-2026-10-31.json`. Public compact summary is generated from that file. `metadata/campaign-run-record-2026-10-31.json` records inputs, result hashes and dependency versions; the canonical diff is empty.

## Preference diagnostic, not a fitted challenger

At Morgan's fixed published primaries, force each published hypothetical final set and apply the existing preference-prior draws. This tests aggregate compatibility without estimating district survival order.

| Comparison | Morgan | Model mean |
|---|---:|---:|
| Labor share vs Coalition | 44.0% | 45.59% |
| Labor share vs ONP | 54.5% | 48.69% |
| Labor three-party share | 43.0% | 36.82% |
| Coalition three-party share | 33.0% | 35.20% |
| ONP three-party share | 24.0% | 27.98% |

The model's near-match on conventional Labor–Coalition preference is insufficient validation. It differs substantially on Labor–ONP and three-party totals, precisely where candidate survival matters. These are not significance tests: survey covariance is unavailable, primaries are fixed, and diagnostic intervals contain preference-prior dispersion only. No mean or concentration was fitted to Morgan. The existing collapsed OTH family remains an explicit limitation.

## Nomination preparation

VEC verified 31 October: roll closes 8pm 3 November; nominations 4–9 November, closing noon; early voting 18–27 November; election 28 November. Dates are Melbourne time.

After the VEC publishes candidates and ballot order, capture a review packet:

```json
{
  "sourceUrl": "https://www.vec.vic.gov.au/ACTUAL-PUBLISHED-PAGE",
  "capturedAt": "ACTUAL-ISO-TIMESTAMP",
  "complete": false,
  "candidates": [
    {"name": "AS-PUBLISHED", "contest": "Melbourne", "party": "AS-PUBLISHED", "ballotOrder": "AS-PUBLISHED"}
  ]
}
```

`node scripts/reconcile-official-nominations.mjs --official captured-vec.json --output reconciliation.json`

This validates VEC HTTPS authority, nomination-opening time, known contests, identity duplicates and ballot-position collisions. It reports names/party labels requiring review, accepted names absent from the supplied list and missing contests. It never silently treats missing names as withdrawals, claims a partial packet is complete, mutates the registry or promotes candidate research. For Council ballot positions, preserve an unambiguous group+within-group position from the official list.

A capture adapter must follow the actual published VEC format when available; no speculative scraper or future official list is presented as completed. After reconciliation, apply separately governed registry decisions and run validation. The prior discovery queue is not automatically approved by this batch.

## Remaining gates and next actions

1. Obtain explicit wave-specific canonical eligibility decisions for the five campaign records; retain earlier holds unless expressly superseded.
2. Obtain complete newer Council regional source tables, or separately specify and review a partial-evidence model. Do not relabel statewide-sensitive Council runs as a new regional forecast.
3. Reconcile actual nominations after their publication. Announcement coverage is not ballot completeness.
4. Run canonical refresh only after eligible input decisions are recorded. Preserve the first prospective seal; execute future milestone seals only under the registered protocol/window.
5. Research promotion remains blocked under #140/#142. Do not tune until the Coalition wins, lower an observed failed threshold, or reinterpret conditional historical preference tests as complete-model calibration.

## Validation

Validation: 203 JavaScript build/render tests and 91 Python model tests pass; lint and GitHub Pages static export pass. The repository-wide TypeScript check retains Cloudflare runtime declaration errors outside this static app; the two dashboard inference errors encountered during review were repaired. Browser-level verification of this local build is unavailable because the remote browser cannot reach the container's localhost; this is not represented as a completed mobile interaction audit. The current live app was inspected in the preceding review; it is unchanged until merge/deployment.
