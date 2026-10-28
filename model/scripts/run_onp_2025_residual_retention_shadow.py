#!/usr/bin/env python3
"""Test how much genuinely new AEC-2025 ONP spatial information to retain.

Shadow research only.  The existing 2022 ONP geography and the official 2025
House polling-place surface are decomposed as:

    delta_2025 = beta * delta_2022 + residual_2025

where beta is an enrolment-weighted no-intercept regression on centred spatial
signals.  Treatments retain 0/25/50/75/100% of the 2025 residual while keeping
the stable 2022->2025 component.  This distinguishes persistence from new local
information without choosing a global spatial-shrinkage lambda by inspection.

Each treatment then receives the same central-vote conservation calibration used
by the other governed geography shadows.  No canonical artefact is written and
no 2026 seat poll, Roy Morgan observation or candidate adjustment is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import yaml

import vicforecast.forecast_2026 as forecast_module
from vicforecast.forecast_2026 import PARTIES, run_experimental_forecast
from onp_geography_shadow_common import conserve_central_onp_primary, central_weighted_onp_primary


NEW_SURFACE = "data/validation/aec_2025_onp_state_district_surface.csv"
RETENTIONS = (0.00, 0.25, 0.50, 0.75, 1.00)


def _normalise_name(value: str) -> str:
    return str(value).strip().upper()


def _current_seed(model_root: Path, config: dict) -> pd.DataFrame:
    return forecast_module.build_assembly_seed(model_root, config).copy()


def _decomposition(model_root: Path, current_seed: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, float, np.ndarray, dict]:
    challenger = pd.read_csv(model_root / NEW_SURFACE)
    seed_keys = current_seed[["district_name"]].copy()
    seed_keys["district_key"] = seed_keys.district_name.map(_normalise_name)
    challenger = challenger[["district_name", "onp_log_ratio_to_located_state"]].copy()
    challenger["district_key"] = challenger.district_name.map(_normalise_name)
    challenger = challenger.rename(columns={"district_name": "challenger_district_name"})
    merged = seed_keys.merge(challenger, on="district_key", how="left", validate="one_to_one")
    if merged["onp_log_ratio_to_located_state"].isna().any() or len(merged) != len(current_seed):
        missing = merged.loc[merged["onp_log_ratio_to_located_state"].isna(), "district_name"].tolist()
        raise ValueError(f"2025 challenger is missing model districts: {missing}")

    weights = current_seed["enrolled_electors"].to_numpy(float)
    weights /= weights.sum()
    x_raw = current_seed["onp_local_log"].to_numpy(float)
    y_raw = merged["onp_log_ratio_to_located_state"].to_numpy(float)
    x_centre = float(np.sum(weights * x_raw))
    y_centre = float(np.sum(weights * y_raw))
    x = x_raw - x_centre
    y = y_raw - y_centre
    denominator = float(np.sum(weights * x * x))
    if denominator <= 0:
        raise ValueError("2022 ONP spatial signal has zero weighted variance")
    beta = float(np.sum(weights * x * y) / denominator)
    residual = y - beta * x
    residual_centre = float(np.sum(weights * residual))
    if abs(residual_centre) > 1e-10:
        raise ValueError(f"weighted residual should be centred, got {residual_centre}")
    fitted = beta * x
    weighted_r2 = 1.0 - float(np.sum(weights * residual * residual) / np.sum(weights * y * y))
    diagnostics = {
        "weightedSlope2025On2022": beta,
        "weightedRSquared": weighted_r2,
        "weightedStd2022Signal": float(np.sqrt(np.sum(weights * x * x))),
        "weightedStd2025Signal": float(np.sqrt(np.sum(weights * y * y))),
        "weightedStd2025Residual": float(np.sqrt(np.sum(weights * residual * residual))),
        "weightedMeanResidual": residual_centre,
    }
    return x, residual, x_centre, weights, diagnostics


def _candidate_seed(
    current_seed: pd.DataFrame,
    *,
    x: np.ndarray,
    residual: np.ndarray,
    current_centre: float,
    beta: float,
    retention: float,
) -> pd.DataFrame:
    seed = current_seed.copy()
    seed["onp_local_log"] = current_centre + beta * x + float(retention) * residual
    return seed


def _run_with_seed(model_root: Path, replacement: pd.DataFrame, *, simulations: int, seed: int):
    def shadow_builder(root, config=None):
        return replacement.copy()

    with patch("vicforecast.forecast_2026.build_assembly_seed", side_effect=shadow_builder):
        return run_experimental_forecast(model_root, simulations=simulations, seed=seed)


def _weighted_onp_primary(result, seed_frame: pd.DataFrame) -> float:
    weights = seed_frame["enrolled_electors"].to_numpy(float)
    weights /= weights.sum()
    districts = result.districts.set_index("district_name")
    primaries = np.array([float(districts.loc[name, "primary_onp"]) for name in seed_frame["district_name"]])
    return float(np.sum(weights * primaries))


def _summary(result, seed_frame: pd.DataFrame, calibration: dict) -> dict:
    chamber = result.chamber.set_index("party")
    return {
        "hungProbability": float(result.chamber.hung_probability.iloc[0]),
        "weightedMeanDistrictOnpPrimary": _weighted_onp_primary(result, seed_frame),
        "centralVoteCalibration": calibration,
        "parties": {
            party: {
                "meanSeats": float(chamber.loc[party, "mean"]),
                "majorityProbability": float(chamber.loc[party, "majority_probability"]),
            }
            for party in PARTIES
        },
        "districts": {
            str(row.district_name): {
                "favouredParty": str(row.favoured_party),
                "favouredProbability": float(row.favoured_probability),
                "likelyFinalPair": str(row.likely_final_pair),
                "finalPairProbability": float(row.final_pair_probability),
                "primaryONP": float(row.primary_onp),
                "winONP": float(row.win_onp),
            }
            for row in result.districts.itertuples()
        },
    }


def _compare(control: dict, challenger: dict) -> dict:
    rows = []
    for name, current in control["districts"].items():
        other = challenger["districts"][name]
        rows.append({
            "district": name,
            "deltaPrimaryONP": other["primaryONP"] - current["primaryONP"],
            "deltaWinONP": other["winONP"] - current["winONP"],
            "modalWinnerChanged": other["favouredParty"] != current["favouredParty"],
            "modalFinalPairChanged": other["likelyFinalPair"] != current["likelyFinalPair"],
        })
    ranked = sorted(rows, key=lambda row: abs(row["deltaWinONP"]), reverse=True)
    return {
        "deltaHungProbability": challenger["hungProbability"] - control["hungProbability"],
        "deltaWeightedMeanDistrictOnpPrimary": challenger["weightedMeanDistrictOnpPrimary"] - control["weightedMeanDistrictOnpPrimary"],
        "partyDeltas": {
            party: {
                "meanSeats": challenger["parties"][party]["meanSeats"] - control["parties"][party]["meanSeats"],
                "majorityProbability": challenger["parties"][party]["majorityProbability"] - control["parties"][party]["majorityProbability"],
            }
            for party in PARTIES
        },
        "modalWinnerChanges": [row["district"] for row in rows if row["modalWinnerChanged"]],
        "modalFinalPairChanges": [row["district"] for row in rows if row["modalFinalPairChanged"]],
        "seatsWithOnpWinProbabilityShiftAtLeast5pp": sum(abs(row["deltaWinONP"]) >= 0.05 for row in rows),
        "seatsWithOnpWinProbabilityShiftAtLeast10pp": sum(abs(row["deltaWinONP"]) >= 0.10 for row in rows),
        "largestOnpWinProbabilityChanges": ranked[:20],
    }


def run_shadow(repo_root: Path, *, simulations: int) -> dict:
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed_value = int(config["seed"])
    current_seed = _current_seed(model_root, config)
    x, residual, current_centre, _, diagnostics = _decomposition(model_root, current_seed)
    beta = float(diagnostics["weightedSlope2025On2022"])

    target = central_weighted_onp_primary(model_root, config, current_seed) * 100.0
    control_result = _run_with_seed(model_root, current_seed, simulations=simulations, seed=seed_value)
    control_calibration = {
        "rule": "control geography; no calibration required",
        "targetCentralWeightedPrimary": target,
        "candidateBeforeCalibration": target,
        "candidateAfterCalibration": target,
        "additiveLogitOffset": 0.0,
        "absoluteResidualPercentagePoints": 0.0,
    }
    control = _summary(control_result, current_seed, control_calibration)

    treatments = {}
    comparisons = {}
    for retention in RETENTIONS:
        raw = _candidate_seed(
            current_seed,
            x=x,
            residual=residual,
            current_centre=current_centre,
            beta=beta,
            retention=retention,
        )
        calibrated, calibration = conserve_central_onp_primary(model_root, config, raw, current_seed)
        result = _run_with_seed(model_root, calibrated, simulations=simulations, seed=seed_value)
        summary = _summary(result, calibrated, calibration)
        key = str(retention)
        treatments[key] = summary
        comparisons[key] = _compare(control, summary)

    return {
        "schemaVersion": 1,
        "mode": "onp-aec-2025-residual-retention-shadow",
        "asOf": str(config["as_of"]),
        "simulationsPerTreatment": simulations,
        "seed": seed_value,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "controlSurface": "existing AEC_2022_ecological_auxiliary",
        "challengerSurface": "AEC 2025 House ordinary polling-place geography mapped to current Assembly districts",
        "decomposition": "centred delta_2025 = weighted_beta * centred delta_2022 + residual_2025",
        "decompositionDiagnostics": diagnostics,
        "newInformationRetentions": list(RETENTIONS),
        "centralVoteConservation": True,
        "control": control,
        "treatments": treatments,
        "comparisonsVsCurrent": comparisons,
        "governance": {
            "productionInput": False,
            "royMorganRead": False,
            "candidateEffectsAdded": False,
            "statewidePollingChanged": False,
            "purpose": "separate stable geographic persistence from new 2025 local residual information",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--simulations", type=int, default=5000)
    parser.add_argument("--output", default="model/data/validation/onp-geography-shadow-2025-residual-retention.json")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = run_shadow(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"AEC-2025 ONP residual-retention shadow complete: {args.simulations} simulations x "
        f"{1 + len(RETENTIONS)} runs; canonical artefacts untouched."
    )


if __name__ == "__main__":
    main()
