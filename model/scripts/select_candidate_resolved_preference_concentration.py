#!/usr/bin/env python3
"""Select candidate-resolved preference concentration using only allowed training cycles.

This is Gate A for PR #142. It reads 2014 and 2018 historical outcomes only as
specified by the preregistered walk-forward design. It never reads or generates
2022 target scores for model selection and never touches 2026 forecast outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "model/src"))

from score_candidate_resolved_irv_historical import (  # noqa: E402
    PARTIES,
    PREFERENCE_PRIOR,
    aggregate,
    count_r1,
    district_records,
    init_counts,
    load_candidate_states,
    load_exact_pair_signatures,
    load_outcomes,
    load_primaries,
    sha256,
)

DEFAULT_PREREG = ROOT / "metadata/candidate-resolution-preference-uncertainty-preregistration-2026-10-29.json"
DEFAULT_QOTH_FREEZE = ROOT / "metadata/candidate-resolution-irv-qoth-freeze-2026-10-29.json"
DEFAULT_R1_PREREG = ROOT / "metadata/candidate-resolution-irv-preregistration-2026-10-29.json"
TRAINING_YEARS = (2014, 2018)
ALLOCATIONS = ("equal", "proportional")


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def simulate_year(
    year: int,
    concentration: float,
    allocation: str,
    q_draws: np.ndarray,
    simulations: int,
    seed: int,
) -> tuple[dict, list[dict]]:
    family_primaries = load_primaries(year)
    outcomes = load_outcomes(year)
    candidate_states = load_candidate_states(year, family_primaries)
    exact_observed = load_exact_pair_signatures(year, outcomes)
    ids = sorted(set(family_primaries) & set(outcomes) & set(candidate_states))
    if len(q_draws) != simulations:
        raise ValueError(f"{year}: expected {simulations} q_oth draws, got {len(q_draws)}")

    counts = init_counts(ids)
    # Reset to the same seed for every grid point. This keeps the random stream
    # aligned across concentration treatments as far as numpy's gamma sampler permits.
    rng = np.random.default_rng(seed + year)
    for simulation in range(simulations):
        pref = np.vstack([
            rng.dirichlet(np.maximum(row * concentration, .02))
            for row in PREFERENCE_PRIOR
        ])
        q_oth = float(q_draws[simulation])
        any_oth = False
        for did in ids:
            state = candidate_states[did]
            winner, pair, exact_pair, oth_steps = count_r1(
                state["primary"],
                state["node_families"],
                state["node_labels"],
                pref,
                q_oth,
                allocation,
            )
            counts["winner"][did][winner] += 1
            counts["pair"][did][pair] += 1
            counts["exact_pair"][did][exact_pair] += 1
            counts["oth_to_oth_steps"] += oth_steps
            any_oth = any_oth or oth_steps > 0
        counts["simulations_with_oth_to_oth"] += int(any_oth)

    records = district_records(
        counts,
        ids,
        outcomes,
        exact_observed,
        simulations,
        include_exact=True,
    )
    return aggregate(records), records


def selection_objective(summary: dict) -> float:
    return 0.5 * float(summary["winnerMeanLogLoss"]) + 0.5 * float(summary["pairMeanLogLoss"])


def choose(grid_rows: list[dict], tie_tolerance: float) -> dict:
    best = min(float(row["objective"]) for row in grid_rows)
    eligible = [row for row in grid_rows if float(row["objective"]) <= best + tie_tolerance]
    selected = max(eligible, key=lambda row: float(row["concentration"]))
    return {
        "concentration": float(selected["concentration"]),
        "objective": float(selected["objective"]),
        "tieTolerance": tie_tolerance,
        "tieRule": "choose-higher-concentration",
    }


def pooled_summary(records_by_year: dict[int, list[dict]], years: tuple[int, ...]) -> dict:
    rows: list[dict] = []
    for year in years:
        rows.extend(records_by_year[year])
    return aggregate(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--preregistration", type=Path, default=DEFAULT_PREREG)
    ap.add_argument("--qoth-freeze", type=Path, default=DEFAULT_QOTH_FREEZE)
    ap.add_argument("--r1-preregistration", type=Path, default=DEFAULT_R1_PREREG)
    args = ap.parse_args()

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    qfreeze = json.loads(args.qoth_freeze.read_text(encoding="utf-8"))
    r1_prereg = json.loads(args.r1_preregistration.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))

    if prereg.get("status") != "preregistered-before-new-uncertainty-scoring":
        raise ValueError("preference-uncertainty protocol is not preregistered")
    if sha256(args.fit) != qfreeze["qOthFitSha256"]:
        raise ValueError("q_oth fit does not match the PR #140 pre-score freeze")
    if fit.get("guardrails", {}).get("historicalOutcomesRead") is not False:
        raise ValueError("q_oth fit is not outcome-isolated")

    grid = [float(x) for x in prereg["parameter"]["grid"]]
    if grid != [4.0, 8.0, 12.0, 18.0, 24.0, 36.0, 48.0, 72.0, 108.0, 144.0]:
        raise ValueError("concentration grid differs from frozen protocol")
    simulations = int(r1_prereg["r0"]["simulationsPerTarget"])
    seed = int(r1_prereg["r0"]["electionSeed"])
    tie_tolerance = float(prereg["walkForward"]["tieTolerance"])
    fit_by_target = {int(item["targetYear"]): item for item in fit["targets"]}

    all_scores: dict[str, list[dict]] = {}
    selections: dict[str, dict] = {}
    evidence_hashes: dict[str, dict] = {}

    for allocation in ALLOCATIONS:
        records_by_concentration: dict[float, dict[int, list[dict]]] = {}
        summaries_by_concentration: dict[float, dict[int, dict]] = {}
        for concentration in grid:
            records_by_concentration[concentration] = {}
            summaries_by_concentration[concentration] = {}
            for year in TRAINING_YEARS:
                q_target = fit_by_target[year]
                if not q_target["identified"]:
                    raise ValueError(f"{year}: q_oth identification gate failed")
                q_draws = np.asarray(q_target["bootstrapDraws"], dtype=float)
                summary, records = simulate_year(
                    year,
                    concentration,
                    allocation,
                    q_draws,
                    simulations,
                    seed,
                )
                records_by_concentration[concentration][year] = records
                summaries_by_concentration[concentration][year] = summary

        grid_rows_2018 = []
        grid_rows_2022 = []
        for concentration in grid:
            s2014 = summaries_by_concentration[concentration][2014]
            pooled = pooled_summary(records_by_concentration[concentration], (2014, 2018))
            grid_rows_2018.append({
                "concentration": concentration,
                "trainingYears": [2014],
                "summary": s2014,
                "objective": selection_objective(s2014),
            })
            grid_rows_2022.append({
                "concentration": concentration,
                "trainingYears": [2014, 2018],
                "summary": pooled,
                "perYear": {
                    "2014": summaries_by_concentration[concentration][2014],
                    "2018": summaries_by_concentration[concentration][2018],
                },
                "objective": selection_objective(pooled),
            })

        selection_2018 = choose(grid_rows_2018, tie_tolerance)
        selection_2022 = choose(grid_rows_2022, tie_tolerance)
        selection_2018["trainingYears"] = [2014]
        selection_2022["trainingYears"] = [2014, 2018]

        all_scores[allocation] = [
            {"targetYear": 2018, "grid": grid_rows_2018},
            {"targetYear": 2022, "grid": grid_rows_2022},
        ]
        selections[allocation] = {
            "2018": selection_2018,
            "2022": selection_2022,
        }
        evidence_hashes[allocation] = {
            "2018TrainingEvidenceSha256": canonical_hash(grid_rows_2018),
            "2022TrainingEvidenceSha256": canonical_hash(grid_rows_2022),
        }

    payload = {
        "schemaVersion": 1,
        "status": "preference-concentration-selected-before-heldout-target-score",
        "workstream": "candidate-resolution-preference-uncertainty",
        "simulationsPerTrainingCycle": simulations,
        "electionSeed": seed,
        "grid": grid,
        "qOthFitSha256": sha256(args.fit),
        "selectionObjective": prereg["walkForward"]["selectionObjective"],
        "trainingGridScores": all_scores,
        "selections": selections,
        "trainingEvidenceHashes": evidence_hashes,
        "guardrails": {
            "uses2022TargetOutcomeForSelection": False,
            "uses2026ForecastOutput": False,
            "uses2026SeatPolling": False,
            "modifiesPreferenceMeans": False,
            "modifiesCandidateResolutionArchitecture": False,
            "equalAndProportionalSelectedSeparatelyUnderFrozenRule": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selections": selections,
        "trainingEvidenceHashes": evidence_hashes,
        "output": str(args.output),
        "sha256": sha256(args.output),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
