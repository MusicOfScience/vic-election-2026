#!/usr/bin/env python3
"""Run the preregistered 2026 ONP frozen-persistence Assembly shadow.

The challenger consumes only the amended, checksummed joint persistence mixture
frozen before this runner was added. Control and challenger share common random
numbers; the only treatment difference is the ONP local spatial field.

This script never writes canonical forecast artefacts and does not read held-out
2026 seat polling or analyst/campaign seat calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import vicforecast.forecast_2026 as forecast_module
from vicforecast.forecast_2026 import (
    ASSEMBLY_2022_TARGET,
    PARTIES,
    PREFERENCE_PRIOR,
    _count_irv,
    build_assembly_seed,
    fit_latent_poll_state,
)

from onp_geography_shadow_common import _by_election_boosts, central_weighted_onp_primary
from run_onp_2025_residual_retention_shadow import _decomposition


FREEZE_PATH = "metadata/onp-spatial-persistence-freeze-v2-2026-10-28.json"
MIXTURE_PATH = "model/data/validation/onp-spatial-persistence-mixture.csv"
PERSISTENCE_SEED = 20261028
SIMULATIONS = 5000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_frozen_mixture(repo_root: Path, simulations: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    freeze_path = repo_root / FREEZE_PATH
    mixture_path = repo_root / MIXTURE_PATH
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("status") != "frozen-pre-2026-seat-run-amended":
        raise ValueError("amended persistence freeze is missing or not frozen")
    expected = freeze["mixture"]
    actual_sha = _sha256(mixture_path)
    if actual_sha != expected["sha256"]:
        raise ValueError(f"persistence mixture hash mismatch: {actual_sha} != {expected['sha256']}")
    mixture = pd.read_csv(mixture_path)
    if len(mixture) != int(expected["draws"]):
        raise ValueError("persistence mixture row count differs from frozen metadata")
    if not mixture[["aTarget", "kappaTarget"]].apply(lambda s: s.between(0, 1).all()).all():
        raise ValueError("persistence mixture contains values outside [0,1]")
    rng = np.random.default_rng(PERSISTENCE_SEED)
    indices = rng.integers(0, len(mixture), size=simulations)
    selected = mixture.iloc[indices].reset_index(drop=True).copy()
    selected.insert(0, "simulation", np.arange(simulations))
    selected["mixtureRow"] = indices
    return mixture, selected, freeze


def _control_local_pattern(districts: pd.DataFrame, config: dict) -> np.ndarray:
    assembly = config["assembly"]
    baseline_state = ASSEMBLY_2022_TARGET / 100.0
    base = districts.loc[:, PARTIES].to_numpy(float)
    local_pattern = np.log(np.clip(base, .002, None) / baseline_state)
    limits = np.array([float(assembly["local_logit_limits"][party]) for party in PARTIES])
    local_pattern = np.clip(local_pattern, -limits, limits)
    local_pattern[:, 2] = districts.onp_local_log.to_numpy(float)
    greens_limit = float(assembly["greens_local_logit_limit"])
    local_pattern[:, 3] = np.clip(
        local_pattern[:, 3] * float(assembly["greens_local_pattern_multiplier"]),
        -greens_limit,
        greens_limit,
    )
    return local_pattern


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    values = np.exp(shifted)
    return values / values.sum(axis=1, keepdims=True)


def _central_candidate_calibration(
    model_root: Path,
    config: dict,
    districts: pd.DataFrame,
    control_local: np.ndarray,
    raw_candidate_onp: np.ndarray,
) -> tuple[np.ndarray, dict]:
    """Vectorised common-intercept solve for every persistence draw."""
    target = central_weighted_onp_primary(model_root, config, districts)
    manifest = json.loads((model_root / "data/processed/experimental_forecast_2026.json").read_text())
    mean = manifest["polling"]["mean"]
    state = np.array([float(mean[p]) / 100.0 for p in PARTIES])
    boosts = _by_election_boosts(model_root, config, districts)
    weights = districts.enrolled_electors.to_numpy(float)
    weights /= weights.sum()

    other_logits = np.log(np.clip(state, 1e-6, None))[None, :] + control_local + boosts
    other_exp = np.exp(other_logits)
    other_sum = other_exp.sum(axis=1) - other_exp[:, 2]
    base_onp = np.log(max(state[2], 1e-6)) + raw_candidate_onp + boosts[:, 2][None, :]

    def evaluate(offsets: np.ndarray) -> np.ndarray:
        onp_exp = np.exp(base_onp + offsets[:, None])
        share = onp_exp / (other_sum[None, :] + onp_exp)
        return share @ weights

    zero = np.zeros(raw_candidate_onp.shape[0])
    before = evaluate(zero)
    low = np.full_like(zero, -2.0)
    high = np.full_like(zero, 2.0)
    if np.any(evaluate(low) > target) or np.any(evaluate(high) < target):
        raise ValueError("central ONP conservation target is not bracketed for all persistence draws")
    for _ in range(70):
        mid = (low + high) / 2.0
        value = evaluate(mid)
        mask = value < target
        low[mask] = mid[mask]
        high[~mask] = mid[~mask]
    offsets = (low + high) / 2.0
    after = evaluate(offsets)
    calibrated = raw_candidate_onp + offsets[:, None]
    return calibrated, {
        "rule": "one common additive ONP logit intercept solved separately for each frozen persistence draw at the canonical statewide latent mean",
        "targetCentralWeightedPrimaryPct": float(target * 100.0),
        "candidateBeforePct": {
            "mean": float(before.mean() * 100.0),
            "min": float(before.min() * 100.0),
            "max": float(before.max() * 100.0),
        },
        "additiveOffset": {
            "mean": float(offsets.mean()),
            "min": float(offsets.min()),
            "max": float(offsets.max()),
        },
        "maximumAbsoluteResidualPercentagePoints": float(np.max(np.abs(after - target)) * 100.0),
    }


def _init_accumulator(district_count: int, simulations: int) -> dict:
    return {
        "wins": np.zeros((district_count, len(PARTIES)), dtype=int),
        "primary_sum": np.zeros((district_count, len(PARTIES)), dtype=float),
        "pairs": [dict() for _ in range(district_count)],
        "chamber": np.zeros((simulations, len(PARTIES)), dtype=int),
    }


def _record(acc: dict, primaries: np.ndarray, pref: np.ndarray, simulation: int) -> None:
    acc["primary_sum"] += primaries
    for d in range(len(primaries)):
        winner, pair = _count_irv(primaries[d], pref)
        acc["wins"][d, winner] += 1
        acc["chamber"][simulation, winner] += 1
        label = "–".join(PARTIES[x] for x in pair)
        acc["pairs"][d][label] = acc["pairs"][d].get(label, 0) + 1


def _summarise(acc: dict, districts: pd.DataFrame, simulations: int) -> dict:
    chamber = acc["chamber"]
    party_summary = {}
    for j, party in enumerate(PARTIES):
        values = chamber[:, j]
        party_summary[party] = {
            "meanSeats": float(values.mean()),
            "medianSeats": float(np.median(values)),
            "lower80": float(np.quantile(values, .1)),
            "upper80": float(np.quantile(values, .9)),
            "majorityProbability": float((values >= 45).mean()),
        }
    hung = float((chamber.max(axis=1) < 45).mean())
    district_summary = {}
    for i, row in districts.iterrows():
        probabilities = acc["wins"][i] / simulations
        pair = max(acc["pairs"][i], key=acc["pairs"][i].get)
        district_summary[str(row.district_name)] = {
            "favouredParty": PARTIES[int(np.argmax(acc["wins"][i]))],
            "favouredProbability": float(probabilities.max()),
            "likelyFinalPair": pair,
            "finalPairProbability": float(acc["pairs"][i][pair] / simulations),
            "primaryONP": float(acc["primary_sum"][i, 2] / simulations * 100.0),
            "winONP": float(probabilities[2]),
        }
    return {"parties": party_summary, "hungProbability": hung, "districts": district_summary}


def _compare(control: dict, challenger: dict) -> dict:
    rows = []
    for district, current in control["districts"].items():
        other = challenger["districts"][district]
        rows.append({
            "district": district,
            "deltaPrimaryONP": other["primaryONP"] - current["primaryONP"],
            "deltaWinONP": other["winONP"] - current["winONP"],
            "modalWinnerChanged": other["favouredParty"] != current["favouredParty"],
            "modalFinalPairChanged": other["likelyFinalPair"] != current["likelyFinalPair"],
        })
    ranked = sorted(rows, key=lambda row: abs(row["deltaWinONP"]), reverse=True)
    return {
        "deltaHungProbability": challenger["hungProbability"] - control["hungProbability"],
        "partyDeltas": {
            party: {
                "meanSeats": challenger["parties"][party]["meanSeats"] - control["parties"][party]["meanSeats"],
                "majorityProbability": challenger["parties"][party]["majorityProbability"] - control["parties"][party]["majorityProbability"],
            }
            for party in PARTIES
        },
        "modalWinnerChanges": [row["district"] for row in rows if row["modalWinnerChanged"]],
        "modalFinalPairChanges": [row["district"] for row in rows if row["modalFinalPairChanged"]],
        "seatsWithOnpWinProbabilityShiftAtLeast5pp": int(sum(abs(row["deltaWinONP"]) >= .05 for row in rows)),
        "seatsWithOnpWinProbabilityShiftAtLeast10pp": int(sum(abs(row["deltaWinONP"]) >= .10 for row in rows)),
        "largestOnpWinProbabilityChanges": ranked[:25],
    }


def _regime_summary(chamber: np.ndarray, selected: pd.DataFrame) -> dict:
    output = {}
    for regime in sorted(selected.sourceTriplet.unique()):
        mask = selected.sourceTriplet.eq(regime).to_numpy()
        draws = chamber[mask]
        output[regime] = {
            "simulationCount": int(mask.sum()),
            "meanSeats": {party: float(draws[:, j].mean()) for j, party in enumerate(PARTIES)},
            "majorityProbability": {
                "ALP": float((draws[:, 0] >= 45).mean()),
                "LIB_NAT": float((draws[:, 1] >= 45).mean()),
            },
            "hungProbability": float((draws.max(axis=1) < 45).mean()),
        }
    return output


def _realised_persistence(selected: pd.DataFrame) -> dict:
    def stats(column: str) -> dict:
        values = selected[column].to_numpy(float)
        return {
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "q05": float(np.quantile(values, .05)),
            "q25": float(np.quantile(values, .25)),
            "q75": float(np.quantile(values, .75)),
            "q95": float(np.quantile(values, .95)),
        }
    return {
        "selectionSeed": PERSISTENCE_SEED,
        "sampling": "with replacement from frozen mixture row order",
        "aTarget": stats("aTarget"),
        "kappaTarget": stats("kappaTarget"),
        "aKappaCorrelation": float(np.corrcoef(selected.aTarget, selected.kappaTarget)[0, 1]),
        "sourceTripletCounts": {str(k): int(v) for k, v in selected.sourceTriplet.value_counts().sort_index().items()},
    }


def run_shadow(repo_root: Path, simulations: int) -> dict:
    if simulations != SIMULATIONS:
        raise ValueError(f"protocol requires exactly {SIMULATIONS} simulations")
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed = int(config["seed"])
    assembly = config["assembly"]

    _, selected, freeze = _load_frozen_mixture(repo_root, simulations)
    districts = build_assembly_seed(model_root, config).copy()
    x, residual, current_centre, _, diagnostics = _decomposition(model_root, districts)
    beta = float(diagnostics["weightedSlope2025On2022"])
    persistent_2025 = beta * x
    raw_candidate_onp = (
        current_centre
        + selected.aTarget.to_numpy(float)[:, None] * persistent_2025[None, :]
        + selected.kappaTarget.to_numpy(float)[:, None] * residual[None, :]
    )

    control_local = _control_local_pattern(districts, config)
    candidate_onp, calibration = _central_candidate_calibration(
        model_root, config, districts, control_local, raw_candidate_onp
    )

    events = pd.read_csv(model_root / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(model_root / "data/processed/poll_estimates_seed.csv")
    polling = config["polling"]
    poll = fit_latent_poll_state(
        events,
        estimates,
        as_of=config["as_of"],
        draws=simulations,
        seed=seed,
        half_life_days=float(polling["half_life_days"]),
        effective_sample_cap=int(polling["effective_sample_cap"]),
        systematic_floor=float(polling["systematic_floor"]),
    )

    boosts = _by_election_boosts(model_root, config, districts)
    region_names = sorted(districts.region_name.dropna().unique())
    region_index = {name: i for i, name in enumerate(region_names)}
    district_regions = np.array([region_index.get(x, 0) for x in districts.region_name])
    rng = np.random.default_rng(seed + 1)
    control_acc = _init_accumulator(len(districts), simulations)
    candidate_acc = _init_accumulator(len(districts), simulations)

    for s in range(simulations):
        state = poll.draws[s] / 100.0
        region_shock = rng.normal(0, float(assembly["region_shock_sd"]), size=(len(region_names), len(PARTIES)))
        local_shock = rng.normal(0, float(assembly["district_shock_sd"]), size=(len(districts), len(PARTIES)))
        common = np.log(np.clip(state, 1e-6, None)) + region_shock[district_regions] + local_shock + boosts
        control_logits = common + control_local
        candidate_logits = control_logits.copy()
        candidate_logits[:, 2] += candidate_onp[s] - control_local[:, 2]
        control_primary = _softmax(control_logits)
        candidate_primary = _softmax(candidate_logits)
        pref = np.vstack([
            rng.dirichlet(np.maximum(row * float(assembly["preference_prior_concentration"]), .02))
            for row in PREFERENCE_PRIOR
        ])
        _record(control_acc, control_primary, pref, s)
        _record(candidate_acc, candidate_primary, pref, s)

    control = _summarise(control_acc, districts, simulations)
    challenger = _summarise(candidate_acc, districts, simulations)
    return {
        "schemaVersion": 1,
        "mode": "onp-frozen-historical-persistence-2026-shadow",
        "asOf": str(config["as_of"]),
        "simulations": simulations,
        "canonicalElectionSeed": seed,
        "persistenceSelectionSeed": PERSISTENCE_SEED,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "persistenceFreeze": {
            "path": FREEZE_PATH,
            "status": freeze["status"],
            "mixtureSha256": freeze["mixture"]["sha256"],
            "artifactDigest": freeze["workflowArtifactDigest"],
        },
        "decomposition": {
            "formula": "delta_2025 = beta * delta_2022 + residual_2025; delta_2026_s = a_s * (beta * delta_2022) + kappa_s * residual_2025",
            **diagnostics,
        },
        "spatialUncertaintyLimitation": "No additional district epsilon term was preregistered; this is a lower-bound treatment of geography uncertainty conditional on the two-component historical persistence model.",
        "realisedPersistenceDraws": _realised_persistence(selected),
        "centralVoteCalibration": calibration,
        "control": control,
        "challenger": challenger,
        "comparisonVsCurrent": _compare(control, challenger),
        "challengerByHistoricalRegime": _regime_summary(candidate_acc["chamber"], selected),
        "governance": {
            "productionInput": False,
            "royMorganRead": False,
            "campaignSeatClaimsRead": False,
            "analystSeatCallsRead": False,
            "statewidePollingChanged": False,
            "preferenceModelChanged": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--simulations", type=int, default=SIMULATIONS)
    parser.add_argument("--output", default="model/data/validation/onp-frozen-persistence-2026-shadow.json")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    report = run_shadow(repo_root, args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "mode": report["mode"],
        "controlONP": report["control"]["parties"]["ONP"]["meanSeats"],
        "challengerONP": report["challenger"]["parties"]["ONP"]["meanSeats"],
        "controlHung": report["control"]["hungProbability"],
        "challengerHung": report["challenger"]["hungProbability"],
        "winnerChanges": len(report["comparisonVsCurrent"]["modalWinnerChanges"]),
        "finalPairChanges": len(report["comparisonVsCurrent"]["modalFinalPairChanges"]),
        "maxCentralVoteResidualPP": report["centralVoteCalibration"]["maximumAbsoluteResidualPercentagePoints"],
    }, indent=2))


if __name__ == "__main__":
    main()
