import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def test_2022_selection_is_frozen_before_scoring_and_remains_blocked():
    selection = json.loads((REPO / "metadata/historical-replay-next-cycle-selection.json").read_text())
    assert selection["selectedCycle"] == "vic_la_2022"
    assert "pending" in selection["status"]
    assert selection["candidates"]["vic_la_2022"]["blockingInputs"]


def test_2022_poll_cases_are_cutoff_safe_but_not_auto_promoted():
    review = json.loads((REPO / "metadata/historical-poll-reuse-review-2022.json").read_text())
    assert review["decision"] == "awaiting-project-owner-approval"
    assert review["checks"]["ownerReuseBasisApproval"] is False
    for case_path in sorted((REPO / "metadata").glob("historical-poll-reuse-case-2022-*.json")):
        case = json.loads(case_path.read_text())
        assert case["cycleId"] == "vic_la_2022"
        assert case["evidenceAvailableByDate"] <= "2022-11-25"
        assert case["replayEligible"] is False
        assert case["modelInputAdmissible"] is False
    canonical = json.loads((ROOT / "data/validation/historical-replay-poll-observations.json").read_text())
    assert not any(row["cycleId"] == "vic_la_2022" for row in canonical["observations"])


def test_2022_boundary_audit_does_not_substitute_target_outcomes():
    audit = json.loads((REPO / "metadata/historical-replay-2022-boundary-audit.json").read_text())
    assert audit["availability"]["presentLocally"] is True
    assert audit["availability"]["preCutoffPublicationProven"] is True
    assert audit["availability"]["coverageRows"] == 87
    assert audit["targetGeography"]["excludedSupplementaryDistrict"] == "Narracan"
    assert audit["councilRegionAudit"]["directContinuityAssumed"] is False


def test_2022_boundary_baseline_has_one_cutoff_safe_row_per_general_election_district():
    import csv

    path = ROOT / "data/processed/vec_2018_estimated_2022_boundary_2cp.csv"
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 87
    assert len({row["district_id"] for row in rows}) == 87
    assert all(row["district_name"] != "Narracan" for row in rows)
    for row in rows:
        alp = float(row["estimated_2018_alp_tpp_share"])
        coalition = float(row["estimated_2018_coalition_tpp_share"])
        assert abs((alp + coalition) - 100) <= 0.05


def test_2022_boundary_baseline_provenance_is_pre_cutoff_and_declares_tpp_limit():
    record = json.loads((REPO / "metadata/historical-replay-2022-boundary-baseline.json").read_text())
    assert record["source"]["publisher"] == "Victorian Electoral Commission"
    assert record["source"]["publicationDate"] < "2022-11-25"
    assert record["source"]["availableByCutoff"] is True
    assert "multi-party" in record["limitations"][0]


def test_2022_council_region_audit_rejects_direct_name_join_for_changed_region():
    audit = json.loads((REPO / "metadata/historical-replay-2022-council-region-audit.json").read_text())
    assert audit["directNameContinuity"] is False
    assert "North-Eastern Metropolitan Region" in audit["targetRegions"]
    assert "Eastern Metropolitan Region" in audit["priorRegions"]
    assert audit["targetOutcomesScoringOnly"] is True
