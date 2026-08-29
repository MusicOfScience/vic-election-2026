#!/usr/bin/env python3
"""Run a full-election shadow comparison using staged polls without promotion.

This script never writes canonical model inputs or forecast artefacts. It runs the
existing forecast twice with common random numbers: once with the canonical poll
registry and once with DemosAU + Resolve temporarily injected in memory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from run_staged_poll_shadow import _estimate_rows, _event_row
from vicforecast.forecast_2026 import PARTIES, run_experimental_forecast


SHADOW_INPUT_PATHS = (
    "metadata/manual-source-evidence-2026.json",
    "metadata/research-source-evidence-2026.json",
    "model/config/experimental_forecast.yml",
    "model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz",
    "model/data/processed/aec_2022_state_region_party_surface_vic.csv.gz",
    "model/data/processed/district_region_membership_2026.csv",
    "model/data/processed/poll_estimates_seed.csv",
    "model/data/processed/poll_events_seed.csv",
    "model/data/processed/upper_house_region_poll_2026-08.csv",
    "model/data/processed/vec_2022_indicative_candidate_evidence.csv",
    "model/data/processed/vec_enrolment_district_2026-06.csv",
    "model/data/processed/vec_enrolment_region_2026-06.csv",
    "model/data/seed/recent_state_by_elections.json",
    "model/scripts/run_staged_poll_seat_shadow.py",
    "model/scripts/run_staged_poll_shadow.py",
    "model/src/vicforecast/forecast_2026.py",
    "model/src/vicforecast/polling/latent.py",
    "model/src/vicforecast/polling/registry.py",
)


def _input_fingerprint(repo_root: Path) -> dict:
    digest = hashlib.sha256()
    files = {}
    for relative in SHADOW_INPUT_PATHS:
        payload = (repo_root / relative).read_bytes()
        sha = hashlib.sha256(payload).hexdigest()
        files[relative] = sha
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return {"combinedSha256": digest.hexdigest(), "files": files}


def _load_staged(repo_root: Path) -> list[dict]:
    records: list[dict] = []
    for name in ("manual-source-evidence-2026.json", "research-source-evidence-2026.json"):
        payload = json.loads((repo_root / "metadata" / name).read_text())
        records.extend(record for record in payload.get("records", []) if record.get("kind") == "poll")
    by_pollster = {record["pollster"]: record for record in records}
    return [by_pollster["DemosAU"], by_pollster["Resolve Strategic"]]


def _scenario_registry(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_root = repo_root / "model"
    events = pd.read_csv(model_root / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(model_root / "data/processed/poll_estimates_seed.csv")
    for record in _load_staged(repo_root):
        events = pd.concat([events, pd.DataFrame([_event_row(record, list(events.columns))])], ignore_index=True)
        estimates = pd.concat([estimates, pd.DataFrame(_estimate_rows(record))], ignore_index=True)
    return events, estimates


def _run_with_registry(model_root: Path, events: pd.DataFrame, estimates: pd.DataFrame, *, simulations: int, seed: int):
    event_path = (model_root / "data/processed/poll_events_seed.csv").resolve()
    estimate_path = (model_root / "data/processed/poll_estimates_seed.csv").resolve()
    real_read_csv = pd.read_csv

    def shadow_read_csv(path, *args, **kwargs):
        try:
            resolved = Path(path).resolve()
        except TypeError:
            resolved = None
        if resolved == event_path:
            return events.copy()
        if resolved == estimate_path:
            return estimates.copy()
        return real_read_csv(path, *args, **kwargs)

    # forecast_2026 uses one pandas module object throughout, so patching this
    # read path provides an in-memory registry view while every other dataset is
    # read normally from the audited model root.
    with patch("vicforecast.forecast_2026.pd.read_csv", side_effect=shadow_read_csv):
        return run_experimental_forecast(model_root, simulations=simulations, seed=seed)


def _chamber_comparison(canonical: pd.DataFrame, shadow: pd.DataFrame, majority: int) -> dict:
    c = canonical.set_index("party")
    s = shadow.set_index("party")
    parties = {}
    for party in PARTIES:
        parties[party] = {
            "canonicalMeanSeats": float(c.loc[party, "mean"]),
            "shadowMeanSeats": float(s.loc[party, "mean"]),
            "deltaMeanSeats": float(s.loc[party, "mean"] - c.loc[party, "mean"]),
            "canonicalMedianSeats": float(c.loc[party, "median"]),
            "shadowMedianSeats": float(s.loc[party, "median"]),
            "canonicalMajorityProbability": float(c.loc[party, "majority_probability"]),
            "shadowMajorityProbability": float(s.loc[party, "majority_probability"]),
            "deltaMajorityProbability": float(s.loc[party, "majority_probability"] - c.loc[party, "majority_probability"]),
            "majorityThreshold": majority,
        }
    return parties


def _district_impact(canonical: pd.DataFrame, shadow: pd.DataFrame) -> dict:
    c = canonical.set_index("district_id")
    s = shadow.set_index("district_id")
    rows = []
    for district_id in c.index:
        deltas = {party: float(s.loc[district_id, f"win_{party.lower()}"] - c.loc[district_id, f"win_{party.lower()}"]) for party in PARTIES}
        driver = max(PARTIES, key=lambda party: abs(deltas[party]))
        canonical_favourite = str(c.loc[district_id, "favoured_party"])
        shadow_favourite = str(s.loc[district_id, "favoured_party"])
        rows.append({
            "districtId": district_id,
            "districtName": str(c.loc[district_id, "district_name"]),
            "canonicalFavourite": canonical_favourite,
            "shadowFavourite": shadow_favourite,
            "modalWinnerChanged": canonical_favourite != shadow_favourite,
            "largestShiftParty": driver,
            "largestWinProbabilityShift": deltas[driver],
            "absoluteLargestShift": abs(deltas[driver]),
            "winProbabilityDeltas": deltas,
            "canonicalFavouriteProbability": float(c.loc[district_id, f"win_{canonical_favourite.lower()}"]),
            "shadowFavouriteProbability": float(s.loc[district_id, f"win_{shadow_favourite.lower()}"]),
        })
    rows.sort(key=lambda row: row["absoluteLargestShift"], reverse=True)
    return {
        "modalWinnerChanges": [row for row in rows if row["modalWinnerChanged"]],
        "seatsWithFivePointOrLargerProbabilityShift": sum(row["absoluteLargestShift"] >= .05 for row in rows),
        "seatsWithTenPointOrLargerProbabilityShift": sum(row["absoluteLargestShift"] >= .10 for row in rows),
        "largestProbabilityShifts": rows[:20],
    }


def _council_region_impact(canonical: pd.DataFrame, shadow: pd.DataFrame) -> dict:
    c = canonical.set_index("region_id")
    s = shadow.set_index("region_id")
    rows = []
    for region_id in c.index:
        canonical_pattern = {party: int(c.loc[region_id, f"seats_{party.lower()}"]) for party in PARTIES}
        shadow_pattern = {party: int(s.loc[region_id, f"seats_{party.lower()}"]) for party in PARTIES}
        deltas = {party: float(s.loc[region_id, f"at_least_one_{party.lower()}"] - c.loc[region_id, f"at_least_one_{party.lower()}"]) for party in PARTIES}
        driver = max(PARTIES, key=lambda party: abs(deltas[party]))
        rows.append({
            "regionId": region_id,
            "regionName": str(c.loc[region_id, "region_name"]),
            "canonicalModalPattern": canonical_pattern,
            "shadowModalPattern": shadow_pattern,
            "modalPatternChanged": canonical_pattern != shadow_pattern,
            "largestAtLeastOneShiftParty": driver,
            "largestAtLeastOneProbabilityShift": deltas[driver],
            "absoluteLargestShift": abs(deltas[driver]),
            "atLeastOneProbabilityDeltas": deltas,
        })
    rows.sort(key=lambda row: row["absoluteLargestShift"], reverse=True)
    return {
        "modalPatternChanges": [row for row in rows if row["modalPatternChanged"]],
        "largestProbabilityShifts": rows,
    }


def build_impact_report(canonical, shadow, *, simulations: int, seed: int, as_of: str) -> dict:
    canonical_poll = canonical.poll_state.mean
    shadow_poll = shadow.poll_state.mean
    return {
        "schemaVersion": 1,
        "mode": "full-election-shadow-sensitivity-only",
        "asOf": as_of,
        "simulationsPerScenario": simulations,
        "seed": seed,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "scenarioEvidencePromoted": False,
        "policy": "This report is a counterfactual sensitivity test. Staged DemosAU and Resolve evidence is injected only in memory; it does not become accepted or model-eligible evidence and cannot update the published forecast.",
        "polling": {
            "canonicalPollCount": canonical.poll_state.poll_count,
            "shadowPollCount": shadow.poll_state.poll_count,
            "canonicalMean": {party: float(canonical_poll[party]) for party in PARTIES},
            "shadowMean": {party: float(shadow_poll[party]) for party in PARTIES},
            "deltaMean": {party: float(shadow_poll[party] - canonical_poll[party]) for party in PARTIES},
        },
        "assembly": {
            "canonicalHungProbability": float(canonical.chamber.hung_probability.iloc[0]),
            "shadowHungProbability": float(shadow.chamber.hung_probability.iloc[0]),
            "deltaHungProbability": float(shadow.chamber.hung_probability.iloc[0] - canonical.chamber.hung_probability.iloc[0]),
            "parties": _chamber_comparison(canonical.chamber, shadow.chamber, 45),
            "districts": _district_impact(canonical.districts, shadow.districts),
        },
        "council": {
            "canonicalMajorPartyNoControlProbability": float(canonical.council.major_party_no_control_probability.iloc[0]),
            "shadowMajorPartyNoControlProbability": float(shadow.council.major_party_no_control_probability.iloc[0]),
            "deltaMajorPartyNoControlProbability": float(shadow.council.major_party_no_control_probability.iloc[0] - canonical.council.major_party_no_control_probability.iloc[0]),
            "parties": _chamber_comparison(canonical.council, shadow.council, 21),
            "regions": _council_region_impact(canonical.council_regions, shadow.council_regions),
        },
    }


def run_shadow(repo_root: Path, *, simulations: int) -> dict:
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed = int(config["seed"])
    canonical = run_experimental_forecast(model_root, simulations=simulations, seed=seed)
    events, estimates = _scenario_registry(repo_root)
    shadow = _run_with_registry(model_root, events, estimates, simulations=simulations, seed=seed)
    report = build_impact_report(canonical, shadow, simulations=simulations, seed=seed, as_of=str(config["as_of"]))
    staged = _load_staged(repo_root)
    report["scenario"] = {
        "id": "plus-demosau-resolve-august",
        "label": "Two newest staged August polls",
        "evidence": [
            {
                "id": record["id"],
                "pollster": record["pollster"],
                "fieldworkStart": record["fieldworkStart"],
                "fieldworkEnd": record["fieldworkEnd"],
                "sourceTier": record.get("sourceTier", "primary_pollster"),
                "verificationStatus": record.get("verificationStatus", "primary-source-captured-awaiting-review"),
                "status": record["status"],
                "sourceUrl": record["sourceUrl"],
            }
            for record in staged
        ],
    }
    report["inputFingerprint"] = _input_fingerprint(repo_root)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", default="staged-poll-seat-shadow.json")
    parser.add_argument("--simulations", type=int, default=2000)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_shadow(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    rendered = json.dumps(report, indent=2) + "\n"
    if args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(f"staged poll seat shadow is stale: regenerate {output}")
    else:
        output.write_text(rendered)
    assembly = report["assembly"]
    changes = len(assembly["districts"]["modalWinnerChanges"])
    print(f"Full-election shadow: hung {assembly['deltaHungProbability']:+.3f}; modal seat changes={changes}; canonical files untouched.")


if __name__ == "__main__":
    main()
