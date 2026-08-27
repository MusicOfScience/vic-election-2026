"""Experimental multivariate poll-of-polls for the 2026 Victorian election.

The model works in additive-log-ratio space so every posterior draw is a
coherent five-party composition. Polls are precision- and recency-weighted;
pollster effects are estimated with partial pooling and the residual covariance
is retained for downstream correlated election simulations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

import numpy as np
import pandas as pd

from .benchmark import TARGET_PARTIES, eligible_poll_events


PARTIES = tuple(TARGET_PARTIES)
REFERENCE_PARTY = "OTH_IND"


@dataclass(frozen=True)
class LatentPollState:
    as_of: date
    parties: tuple[str, ...]
    poll_count: int
    mean: dict[str, float]
    median: dict[str, float]
    lower80: dict[str, float]
    upper80: dict[str, float]
    house_effects: dict[str, dict[str, float]]
    covariance_alr: np.ndarray
    draws: np.ndarray
    production_compatible: bool = False


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def _alr(values: np.ndarray) -> np.ndarray:
    values = np.clip(values, 1e-6, None)
    return np.log(values[..., :-1] / values[..., -1, None])


def _inverse_alr(values: np.ndarray) -> np.ndarray:
    exp = np.exp(np.clip(values, -30, 30))
    full = np.concatenate([exp, np.ones((*exp.shape[:-1], 1))], axis=-1)
    return 100.0 * full / full.sum(axis=-1, keepdims=True)


def fit_latent_poll_state(
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    as_of: str | date | datetime,
    draws: int = 5000,
    seed: int = 20260826,
    half_life_days: float = 45.0,
    effective_sample_cap: int = 2500,
    systematic_floor: float = 0.035,
) -> LatentPollState:
    """Fit a transparent empirical-Bayes logistic-normal polling state."""
    if draws <= 0 or half_life_days <= 0 or effective_sample_cap <= 0:
        raise ValueError("draws, half_life_days and effective_sample_cap must be positive")
    as_of_date = _as_date(as_of)
    ev, harmonised = eligible_poll_events(events, estimates)
    ev = ev[ev.fieldwork_mid.map(_as_date) <= as_of_date].copy()
    harmonised = harmonised[harmonised.poll_id.isin(set(ev.poll_id))]
    if ev.empty:
        raise ValueError("no eligible complete polls available")

    wide = harmonised.pivot(index="poll_id", columns="party_id", values="primary_pct")
    wide = wide.loc[:, PARTIES].loc[ev.poll_id]
    y = _alr(wide.to_numpy(float))
    pollsters = ev.pollster.astype(str).to_numpy()
    ages = np.array([(as_of_date - _as_date(x)).days for x in ev.fieldwork_mid], float)
    ess = ev.effective_sample_size.fillna(ev.sample_size).to_numpy(float)
    weights = np.minimum(ess, float(effective_sample_cap)) * np.power(0.5, ages / half_life_days)

    # Iterative empirical-Bayes house effects. Sparse pollsters shrink strongly
    # toward zero; the weighted latent state is re-estimated after correction.
    centre = np.average(y, axis=0, weights=weights)
    effects = {p: np.zeros(y.shape[1]) for p in sorted(set(pollsters))}
    for _ in range(12):
        for pollster in effects:
            mask = pollsters == pollster
            raw = np.average(y[mask] - centre, axis=0, weights=weights[mask])
            shrink = float(weights[mask].sum() / (weights[mask].sum() + 2400.0))
            effects[pollster] = raw * shrink
        corrected = np.vstack([row - effects[p] for row, p in zip(y, pollsters)])
        centre = np.average(corrected, axis=0, weights=weights)

    corrected = np.vstack([row - effects[p] for row, p in zip(y, pollsters)])
    residual = corrected - centre
    cov = np.cov(residual, rowvar=False, aweights=weights, ddof=0)
    # Posterior uncertainty includes sampling precision plus a non-sampling
    # systematic floor. Regularisation guarantees a valid joint distribution.
    eff_total = max(weights.sum() / 1000.0, 1.0)
    cov = cov / eff_total + np.eye(y.shape[1]) * systematic_floor**2
    vals, vecs = np.linalg.eigh(cov)
    cov = (vecs * np.maximum(vals, 1e-8)) @ vecs.T
    rng = np.random.default_rng(seed)
    composition_draws = _inverse_alr(rng.multivariate_normal(centre, cov, size=draws))

    def stat(values: np.ndarray) -> dict[str, float]:
        return {p: float(v) for p, v in zip(PARTIES, values)}

    central = _inverse_alr(centre[None, :])[0]
    house = {}
    for pollster, effect in effects.items():
        shifted = _inverse_alr((centre + effect)[None, :])[0] - central
        house[pollster] = stat(shifted)
    return LatentPollState(
        as_of=as_of_date,
        parties=PARTIES,
        poll_count=len(ev),
        mean=stat(composition_draws.mean(axis=0)),
        median=stat(np.median(composition_draws, axis=0)),
        lower80=stat(np.quantile(composition_draws, 0.10, axis=0)),
        upper80=stat(np.quantile(composition_draws, 0.90, axis=0)),
        house_effects=house,
        covariance_alr=cov,
        draws=composition_draws,
    )
