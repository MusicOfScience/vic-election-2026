#!/usr/bin/env python3
"""Walk-forward comparison of statewide voting-intention estimators."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from vicforecast.polling.benchmark import eligible_poll_events
from vicforecast.polling.latent import PARTIES, _alr, _inverse_alr, fit_latent_poll_state

LEADERSHIP_CHANGE = pd.Timestamp("2026-07-28")


def fit(events, votes, target, *, trend):
    """Recency/precision weighted compositional regression with shrinkage."""
    age = (target - events.fieldwork_mid).dt.total_seconds().to_numpy() / 86400
    sample = events.effective_sample_size.fillna(events.sample_size).to_numpy()
    weights = np.minimum(sample, 2500) / 1000 * 2 ** (-age / 45)
    houses = pd.get_dummies(events.pollster, dtype=float).to_numpy()
    time = -age / 28
    design = np.column_stack((np.ones(len(events)), time, houses))
    # Penalise a four-week slope more heavily than a pollster intercept.
    penalty = np.diag([0, 8, *([2.4] * houses.shape[1])])
    if not trend:
        design[:, 1] = 0
    coefs = np.linalg.solve(design.T @ (weights[:, None] * design) + penalty,
                            design.T @ (weights[:, None] * _alr(votes)))
    return _inverse_alr(coefs[0]), coefs


def score(events, votes, raw_estimates):
    losses = {"current": [], "matched_level": [], "drift": []}
    folds = []
    for held in events.itertuples():
        # Hold out waves unavailable when the target began, including overlapping fieldwork.
        prior = events[(events.publication_date < held.fieldwork_start)
                       & (events.fieldwork_end < held.fieldwork_start)]
        if len(prior) < 5 or prior.pollster.nunique() < 3:
            continue
        truth = votes.loc[held.poll_id].to_numpy()
        train = votes.loc[prior.poll_id].to_numpy()
        current = fit_latent_poll_state(
            prior.drop(columns="fieldwork_mid"), raw_estimates.loc[
                lambda frame: frame.poll_id.isin(prior.poll_id)],
            as_of=held.fieldwork_mid, draws=5000,
        )
        predictions = {"current": np.array([current.mean[p] for p in PARTIES])}
        for name in ("matched_level", "drift"):
            predictions[name], _ = fit(prior, train, held.fieldwork_mid, trend=name == "drift")
        for name, prediction in predictions.items():
            losses[name].append(float(np.mean(np.abs(prediction - truth))))
        folds.append({"poll": held.poll_id, **{name: round(values[-1], 3) for name, values in losses.items()}})
    if not folds:
        raise ValueError("No walk-forward folds meet the minimum evidence requirements")
    return {"folds": folds, "meanAbsoluteErrorPp": {name: round(float(np.mean(values)), 3)
                                                    for name, values in losses.items()}}


def leadership(events, votes):
    nearby = events[(events.fieldwork_end >= LEADERSHIP_CHANGE - pd.Timedelta(days=56))
                    & (events.fieldwork_start <= LEADERSHIP_CHANGE + pd.Timedelta(days=56))]
    pairs = []
    for house, rows in nearby.groupby("pollster"):
        before = rows[rows.fieldwork_end < LEADERSHIP_CHANGE].sort_values("fieldwork_end")
        after = rows[rows.fieldwork_start > LEADERSHIP_CHANGE].sort_values("fieldwork_start")
        if before.empty or after.empty:
            continue
        left, right = before.iloc[-1], after.iloc[0]
        pairs.append({"house": house, "before": left.poll_id, "after": right.poll_id,
                      "gapDays": (right.fieldwork_start - left.fieldwork_end).days,
                      "laborDeltaPp": round(float(votes.loc[right.poll_id, "ALP"] - votes.loc[left.poll_id, "ALP"]), 3)})
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--as-of", default="2026-10-31")
    args = parser.parse_args()
    data = args.root / "data/processed"
    raw_events = pd.read_csv(data / "poll_events_seed.csv")
    raw_estimates = pd.read_csv(data / "poll_estimates_seed.csv")
    events, estimates = eligible_poll_events(raw_events, raw_estimates)
    for column in ("publication_date", "fieldwork_start", "fieldwork_end", "fieldwork_mid"):
        events[column] = pd.to_datetime(events[column])
    as_of = pd.Timestamp(args.as_of)
    if as_of > pd.Timestamp("2026-11-28"):
        parser.error("--as-of must fall on or before election day")
    events = events[(events.publication_date <= as_of) & (events.fieldwork_end <= as_of)]
    votes = estimates.pivot(index="poll_id", columns="party_id", values="primary_pct").loc[:, list(PARTIES)]
    now, coefs = fit(events, votes.loc[events.poll_id].to_numpy(), as_of, trend=True)
    election = pd.Timestamp("2026-11-28")
    # Cap the drift horizon at four weeks for this diagnostic.
    horizon = min(28, max(0, (election - as_of).days)) / 28
    forward = _inverse_alr(coefs[0] + horizon * coefs[1])
    print(json.dumps({"asOf": args.as_of, "polls": len(events), "walkForward": score(events, votes, raw_estimates),
                      "driftNowcastPct": dict(zip(PARTIES, now.round(2))),
                      "driftElectionPointPct": dict(zip(PARTIES, forward.round(2))),
                      "leadershipMatchedPairs": leadership(events, votes)}, indent=2))


if __name__ == "__main__":
    main()
