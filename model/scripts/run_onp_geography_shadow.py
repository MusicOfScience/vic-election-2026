#!/usr/bin/env python3
"""Run governed ONP geographic-persistence shadow sensitivities.

This runner does not write canonical forecast artefacts. It scales the existing
AEC-2022 ecological ONP district propensity and uses a solved common ONP logit
intercept so each treatment preserves the control's central statewide vote level.
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


def _scaled_seed(control: pd.DataFrame, lam: float) -> pd.DataFrame:
    """Scale the existing ONP spatial deviation while preserving its weighted centre."""
    seed = control.copy()
    raw = seed["onp_local_log"].to_numpy(float)
    weights = seed["enrolled_electors"].to_numpy(float)
    weights /= weights.sum()
    centre = float(np.sum(raw * weights))
    seed["onp_local_log"] = centre + float(lam) * (raw - centre)
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
    primaries = np.array([
        float(districts.loc[name, "primary_onp"])
        for name in seed_frame["district_name"]
    ])
    return float(np.sum(weights * primaries))


def _summary(result, seed_frame: pd.DataFrame, calibration: dict) -> dict:
    chamber = result.chamber.set_index("party")
    districts = result.districts.copy()
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
            for row in districts.itertuples()
        },
    }


def _compare(control: dict, challenger: dict) -> dict:
    seats = {}
    for name, row in control["districts"].items():
        other = challenger["districts"][name]
        seats[name] = {
            "deltaPrimaryONP": other["primaryONP"] - row["primaryONP"],
            "deltaWinONP": other["winONP"] - row["winONP"],
            "modalWinnerChanged": other["favouredParty"] != row["favouredParty"],
            "modalFinalPairChanged": other["likelyFinalPair"] != row["likelyFinalPair"],
        }
    ranked = sorted(seats.items(), key=lambda item: abs(item[1]["deltaWinONP"]), reverse=True)
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
        "modalWinnerChanges": [name for name, row in seats.items() if row["modalWinnerChanged"]],
        "modalFinalPairChanges": [name for name, row in seats.items() if row["modalFinalPairChanged"]],
        "largestONPWinProbabilityChanges": [{"district": name, **row} for name, row in ranked[:20]],
    }


def run_shadow(repo_root: Path, *, simulations: int) -> dict:
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed_value = int(config["seed"])
    control_seed = forecast_module.build_assembly_seed(model_root, config).copy()
    target = central_weighted_onp_primary(model_root, config, control_seed) * 100.0
    treatments = (0.0, 0.5, 0.75, 1.0)
    runs = {}
    for lam in treatments:
        raw = _scaled_seed(control_seed, lam)
        if lam == 1.0:
            calibrated = control_seed.copy()
            calibration = {
                "rule": "control geography; no calibration required",
                "targetCentralWeightedPrimary": target,
                "candidateBeforeCalibration": target,
                "candidateAfterCalibration": target,
                "additiveLogitOffset": 0.0,
                "absoluteResidualPercentagePoints": 0.0,
            }
        else:
            calibrated, calibration = conserve_central_onp_primary(model_root, config, raw, control_seed)
        result = _run_with_seed(model_root, calibrated, simulations=simulations, seed=seed_value)
        runs[lam] = _summary(result, calibrated, calibration)
    control = runs[1.0]
    return {
        "schemaVersion": 3,
        "mode": "onp-geography-shadow-sensitivity-only",
        "asOf": str(config["as_of"]),
        "simulationsPerTreatment": simulations,
        "seed": seed_value,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "sourceSurface": "existing AEC_2022_ecological_auxiliary",
        "centralVoteConservation": True,
        "controlLambda": 1.0,
        "treatments": {str(lam): runs[lam] for lam in treatments},
        "comparisonsVsCurrent": {str(lam): _compare(control, runs[lam]) for lam in treatments if lam != 1.0},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--simulations", type=int, default=5000)
    parser.add_argument("--output", default="model/data/validation/onp-geography-shadow-2022-surface.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = run_shadow(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(f"ONP geography shadow is stale: regenerate {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
    print(f"ONP geography shadow complete: {args.simulations} simulations x 4 treatments; central ONP vote conserved; canonical artefacts untouched.")


if __name__ == "__main__":
    main()
