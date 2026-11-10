#!/usr/bin/env python3
"""Four-cell, *unadmitted* 2026 Assembly sensitivity for ONP locality and preferences.

Frozen reference vintage: 31 Oct 2026, canonical polls/seed, same model engine.
Never writes a canonical election forecast, preference prior or approval record.
This is a mechanism stress test, not a calibrating backtest or a proposed
numerical replacement for the registered experimental forecast.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "model/src"))

import vicforecast.forecast_2026 as forecast  # noqa: E402

SCENARIOS = (
    ("reference", False, 72),
    ("onp_geography_bounded", True, 72),
    ("preferences_wider_stress", False, 4),
    ("bounded_plus_wider", True, 4),
)
INPUTS = (
    "model/config/experimental_forecast.yml",
    "model/constraints.txt",
    "model/src/vicforecast/forecast_2026.py",
    "model/src/vicforecast/polling/latent.py",
    "model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz",
    "model/data/processed/aec_2022_state_region_party_surface_vic.csv.gz",
    "model/data/processed/vec_2022_indicative_candidate_evidence.csv",
    "model/data/processed/vec_enrolment_district_2026-09-04.csv",
    "model/data/processed/vec_enrolment_region_2026-09-04.csv",
    "model/data/processed/district_region_membership_2026.csv",
    "model/data/processed/poll_events_seed.csv",
    "model/data/processed/poll_estimates_seed.csv",
    "model/data/processed/upper_house_region_poll_2026-08.csv",
    "model/data/seed/recent_state_by_elections.json",
    "metadata/accepted-polls-2026.json",
)
FOCUS = (
    "Greenvale", "Kororoit", "Sydenham", "Morwell", "Kalkallo", "Mill Park",
    "Pakenham", "Hawthorn", "Kew", "Benambra", "Ripon",
)


def fingerprint(repo: Path) -> dict:
    digests: dict[str, str] = {}
    h = hashlib.sha256()
    for relative in INPUTS:
        data = (repo / relative).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        digests[relative] = digest
        h.update(relative.encode())
        h.update(b"\x00")
        h.update(bytes.fromhex(digest))
        h.update(b"\x00")
    return {"combinedSha256": h.hexdigest(), "files": digests}


def bound_onp_geography(assembly_seed: pd.DataFrame, limit: float) -> pd.DataFrame:
    """Clip only the ONP federal-auxiliary log-odds pattern; preserve all others."""
    if not np.isfinite(limit) or not 0 < limit <= 1.2:
        raise ValueError("Invalid ONP locality bound")
    if "onp_local_log" not in assembly_seed.columns:
        raise ValueError("No verified AEC ONP auxiliary to bound")
    result = assembly_seed.copy(deep=True)
    before = result["onp_local_log"].to_numpy(dtype=float)
    if len(result) != 88 or not np.isfinite(before).all():
        raise ValueError("Unexpected AEC locality universe")
    result["onp_local_log"] = np.clip(before, -limit, limit)
    if not np.allclose(result.loc[:, list(forecast.PARTIES)],
                       assembly_seed.loc[:, list(forecast.PARTIES)]):
        raise ValueError("Assembly baseline changed while clipping ONP locality")
    return result


def load_registered_reference(repo: Path) -> tuple[dict, dict]:
    config = yaml.safe_load((repo / "model/config/experimental_forecast.yml").read_text())
    canonical = json.loads((repo / "model/data/processed/experimental_forecast_2026.json").read_text())
    if (config["as_of"] != "2026-10-31" or config["seed"] != 20260826 or
            canonical["as_of"] != config["as_of"] or
            canonical["seed"] != config["seed"] or
            canonical["status"] != "experimental_forecast" or
            float(config["assembly"]["local_logit_limits"]["ONP"]) != .45 or
            float(config["assembly"]["preference_prior_concentration"]) != 72 or
            canonical["production_compatible"] is not False):
        raise ValueError("Reference model vintage/config has changed; do not silently rebase shadow study")
    return config, canonical


def run_cell(repo: Path, configuration: dict, bounded: bool, concentration: int,
             simulations: int, seed: int) -> dict:
    config = deepcopy(configuration)
    config["assembly"]["preference_prior_concentration"] = concentration
    original_builder = forecast.build_assembly_seed

    def corrected_assembly_seed(root, config=None):
        base = original_builder(root, config)
        return bound_onp_geography(base, .45) if bounded else base

    # All interventions are in memory: the original Python model file,
    # canonical config, registered CSVs, and prospective archives stay intact.
    with patch.object(forecast, "load_forecast_config", return_value=config), \
         patch.object(forecast, "build_assembly_seed", side_effect=corrected_assembly_seed):
        result = forecast.run_experimental_forecast(repo / "model",
                                                   simulations=simulations, seed=seed)

    chamber = result.chamber.set_index("party")
    district = result.districts
    assert len(district) == 88 and np.isclose(chamber["mean"].sum(), 88.0, atol=1e-6)
    rows = []
    for _, row in district.iterrows():
        probabilities = {p: float(row[f"win_{p.lower()}"]) for p in forecast.PARTIES}
        if not np.isclose(sum(probabilities.values()), 1.0):
            raise ValueError("District simulation has invalid winner probability sum")
        rows.append({
            "district": str(row.district_name),
            "region": str(row.region_name),
            "winner": str(row.favoured_party),
            "winnerFrequency": float(row.favoured_probability),
            "winningFrequencies": probabilities,
            "modalPair": str(row.likely_final_pair),
            "modalPairFrequency": float(row.final_pair_probability),
            "oneNationPrimaryPercent": float(row.primary_onp),
        })
    rows.sort(key=lambda d: d["district"])
    return {
        "boundedOnpAuxiliary": bounded,
        "onpAuxiliaryEffectiveBound": [-.45, .45] if bounded else [-1.2, 1.1],
        "assemblyPreferenceConcentration": concentration,
        "chamberMeanSeats": {party: float(chamber.loc[party, "mean"]) for party in forecast.PARTIES},
        "chamberMedianSeats": {party: float(chamber.loc[party, "median"]) for party in forecast.PARTIES},
        "chamber80PercentRange": {party: [float(chamber.loc[party, "lower80"]),
                                               float(chamber.loc[party, "upper80"])]
                                 for party in forecast.PARTIES},
        "majorityFrequency": {
            "ALP": float(chamber.loc["ALP", "majority_probability"]),
            "LIB_NAT": float(chamber.loc["LIB_NAT", "majority_probability"]),
        },
        "hungFrequency": float(chamber["hung_probability"].iloc[0]),
        "oneNationSeatsAtOrAbove80Percent": sum(r["winningFrequencies"]["ONP"] >= .8 for r in rows),
        "districts": rows,
    }


def compare_cells(cells: dict) -> dict:
    baseline = cells["reference"]
    scenarios = {}
    for name, state in cells.items():
        if name == "reference":
            continue
        previous = {x["district"]: x for x in baseline["districts"]}
        shifts = []
        for d in state["districts"]:
            old = previous[d["district"]]
            delta = {party: d["winningFrequencies"][party] - old["winningFrequencies"][party]
                     for party in forecast.PARTIES}
            shifts.append({
                "district": d["district"],
                "oldWinner": old["winner"],
                "newWinner": d["winner"],
                "modalWinnerChanged": old["winner"] != d["winner"],
                "deltaWinProbability": delta,
                "largestAbsoluteShift": max(abs(x) for x in delta.values()),
                "oldOnpPrimaryPercent": old["oneNationPrimaryPercent"],
                "newOnpPrimaryPercent": d["oneNationPrimaryPercent"],
                "oldOnpWinFrequency": old["winningFrequencies"]["ONP"],
                "newOnpWinFrequency": d["winningFrequencies"]["ONP"],
            })
        shifts.sort(key=lambda x: (-x["largestAbsoluteShift"], x["district"]))
        scenarios[name] = {
            "deltaMeanSeats": {p: state["chamberMeanSeats"][p] - baseline["chamberMeanSeats"][p]
                               for p in forecast.PARTIES},
            "deltaHungFrequency": state["hungFrequency"] - baseline["hungFrequency"],
            "deltaCoalitionMajorityFrequency": state["majorityFrequency"]["LIB_NAT"] -
                                               baseline["majorityFrequency"]["LIB_NAT"],
            "changedModalWinners": [r for r in shifts if r["modalWinnerChanged"]],
            "districtsWithAtLeastFivePointWinFrequencyShift": sum(
                r["largestAbsoluteShift"] >= .05 for r in shifts),
            "largestShifts": shifts[:20],
            "allDistrictShifts": shifts,
        }

    interaction = {}
    for p in forecast.PARTIES:
        interaction[p] = (cells["bounded_plus_wider"]["chamberMeanSeats"][p]
                          - cells["onp_geography_bounded"]["chamberMeanSeats"][p]
                          - cells["preferences_wider_stress"]["chamberMeanSeats"][p]
                          + baseline["chamberMeanSeats"][p])
    return {
        "reference": {
            "meanSeats": baseline["chamberMeanSeats"],
            "majorityFrequency": baseline["majorityFrequency"],
            "hungFrequency": baseline["hungFrequency"],
            "onpSeatsAtOrAbove80Percent": baseline["oneNationSeatsAtOrAbove80Percent"]
        },
        "scenarios": scenarios,
        "factorInteractionMeanSeats": interaction,
        "focusDistricts": {
            seat: {
                case: next(d for d in run["districts"] if d["district"] == seat)
                for case, run in cells.items()
            } for seat in FOCUS
        }
    }


def run_experiment(repo: Path = REPO, *, simulations: int = 2000, seed: int = 20260826) -> dict:
    if simulations < 100 or simulations > 20000:
        raise ValueError("Simulation count must be 100–20000")
    if seed != 20260826:
        raise ValueError("Use preregistered forecast random seed")
    config, manifest = load_registered_reference(repo)
    before = fingerprint(repo)
    cells = {}
    for name, bound, concentration in SCENARIOS:
        cells[name] = run_cell(repo, config, bound, concentration, simulations, seed)
        print(json.dumps({
            "scenario": name, "meanSeats": cells[name]["chamberMeanSeats"],
            "hung": cells[name]["hungFrequency"],
            "onp80": cells[name]["oneNationSeatsAtOrAbove80Percent"]
        }, sort_keys=True), flush=True)
    after = fingerprint(repo)
    if before != after:
        raise RuntimeError("Canonical source/input files changed during review-only experiment")
    return {
        "schemaVersion": 1,
        "status": "SHADOW_ONLY_NO_MODEL_ADMISSION_NO_PRODUCTION_AUTHORITY",
        "sourceAsOf": config["as_of"],
        "electionDate": config["election_date"],
        "referenceForecastId": manifest["forecast_id"],
        "referenceSimulationCount": manifest["simulations"],
        "shadowSimulationCountPerCase": simulations,
        "seed": seed,
        "runCompletedAtUtc": datetime.now(timezone.utc).isoformat(),
        "sourceFingerprint": before,
        "design": {
            "cells": [c[0] for c in SCENARIOS],
            "factors": {
                "onpLocality": ["current special AEC cap -1.20/+1.10", "explicit clip -0.45/+0.45"],
                "assemblyPreferenceConcentration": [72, 4]
            },
            "fixed": "31 Oct frozen poll registry, preference mean matrix, 2022 baseline, other geographic patterns, 2026 election date, 20260826 seed",
            "control": "Same random seed and run size; stochastic Dirichlet generation is NOT asserted to give strict common-random-number pairing across different concentration parameters.",
            "comparability": "The sample-matched 2000-draw shadow reference is the comparator for all three interventions, NOT the separate official 5000-draw published snapshot.",
            "council": "Council was simulated by the original joint engine but intentionally NOT interpreted here: parameter changes can advance the pseudorandom stream, producing irrelevant downstream Council Monte Carlo differences.",
            "caveat": "Stress-test concentration=4 came from historical candidate-resolved research; this is the unchanged five-family model, so historical production validation of concentration 4 does not transfer.",
            "effectIdentification": "Controlled conditional sensitivity within one assumed architecture, not observed election effects, empirically calibrated win probabilities or causal proof of a real-world mechanism."
        },
        "baselineReferenceComparison": {
            "published5000DrawMeanSeats": {"ALP": 34.4074, "LIB_NAT": 35.7782,
                                             "ONP": 15.3608, "GRN": 2.443, "OTH_IND": .0106},
            "note": "Published reference used 5000 draws, so a smaller simulation reference should differ modestly from pure Monte Carlo uncertainty; not a numerical identity test."
        },
        "results": compare_cells(cells),
        "candidateMask": "No candidate-resolved ballot-mask run. All districts have a candidate from all five families, but distinct minor/independent candidates are still aggregated.",
        "permissions": {"newPollsAdmitted": False, "canonicalForecastModified": False,
                         "candidateRegistryModified": False,
                         "prospectiveRegistrationChanged": False,
                         "productionGatesChanged": False}
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to((REPO / "model/data").resolve()) or \
       args.output.resolve().is_relative_to((REPO / "metadata").resolve()):
        raise ValueError("Review-only output must not overwrite model or metadata files")
    result = run_experiment(simulations=args.simulations, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": str(args.output),
                      "sourceAsOf": result["sourceAsOf"],
                      "cases": list(result["results"]["scenarios"])}), flush=True)


if __name__ == "__main__":
    main()
