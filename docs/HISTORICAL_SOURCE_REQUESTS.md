# Historical validation source requests

These are the two external requests that would most efficiently unblock complete-model historical validation. Their status is tracked in `metadata/historical-source-acquisition-plan.json`. A response is evidence for review, not permission to change the forecast automatically.

## Request 1 — Victorian Electoral Commission

**Subject:** Request for machine-readable Victorian Legislative Assembly candidate results, 2010–2022

Hello VEC team,

I am maintaining a reproducible, non-commercial research project examining Victorian state-election forecasting and historical model validation.

Could you please provide, or direct me to, machine-readable candidate-level Legislative Assembly first-preference results for every district at the 2010, 2014, 2018 and 2022 Victorian state elections?

CSV, XLSX or XLS would be ideal. For each election and district, we need:

- election identifier and election date;
- district name;
- candidate name;
- candidate party label or independent status;
- candidate first-preference votes;
- district formal-vote total;
- any source-file or revision metadata; and
- the applicable reuse or licensing terms.

If these records already exist as bulk downloads or an API, a link would be perfect. Individual district PDFs alone would not be sufficient for reproducible validation.

Many thanks for your assistance.

## Request 2 — historical polling dataset maintainer

**Subject:** Victorian historical polling data: provenance fields and reuse permission

Hello,

I am auditing the Victorian polling file in `d-j-hirst/aus-polling-analyser` at commit `a244da459807a22284d569b0b7e95ce79dfc53ff`, path `analysis/Data/poll-data-vic.csv`, for a reproducible non-commercial election-model validation project.

The file provides a valuable 200-observation candidate series across the 2010, 2014, 2018 and 2022 Victorian election cycles. Before we can use it in leakage-safe historical replays, could you please clarify:

- whether the data may be copied and reused, and under what licence or terms;
- whether observation publication dates are available separately from `MidDate`;
- whether sample sizes and explicit collection methods are available;
- whether observation-level source URLs or citations exist; and
- whether you would prefer us to link to the pinned file rather than redistribute it.

Until those points are resolved, our project records the series as quarantined and imports zero rows.

Many thanks for maintaining this resource.
