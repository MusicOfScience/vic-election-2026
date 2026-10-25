# Deterministic forecast diagnostic — 25 October 2026

This is a **stale-input diagnostic**, not a public-evidence-complete forecast.

The model assessment date advances from 8 October to 25 October while the admitted statewide poll registry remains fixed at 13 observations. Newer October evidence is staged under the project's evidence-governance rules but is not silently promoted. The resulting changes therefore measure the effect of recency weighting and wider uncertainty as eligible observations age.

## Polling state

| Family | 8 Oct mean | 25 Oct mean | Change | 25 Oct 80% interval |
| --- | ---: | ---: | ---: | ---: |
| Labor | 25.3356 | 25.3174 | -0.0182pp | 23.8188–26.7949 |
| Coalition | 27.7978 | 27.7927 | -0.0050pp | 26.0198–29.6228 |
| One Nation | 23.1037 | 23.1037 | -0.0001pp | 21.3632–24.8491 |
| Greens | 13.5311 | 13.5361 | +0.0049pp | 12.7589–14.3451 |
| Other/independent | 10.2318 | 10.2501 | +0.0183pp | 9.2553–11.3091 |

Central values barely move because all admitted observations age together. Intervals widen as the effective recency-weighted information decays.

## Legislative Assembly

| Family | Expected seats 8 Oct | Expected seats 25 Oct | Median | 25 Oct 80% range | Majority probability 8 Oct → 25 Oct |
| --- | ---: | ---: | ---: | ---: | ---: |
| Labor | 38.2896 | 38.2394 | 38 | 29–48 | 19.30% → 19.72% |
| Coalition | 31.0216 | 31.0236 | 31 | 23–40 | 3.10% → 3.48% |
| One Nation | 16.2792 | 16.3210 | 16 | 10–23 | 0 → 0 |
| Greens | 2.4032 | 2.4092 | 2 | 1–4 | 0 → 0 |
| Other/independent | 0.0064 | 0.0068 | 0 | 0–0 | 0 → 0 |

Hung-parliament frequency changes **77.60% → 76.80%** (-0.80 percentage points). Both major-party majority tails rise slightly because posterior uncertainty broadens; this is not evidence of an electoral movement toward both parties.

No district meets the project's material-movement threshold of a five-percentage-point change in any family's win probability. There are **zero favoured-party changes** and **zero likely-final-pair changes**.

The largest movement is Eureka: Labor 62.12% → 61.50% (-0.62pp), Coalition 13.84% → 14.02% (+0.18pp), One Nation 24.04% → 24.48% (+0.44pp). Other leading movements are similarly sub-one-point and are not election-signal claims.

## Legislative Council

The Council output also moves only trivially because the active regional evidence remains the August Roy Morgan table.

| Family | Expected seats, 25 Oct | Median | 80% range |
| --- | ---: | ---: | ---: |
| Labor | 11.5716 | 12 | 10–13 |
| Coalition | 12.5648 | 13 | 11–14 |
| One Nation | 9.9986 | 10 | 8–12 |
| Greens | 2.9932 | 3 | 2–4 |
| Other/independent | 2.8718 | 3 | 1–5 |

Major-party no-control probability remains 100% under this experimental Council model. The newer 20 October Roy Morgan regional study is recorded as evidence but not numerically substituted because a complete eight-region five-family table has not yet been captured.

## Release-readiness consequence

At the true 25 October assessment date the repository correctly reports `experimental-blocked`, **4/9 required gates passing**. Critical-source freshness fails because the newest admitted poll is 27 days old against the 21-day threshold. Model-input freshness also fails because newer staged evidence remains unresolved. Complete forecast backtesting, probability calibration and production authorisation remain blocked.

This is the desired governance result: a newly generated timestamp does not disguise stale model inputs.

Full machine-readable comparison: `metadata/forecast-refresh-2026-10-25.json`.
