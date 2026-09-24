from pathlib import Path
import json

import pytest

from vicforecast.historical_replay import (
    ReplayContractError,
    _score_prediction,
    eligible_pre_cutoff_records,
    run_historical_replay,
)


ROOT = Path(__file__).resolve().parents[1]


def test_incomplete_cycles_fail_closed_with_structured_blockers():
    for cycle_id in ("vic_la_2010", "vic_la_2014", "vic_la_2022"):
        result = run_historical_replay(ROOT, cycle_id)
        assert result.status == "blocked"
        assert result.blockers
        assert all(blocker in {"pollEvidence", "ballotContest", "incumbencyLocal", "councilInput"} for blocker in result.blockers)
        assert result.prediction is None
        assert result.metrics is None


def test_2018_replay_execution_is_separate_from_production_compatibility():
    config = json.loads((ROOT / "config/historical-validation-cycles.json").read_text())
    assert config["replayExecutable"] is True
    assert config["productionCompatible"] is False
    with pytest.raises(ReplayContractError, match="prediction is immutable"):
        run_historical_replay(ROOT, "vic_la_2018")


def test_later_evidence_is_a_contract_error_not_silently_ignored():
    with pytest.raises(ReplayContractError, match="published after 2018-11-23"):
        eligible_pre_cutoff_records(
            [{"id": "later-poll", "publicationDate": "2018-11-24"}],
            "2018-11-23",
        )


def test_missing_availability_date_cannot_prove_cutoff_eligibility():
    with pytest.raises(ReplayContractError, match="publicationDate"):
        eligible_pre_cutoff_records([{"id": "undated"}], "2022-11-25")


def test_outcomes_cannot_enter_prediction_phase():
    with pytest.raises(ReplayContractError, match="before prediction is frozen"):
        run_historical_replay(ROOT, "vic_la_2022", outcomes=[{"district": "Example"}])


def test_scoring_requires_frozen_probabilities_and_outcomes():
    with pytest.raises(ReplayContractError, match="scoring requires"):
        _score_prediction({}, [{"outcome": 1}])


def test_scoring_rejects_length_mismatch_before_metric_import():
    with pytest.raises(ReplayContractError, match="equal length"):
        _score_prediction({"probabilities": [0.5, 0.6]}, [{"outcome": 1}])
