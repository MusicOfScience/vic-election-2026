# Community independents in the 2026 Victorian election

[Climate 200 identified four supported campaigns in October](https://www.climate200.com.au/event/vic26-mega-event).
Three challenge Liberal incumbents and Footscray challenges Labor. The
campaigns are a useful group to study. Their shared backing and selected
electorates cannot establish a swing across the state. Benambra is a distinct
regional succession case, as is Shepparton, where former independent MP
[Suzanna Sheed endorsed Lou Costa](https://www.sheppadviser.com.au/suzanna-sheed-backs-lou-costa/).
[The Benambra community group selected Lachie McKeeman to succeed Jacqui Hawkins](https://www.theguardian.com/australia-news/2026/nov/14/jess-wilson-wodonga-pub-vic-election-campaign-2026-ntwnfb).

## Ballot and results audit

Reproduce with `python model/scripts/audit_community_independents.py`. The
script checks the official 2026 nominations and joins 2022 Victorian Electoral
Commission candidate primaries and actual final distributions to the dated
experimental forecast. The earlier candidates are contest comparators.
Torney is the only returning candidate in this table.

| Electorate | 2026 nominee | 2022 comparator | First preferences (rank) | Actual final count |
| --- | --- | --- | ---: | ---: |
| Kew | Sophie Torney | Sophie Torney | 21.10% (3rd) | Eliminated |
| Hawthorn | Shima Ibuki | Melissa Lowe | 19.98% (3rd) | Eliminated |
| Mornington | Melissa Goffin | Kate Lardner | 22.42% (2nd) | 49.30% |
| Footscray | Jess Marsh | No equivalent 2022 candidate | — | — |
| Benambra | Lachie McKeeman | Jacqui Hawkins | 31.70% (2nd) | 49.06% |
| Shepparton | Lou Costa | Suzanna Sheed | 29.41% (2nd) | 43.21% |
| Caulfield | 2022 comparison only | Nomi Kaltmann | 6.50% (4th) | Eliminated |

The four Climate 200-backed 2022 contests in the table produced zero wins
and one actual finalist. Their first preferences varied from 6.50% to
22.42%. The sample is one selected state election. It supports variation in
local strength and separate modelling of final-pair survival. It cannot
identify a common wave coefficient or a causal effect of backing.

Kew and Hawthorn expose the pooled model's blind spot. Others/independents
receive 26.43% and 27.13% of projected first preferences respectively, but the
group wins 0.06% and 0.92% of runs. Mornington's pooled group has 13.69%
first preferences and zero wins in the recorded runs, after Lardner reached
49.30% in the 2022 final count. These comparisons flag representation risk.
They do not establish that the 2026 independent is more likely to win.

## Candidate-level modelling decision

Keep statewide polling as the party baseline. Split the local residual into
named candidates and remaining minor parties. Model candidate entry first,
then a candidate's primary using local evidence with separate priors for
returning challengers, credible successors and new entries. Allow vote gains
to come from more than one party and conserve the electorate's vote total.
Footscray and the Liberal-held seats plausibly draw from different coalitions
of voters, so ideological adjacency alone supplies no transfer rate.

Use shared campaign backing as a possible predictor of correlated swings
across targeted seats. Use the ballot, candidate identity and local evidence
to determine individual strength. Benchmark a shared term against seat-only
priors on held-out elections, using candidate first-preference error,
actual finalist identification and 2CP error conditional on the correct pair.
Keep historical transfer patterns separate by opponent. Federal community
independent results can motivate a sensitivity range after boundary matching,
with state evidence carrying the primary weight. Current seat forecasts
retain their pooled definition until candidate-level calibration is available.
