# November polling and preference-flow audit

## New evidence since the prior review

The [News Corp report of 13 November](https://www.news.com.au/finance/work/leaders/ben-carroll-risks-losing-his-seat-at-victorian-election-as-coalition-extends-primary-vote-lead-in-new-opinion-poll/news-story/f819afaf30e91e884afecb139f65d7b3)
reports Lighthouse wave 2 at Coalition 32%, Labor 21%, One Nation 23%,
Greens 14%, and Others 10%. It identifies this as the second tracking wave.
Keep it under review until fieldwork dates, effective sample and overlap with
wave 1 are established. The release date alone cannot stand in for fieldwork end.
The earlier November RedBridge, DemosAU and Resolve leads remain held under
the [existing evidence review](../metadata/november-poll-evidence-review-2026-11-11.json).
No tracked poll enters the canonical registry through this audit.

## Compare the same first preferences

Run from the repository root:

```sh
PYTHONPATH=model/src python model/scripts/audit_november_preference_gap.py
```

Use each poll's reported primaries and allocate the remaining share to the
pooled Others group for this calculation. Keep Labor and the Coalition in
the count. Vary only transfers over 5,000 draws from the existing priors.

| Wave | Published Coalition 2PP | Model mean | Middle 80% of transfer draws | Published minus model |
| --- | ---: | ---: | ---: | ---: |
| RedBridge/Accent | 57% | 52.57% | 50.18–54.89% | +4.43 pp |
| DemosAU | 56% | 55.14% | 52.70–57.52% | +0.86 pp |

Holding primaries fixed leaves a substantial RedBridge gap. Closing it would
require a net additional 9.62 percentage points of its non-major primary
votes ending with the Coalition in this calculation. Many different transfer
patterns could produce that change. DemosAU lies within the range of the
existing transfer draws, so applying a universal adjustment would be premature.
The ranges exclude survey uncertainty and uncertainty about the pollsters'
2PP methods. Obtain the original preference tables and methods before treating
either published 2PP as calibration evidence. Statewide forced 2PP tells us
little about who reaches the final pair in any one electorate.
