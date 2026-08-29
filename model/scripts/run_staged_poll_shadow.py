#!/usr/bin/env python3
"""Preview the polling-layer effect of staged 2026 evidence without model promotion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from vicforecast.polling.latent import PARTIES, fit_latent_poll_state


def _estimate_rows(record: dict) -> list[dict]:
    mapping = (
        ("coalition", "LIB_NAT"),
        ("alp", "ALP"),
        ("oneNation", "ONP"),
        ("greens", "GRN"),
        ("independents", "IND"),
        ("otherParties", "OTH"),
    )
    return [
        {
            "poll_id": record["proposedModelPollId"],
            "party_id": party,
            "primary_pct": float(record["primaryVote"][key]),
            "estimate_status": "reported",
            "notes": "SHADOW SCENARIO ONLY — staged evidence is not a canonical model input.",
        }
        for key, party in mapping
        if record.get("primaryVote", {}).get(key) is not None
    ]


def _event_row(record: dict, columns: list[str]) -> dict:
    primary = record.get("captureMode") == "manual-primary-source-capture"
    values = {
        "poll_id": record["proposedModelPollId"],
        "pollster": record["pollster"],
        "commissioner": record.get("commissioner", ""),
        "fieldwork_start": record["fieldworkStart"],
        "fieldwork_end": record["fieldworkEnd"],
        "publication_date": record.get("pollPublicationDate") or record.get("publicationDate") or "",
        "sample_size": int(record["sampleSize"]),
        "effective_sample_size": np.nan,
        "method": record.get("method", "shadow scenario"),
        "geography": record.get("geography", "Victoria"),
        "population": "Victorian voters",
        "vote_base": "decided_reallocated",
        "undecided_treatment": "published primary composition sums to 100",
        "one_nation_prompted": True,
        "questionnaire_regime": "explicit_multi_party",
        "leader_regime": "Carroll-Wilson-Pickering",
        "source_tier": "primary_pollster" if primary else record.get("sourceTier", "reputable_secondary"),
        "verification_status": "verified" if primary else "partially_verified",
        "model_eligible": True,
        "source_url": record["sourceUrl"],
        "notes": "SHADOW SCENARIO ONLY — does not confer evidence acceptance or model eligibility.",
        "sample_family": "",
        "source_document_title": "",
    }
    return {column: values.get(column, "") for column in columns}


def _fit(events: pd.DataFrame, estimates: pd.DataFrame, config: dict, seed: int, draws: int) -> dict:
    polling = config["polling"]
    fitted = fit_latent_poll_state(
        events,
        estimates,
        as_of=config["as_of"],
        draws=draws,
        seed=seed,
        half_life_days=float(polling["half_life_days"]),
        effective_sample_cap=int(polling["effective_sample_cap"]),
        systematic_floor=float(polling["systematic_floor"]),
    )
    return {
        "pollCount": fitted.poll_count,
        "mean": {party: float(fitted.mean[party]) for party in PARTIES},
        "median": {party: float(fitted.median[party]) for party in PARTIES},
        "lower80": {party: float(fitted.lower80[party]) for party in PARTIES},
        "upper80": {party: float(fitted.upper80[party]) for party in PARTIES},
    }


def build_shadow_report(repo_root: Path, *, draws: int | None = None) -> dict:
    model_root = repo_root / "model"
    config = yaml.safe_load((model_root / "config/experimental_forecast.yml").read_text())
    draws = int(draws or config["simulations"])
    seed = int(config["seed"])
    events = pd.read_csv(model_root / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(model_root / "data/processed/poll_estimates_seed.csv")
    manual = json.loads((repo_root / "metadata/manual-source-evidence-2026.json").read_text())
    research = json.loads((repo_root / "metadata/research-source-evidence-2026.json").read_text())
    staged = {record["pollster"]: record for record in [*manual.get("records", []), *research.get("records", [])] if record.get("kind") == "poll"}

    scenarios = {
        "canonical": [],
        "plus_demosau": [staged["DemosAU"]],
        "plus_resolve": [staged["Resolve Strategic"]],
        "plus_both": [staged["DemosAU"], staged["Resolve Strategic"]],
    }
    fitted: dict[str, dict] = {}
    for name, additions in scenarios.items():
        scenario_events = events.copy()
        scenario_estimates = estimates.copy()
        for record in additions:
            scenario_events = pd.concat(
                [scenario_events, pd.DataFrame([_event_row(record, list(events.columns))])],
                ignore_index=True,
            )
            scenario_estimates = pd.concat(
                [scenario_estimates, pd.DataFrame(_estimate_rows(record))],
                ignore_index=True,
            )
        fitted[name] = _fit(scenario_events, scenario_estimates, config, seed, draws)

    baseline = fitted["canonical"]["mean"]
    scenario_rows = {}
    for name, result in fitted.items():
        delta = {party: result["mean"][party] - baseline[party] for party in PARTIES}
        scenario_rows[name] = {
            **result,
            "deltaMeanVsCanonical": delta,
            "maxAbsoluteMeanShift": max(abs(value) for value in delta.values()),
        }

    return {
        "schemaVersion": 1,
        "asOf": str(config["as_of"]),
        "drawsPerScenario": draws,
        "seed": seed,
        "mode": "shadow-polling-sensitivity-only",
        "canonicalModelInputsChanged": False,
        "seatForecastRecomputed": False,
        "policy": "Staged evidence is temporarily marked eligible only inside an in-memory copy of the polling registry. This does not accept, promote or write the evidence and does not update seat forecasts.",
        "evidenceCaveats": {
            "DemosAU": "Primary-source figures are captured but still require explicit human evidence acceptance before canonical use.",
            "Resolve Strategic": "Corroborated secondary evidence only; primary-source reconciliation or a reviewed exception remains required before canonical use.",
        },
        "scenarios": scenario_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", default="staged-poll-shadow-sensitivity.json")
    parser.add_argument("--draws", type=int, default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = build_shadow_report(repo_root, draws=args.draws)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_root / output
    output.write_text(json.dumps(report, indent=2) + "\n")
    both = report["scenarios"]["plus_both"]
    shifts = ", ".join(f"{party} {both['deltaMeanVsCanonical'][party]:+.2f}" for party in PARTIES)
    print(f"Shadow polling sensitivity: {shifts} pp; canonical inputs unchanged.")


if __name__ == "__main__":
    main()
