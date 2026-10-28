#!/usr/bin/env python3
"""Fit preregistered operational OTH-to-OTH retention distributions.

This script implements the fitting stage of the 29 October candidate-resolution
IRV protocol.  It reads only the official-VEC effective elimination-parcel audit
and the preregistration.  Historical winners/final pairs and all 2026 forecast
outputs are deliberately outside this stage.

`q_oth` is an operational elimination-stage quantity.  Mixed parcels are never
relabelled as original voter preferences.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PREREG = ROOT / "metadata/candidate-resolution-irv-preregistration-2026-10-29.json"
TARGET_TRAINING = {
    2014: (2010,),
    2018: (2010, 2014),
    2022: (2010, 2014, 2018),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def eligible_event(event: dict) -> bool:
    if event.get("source_family") != "OTH_IND":
        return False
    parcel = float(event.get("parcel_votes") or 0)
    if parcel <= 0:
        return False
    destination_counts = event.get("destination_candidate_count") or {}
    if int(destination_counts.get("OTH_IND") or 0) < 1:
        return False
    within = float(event.get("within_source_family_votes") or 0)
    if within < 0 or within > parcel:
        raise ValueError(
            f"invalid within-family transfer {within} / {parcel} in "
            f"{event.get('election_year')} {event.get('district_name')}"
        )
    return True


def unit_table(events: list[dict]) -> list[dict]:
    grouped: dict[tuple[int, str], list[float]] = defaultdict(list)
    names: dict[tuple[int, str], str] = {}
    for event in events:
        if not eligible_event(event):
            continue
        year = int(event["election_year"])
        did = str(event["district_id"])
        key = (year, did)
        grouped[key].append(float(event["within_source_family_votes"]) / float(event["parcel_votes"]))
        names[key] = str(event.get("district_name") or did)
    return [
        {
            "electionYear": year,
            "districtId": did,
            "districtName": names[(year, did)],
            "eligibleEvents": len(values),
            "meanEventRetention": float(np.mean(values)),
        }
        for (year, did), values in sorted(grouped.items())
    ]


def fit_target(
    target: int,
    training_years: tuple[int, ...],
    events: list[dict],
    units: list[dict],
    prereg: dict,
    rng: np.random.Generator,
) -> dict:
    eligible = [e for e in events if eligible_event(e) and int(e["election_year"]) in training_years]
    train_units = [u for u in units if int(u["electionYear"]) in training_years]
    minimum_events = int(prereg["qOth"]["minimumEligibleEvents"])
    minimum_units = int(prereg["qOth"]["minimumDistrictElectionUnits"])
    draws_n = int(prereg["qOth"]["bootstrapDraws"])
    identified = len(eligible) >= minimum_events and len(train_units) >= minimum_units

    result = {
        "targetYear": target,
        "trainingYears": list(training_years),
        "eligibleEvents": len(eligible),
        "districtElectionUnits": len(train_units),
        "identified": identified,
        "minimumEligibleEvents": minimum_events,
        "minimumDistrictElectionUnits": minimum_units,
        "eventsByYear": {
            str(year): sum(int(e["election_year"]) == year for e in eligible)
            for year in training_years
        },
        "unitsByYear": {
            str(year): sum(int(u["electionYear"]) == year for u in train_units)
            for year in training_years
        },
    }
    if not identified:
        result["bootstrapDraws"] = []
        result["summary"] = None
        return result

    values = np.asarray([u["meanEventRetention"] for u in train_units], dtype=float)
    draws = np.empty(draws_n, dtype=float)
    for i in range(draws_n):
        sampled = rng.integers(0, len(values), size=len(values))
        draws[i] = float(np.mean(values[sampled]))
    result["summary"] = {
        "unitMean": float(values.mean()),
        "unitSd": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "bootstrapMean": float(draws.mean()),
        "bootstrapSd": float(draws.std(ddof=1)) if len(draws) > 1 else 0.0,
        "q05": float(np.quantile(draws, 0.05)),
        "q25": float(np.quantile(draws, 0.25)),
        "q50": float(np.quantile(draws, 0.50)),
        "q75": float(np.quantile(draws, 0.75)),
        "q95": float(np.quantile(draws, 0.95)),
        "minimum": float(draws.min()),
        "maximum": float(draws.max()),
    }
    result["bootstrapDraws"] = draws.tolist()
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--preregistration", type=Path, default=DEFAULT_PREREG)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    evidence = load_json(args.evidence)
    prereg = load_json(args.preregistration)
    if prereg.get("status") != "preregistered-before-r1-fit-or-score":
        raise ValueError("candidate-resolution preregistration is not in the expected frozen state")
    if prereg.get("r1", {}).get("fitNewCrossFamilyMeans") is not False:
        raise ValueError("preregistration unexpectedly permits cross-family mean fitting")
    if evidence.get("guardrails", {}).get("official_vec_only") is not True:
        raise ValueError("effective-transfer evidence is not marked official-VEC-only")
    if evidence.get("guardrails", {}).get("uses_2026_forecast_output") is not False:
        raise ValueError("effective-transfer evidence may read 2026 forecast output")

    events = list(evidence.get("events") or [])
    units = unit_table(events)
    rng = np.random.default_rng(int(prereg["qOth"]["bootstrapSeed"]))
    targets = [
        fit_target(target, years, events, units, prereg, rng)
        for target, years in TARGET_TRAINING.items()
    ]

    payload = {
        "schemaVersion": 1,
        "status": "pre-outcome-walk-forward-operational-fit",
        "parameter": "q_oth_effective_same-family-retention",
        "interpretation": (
            "Operational elimination-stage retention among continuing OTH/Independent candidates. "
            "Later mixed parcels are not original voter preference observations."
        ),
        "evidenceSha256": sha256(args.evidence),
        "preregistrationSha256": sha256(args.preregistration),
        "bootstrapSeed": int(prereg["qOth"]["bootstrapSeed"]),
        "bootstrapDrawsPerTarget": int(prereg["qOth"]["bootstrapDraws"]),
        "eligibleUnitRule": prereg["qOth"]["unit"],
        "guardrails": {
            "historicalOutcomesRead": False,
            "uses2026ForecastOutput": False,
            "fitsCrossFamilyMeans": False,
            "ballotWeightedPseudoSample": False,
        },
        "eligibleUnitsAllCycles": units,
        "targets": targets,
    }
    if not all(target["identified"] for target in targets):
        payload["status"] = "identification-gate-failed-for-one-or-more-targets"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "targets": [
            {
                "targetYear": target["targetYear"],
                "identified": target["identified"],
                "eligibleEvents": target["eligibleEvents"],
                "districtElectionUnits": target["districtElectionUnits"],
                "summary": target["summary"],
            }
            for target in targets
        ],
        "output": str(args.output),
        "sha256": sha256(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
