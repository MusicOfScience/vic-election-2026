#!/usr/bin/env python3
"""Run governed ONP geographic-persistence shadow sensitivities.

This runner does not write canonical forecast artefacts.  It scales the existing
AEC-2022 ecological ONP district propensity already used by the model and runs
common-random-number counterfactuals.  It is an infrastructure/sensitivity test,
not the proposed AEC-2025 challenger: the latter requires a separately
provenanced 2025 district surface before it can be evaluated.
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


def _scaled_seed(model_root: Path, config: dict, lam: float) -> pd.DataFrame:
    """Scale the existing ONP spatial deviation while preserving its weighted centre."""
    seed = forecast_module.build_assembly_seed(model_root, config).copy()
    raw = seed["onp_local_log"].to_numpy(float)
    weights = seed["enrolled_electors"].to_numpy(float)
    weights = weights / weights.sum()
    centre = float(np.sum(raw * weights))
    seed["onp_local_log"] = centre + float(lam) * (raw - centre)
    return seed


def _run(model_root: Path, *, simulations: int, seed: int, lam: float):
    config = forecast_module.load_forecast_config(model_root)
    scaled = _scaled_seed(model_root, config, lam)
    real_builder = forecast_module.build_assembly_seed

    def shadow_builder(root, config=None):
        return scaled.copy()

    with patch("vicforecast.forecast_2026.build_assembly_seed", side_effect=shadow_builder):
        result = run_experimental_forecast(model_root, simulations=simulations, seed=seed)
    # Defensive assertion: the patched builder must not mutate the stored seed.
    assert np.allclose(scaled["onp_local_log"], _scaled_seed(model_root, config, lam)["onp_local_log"])
    return result


def _summary(result) -> dict:
    chamber = result.chamber.set_index("party")
    districts = result.districts.copy()
    return {
        "hungProbability": float(result.chamber.hung_probability.iloc[0]),
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
        "partyDeltas": {
            party: {
                "meanSeats": challenger["parties"][party]["meanSeats"] - control["parties"][party]["meanSeats"],
                "majorityProbability": challenger["parties"][party]["majorityProbability"] - control["parties"][party]["majorityProbability"],
            }
            for party in PARTIES
        },
        "modalWinnerChanges": [name for name, row in seats.items() if row["modalWinnerChanged"]],
        "modalFinalPairChanges": [name for name, row in seats.items() if row["modalFinalPairChanged"]],
        "largestONPWinProbabilityChanges": [
            {"district": name, **row} for name, row in ranked[:20]
        ],
    }


def run_shadow(repo_root: Path, *, simulations: int) -> dict:
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed = int(config["seed"])
    # lambda=1 is the current model's AEC-2022 ONP geography treatment.
    treatments = (0.0, 0.5, 0.75, 1.0)
    runs = {lam: _summary(_run(model_root, simulations=simulations, seed=seed, lam=lam)) for lam in treatments}
    control = runs[1.0]
    return {
        "schemaVersion": 1,
        "mode": "onp-geography-shadow-sensitivity-only",
        "asOf": str(config["as_of"]),
        "simulationsPerTreatment": simulations,
        "seed": seed,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "sourceSurface": "existing AEC_2022_ecological_auxiliary",
        "importantLimitation": "This tests persistence/shrinkage of the geography already in PROD. It does not yet test the proposed AEC-2025 geography update.",
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
    print(f"ONP geography shadow complete: {simulations} simulations x 4 treatments; canonical artefacts untouched.")


if __name__ == "__main__":
    main()
