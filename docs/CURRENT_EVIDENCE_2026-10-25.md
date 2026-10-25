# Current election evidence refresh — 25 October 2026

## Status

This refresh preserves the repository's existing evidence-governance rules. It does **not** promote new polling into the canonical registry and does **not** rewrite the published 8 October experimental forecast.

The canonical forecast remains explicitly experimental and `production_compatible: false`. The purpose of this refresh is to record verified post-8 October evidence, run it through the repository's actual multi-party IRV/STV engine as controlled shadow scenarios, and expose the resulting district/chamber distributions for review before any owner admission decision.

## Evidence staged for Assembly shadow runs

### DemosAU / PremierNational — September wave

- Fieldwork: 10–20 September 2026
- N = 1,020
- Primary: Coalition 30, Labor 25, One Nation 20, Greens 14, other 11
- Published two-party preferred: Coalition 52, Labor 48
- Primary source: https://demosau.com/news/coalition-lead-narrows-as-labor-rises-in-latest-victorian-poll/
- Status: first-party evidence now resolves the earlier topline/method/residual evidence gap, but cross-wave respondent independence is not disclosed. Canonical admission remains an owner decision.

### RedBridge / Accent Research — October wave

- Fieldwork: 2–8 October 2026
- N = 1,008; effective N = 775
- Primary: Coalition 30, Labor 24, One Nation 24, Greens 16, other 6
- Respondent-allocated two-party preferred: Coalition 56, Labor 44
- Method: online panel; demographic and 2025 federal-vote quotas; rim weighting; undecided leaner; remaining undecided excluded
- Primary source: https://www.accent-research.com/projects/afr-redbridge-group-and-accent-research-october-2026-victorian-state-poll
- Status: first-party methodology is available, but the existing project-owner rule requires a documented decision on cross-wave respondent/sample-family independence before canonical admission. This refresh does not override that rule.

### Resolve Strategic — October wave

- Fieldwork: 6–10 October 2026
- N = 1,000
- Primary: Coalition 28, Labor 25, One Nation 23, Greens 15, other 9
- Corroborating ledger: https://electiontracker.au/elections/vic/2026/polls
- Status: staged only in the expanded sensitivity scenario. Primary pollster/publisher methodology has not yet been captured into the project evidence trail, so canonical admission remains on hold.

## Full-election shadow results

Each scenario uses the repository's existing `correlated_multi_party_irv` / voter-directed Council approximation, 5,000 simulations, the configured seed, and common random numbers. Canonical poll files and generated forecast artefacts are not written.

### Canonical registry re-aged to 25 October

This isolates ordinary time-decay from new evidence.

| Measure | Result |
|---|---:|
| Labor mean seats | 38.24 |
| Coalition mean seats | 31.02 |
| One Nation mean seats | 16.32 |
| Greens mean seats | 2.41 |
| Labor majority probability | 19.72% |
| Coalition majority probability | 3.48% |
| Hung Assembly probability | 76.80% |

### Latest primary-source scenario: DemosAU + RedBridge/Accent

Latent statewide polling mean:

| Party | Mean |
|---|---:|
| Labor | 25.12% |
| Coalition | 28.58% |
| One Nation | 22.74% |
| Greens | 14.05% |
| Other/Independent | 9.52% |

Assembly output:

| Measure | Result | Change vs re-aged canonical |
|---|---:|---:|
| Labor mean seats | 37.47 | -0.77 |
| Coalition mean seats | 33.05 | +2.02 |
| One Nation mean seats | 14.84 | -1.49 |
| Greens mean seats | 2.65 | +0.24 |
| Labor majority probability | 15.80% | -3.92 pp |
| Coalition majority probability | 5.18% | +1.70 pp |
| Hung Assembly probability | 79.02% | +2.22 pp |

There are 16 districts with a win-probability movement of at least five percentage points and none at or above ten points. The only modal-winner change is **Bass: One Nation → Coalition**, but the new Coalition probability is only 49.74%, so this is not a robust seat call.

Largest probability movements include Prahran, Shepparton, Albert Park, Melbourne, Richmond, Benambra, Gippsland South, Euroa, Narracan, Narre Warren North, Ripon, Caulfield, Pakenham and Sunbury.

