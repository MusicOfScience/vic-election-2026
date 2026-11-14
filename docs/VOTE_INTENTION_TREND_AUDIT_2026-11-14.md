# Victorian Assembly voting intention and the leadership change

The 31 October snapshot already estimates statewide first preferences from a
poll-of-polls with a 45-day recency half-life, capped sample-size weighting
and shrunk pollster effects. It is a current-level estimate. Seat winning
frequencies represent how that vote estimate, local baselines and preference
assumptions translate into simulated results.

## Rolling polling test

Reproduce from repository root:

```sh
PYTHONPATH=model/src python model/scripts/audit_vote_intention_trend.py --as-of 2026-10-31
```

Fifteen admitted five-way polls were available at the cutoff. The ten eligible
holdouts each had at least five earlier polls from at least three houses.
Training polls had to finish and be published before the target's fieldwork
began. Scores average absolute error equally across each wave and five party
groups. They measure next-poll prediction, with sampling and house noise still
in the targets. Historical admission timing is proxied by publication within
the current registry. This is a retrospective diagnostic within one campaign.

| Estimator | Mean absolute error (percentage points) |
| --- | ---: |
| Existing recency-weighted polling model | 1.725 |
| Matched ridge model with a level and house terms | 1.726 |
| Matched ridge model with a shrunk drift term | 1.785 |

The drift model improved on the matched level in four of ten folds. Its
October 31 point estimate for election day was Coalition 30.09%, Labor 23.08%,
One Nation 21.55%, Greens 13.01%, Others 12.27%. The result is sensitive to the
trend penalty and the sparse poll schedule. Keep the existing central estimate.
Investigate a dynamic model with a flat expected drift and uncertainty growing
with forecast horizon once there is enough evidence to test it across elections.

## Labor leadership

[Ben Carroll took office on 28 July 2026](https://www.vic.gov.au/premier).
Within eight weeks on either side, only two pollsters in the admitted series
have fully before-and-after fieldwork. Labor's raw same-house changes were
+1.659 points at Freshwater (53 days between fieldwork windows) and +4.0 points
at DemosAU (91 days). This comparison confounds leadership, concurrent campaign
events, trend and possible changes in survey execution. Use the date as a chart
annotation. The evidence does not support a numerical leadership adjustment.

## Incoming polls and seat conversion

The diagnostic uses the admitted poll ledger and leaves official forecasts
untouched. The newer November waves are recorded in
[the evidence review](../metadata/november-poll-evidence-review-2026-11-11.json).
Adjudicating wave comparability, sample overlaps and admission is more valuable
than extrapolating the October series. Keep published 2PP estimates by pollster
and preference method as an external check on modelled 2PP. A statewide trend
does not establish a local candidate's first preferences or preference flows.
