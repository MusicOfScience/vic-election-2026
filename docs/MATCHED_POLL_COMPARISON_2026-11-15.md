# Matched polling comparison — 15 November 2026

This diagnostic freezes publication and fieldwork at 31 October 2026. Both estimators receive identical inputs within each pair of rows. The recent subset keeps the latest poll per project pollster label within 45 days of the latest fieldwork end.

| Common input set | Estimator | Labor | Coalition | One Nation | Greens | Others | Coalition lead |
|---|---|---:|---:|---:|---:|---:|---:|
| All admitted (15) | Project latent model, 45-day half-life | 24.28 | 28.80 | 22.41 | 13.27 | 11.24 | 4.52 |
| All admitted (15) | Arithmetic, 21-day half-life | 23.00 | 29.31 | 22.05 | 12.77 | 12.87 | 6.32 |
| Recent subset (3) | Project latent model, 45-day half-life | 23.22 | 29.44 | 21.79 | 13.16 | 12.38 | 6.22 |
| Recent subset (3) | Arithmetic, 21-day half-life | 22.76 | 29.47 | 21.91 | 12.74 | 13.12 | 6.72 |

Vote shares are percentages. Leads are percentage points calculated before rounding.

Using all 15 polls, switching estimator widens the Coalition primary lead by 1.8 points. Using the recent set, the difference between estimators falls to 0.5 points. The project estimator alone widens the lead by 1.7 points when restricted to the recent subset. These differences interact and should not be added. One Nation remains within 0.7 points across all four runs.

The arithmetic benchmark follows [Election Tracker's published weighting rule](https://github.com/coldix/elections/blob/main/docs/poll-methodology.md), using effective sample size and fieldwork-end decay, with sample size divided by 1.3 where effective size is missing. It uses our harmonised primary shares and project pollster identities. The all-admitted arithmetic row deliberately relaxes the Tracker's window and pollster rules to isolate the estimator on common inputs. This is a controlled comparison on our admitted October evidence. The live Tracker uses a different poll set and now includes November evidence.

Reproduce from the repository root:

```sh
PYTHONPATH=model/src python model/scripts/compare_poll_aggregation.py
```

The audit does not admit polls or calculate seat outcomes. A same-primary-vector seat comparison is needed to measure geographic and preference effects.
