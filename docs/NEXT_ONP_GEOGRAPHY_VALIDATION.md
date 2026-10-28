# Next ONP geography validation step

Updated: 28 October 2026

The 2025 geography challenger is retained, but PR #135 does not promote it. The next research task is to estimate a defensible ONP spatial-persistence distribution from external pre-election evidence and then freeze that distribution before examining 2026 Assembly outputs.

## Required work

1. Build comparable official federal spatial surfaces across prior cycles where ballot coverage permits.
2. Estimate cross-cycle persistence of centred ONP geographic log-ratios and quantify measurement error / chamber effects.
3. Separate temporal persistence from federal candidate-field effects; House/Senate comparisons may inform uncertainty but must not be treated as independent observations.
4. Pre-register a lambda distribution or model before running it through the 2026 Assembly simulator.
5. Re-run the 2025 surface with that frozen persistence model and common random numbers.
6. Validate final-pair / preference behaviour separately; geography cannot repair an uncalibrated elimination model.
7. Keep Roy Morgan seat polling, campaign-source seat claims and analyst calls held out from fitting.

## Existing clues, not parameters

- 2025-on-2022 House spatial slope: 0.7749 over roughly three years.
- 2025 House-versus-Senate spatial slope: 0.9102 within the same election.
- Current forecast ONP treatment: lambda effectively 1.00.
- General Assembly AEC local-pattern shrinkage configured elsewhere in the model: 0.62.

None of these values is automatically the correct 2026 ONP persistence parameter. The next step is calibration, not selection among values based on desirable seat outcomes.
