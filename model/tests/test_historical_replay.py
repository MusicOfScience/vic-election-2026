from pathlib import Path

import pytest

from vicforecast.historical_replay import (
    ReplayContractError,
    eligible_pre_cutoff_records,
    run_historical_replay,
)


ROOT = Path(__file__).resolve().parents[1]


def test_all_frozen_cycles_fail_closed_with_structured_blockers():
    for cycle_id in ("vic_la_2010", "vic_la_2014", "vic_la_2018", "vic_la_2022"):
        result = run_historical_replay(ROOT, cycle_id)
        assert result.status == "blocked"
        assert result.blockers == (
            "pre-election-poll-vintages",
            "ballot-and-contest-slates",
            "preference-flows-and-final-pairs",
        )
        assert result.prediction is None
        assert result.metrics is None


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
