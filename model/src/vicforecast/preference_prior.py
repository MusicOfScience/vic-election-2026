"""Leakage-safe preference priors for historical replay.

This module is deliberately separate from the 2026 forecast constants.  It
can construct a walk-forward prior for a frozen historical cycle without
promoting any post-cutoff transfer observations into forecast inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

import numpy as np


class PreferencePriorError(ValueError):
    """Raised when preference evidence violates the replay contract."""


@dataclass(frozen=True)
class PreferencePriorResult:
    matrix: np.ndarray
    concentration: float
    source_cycle_ids: tuple[str, ...]
    used_broad_fallback: bool


def _as_date(value: object, field: str) -> date:
    if value in (None, ""):
        raise PreferencePriorError(f"preference evidence is missing {field}")
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise PreferencePriorError(f"preference evidence has invalid {field}: {value!r}") from exc


def _broad_matrix(size: int) -> np.ndarray:
    if size < 2:
        raise PreferencePriorError("preference prior requires at least two parties")
    matrix = np.full((size, size), 1.0 / (size - 1), dtype=float)
    np.fill_diagonal(matrix, 0.0)
    return matrix


def build_walk_forward_preference_prior(
    target_cycle: Mapping[str, object],
    evidence_records: Iterable[Mapping[str, object]] = (),
    *,
    party_count: int = 5,
) -> PreferencePriorResult:
    """Build a prior using only evidence from cycles before ``target_cycle``.

    Evidence records must provide ``cycleId``, ``publicationDate`` and a
    square ``matrix``.  A record from the target cycle is rejected even when
    its publication date precedes the cutoff: target-cycle outcomes or
    parameters cannot train that cycle's prior.  With no eligible earlier
    record, the broad off-diagonal prior is retained with low concentration,
    representing uncertainty rather than fabricated precision.
    """
    target_id = str(target_cycle.get("id", ""))
    cutoff = _as_date(target_cycle.get("informationCutoff"), "target informationCutoff")
    target_year = int(target_id.rsplit("_", 1)[-1]) if target_id.rsplit("_", 1)[-1].isdigit() else None
    matrices: list[np.ndarray] = []
    source_ids: list[str] = []

    for record in evidence_records:
        cycle_id = str(record.get("cycleId", ""))
        available = _as_date(record.get("publicationDate"), "publicationDate")
        if available > cutoff:
            raise PreferencePriorError(
                f"preference evidence {cycle_id or '<unknown>'} is published after {cutoff.isoformat()}"
            )
        if cycle_id == target_id:
            raise PreferencePriorError("target-cycle preference evidence cannot train its own prior")
        cycle_year_text = cycle_id.rsplit("_", 1)[-1]
        cycle_year = int(cycle_year_text) if cycle_year_text.isdigit() else None
        if target_year is not None and (cycle_year is None or cycle_year >= target_year):
            raise PreferencePriorError("preference prior evidence must come from an earlier cycle")
        matrix = np.asarray(record.get("matrix"), dtype=float)
        if matrix.shape != (party_count, party_count):
            raise PreferencePriorError(f"preference matrix must be {party_count}x{party_count}")
        if not np.isfinite(matrix).all() or (matrix < 0).any():
            raise PreferencePriorError("preference matrix must contain finite non-negative values")
        matrix = matrix.copy()
        np.fill_diagonal(matrix, 0.0)
        row_totals = matrix.sum(axis=1)
        if not np.allclose(row_totals, 1.0, atol=1e-8):
            raise PreferencePriorError("preference matrix rows must sum to one off diagonal")
        matrices.append(matrix)
        source_ids.append(cycle_id)

    if not matrices:
        return PreferencePriorResult(_broad_matrix(party_count), 2.0, (), True)

    mean = np.mean(matrices, axis=0)
    mean /= mean.sum(axis=1, keepdims=True)
    return PreferencePriorResult(mean, float(max(2.0, 12.0 * len(matrices))), tuple(sorted(source_ids)), False)

