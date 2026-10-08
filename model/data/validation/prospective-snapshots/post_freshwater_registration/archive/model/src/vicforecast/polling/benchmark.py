"""Transparent poll-average benchmark.

This is intentionally *not* the production latent polling model.  It provides a
simple, inspectable comparator that later Bayesian/state-space models should
outperform in calibration/backtesting.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from math import log

import numpy as np
import pandas as pd

from .registry import PollDataError, validate_poll_estimates, validate_poll_events


TARGET_PARTIES = ("ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND")


@dataclass(frozen=True)
class PollBenchmarkResult:
    as_of: date
    regime_filter: str
    half_life_days: float
    poll_count: int
    estimates: dict[str, float]
    effective_weight_sum: float


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def harmonise_poll_estimates(events: pd.DataFrame, estimates: pd.DataFrame) -> pd.DataFrame:
    """Map varying published residual categories to a common five-way frame.

    Roy Morgan-style separate OTH + IND rows are summed. Five-category polls
    reporting only OTH may use that row as the broad residual only when their
    complete composition is a decided-vote 100% allocation and IND is absent.
    This transform creates a derived analysis table; original rows remain intact.
    """
    ev = validate_poll_events(events)
    est = validate_poll_estimates(ev, estimates)
    event_by_id = ev.set_index("poll_id")
    rows = []
    for poll_id, group in est.groupby("poll_id", observed=True):
        values = dict(zip(group.party_id, group.primary_pct))
        for party in ("ALP", "LIB_NAT", "ONP", "GRN"):
            if party not in values:
                continue
            rows.append({"poll_id": poll_id, "party_id": party, "primary_pct": float(values[party])})

        if "OTH_IND" in values:
            residual = float(values["OTH_IND"])
        elif "OTH" in values and "IND" in values:
            residual = float(values["OTH"] + values["IND"])
        elif "OTH" in values and "IND" not in values:
            total = float(group.primary_pct.sum())
            event = event_by_id.loc[poll_id]
            if event.vote_base != "decided_reallocated" or abs(total - 100.0) > 0.75:
                # Do not guess what an incomplete residual means.
                continue
            residual = float(values["OTH"])
        else:
            continue
        rows.append({"poll_id": poll_id, "party_id": "OTH_IND", "primary_pct": residual})

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["poll_id", "party_id", "primary_pct"])
    return out.sort_values(["poll_id", "party_id"]).reset_index(drop=True)


def eligible_poll_events(
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    current_leader_regime: str | None = None,
    regime_filter: str = "all_eligible",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ev = validate_poll_events(events)
    harmonised = harmonise_poll_estimates(ev, estimates)
    mask = ev.model_eligible.astype(bool)
    mask &= ev.vote_base.eq("decided_reallocated")
    if "questionnaire_regime" in ev.columns:
        mask &= ev.questionnaire_regime.eq("explicit_multi_party")
    if regime_filter == "current_leader_regime_only":
        if not current_leader_regime:
            raise PollDataError("current_leader_regime required for current-regime filter")
        if "leader_regime" not in ev.columns:
            raise PollDataError("poll events do not contain leader_regime")
        mask &= ev.leader_regime.eq(current_leader_regime)
    elif regime_filter != "all_eligible":
        raise PollDataError(f"unknown regime_filter: {regime_filter}")

    ev = ev.loc[mask].copy()
    # A poll is usable only if the harmonised five-party composition is complete.
    counts = harmonised.groupby("poll_id", observed=True).party_id.nunique()
    complete_ids = set(counts[counts.eq(len(TARGET_PARTIES))].index)
    ev = ev[ev.poll_id.isin(complete_ids)].copy()
    harmonised = harmonised[harmonised.poll_id.isin(set(ev.poll_id))].copy()
    return ev, harmonised


def poll_benchmark(
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    as_of: str | date | datetime,
    half_life_days: float = 45,
    effective_sample_cap: int = 2500,
    regime_filter: str = "all_eligible",
    current_leader_regime: str | None = None,
) -> PollBenchmarkResult:
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    if effective_sample_cap <= 0:
        raise ValueError("effective_sample_cap must be positive")
    as_of_date = _as_date(as_of)
    ev, harmonised = eligible_poll_events(
        events,
        estimates,
        current_leader_regime=current_leader_regime,
        regime_filter=regime_filter,
    )
    ev = ev[ev.fieldwork_mid.map(_as_date) <= as_of_date].copy()
    harmonised = harmonised[harmonised.poll_id.isin(set(ev.poll_id))].copy()
    if ev.empty:
        raise PollDataError("no complete eligible polls available for benchmark")

    def event_weight(row) -> float:
        mid = _as_date(row.fieldwork_mid)
        age = (as_of_date - mid).days
        decay = 0.5 ** (age / half_life_days)
        eff = row.get("effective_sample_size")
        if pd.isna(eff):
            eff = row.sample_size
        precision = min(float(eff), float(effective_sample_cap))
        return precision * decay

    ev["benchmark_weight"] = ev.apply(event_weight, axis=1)
    weights = ev.set_index("poll_id").benchmark_weight
    merged = harmonised.merge(weights.rename("weight"), left_on="poll_id", right_index=True)
    estimates_out = {}
    for party, group in merged.groupby("party_id", observed=True):
        estimates_out[party] = float(np.average(group.primary_pct, weights=group.weight))

    # Numeric noise aside, every included poll is a coherent five-way 100% vector.
    total = sum(estimates_out.values())
    if abs(total - 100.0) > 1e-7:
        raise PollDataError(f"benchmark composition sums to {total}, not 100")

    return PollBenchmarkResult(
        as_of=as_of_date,
        regime_filter=regime_filter,
        half_life_days=float(half_life_days),
        poll_count=len(ev),
        estimates=estimates_out,
        effective_weight_sum=float(ev.benchmark_weight.sum()),
    )


def benchmark_sensitivity(
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    as_of: str | date | datetime,
    current_leader_regime: str,
    half_lives: tuple[int, ...] = (21, 45, 90),
) -> pd.DataFrame:
    rows = []
    for regime in ("all_eligible", "current_leader_regime_only"):
        for half_life in half_lives:
            try:
                result = poll_benchmark(
                    events,
                    estimates,
                    as_of=as_of,
                    half_life_days=half_life,
                    regime_filter=regime,
                    current_leader_regime=current_leader_regime,
                )
            except PollDataError:
                continue
            for party, value in result.estimates.items():
                rows.append({
                    "as_of": result.as_of.isoformat(),
                    "regime_filter": regime,
                    "half_life_days": half_life,
                    "poll_count": result.poll_count,
                    "party_id": party,
                    "primary_pct": value,
                })
    return pd.DataFrame(rows)
