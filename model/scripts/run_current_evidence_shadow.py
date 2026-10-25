#!/usr/bin/env python3
"""Run current-evidence full-election sensitivity scenarios without canonical promotion.

This is deliberately separate from the historical August staged-poll shadow. It
uses the existing governed forecast engine, re-ages the unchanged canonical poll
registry to the scenario as-of date, then injects only the evidence records named
in metadata/current-evidence-shadow-2026-10-25.json. Canonical input files and
forecast artefacts are never written.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from run_staged_poll_shadow import _estimate_rows, _event_row
from run_staged_poll_seat_shadow import (
    _chamber_comparison,
    _council_region_impact,
    _district_impact,
)
from vicforecast.forecast_2026 import PARTIES, run_experimental_forecast


def _load_evidence(repo_root: Path) -> dict:
    path = repo_root / "metadata/current-evidence-shadow-2026-10-25.json"
    return json.loads(path.read_text())


def _json_rows(frame: pd.DataFrame) -> list[dict]:
    """Convert model DataFrames to JSON-native rows without type guessing."""
    return json.loads(frame.to_json(orient="records"))


def _run_with_registry(
    model_root: Path,
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    as_of: str,
    simulations: int,
    seed: int,
):
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

    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    config["as_of"] = as_of
    with patch(
        "vicforecast.forecast_2026.pd.read_csv", side_effect=shadow_read_csv
    ), patch(
        "vicforecast.forecast_2026.load_forecast_config", return_value=config
    ):
        return run_experimental_forecast(
            model_root, simulations=simulations, seed=seed
        )


def _scenario_registry(
    canonical_events: pd.DataFrame,
    canonical_estimates: pd.DataFrame,
    records: list[dict],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = canonical_events.copy()
    estimates = canonical_estimates.copy()
    existing_ids = set(events["poll_id"].astype(str))
    for record in records:
        poll_id = record["proposedModelPollId"]
        if poll_id in existing_ids:
            raise ValueError(f"shadow poll_id already exists in canonical registry: {poll_id}")
        events = pd.concat(
            [events, pd.DataFrame([_event_row(record, list(events.columns))])],
            ignore_index=True,
        )
        estimates = pd.concat(
            [estimates, pd.DataFrame(_estimate_rows(record))], ignore_index=True
        )
        existing_ids.add(poll_id)
    return events, estimates


def _summarise_run(run) -> dict:
    poll_mean = run.poll_state.mean
    return {
        "polling": {
            "pollCount": int(run.poll_state.poll_count),
            "mean": {party: float(poll_mean[party]) for party in PARTIES},
            "median": {
                party: float(run.poll_state.median[party]) for party in PARTIES
            },
            "lower80": {
                party: float(run.poll_state.lower80[party]) for party in PARTIES
            },
            "upper80": {
                party: float(run.poll_state.upper80[party]) for party in PARTIES
            },
        },
        "assembly": {
            "hungProbability": float(run.chamber.hung_probability.iloc[0]),
            "parties": {
                party: {
                    "meanSeats": float(
                        run.chamber.set_index("party").loc[party, "mean"]
                    ),
                    "medianSeats": float(
                        run.chamber.set_index("party").loc[party, "median"]
                    ),
                    "majorityProbability": float(
                        run.chamber.set_index("party").loc[
                            party, "majority_probability"
                        ]
                    ),
                }
                for party in PARTIES
            },
            "districts": _json_rows(run.districts),
            "seatDistribution": _json_rows(run.seat_distribution),
        },
        "council": {
            "majorPartyNoControlProbability": float(
                run.council.major_party_no_control_probability.iloc[0]
            ),
            "parties": {
                party: {
                    "meanSeats": float(
                        run.council.set_index("party").loc[party, "mean"]
                    ),
                    "medianSeats": float(
                        run.council.set_index("party").loc[party, "median"]
                    ),
                    "majorityProbability": float(
                        run.council.set_index("party").loc[
                            party, "majority_probability"
                        ]
                    ),
                }
                for party in PARTIES
            },
            "regions": _json_rows(run.council_regions),
        },
    }


def _compare(base, scenario) -> dict:
    base_mean = base.poll_state.mean
    scenario_mean = scenario.poll_state.mean
    return {
        "pollingDeltaMean": {
            party: float(scenario_mean[party] - base_mean[party])
            for party in PARTIES
        },
        "assembly": {
            "deltaHungProbability": float(
                scenario.chamber.hung_probability.iloc[0]
                - base.chamber.hung_probability.iloc[0]
            ),
            "parties": _chamber_comparison(base.chamber, scenario.chamber, 45),
            "districts": _district_impact(base.districts, scenario.districts),
        },
        "council": {
            "deltaMajorPartyNoControlProbability": float(
                scenario.council.major_party_no_control_probability.iloc[0]
                - base.council.major_party_no_control_probability.iloc[0]
            ),
            "parties": _chamber_comparison(base.council, scenario.council, 21),
            "regions": _council_region_impact(
                base.council_regions, scenario.council_regions
            ),
        },
    }


def build_report(repo_root: Path, *, simulations: int) -> dict:
    evidence = _load_evidence(repo_root)
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    seed = int(config["seed"])
    as_of = str(evidence["asOf"])

    canonical_events = pd.read_csv(model_root / "data/processed/poll_events_seed.csv")
    canonical_estimates = pd.read_csv(model_root / "data/processed/poll_estimates_seed.csv")
    canonical = _run_with_registry(
        model_root,
        canonical_events,
        canonical_estimates,
        as_of=as_of,
        simulations=simulations,
        seed=seed,
    )

    by_id = {record["id"]: record for record in evidence["assemblyPolls"]}
    scenario_runs = {}
    for name, ids in evidence["assemblyScenarios"].items():
        records = [by_id[evidence_id] for evidence_id in ids]
        events, estimates = _scenario_registry(
            canonical_events, canonical_estimates, records
        )
        scenario_runs[name] = _run_with_registry(
            model_root,
            events,
            estimates,
            as_of=as_of,
            simulations=simulations,
            seed=seed,
        )

    return {
        "schemaVersion": 1,
        "mode": "current-evidence-full-election-shadow-sensitivity-only",
        "asOf": as_of,
        "simulationsPerScenario": simulations,
        "seed": seed,
        "commonRandomNumbers": True,
        "canonicalModelInputsChanged": False,
        "canonicalForecastArtifactsWritten": False,
        "scenarioEvidencePromoted": False,
        "policy": evidence["policy"],
        "interpretation": {
            "canonicalCurrentDate": "Existing canonical registry re-aged to the current evidence date. This is not a newly published canonical forecast.",
            "latestPrimary": "Adds the latest first-party DemosAU and RedBridge/Accent waves only in memory.",
            "latestPrimaryPlusResolve": "Also adds the latest Resolve topline from corroborated secondary evidence only in memory.",
            "council": "Roy Morgan July-September regional evidence is recorded but is not injected into the STV model until a complete five-way regional table is captured without inference. Council changes in these scenarios therefore arise only from statewide polling changes, not the new regional Roy Morgan dataset."
        },
        "evidence": {
            "assemblyPolls": evidence["assemblyPolls"],
            "councilEvidence": evidence["councilEvidence"],
        },
        "canonicalCurrentDate": _summarise_run(canonical),
        "scenarios": {
            name: {
                "summary": _summarise_run(run),
                "comparisonVsCanonicalCurrentDate": _compare(canonical, run),
            }
            for name, run in scenario_runs.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", default="current-evidence-shadow-2026-10-25.json")
    parser.add_argument("--simulations", type=int, default=5000)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = build_report(repo_root, simulations=args.simulations)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.write_text(json.dumps(report, indent=2) + "\n")

    primary = report["scenarios"]["latest_primary"]
    expanded = report["scenarios"]["latest_primary_plus_resolve"]
    print(
        "Current-evidence shadow: "
        f"canonical-date hung={report['canonicalCurrentDate']['assembly']['hungProbability']:.3f}; "
        f"primary hung={primary['summary']['assembly']['hungProbability']:.3f}; "
        f"expanded hung={expanded['summary']['assembly']['hungProbability']:.3f}. "
        "Canonical files untouched."
    )


if __name__ == "__main__":
    main()
