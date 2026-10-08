"""Cycle-aware historical poll category handling.

This adapter preserves what a poll reported and separately describes which
families could appear on that cycle's Assembly ballot. It never turns an
unreported family into a zero and never decomposes a grouped residual.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistoricalPollCategories:
    cycle_id: str
    active_families: tuple[str, ...]
    explicit_shares: dict[str, float]
    residual_share: float | None
    reported_but_unavailable: tuple[str, ...]


def translate_poll_categories(
    cycle_id: str,
    active_families: tuple[str, ...],
    reported_shares: dict[str, float],
    *,
    residual_key: str = "Other",
) -> HistoricalPollCategories:
    """Map reported categories without inventing missing shares.

    ``residual_key`` is retained as one grouped residual. A reported family
    outside the cycle ballot universe is diagnosed separately rather than
    silently reallocated.
    """
    active = set(active_families)
    explicit = {family: float(value) for family, value in reported_shares.items() if family in active and family != residual_key}
    residual = reported_shares.get(residual_key)
    unavailable = tuple(sorted(family for family in reported_shares if family not in active and family != residual_key))
    return HistoricalPollCategories(cycle_id, tuple(active_families), explicit, None if residual is None else float(residual), unavailable)
