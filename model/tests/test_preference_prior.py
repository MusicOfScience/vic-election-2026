import numpy as np
import pytest

from vicforecast.preference_prior import PreferencePriorError, build_walk_forward_preference_prior


def cycle(year):
    return {"id": f"vic_la_{year}", "informationCutoff": f"{year}-11-25"}


def test_missing_earlier_evidence_uses_low_concentration_broad_prior():
    result = build_walk_forward_preference_prior(cycle(2010))
    assert result.used_broad_fallback is True
    assert result.concentration == 2.0
    assert np.allclose(result.matrix.sum(axis=1), 1.0)
    assert np.allclose(np.diag(result.matrix), 0.0)


def test_prior_uses_only_earlier_cycle_evidence():
    matrix = np.full((5, 5), 0.25)
    np.fill_diagonal(matrix, 0.0)
    result = build_walk_forward_preference_prior(cycle(2018), [{
        "cycleId": "vic_la_2014", "publicationDate": "2014-11-28", "matrix": matrix
    }])
    assert result.used_broad_fallback is False
    assert result.source_cycle_ids == ("vic_la_2014",)
    assert result.concentration == 12.0


@pytest.mark.parametrize("record", [
    {"cycleId": "vic_la_2018", "publicationDate": "2018-11-20", "matrix": np.full((5, 5), 0.25)},
    {"cycleId": "vic_la_2014", "publicationDate": "2018-11-29", "matrix": np.full((5, 5), 0.25)},
])
def test_target_or_post_cutoff_evidence_is_rejected(record):
    with pytest.raises(PreferencePriorError):
        build_walk_forward_preference_prior(cycle(2018), [record])

