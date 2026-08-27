from pathlib import Path

import numpy as np
import pandas as pd

from vicforecast.forecast_2026 import (
    ASSEMBLY_2022_TARGET, PARTIES, PREFERENCE_PRIOR, _count_group_stv,
    _count_irv, build_assembly_seed, build_council_seed, run_experimental_forecast,
)
from vicforecast.polling.latent import fit_latent_poll_state

ROOT = Path(__file__).resolve().parents[1]


def test_latent_polling_is_coherent_and_reproducible():
    events = pd.read_csv(ROOT / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(ROOT / "data/processed/poll_estimates_seed.csv")
    a = fit_latent_poll_state(events, estimates, as_of="2026-08-26", draws=100, seed=7)
    b = fit_latent_poll_state(events, estimates, as_of="2026-08-26", draws=100, seed=7)
    assert a.poll_count >= 5
    assert np.allclose(a.draws.sum(axis=1), 100)
    assert np.array_equal(a.draws, b.draws)
    assert set(a.mean) == set(PARTIES)
    assert len(a.house_effects) >= 3


def test_assembly_seed_has_88_districts_and_rakes_to_official_anchor():
    seed = build_assembly_seed(ROOT)
    assert len(seed) == 88
    weights = seed.enrolled_electors / seed.enrolled_electors.sum()
    actual = (seed.loc[:, PARTIES].to_numpy() * weights.to_numpy()[:, None]).sum(axis=0) * 100
    assert np.allclose(actual, ASSEMBLY_2022_TARGET, atol=.02)


def test_irv_does_not_force_labor_coalition_final_pair():
    primary = np.array([.12, .10, .55, .15, .08])
    winner, pair = _count_irv(primary, PREFERENCE_PRIOR)
    assert winner == 2
    assert 2 in pair
    assert set(pair) != {0, 1}


def test_council_seed_and_count_conserve_five_seats():
    seed = build_council_seed(ROOT)
    assert len(seed) == 8
    seats = _count_group_stv(seed.loc[0, list(PARTIES)].to_numpy(float), PREFERENCE_PRIOR)
    assert seats.sum() == 5


def test_end_to_end_reproducible_and_conserves_chambers():
    a = run_experimental_forecast(ROOT, simulations=30, seed=11)
    b = run_experimental_forecast(ROOT, simulations=30, seed=11)
    assert a.districts.equals(b.districts)
    assert np.isclose(a.chamber["mean"].sum(), 88)
    assert np.isclose(a.council["mean"].sum(), 40)
    seat_columns = [f"seats_{p.lower()}" for p in PARTIES]
    assert (a.council_regions[seat_columns].sum(axis=1) == 5).all()
