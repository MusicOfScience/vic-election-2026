"""Test November Assembly polls on a copy of the canonical polling inputs."""
import json
from pathlib import Path

import pandas as pd

from run_staged_poll_shadow import _event_row, _fit
from vicforecast.forecast_2026 import load_forecast_config


def main():
    model = Path(__file__).resolve().parents[1]
    config = load_forecast_config(model)
    config["as_of"] = "2026-11-15"
    events = pd.read_csv(model / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(model / "data/processed/poll_estimates_seed.csv")
    review_path = model.parent / "metadata/november-poll-evidence-review-2026-11-11.json"
    evidence = json.loads(review_path.read_text())["evidence"]
    selected = {
        "redbridge-accent-victoria-2026-11-03-10-publisher": "2026-11-10",
        "demosau-victoria-2026-10-30-11-05-media": "2026-11-05",
        "resolve-victoria-2026-11-early-media": "2026-11-07",
    }
    new_events, new_estimates = [], []
    for wave in evidence:
        poll_id = wave["id"]
        if poll_id not in selected:
            continue
        record = {
            **wave,
            "proposedModelPollId": poll_id,
            "fieldworkStart": wave["reportedDates"]["start"],
            "fieldworkEnd": selected[poll_id],
            "sampleSize": wave["reportedSampleSize"],
            "captureMode": "manual-primary-source-capture" if wave["effectiveSampleSize"] else "",
        }
        event = _event_row(record, list(events.columns))
        if wave["pollster"] == "RedBridge Group / Accent Research":
            event["pollster"] = "RedBridge / Accent Research"
        event["effective_sample_size"] = wave["effectiveSampleSize"]
        new_events.append(event)
        primary = wave["reportedPrimaries"]
        shares = {party: primary[key] for party, key in zip(
            ("ALP", "LIB_NAT", "ONP", "GRN"), ("alp", "coalition", "onp", "greens")
        )}
        shares["OTH_IND"] = primary.get("other", 100 - sum(shares.values()))
        new_estimates.extend(
            {"poll_id": poll_id, "party_id": party, "primary_pct": share,
             "estimate_status": "reported" if party != "OTH_IND" or "other" in primary else "derived_remainder",
             "notes": "November shadow only"}
            for party, share in shares.items()
        )
    staged = pd.DataFrame(new_events)
    staged_estimates = pd.DataFrame(new_estimates)
    assert set(staged.poll_id) == set(selected)
    verified = staged[staged.effective_sample_size.notna()]
    latest_only = events.assign(
        model_eligible=events.model_eligible & ~events.pollster.isin(verified.pollster)
    )
    scenarios = {
        "existing_inputs": events,
        "add_verified_pair": pd.concat([events, verified]),
        "replace_earlier_same_house_waves": pd.concat([latest_only, verified]),
        "add_verified_pair_and_resolve": pd.concat([events, staged]),
    }
    result = {}
    for name, inputs in scenarios.items():
        additions = staged_estimates[staged_estimates.poll_id.isin(inputs.poll_id)]
        fitted = _fit(inputs, pd.concat([estimates, additions]), config, config["seed"], config["simulations"])
        result[name] = {"polls": fitted["pollCount"], "mean": fitted["mean"]}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
