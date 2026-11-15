"""Compare polling estimators on frozen common inputs, without running seats."""

from pathlib import Path

import numpy as np
import pandas as pd

from vicforecast.forecast_2026 import load_forecast_config
from vicforecast.polling.benchmark import eligible_poll_events
from vicforecast.polling.latent import PARTIES, fit_latent_poll_state


def main():
    root = Path(__file__).resolve().parents[1]
    config = load_forecast_config(root)
    cutoff = pd.Timestamp(config["as_of"])
    events = pd.read_csv(root / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(root / "data/processed/poll_estimates_seed.csv")
    eligible, harmonised = eligible_poll_events(events, estimates)
    available = eligible.loc[
        (pd.to_datetime(eligible.publication_date) <= cutoff)
        & (pd.to_datetime(eligible.fieldwork_end) <= cutoff)
    ].copy()
    latest_end = pd.to_datetime(available.fieldwork_end).max()
    recent = available.assign(end=pd.to_datetime(available.fieldwork_end))
    recent = recent.loc[recent.end >= latest_end - pd.Timedelta(days=45)]
    recent = recent.sort_values(["end", "publication_date", "poll_id"])
    recent = recent.drop_duplicates("pollster", keep="last")

    shares = harmonised.pivot(index="poll_id", columns="party_id", values="primary_pct")
    print(f"Publication cutoff: {cutoff.date()}")
    print("Input set / estimator | n | " + " | ".join(PARTIES) + " | Coalition lead")
    for label, rows in [("All admitted", available), ("Recent, latest per pollster", recent)]:
        ends = pd.to_datetime(rows.fieldwork_end)
        ages = (ends.max() - ends).dt.days
        ess = rows.effective_sample_size.fillna(rows.sample_size / 1.3)
        weights = ess * np.power(0.5, ages / 21)
        arithmetic = np.average(shares.loc[rows.poll_id, list(PARTIES)], axis=0, weights=weights)
        comparable_events = events.assign(model_eligible=events.poll_id.isin(rows.poll_id))
        polling = config["polling"]
        latent = fit_latent_poll_state(
            comparable_events, estimates, as_of=cutoff.date(),
            draws=config["simulations"], seed=config["seed"],
            half_life_days=polling["half_life_days"],
            effective_sample_cap=polling["effective_sample_cap"],
            systematic_floor=polling["systematic_floor"],
        )
        for method, values in [("arithmetic 21d", arithmetic), ("latent 45d", list(latent.mean.values()))]:
            columns = [*values, values[PARTIES.index("LIB_NAT")] - values[PARTIES.index("ALP")]]
            print(f"{label} / {method} | {len(rows)} | " + " | ".join(f"{v:.2f}" for v in columns))
        print("Inputs:", "; ".join(f"{row.pollster} ({row.fieldwork_end})" for row in rows.itertuples()))


if __name__ == "__main__":
    main()
