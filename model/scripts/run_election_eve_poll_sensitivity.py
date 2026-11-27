"""Reproduce the 27 November Assembly polling sensitivity against the frozen registry."""
import json
from pathlib import Path

import pandas as pd

from run_current_evidence_shadow import _run_with_registry, _scenario_registry
from vicforecast.forecast_2026 import load_forecast_config

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "model"
REVIEW = ROOT / "metadata/election-eve-poll-review-2026-11-27.json"


def main():
    evidence = json.loads(REVIEW.read_text())
    config = load_forecast_config(MODEL)
    events = pd.read_csv(MODEL / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(MODEL / "data/processed/poll_estimates_seed.csv")
    primary = evidence["polls"][:3]
    newspoll, resolve = evidence["polls"][3:]
    replaced = events.loc[~events.poll_id.isin(evidence["replaceEarlier"])]
    cases = [
        ("reaged", events, []),
        ("three", events, primary),
        ("replace", replaced, primary),
        ("plusNewspoll", events, [*primary, newspoll]),
        ("plusResolve", events, [*primary, resolve]),
        ("allFive", events, [*primary, newspoll, resolve]),
    ]
    result = {"asOf": evidence["asOf"], "simulations": config["simulations"], "scenarios": {}}
    for name, starting_events, additions in cases:
        starting_estimates = estimates.loc[estimates.poll_id.isin(starting_events.poll_id)]
        e, p = _scenario_registry(starting_events, starting_estimates, additions)
        run = _run_with_registry(MODEL, e, p, as_of=evidence["asOf"],
                                 simulations=config["simulations"], seed=config["seed"])
        chamber = run.chamber.set_index("party")
        result["scenarios"][name] = {
            "pollCount": run.poll_state.poll_count,
            "pollingMean": {key: round(float(value), 3) for key, value in run.poll_state.mean.items()},
            "meanSeats": {key: round(float(value), 3) for key, value in chamber["mean"].items()},
            "coalitionMajority": float(chamber.loc["LIB_NAT", "majority_probability"]),
            "hungAssembly": float(chamber.loc["LIB_NAT", "hung_probability"]),
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
