#!/usr/bin/env python3
"""Publish vote-share diagnostics by observing the unchanged seeded engine."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from vicforecast import forecast_2026 as engine
from vicforecast.polling.benchmark import eligible_poll_events


def count(primary, preference, finalists=None):
    """Apply the engine's transfers, optionally keeping two groups in the count."""
    votes = primary.copy()
    continuing = set(range(len(engine.PARTIES)))
    while len(continuing) > 2:
        removable = continuing if finalists is None else continuing.difference(finalists)
        source = min(removable, key=lambda x: (votes[x], x))
        continuing.remove(source)
        destinations = sorted(continuing)
        probs = preference[source, destinations]
        votes[destinations] += votes[source] * (probs / probs.sum())
        votes[source] = 0.0
    pair = tuple(sorted(continuing, key=lambda x: votes[x], reverse=True))
    return pair, votes


def summary(values):
    return {
        "mean": round(float(np.mean(values)) * 100, 4),
        "low": round(float(np.quantile(values, .1)) * 100, 4),
        "high": round(float(np.quantile(values, .9)) * 100, 4),
    }


def build(root):
    processed = root / "data/processed"
    manifest_bytes = (processed / "experimental_forecast_2026.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    n = manifest["simulations"]
    districts = engine.build_assembly_seed(root, engine.load_forecast_config(root))
    weights = districts.enrolled_electors.to_numpy(float)
    weights /= weights.sum()
    statewide = np.zeros(n)
    seat_pairs = [{} for _ in weights]
    labour, coalition = (engine.PARTIES.index(p) for p in ("ALP", "LIB_NAT"))
    original_count = engine._count_irv
    calls = 0

    def observe(primary, preference):
        nonlocal calls
        draw, seat = divmod(calls, len(weights))
        winner, ordered = original_count(primary, preference)
        pair, votes = count(primary, preference)
        if pair != ordered:
            raise ValueError("Diagnostic count diverged from the canonical engine")
        first, second = sorted(ordered)
        total, wins = seat_pairs[seat].setdefault((first, second), ([], []))
        total.append(votes[first])
        wins.append(winner == first)
        _, forced = count(primary, preference, (labour, coalition))
        statewide[draw] += weights[seat] * forced[labour]
        calls += 1
        return winner, ordered

    with patch.object(engine, "_count_irv", observe):
        replay = engine.run_experimental_forecast(root, simulations=n, seed=manifest["seed"])
    if calls != n * len(weights):
        raise ValueError("Diagnostic replay did not observe every district draw")
    recorded = pd.read_csv(processed / "experimental_forecast_2026_districts.csv")
    columns = ["district_id", "favoured_party", "likely_final_pair"]
    if not replay.districts[columns].equals(recorded[columns]):
        raise ValueError("Diagnostic replay does not match the published districts")
    probability_columns = ["favoured_probability", "final_pair_probability", *[f"win_{p.lower()}" for p in engine.PARTIES]]
    if not np.allclose(replay.districts[probability_columns], recorded[probability_columns], atol=1e-12, rtol=0):
        raise ValueError("Diagnostic replay does not match published win or pair frequencies")
    polls, _ = eligible_poll_events(pd.read_csv(processed / "poll_events_seed.csv"),
                                    pd.read_csv(processed / "poll_estimates_seed.csv"))
    ids = sorted(polls.loc[pd.to_datetime(polls.fieldwork_mid) <= pd.Timestamp(manifest["as_of"]), "poll_id"])
    if len(ids) != replay.poll_state.poll_count or len(set(ids)) != len(ids):
        raise ValueError("Diagnostic poll lineage mismatch")

    seats = {}
    for district_id, pairs in zip(districts.district_id, seat_pairs):
        (first, second), (shares, wins) = max(sorted(pairs.items()), key=lambda item: len(item[1][0]))
        seats[district_id] = {
            "pair": [engine.PARTIES[first], engine.PARTIES[second]],
            "draws": len(shares),
            "firstShare": summary(shares),
            "firstWins": sum(wins),
        }
    return {"asOf": manifest["as_of"], "simulations": n,
            "forecastSha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "pollIds": ids, "statewideLabor2pp": summary(statewide), "seats": seats}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    output = args.root.parent / "app/assembly-vote-diagnostics.generated.json"
    data = build(args.root)
    content = json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n"
    temp = output.with_suffix(".tmp")
    temp.write_text(content)
    temp.replace(output)