### Expanded scenario: add Resolve October

This is lower-confidence because Resolve remains secondary-captured in the project trail.

| Measure | Result | Change vs re-aged canonical |
|---|---:|---:|
| Labor mean seats | 37.68 | -0.56 |
| Coalition mean seats | 32.71 | +1.69 |
| One Nation mean seats | 14.91 | -1.42 |
| Greens mean seats | 2.70 | +0.30 |
| Labor majority probability | 16.54% | -3.18 pp |
| Coalition majority probability | 4.02% | +0.54 pp |
| Hung Assembly probability | 79.44% | +2.64 pp |

In this expanded scenario Prahran changes modal favourite from Labor to Coalition and Bass from One Nation to Coalition, but both remain highly uncertain rather than stable calls.

## Interpretation

The post-8 October polling does **not** produce a clean Coalition-majority signal inside this model. Its dominant effect is to transfer expected seats from One Nation toward the Coalition while slightly reducing Labor's expectation and increasing the Greens marginally. Because the Coalition majority gain is smaller than the fall in Labor-majority probability, the simulated hung-parliament frequency rises modestly.

The important modelling signal is therefore not a conventional two-party swing. The new evidence changes elimination-order probabilities and the efficiency with which the Coalition and One Nation convert their respective statewide votes into seats.

These outputs are conditional on the repository's model architecture and must not be treated as objective election probabilities. The model remains experimental and has not passed all production gates.

## Legislative Council: material new evidence, not yet injected

Roy Morgan published new July–September regional Council polling on 20 October 2026 (N = 2,845; approximately 360 respondents per region):

https://www.roymorgan.com/findings/10361-victorian-state-voting-intention-september-2026

Its published minimum allocation is:

| Party | Minimum seats |
|---|---:|
| Coalition | 12 |
| Labor | 10 |
| One Nation | 6 |
| Greens | 8 |
| Unresolved | 4 |

That is Coalition + One Nation 18 versus Labor + Greens 18 before four unresolved seats, materially different from Morgan's August picture.

The current repository Council engine still points to `upper_house_region_poll_2026-08.csv`. The new Morgan evidence is recorded in the 25 October evidence ledger but is **not** injected into the STV approximation because the publicly accessible text does not expose a complete five-way regional primary table without inference. In particular, missing One Nation/Other values in Northern Metropolitan and Southern Metropolitan should not be manufactured from residual arithmetic.

Consequently, Council values emitted by the current shadow scenarios are **not a 25 October Council forecast**. Updating the regional Council model requires either the complete source table/crosstabs or an explicit, documented modelling decision about partial regional evidence.

## Candidate, preference and election-administration evidence

The 23 October source-monitor run successfully produced 209 review records (196 candidate records and 13 poll records) and validated 305 accepted candidate records covering all 88 Assembly districts and all eight Council regions. It intentionally stopped at the repository's review/freshness gates rather than silently changing model inputs.

Candidate announcements remain pre-election evidence rather than official nominations until the Victorian Electoral Commission nomination period. Current VEC timetable: roll closes 8pm 3 November; nominations open 4 November; early voting 18–27 November; election day 28 November.

No final statewide Liberal–One Nation how-to-vote agreement is treated as established evidence in this refresh. Reported preference negotiations remain contingent on final nominations and local candidates. The Council group-voting-ticket abolition is already part of the 2026 structural context; no post-8 October redistribution is introduced here.

## Decisions required before canonical promotion

1. Decide whether the DemosAU September wave is sufficiently independent of earlier DemosAU samples for canonical model admission.
2. Decide whether the RedBridge/Accent October wave satisfies or supersedes the existing sample-family-independence safeguard.
3. Capture/verify the October Resolve primary-source methodology before admission.
4. Capture a complete five-way Roy Morgan July–September regional Council table, or explicitly approve a principled partial-evidence method; do not fill missing cells by guesswork.
5. Re-run the normal forecast refresh and release-readiness gates only after those evidence decisions are recorded.

Until then, the 25 October outputs are governed **shadow sensitivity runs**, not a replacement canonical forecast.
