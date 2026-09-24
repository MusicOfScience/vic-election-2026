"""Fail-closed orchestration for leakage-safe historical replays.

The four cycle specifications are intentionally unrunnable until their input
evidence is complete.  This module makes that state executable: callers get a
machine-readable blocker result instead of accidentally falling back to the
current 2026 inputs or loading scoring outcomes during prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping



class ReplayContractError(ValueError):
    """Raised when a replay request would violate the frozen contract."""


@dataclass(frozen=True)
class ReplayResult:
    cycle_id: str
    status: str
    information_cutoff: str
    seed: int
    blockers: tuple[str, ...] = ()
    prediction: Mapping[str, Any] | None = None
    metrics: Mapping[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cycleId": self.cycle_id,
            "status": self.status,
            "informationCutoff": self.information_cutoff,
            "seed": self.seed,
            "blockers": list(self.blockers),
            "prediction": self.prediction,
            "metrics": self.metrics,
        }


def _load_config(root: Path) -> dict[str, Any]:
    path = root / "config/historical-validation-cycles.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _cycle(config: Mapping[str, Any], cycle_id: str) -> Mapping[str, Any]:
    for cycle in config.get("cycles", []):
        if cycle.get("id") == cycle_id:
            return cycle
    raise ReplayContractError(f"unknown historical replay cycle: {cycle_id}")


def _iso(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ReplayContractError(f"invalid ISO date in replay evidence: {value}") from exc


def eligible_pre_cutoff_records(records: Iterable[Mapping[str, Any]], cutoff: str, *, date_field: str = "publicationDate") -> list[Mapping[str, Any]]:
    """Return records available by cutoff and reject records without dates.

    A missing availability date cannot prove pre-cutoff availability.  A later
    record is a contract violation rather than something to silently discard,
    because silently discarding it would hide a leakage bug in a caller.
    """
    cutoff_date = _iso(cutoff)
    eligible: list[Mapping[str, Any]] = []
    for record in records:
        value = record.get(date_field)
        if not value:
            raise ReplayContractError(f"{record.get('id', '<record>')} has no {date_field}")
        available = _iso(str(value))
        if available > cutoff_date:
            raise ReplayContractError(
                f"{record.get('id', '<record>')} is published after {cutoff}: {value}"
            )
        eligible.append(record)
    return eligible


def run_historical_replay(
    root: str | Path,
    cycle_id: str,
    *,
    poll_records: Iterable[Mapping[str, Any]] = (),
    ballot_records: Iterable[Mapping[str, Any]] = (),
    preference_records: Iterable[Mapping[str, Any]] = (),
    forecast_runner: Callable[..., Mapping[str, Any]] | None = None,
    outcomes: Iterable[Mapping[str, Any]] | None = None,
) -> ReplayResult:
    """Run or block one frozen cycle without mixing prediction and scoring data.

    The current repository marks every cycle ``runnable: false``.  The runner
    therefore validates the contract and returns a structured blocked result.
    A future evidence-complete cycle may supply a forecast runner; outcomes are
    accepted only after that runner has returned an immutable prediction.
    """
    root_path = Path(root)
    config = _load_config(root_path)
    cycle = _cycle(config, cycle_id)
    cutoff = str(cycle["informationCutoff"])
    seed = int(cycle["seed"])

    # Always validate supplied prediction evidence, even while blocked.  This
    # catches a caller attempting to pass future information into a replay.
    poll = eligible_pre_cutoff_records(poll_records, cutoff)
    ballots = eligible_pre_cutoff_records(ballot_records, cutoff)
    preferences = eligible_pre_cutoff_records(preference_records, cutoff)
    del poll, ballots, preferences

    if outcomes is not None and forecast_runner is None:
        raise ReplayContractError("scoring outcomes cannot be supplied before prediction is frozen")

    blockers = tuple(cycle.get("blockedBy", ()))
    if not cycle.get("runnable", False):
        return ReplayResult(cycle_id, "blocked", cutoff, seed, blockers=blockers)
    if config.get("productionCompatible") is not True:
        raise ReplayContractError("historical replay contract is not production-compatible")
    if forecast_runner is None:
        raise ReplayContractError("runnable cycle requires an explicit forecast runner")
    if outcomes is None:
        raise ReplayContractError("runnable cycle requires separately loaded scoring outcomes")

    # Keep the blocked CLI usable in minimal environments; NumPy is required
    # only when an evidence-complete cycle actually reaches forecast execution.
    from .preference_prior import build_walk_forward_preference_prior

    preference_prior = build_walk_forward_preference_prior(cycle, preferences)
    prediction = dict(forecast_runner(root_path, cycle, seed=seed, preference_prior=preference_prior))
    if not prediction:
        raise ReplayContractError("forecast runner returned an empty prediction")
    metrics = {"scoringPending": True}
    return ReplayResult(cycle_id, "scored", cutoff, seed, prediction=prediction, metrics=metrics)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run one guarded historical replay")
    parser.add_argument("cycle_id")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        result = run_historical_replay(args.root, args.cycle_id)
    except ReplayContractError as exc:
        print(json.dumps({"status": "contract-error", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.status == "scored" else 2


if __name__ == "__main__":
    raise SystemExit(main())
