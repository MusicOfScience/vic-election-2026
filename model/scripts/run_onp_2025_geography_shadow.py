#!/usr/bin/env python3
"""Run the official-data AEC-2025 ONP geographic challenger against current geography.

Shadow research only. The canonical model files are never written. The runner
replaces only the district ONP spatial propensity returned by build_assembly_seed
and uses common random numbers with the current AEC-2022 control.
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


NEW_SURFACE = "data/validation/aec_2025_onp_state_district_surface.csv"
TREATMENTS = (0.50, 0.75, 1.00)


def _current_seed(model_root: Path, config: dict) -> pd.DataFrame:
    return forecast_module.build_assembly_seed(model_root, config).copy()


def _challenger_seed(model_root: Path, config: dict, lam: float) -> pd.DataFrame:
    seed = _current_seed(model_root, config)
    challenger = pd.read_csv(model_root / NEW_SURFACE)
    merged = seed[["district_name"]].merge(
        challenger[["district_name", "onp_log_ratio_to_located_state"]],
        on="district_name",
        how="left",
        validate="one_to_one",
    )
    if merged["onp_log_ratio_to_located_state"].isna().any() or len(merged) != len(seed):
        missing = merged.loc[merged["onp_log_ratio_to_located_state"].isna(), "district_name"].tolist()
        raise ValueError(f"2025 challenger is missing model districts: {missing}")

    weights = seed["enrolled_electors"].to_numpy(float)
    weights /= weights.sum()
    current = seed["onp_local_log"].to_numpy(float)
    current_centre = float(np.sum(current * weights))

    raw = merged["onp_log_ratio_to_located_state"].to_numpy(float)
    raw_centre = float(np.sum(raw * weights))
    centred = raw - raw_centre
    seed["onp_local_log"] = current_centre + float(lam) * centred
    return seed


def _run(model_root: Path, *, simulations: int, seed: int, challenger_lambda: float | None):
    config = forecast_module.load_forecast_config(model_root)
    replacement = (
        _current_seed(model_root, config)
        if challenger_lambda is None
        else _challenger_seed(model_root, config, challenger_lambda)
    )

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


def _summary(result, seed_frame: pd.DataFrame) -> dict:
    chamber = result.chamber.set_index("party")
    return {
        "hungProbability": float(result.chamber.hung_probability.iloc[0]),
        "weightedMeanDistrictOnpPrimary": _weighted_onp_primary(result, seed_frame),
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
        "deltaWeightedMeanDistrictOnpPrimary": (
            challenger["weightedMeanDistrictOnpPrimary"] - control["weightedMeanDistrictOnpPrimary"]
        ),
        "partyDeltas": {
            party: {
                "meanSeats": challenger["parties"][party]["meanSeats"] - control["parties"][party]["meanSeats"],
                "majorityProbability": (
                    challenger["parties"][party]["majorityProbability"]
                    - control["parties"][party]["majorityProbability"]
                ),
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
    seed = int(config["seed"])
    current_seed = _current_seed(model_root, config)
    control_result = _run(model_root, simulations=simulations, seed=seed, challenger_lambda=None)
    control = _summary(control_result, current_seed)

    treatments = {}
    comparisons = {}
    for lam in TREATMENTS:
        challenger_seed = _challenger_seed(model_root, config, lam)
        result = _run(model_root, simulations=simulations, seed=seed, challenger_lambda=lam)
        summary = _summary(result, challenger_seed)
        treatments[str(lam)] = summary
        comparisons[str(lam)] = _compare(control, summary)

    return {
        "schemaVersion": 1,
        "mode": "onp-aec-2025-geography-shadow",
        "asOf": str(config["as_of"]),
        "simulationsPerTreatment": simulations,
        "seed": seed,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "controlSurface": "existing AEC_2022_ecological_auxiliary",
        "challengerSurface": "AEC 2025 House ordinary polling-place geography mapped to current Assembly districts",
        "challengerLambdas": list(TREATMENTS),
        "centringRule": (
            "Each 2025 signal is enrolment-weight centred and shifted to the current surface's "
            "enrolment-weighted mean log propensity before lambda scaling."
        ),
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
    parser.add_argument(
        "--output",
        default="model/data/validation/onp-geography-shadow-2025-surface.json",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = run_shadow(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"AEC-2025 ONP geography shadow complete: {simulations} simulations x "
        f"{1 + len(TREATMENTS)} runs; canonical artefacts untouched."
    )


if __name__ == "__main__":
    main()
