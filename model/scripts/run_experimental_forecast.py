#!/usr/bin/env python3
"""Generate auditable experimental forecast artefacts for the website."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from vicforecast.forecast_2026 import PARTIES, run_experimental_forecast


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--simulations", type=int)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    root = args.root.resolve()
    out = root / "data/processed"
    config = yaml.safe_load((root / "config/experimental_forecast.yml").read_text())
    simulations = args.simulations or int(config["simulations"])
    seed = args.seed or int(config["seed"])
    forecast = run_experimental_forecast(root, simulations=simulations, seed=seed)
    files = {
        "districts": out / "experimental_forecast_2026_districts.csv",
        "chamber": out / "experimental_forecast_2026_chamber.csv",
        "seat_distribution": out / "experimental_forecast_2026_seat_distribution.csv",
        "council_regions": out / "experimental_forecast_2026_council_regions.csv",
        "council": out / "experimental_forecast_2026_council.csv",
    }
    forecast.districts.to_csv(files["districts"], index=False)
    forecast.chamber.to_csv(files["chamber"], index=False)
    forecast.seat_distribution.to_csv(files["seat_distribution"], index=False)
    forecast.council_regions.to_csv(files["council_regions"], index=False)
    forecast.council.to_csv(files["council"], index=False)
    poll = forecast.poll_state
    manifest = {
        "forecast_id": "vic_2026_experimental_joint_v1",
        "status": "experimental_forecast",
        "production_compatible": False,
        "as_of": poll.as_of.isoformat(),
        "simulations": forecast.simulations,
        "seed": forecast.seed,
        "party_order": list(PARTIES),
        "polling": {"poll_count": poll.poll_count, "mean": poll.mean, "median": poll.median,
                    "lower80": poll.lower80, "upper80": poll.upper80,
                    "house_effects": poll.house_effects,
                    "sensitivity_by_half_life_days": forecast.poll_sensitivity,
                    "model": "empirical_bayes_logistic_normal"},
        "assembly": {"model": "correlated_multi_party_irv", "districts": len(forecast.districts),
                     "hung_probability": float(forecast.chamber.hung_probability.iloc[0])},
        "council": {"model": "voter_directed_group_stv_approximation", "regions": len(forecast.council_regions),
                    "members_per_region": 5, "candidate_order_forecast": False},
        "assumptions": {"polling": forecast.assumptions["polling"],
                        "assembly": forecast.assumptions["assembly"],
                        "config_path": "config/experimental_forecast.yml",
                        "config_sha256": _hash(root / "config/experimental_forecast.yml")},
        "governance": {"demographic_residual_weight": 0,
                       "demographic_gate": "failed_sealed_four_cycle_promotion_test",
                       "aec_local_pattern_role": "derived_auxiliary_predictor",
                       "official_anchor": "VEC_2022"},
        "outputs": {},
    }
    manifest_path = out / "experimental_forecast_2026.json"
    for name, path in files.items():
        manifest["outputs"][name] = {"path": str(path.relative_to(root)), "sha256": _hash(path)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(manifest_path), "simulations": forecast.simulations,
                      "hung_probability": manifest["assembly"]["hung_probability"]}, indent=2))


if __name__ == "__main__":
    main()
