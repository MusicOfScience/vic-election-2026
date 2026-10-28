#!/usr/bin/env python3
"""Run the official-data AEC-2025 ONP geographic challenger against current geography.

Shadow research only. The canonical model files are never written. Each 2025
spatial treatment is calibrated with one common additive ONP logit intercept so
its central enrolment-weighted statewide ONP primary matches the current 2022
geography control. Common random numbers are used throughout.
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
TREATMENTS = (0.50, 0.62, 0.75, 1.00)


def _normalise_name(value: str) -> str:
    return str(value).strip().upper()


def _current_seed(model_root: Path, config: dict) -> pd.DataFrame:
    return forecast_module.build_assembly_seed(model_root, config).copy()


def _challenger_seed(model_root: Path, config: dict, lam: float, current_seed: pd.DataFrame) -> pd.DataFrame:
    seed = current_seed.copy()
    challenger = pd.read_csv(model_root / NEW_SURFACE)
    seed_keys = seed[["district_name"]].copy()
    seed_keys["district_key"] = seed_keys.district_name.map(_normalise_name)
    challenger = challenger[["district_name", "onp_log_ratio_to_located_state"]].copy()
    challenger["district_key"] = challenger.district_name.map(_normalise_name)
    challenger = challenger.rename(columns={"district_name": "challenger_district_name"})
    merged = seed_keys.merge(challenger, on="district_key", how="left", validate="one_to_one")
    if merged["onp_log_ratio_to_located_state"].isna().any() or len(merged) != len(seed):
        missing = merged.loc[merged["onp_log_ratio_to_located_state"].isna(), "district_name"].tolist()
        raise ValueError(f"2025 challenger is missing model districts: {missing}")

    weights = seed["enrolled_electors"].to_numpy(float)
    weights /= weights.sum()
    current = seed["onp_local_log"].to_numpy(float)
    current_centre = float(np.sum(current * weights))
    raw = merged["onp_log_ratio_to_located_state"].to_numpy(float)
    raw_centre = float(np.sum(raw * weights))
    seed["onp_local_log"] = current_centre + float(lam) * (raw - raw_centre)
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
    for lam in TREATMENTS:
        raw = _challenger_seed(model_root, config, lam, current_seed)
        calibrated, calibration = conserve_central_onp_primary(model_root, config, raw, current_seed)
        result = _run_with_seed(model_root, calibrated, simulations=simulations, seed=seed_value)
        summary = _summary(result, calibrated, calibration)
        treatments[str(lam)] = summary
        comparisons[str(lam)] = _compare(control, summary)

    return {
        "schemaVersion": 4,
        "mode": "onp-aec-2025-geography-shadow",
        "asOf": str(config["as_of"]),
        "simulationsPerTreatment": simulations,
        "seed": seed_value,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "controlSurface": "existing AEC_2022_ecological_auxiliary",
        "challengerSurface": "AEC 2025 House ordinary polling-place geography mapped to current Assembly districts",
        "districtJoinRule": "case-insensitive trimmed district name",
        "challengerLambdas": list(TREATMENTS),
        "configuredAecLocalPatternShrinkageDiagnostic": 0.62,
        "centralVoteConservation": True,
        "conservationRule": "common additive ONP logit intercept solved per treatment at frozen canonical latent mean",
        "control": control,
        "treatments": treatments,
        "comparisonsVsCurrent": comparisons,
        "governance": {
            "productionInput": False,
            "royMorganRead": False,
            "candidateEffectsAdded": False,
            "statewidePollingChanged": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--simulations", type=int, default=5000)
    parser.add_argument("--output", default="model/data/validation/onp-geography-shadow-2025-surface.json")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = run_shadow(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"AEC-2025 ONP geography shadow complete: {args.simulations} simulations x {1 + len(TREATMENTS)} runs; central ONP vote conserved; canonical artefacts untouched.")


if __name__ == "__main__":
    main()
