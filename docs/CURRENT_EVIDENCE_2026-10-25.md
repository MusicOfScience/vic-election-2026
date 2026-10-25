# Current evidence decision packet — 25 October 2026

Assessed against `main` at `b380fbc8a2113e5ce1ff3ea4ac456274f5d142b1`.

## Executive finding

The evidence layer has moved materially since the 8 October refresh, but the central forecast must not silently follow it.

The newest **model-eligible** statewide observation remains Freshwater Strategy fieldwork ending 28 September, published 1 October. At the 25 October assessment date it is 27 days old, beyond the unchanged 21-day critical polling freshness threshold. Newer public evidence is now captured or staged, but none has a new project-owner model-eligibility decision. Release readiness therefore correctly falls to `experimental-blocked`, **4/9 gates passing**: critical-source freshness and model-input freshness are again blocked alongside complete backtesting, calibration and production authorisation.

The canonical 2026 engine was nevertheless rerun deterministically at an assessment date of 25 October with the unchanged 13 admitted polls. This is useful as a staleness/uncertainty diagnostic, not as a claim that the public evidence through 25 October has entered the central forecast.

## Statewide polling discovered or reverified

### DemosAU / PremierNational — September wave

**Evidence recommendation: ACCEPT. Model recommendation: HOLD pending explicit owner re-adjudication.**

DemosAU's first-party release is now available and cures the main factual gaps that caused the 8 October HOLD:

- fieldwork 10–20 September;
- raw `N=1,020`, internet panels;
- Coalition 30%, Labor 25%, One Nation 20%, Greens 14%, Others 11%;
- published Coalition–Labor two-party preferred 52–48;
- remaining undecideds excluded after a leaner question;
- DemosAU lists the September Victorian wave in its methodology statements;
- independent methodological review reports effective `N=572`, rim weighting by age×gender, education, personal income, residential tenure, language, region, 2025 federal vote and left–right self-identification, and documents the preference-flow basis.

Primary release: https://demosau.com/news/coalition-lead-narrows-as-labor-rises-in-latest-victorian-poll/

Methodology index: https://demosau.com/methodology-statements/

The 8 October owner HOLD remains authoritative until explicitly changed. Fieldwork is disjoint from the August DemosAU wave, but cross-wave respondent/panel reuse is not disclosed. Existing project policy does not impose a blanket repeat-respondent exclusion on otherwise comparable disjoint waves; this is therefore an owner dependency/comparability decision rather than an automatic rejection.

### RedBridge / Accent Research — October wave

**Evidence recommendation: ACCEPT. Model recommendation: HOLD.**

First-party Accent evidence verifies fieldwork 2–8 October, raw `N=1,008`, effective `N=775`, online-panel recruitment, quota variables, rim weighting, 77% weighting efficiency and leaner treatment. Published/topline evidence is Labor 24%, Coalition 30%, One Nation 24%, Greens 16%, Others 6%, with respondent-allocated Coalition–Labor 56–44.

Source: https://www.accent-research.com/projects/afr-redbridge-group-and-accent-research-october-2026-victorian-state-poll

The existing RedBridge/Accent sample-family blocker remains unresolved. Separate fieldwork windows and the publisher's description of regular state snapshots support distinct-wave treatment, but they do not establish respondent-level independence or exclude reuse from earlier RedBridge/Accent survey/MRP material. No central observation is added without an explicit eligibility decision.

### Resolve Strategic — October wave

**Evidence recommendation: HOLD. Model recommendation: HOLD.**

Current reputable secondary ledgers agree on fieldwork 6–10 October, `N=1,000`, and primaries Labor 25%, Coalition 28%, One Nation 23%, Greens 15%, Others 9%. No first-party survey carrier/full methodology has been captured in this review. No two-party-preferred result is inferred.

The record remains quarantined rather than borrowing methodology from an older Resolve wave.

## Legislative Council evidence

### Roy Morgan — July to September regional study

**Evidence recommendation: ACCEPT. Model recommendation: HOLD pending complete regional table capture.**

Roy Morgan published a fresh first-party eight-region study on 20 October using `N=2,845` interviews across July–September, approximately 340 respondents per country region and 370 per metropolitan region. Its published seat baseline is:

- Coalition 12;
- Labor 10;
- One Nation 6;
- Greens 8;
- four seats unresolved.

Source: https://www.roymorgan.com/findings/10361-victorian-state-voting-intention-september-2026

The accessible article publishes many party-by-region shares but not a complete five-family table for all eight regions. The current model therefore retains the August Roy Morgan regional table. When complete tables/cross-tabs are captured, the new study should **replace**, not stack with, the August regional input. Missing regional cells must not be manufactured by subtraction.

## VEC official inputs

The Victorian Electoral Commission now reports **4,694,947 electors as at 6 October 2026**, up 11,544 from 4,683,403 in August, and publishes September district and region workbooks.

Source: https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics

The active model still uses the August workbooks extracted on 4 September. The September workbooks should be promoted only after deterministic capture, extraction, 88-district/eight-region coverage checks and reconciliation of both totals to 4,694,947.

Current VEC election rules were reverified on 25 October. The election remains 28 November; the roll closes 8 pm on 3 November; nominations close noon on 9 November; early voting starts 18 November. Group voting tickets have been removed for the Council and voters must number at least five preferences above or below the line. No new redistribution was identified.

## Candidate evidence

The current discovery/review machinery now validates **305 accepted candidate-evidence records**, with accepted evidence coverage across all 88 Assembly districts and all eight Council regions. Current discovery remains quarantined and automatic promotion is disabled. Candidate announcements and endorsements are not treated as official nominations; VEC nomination status remains authoritative after nominations open and close in November.

## Canonical forecast decision

No newly staged statewide poll is promoted in this packet. The canonical engine is rerun at `as_of: 2026-10-25` using the unchanged 13 admitted statewide observations. This deliberately distinguishes:

1. **evidence freshness** — current public evidence has been found and recorded; from
2. **model-input freshness** — the central model remains stale until the newer evidence is admitted or explicitly excluded.

That distinction is now visible in release readiness rather than hidden behind a newer forecast timestamp.

## Exact next decisions

1. Project owner re-adjudicates the now-primary-verified September DemosAU wave for model eligibility and dependency/comparability.
2. RedBridge October remains held unless the existing sample-family independence blocker is resolved or explicitly adjudicated under a revised policy.
3. Resolve October remains held until first-party carrier/methodology capture or an explicit reviewed exception.
4. Capture Roy Morgan's complete July–September Council tables before replacing the August regional input.
5. Capture and reconcile the VEC September district/region enrolment workbooks.
6. After any model-input change, rerun the exact deterministic forecast and compare against the 25 October stale-input diagnostic rather than treating the diagnostic as the current evidence forecast.
