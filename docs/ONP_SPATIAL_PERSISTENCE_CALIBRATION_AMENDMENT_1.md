# ONP spatial-persistence calibration — protocol amendment 1

Date: 28 October 2026  
Status: **pre-2026-output amendment**

## Why this amendment exists

The original preregistration required between-triplet disagreement to be treated as substantive model uncertainty rather than averaged away. The first historical calibration run, completed without executing or inspecting any new 2026 Assembly output, revealed strong disagreement between the two available historical triplets:

- 2016 → 2019 → 2022 target-horizon retention: `a ≈ 0.851`, `kappa ≈ 0.973`
- 2019 → 2022 → 2025 target-horizon retention: `a ≈ 0.985`, `kappa ≈ 0.670`

The initially coded pooled bootstrap averaged the two triplet coefficients within every bootstrap draw. That preserves the pooled mean but mechanically suppresses between-era uncertainty, producing an artificially narrow distribution around approximately `a=0.916`, `kappa=0.808`.

That implementation is inconsistent with the protocol's substantive-uncertainty requirement. It is therefore amended **before any new 2026 Assembly simulation is run**.

## Amended frozen distribution

The production-facing shadow calibration distribution is an **equal-weight empirical mixture** of the two triplet-specific 5,000-draw region-block bootstrap distributions:

1. retain all 5,000 joint `(aTargetTriplet1, kappaTargetTriplet1)` pairs;
2. retain all 5,000 joint `(aTargetTriplet2, kappaTargetTriplet2)` pairs;
3. concatenate them into a 10,000-draw joint empirical distribution with exactly 50% weight on each historical triplet;
4. preserve the within-triplet joint pair on every draw; never sample `a` and `kappa` independently.

The pooled-average distribution remains a diagnostic and point-estimate summary only. It is **not** the allowed distribution for the subsequent 2026 shadow run.

## Why a mixture is preferred here

Only two historical triplets exist. Fitting a smooth random-effects distribution to two era-level observations would add unsupported parametric structure. The empirical mixture is transparent, conservative and makes the observed regime disagreement visible rather than pretending it has been estimated away.

It also preserves the strong joint structure in the historical estimates: one era exhibits lower persistence of established geography but higher persistence of new innovation, while the other exhibits the reverse. A joint mixture retains that dependence.

## Governance

At the time of this amendment:

- no new 2026 Assembly simulation has been executed by PR #136;
- no new 2026 seat, final-pair, chamber or majority output has been inspected;
- Roy Morgan's October 2026 seat poll remains held out;
- campaign-source claims and analyst seat calls remain held out;
- the amendment is motivated solely by the historical calibration diagnostics.

A new machine-readable freeze artefact must be committed after the mixture is generated and checksummed. Any later 2026 shadow runner must require that amended freeze explicitly and reject the earlier pooled-average freeze as a simulation input.
