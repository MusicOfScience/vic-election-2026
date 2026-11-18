# Forecast explorer review

18 November 2026 · Forecast basis: 15 November 2026 experimental release.

| Reference | Applied here | Further use |
| --- | --- | --- |
| [Australian Election Tracker forecast](https://electiontracker.au/forecast) and [poll ledger](https://electiontracker.au/elections/vic/2026/polls) | Explicit controls, source dates and admission lineage. Readers can see new polls at each stop and changes from the previous aggregate. | Use uniform swing as a benchmark and controlled preference scenarios as stress tests. A stated scenario is not a probability distribution. |
| [The Poll Bludger voting intention](https://www.pollbludger.net/vic2026/bludgertrack/) and [seat model](https://www.pollbludger.net/vic2026/bludgertrack/Seats.htm) | Poll trends and seat signals have separate views. | Test external predictors, including the federal vote and incumbency, against held-out state outcomes. Treat South Australian relationships as hypotheses for Victoria. |
| [The Tally Room Victorian guide](https://www.tallyroom.com.au/vic2026) and [Bean and Fremantle booth comparisons](https://www.tallyroom.com.au/60611) | Put a dated reading guide inside the existing seat profile with its historic swing and booth explorer. | Link like-for-like booth comparisons when the pair, boundaries and vote mode support them. Aggregate pre-poll and postal groups separately from ordinary booths. |
| [Antony Green on preference flows](https://antonygreen.com.au/do-greens-voters-follow-how-to-votes/) and [AEC Calwell count](https://results.aec.gov.au/31496/Website/HouseDivisionPage-31496-203.htm) | Show alternative pair frequencies and last-exclusion pressure. Link an observed count alongside the illustrative transfer diagram. | Label the stage and ballot group for every flow. The same source party can produce different figures for original first preferences and exclusion parcels. |
| [Gelman and colleagues on US forecast uncertainty](https://doi.org/10.1162/99608f92.a919e3fa) | Keep the polling interval separate from Assembly simulations and pair-conditional vote shares. | Benchmark correlated miss risk and nonsampling error on Victorian vintages. US state effects have no direct Victorian calibration. |

## Pair frequency correction

The simulation file records winner-first pairs. A pair such as Coalition–Greens appears in two orders as the winning group changes. The old watch cards displayed one order as if it were the complete pairing probability. Albert Park is a visible example. Coalition ahead of Greens occurred in 2,163 of 5,000 runs (43.26%). Greens ahead of Coalition occurred in 455. The pair itself therefore appeared in 2,618 runs (52.36%). Labor won 46.94% of all runs. The explorer sums orientations and validates its pair-conditional wins against the existing district totals. Each simulated election and its winner are retained exactly.

The last-exclusion diagnostic compares the second- and third-ranked continuing groups immediately before one is excluded. Its two-point threshold is a reading aid expressed as a percentage of all formal votes. It does not represent a historical error band. Small samples of a modelled pair are shown with a draw count and no displayed interval below 50 draws.

## Candidate-level feasibility check

The repo’s 2022 VEC-derived transfer corpus covers 39 Assembly districts. Counting unique district, distribution, count number and excluded candidate gives 244 exclusion events. Only 39 have no inbound transfers and qualify as original-only parcels. The 38 Greens exclusions, two Liberal exclusions and two One Nation exclusions are all mixed parcels. Of 53 independent exclusions, 21 are original-only, across 21 districts. This places a concrete limit on the precision of party-by-region transfer estimates. Many regional cells would have zero clean observations.

Reproduce the inventory with:

```python
import pandas as pd

rows = pd.read_csv("model/data/processed/vec_2022_preference_transfer_evidence.csv.gz")
events = rows.drop_duplicates(
    ["district_id", "distribution_type", "count_number", "excluded_candidate_name"]
)
print(events.groupby("source_party_id").agg(
    events=("source_party_id", "size"),
    original_only=("pure_original_parcel", "sum"),
    districts=("district_id", "nunique"),
))
```

The [candidate-resolution experiment](CANDIDATE_RESOLUTION_IRV_RESULTS_2026-10-29.md) and its [wider-transfer follow-up](CANDIDATE_RESOLUTION_PREFERENCE_UNCERTAINTY_RESULTS_2026-10-29.md) justify retaining the research branch. The latter improved log loss but missed the winner Brier tolerance by 0.00651 on the preregistered comparison. The adjudication does not authorise a separate 2026 shadow. The current release has five-family simulation diagnostics and evidence-led named-candidate briefs.

A viable next challenger would share information across districts, model differences by pair type and count stage, and keep party-by-region interactions under strong shrinkage or out of the specification where the historical data do not identify them. Freeze the feature set against historical vintages. Validate first-preference rank, final pairs, conditional margins and winner scores separately against the current engine and a simple benchmark. For named independents, verify nominations and measure historical local candidate evidence before estimating any shared campaign effect. How-to-vote cards describe recommendations and zero-weight local leads remain contextual until admitted.

## Poll history and count-day data

The replay is regenerated from the same model and the frozen admission set, with a publication cutoff at every stop and a reconciliation check at the release endpoint. The replay starts after at least three admitted waves. With two, the earliest fitted frame’s rank-one residual covariance produced small seeded interval differences across numerical libraries. The source ledger still includes both waves. An immutable historical release archive should retain its actual input manifest and estimate whenever a new forecast is issued. Preserve fieldwork, publication and admission dates and assign one identifier to each sample family. Cross-site disagreements can be inspection leads and do not add an observation by themselves.

For election night, ingest time-stamped Victorian Electoral Commission updates with pair identifiers, vote mode and coverage. Display the indicative pair and any reset as distinct events. A reset starts a new comparable series. Append the statutory result and declaration when supplied. This review specifies that workflow pending suitable live data. The Calwell example is an observed federal count with its own source, and the preference lab is illustrative.
