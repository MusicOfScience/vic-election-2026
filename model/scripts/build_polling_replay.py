#!/usr/bin/env python3
"""Reconstruct publication-date frames from the frozen forecast input set."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from vicforecast.polling.benchmark import eligible_poll_events
from vicforecast.polling.latent import fit_latent_poll_state


def build(root):
    processed = root / "data/processed"
    manifest_bytes = (processed / "experimental_forecast_2026.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    events, estimates = (
        pd.read_csv(processed / name) for name in ("poll_events_seed.csv", "poll_estimates_seed.csv")
    )
    eligible, _ = eligible_poll_events(events, estimates)
    cutoff = pd.Timestamp(manifest["as_of"])
    admitted = eligible.loc[pd.to_datetime(eligible.fieldwork_mid) <= cutoff].copy()
    publications = pd.to_datetime(admitted.publication_date, errors="coerce")
    if len(admitted) != manifest["polling"]["poll_count"] or publications.isna().any() or (publications > cutoff).any():
        raise ValueError("Replay cannot reconcile publication dates with the released forecast")
    assumptions = manifest["assumptions"]["polling"]
    windows = sorted({21, 45, 90, int(assumptions["half_life_days"])})
    frames = []
    for date in sorted(set(publications) | {cutoff}):
        poll_ids = set(admitted.loc[publications <= date, "poll_id"])
        # Skip the sparse two-poll frame. Its rank-one residual covariance leaves
        # the seeded finite draws sensitive to the numerical library's choice of basis.
        if len(poll_ids) < 3:
            continue
        available = events[events.poll_id.isin(poll_ids)]
        inputs = estimates[estimates.poll_id.isin(poll_ids)]
        variants = {}
        for days in windows:
            fit = fit_latent_poll_state(
                available, inputs, as_of=date.date(), draws=manifest["simulations"], seed=manifest["seed"],
                half_life_days=days, effective_sample_cap=assumptions["effective_sample_cap"],
                systematic_floor=assumptions["systematic_floor"],
            )
            if fit.poll_count != len(poll_ids):
                raise ValueError(f"Publication frame has inconsistent poll coverage at {date.date()}")
            variants[days] = {
                "mean": {p: round(fit.mean[p], 5) for p in fit.parties},
                "low": {p: round(fit.lower80[p], 5) for p in fit.parties},
                "high": {p: round(fit.upper80[p], 5) for p in fit.parties},
            }
        frames.append({"date": date.date().isoformat(), "pollIds": sorted(poll_ids), "variants": variants})
    baseline = int(assumptions["half_life_days"])
    if not frames or frames[-1]["date"] != manifest["as_of"] or any(
        not np.isclose(frames[-1]["variants"][baseline]["mean"][p], value, atol=0.000006, rtol=0)
        for p, value in manifest["polling"]["mean"].items()
    ):
        raise ValueError("Replay endpoint disagrees with the published polling aggregate")
    return {"asOf": manifest["as_of"], "forecastSha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "defaultHalfLife": baseline, "windows": windows, "frames": frames}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    output = args.root.parent / "app/polling-replay.generated.json"
    content = json.dumps(build(args.root), sort_keys=True, separators=(",", ":")) + "\n"
    temp = output.with_suffix(".tmp")
    temp.write_text(content)
    temp.replace(output)
