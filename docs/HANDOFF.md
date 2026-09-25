# Project handoff

Updated: 2026-09-25

## Current state

- Main is based on merged PR #118, `ad5d1b5dffab4e139e6fff9409eae36d7eb34dc4`.
- Historical counters are runnable 4/4, predicted 4/4, scored 4/4, certifying predicted 3/4 and certifying scored 3/4.
- Certifying v2 cycles are `vic_la_2010`, `vic_la_2014` and `vic_la_2022`. `vic_la_2018` remains non-certifying: v1 implementation defect; v2 post-hoc diagnostic.
- The canonical aggregate is [`historical-certifying-v2-aggregate.json`](../model/data/validation/historical-replays/historical-certifying-v2-aggregate.json), SHA `7680fa6111c01665b24c6fe16bca6ab6d67f9aa4697c8294de1be33d0a4c972e`. Its unweighted three-cycle means are winner accuracy `0.8404301637`, multiclass Brier `0.2193372181`, multiclass log loss `1.0486418097` and district primary MAE `4.7557257435`.
- Complete backtest remains `closed-incomplete-certifying-four-cycle-protocol`; probability calibration remains `closed-incomplete-cycle-clustered-protocol`; production authorisation remains closed.

## Immutable scoring evidence

- 2010 score: [`vic_la_2010-v2-score.json`](../model/data/validation/historical-replays/vic_la_2010-v2-score.json), embedded score SHA `6503d74c2306f8bc08dae6e76f3b055a1c19f477e0b432119cbc820360d0e1b0`. Official VEC final-pair artefact SHA `00533f13f92713e28f30e173a12a786b7113cc02fb00301273e541ea4b74d9fd`; 88 districts, 44 final pairs available and 44 unavailable. Winner accuracy 86.36%, district primary MAE 3.91pp, Brier 0.16798, log loss 0.24398, final-pair accuracy 88.64%. Canonical Council regional MAE is `0.27911458333333333`.
- 2014 score SHA `e96125d51b4b85a365fb457148a0cee411f576c1d09f71b225fd7284175e4bae`; 2022 score SHA `3bc3b150a5a410bbda2c18e679ed0ae03c555a24d7f3b98a1b0e111c22abdb4e`.
- 2018 v1 remains an immutable negative implementation result, and its v2 output remains diagnostic only. No historical score was rewritten or tuned.

## Release-gate classification

The machine-readable classification is [`metadata/prod-1.0-closure-audit.json`](../metadata/prod-1.0-closure-audit.json). Source integrity, deterministic outputs, historical data readiness and candidate evidence pass. Critical-source freshness and model-input freshness are resolvable current-evidence blockers. Complete backtest and probability calibration are structurally blocked under the current protocol. Production authorisation is downstream blocked.

Release readiness was refreshed as of 2026-09-25 without advancing any source effective date. The model-eligible poll registry remains outside the fixed 21-day freshness window.

## Current 2026 evidence decision

The captured `redbridge-accent-vic-2026-09-14-primary` report is evidence-accepted in principle and remains quarantined. It records publication 2026-09-15, fieldwork 1–14 September, full sample 2,371, effective sample 2,009 and published vote-intention base 2,160. Sample-family independence from earlier RedBridge evidence is not proven, so model eligibility is `hold-pending-missing-independence-evidence`. No project-owner/model-eligibility decision was inferred and no poll was promoted into model inputs.

The exact next decision is an explicit owner/model-eligibility determination for that staged September wave. If admitted under the existing policy, current poll inputs may be refreshed in a separate reviewed batch; otherwise retain the last valid forecast.

## Preserved audit history

The 2010 ballot gate was closed through the general contemporaneously-fixed-fact reconstruction policy, with direct PANDORA/NLA and Wayback capture attempts retained as failed routes. The 2014 crosswalk and ballot mask, 2022 Narracan separation, party-family mapping, and all prior score manifests remain governed. Untracked user files `docs/HANDOFF 2.md` and `metadata/historical-assembly-outcome-availability 2.json` were left untouched.

The deterministic 2026 forecast remains unchanged at SHA `70ed0b9b6abc45ed66dd4ac44ed727d8841d2b19358a473d0eb1c2574a9a1aab`.
