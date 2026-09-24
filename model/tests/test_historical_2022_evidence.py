import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def test_2022_selection_remains_frozen_before_scoring():
    selection = json.loads((REPO / "metadata/historical-replay-next-cycle-selection.json").read_text())
    assert selection["selectedCycle"] == "vic_la_2022"
    assert "selected" in selection["status"]


def test_2022_poll_cases_keep_owner_decisions_separate_from_fixed_sufficiency_rule():
    review = json.loads((REPO / "metadata/historical-poll-reuse-review-2022.json").read_text())
    assert review["decision"] == "partially-approved"
    assert len(review["ownerDecision"]["approvedCaseIds"]) == 3
    for case_path in sorted((REPO / "metadata").glob("historical-poll-reuse-case-2022-*.json")):
        case = json.loads(case_path.read_text())
        assert case["cycleId"] == "vic_la_2022"
        assert case["evidenceAvailableByDate"] <= "2022-11-25"
        if "roymorgan" in case["caseId"]:
            assert case["replayEligible"] is True
            assert case["modelInputAdmissible"] is True
        elif "resolve" in case["caseId"]:
            assert case["replayEligible"] is True
            assert case["modelInputAdmissible"] is True
        else:
            assert case["replayEligible"] is False
            assert case["modelInputAdmissible"] is False
    canonical = json.loads((ROOT / "data/validation/historical-replay-poll-observations.json").read_text())
    promoted = [row for row in canonical["observations"] if row["cycleId"] == "vic_la_2022"]
    assert len(promoted) == 3
    assert {row["sourceId"] for row in promoted} == {"roy-morgan-vic-2022-11-09-10", "roy-morgan-vic-2022-11-22-23", "resolve-strategic-vic-2022-11-16-20"}


def test_2022_resolve_case_is_independent_and_owner_approved():
    case = json.loads((REPO / "metadata/historical-poll-reuse-case-2022-resolve-2022-11-16-20.json").read_text())
    assert case["gates"]["provenance"]["passed"] is True
    assert case["gates"]["methodologicalAdequacy"]["passed"] is True
    assert case["reuseBasis"] == "independently_reconstructed_factual_observation"
    assert case["ownerReviewStatus"] == "approved-for-historical-replay"
    assert case["modelInputAdmissible"] is True
    assert case["replayEligible"] is True
    assert case["notFromQuarantinedDataset"] is True
    assert case["sourceId"] not in {"roy-morgan-vic-2022-11-09-10", "roy-morgan-vic-2022-11-22-23"}
    assert case["groupedResidual"]["OTH_IND"] == 18
    assert sum(case["reportedPrimaryCategories"].values()) == 100


def test_2022_poll_sufficiency_passes_only_after_resolve_owner_approval():
    readiness = json.loads((REPO / "metadata/historical-replay-input-readiness.json").read_text())
    cycle = next(item for item in readiness["cycles"] if item["cycleId"] == "vic_la_2022")
    poll = cycle["pollEvidence"]
    assert poll["status"] == "pass"
    assert "fixed minimum" in poll["reason"]
    assert "3 observations" in poll["reason"]
    assert "2 independent source families" in poll["reason"]
    assert (ROOT / "data/validation/historical-replays/vic_la_2022-v2-prediction.json").exists() is True


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


def test_2022_local_surface_is_relative_and_excludes_state_outcome_targets():
    import csv

    audit = json.loads((REPO / "metadata/historical-replay-2022-local-input-audit.json").read_text())
    assert audit["rows"] == 87
    assert "ASSEMBLY_2022_TARGET" in audit["forbiddenInputs"]
    assert "vec_2022_indicative_candidate_evidence.csv" in audit["forbiddenInputs"]
    with (ROOT / "data/validation/historical-replay-2022-local-inputs.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 87
    assert len({row["district_id"] for row in rows}) == 87
    assert all(row["district_name"] != "Narracan" for row in rows)
    assert len({tuple(row[f"aec_local_{party.lower()}"] for party in ("ALP", "LIB_NAT", "GRN", "ONP", "OTH_IND")) for row in rows}) > 1
    for row in rows:
        total = sum(float(row[f"aec_local_{party.lower()}"]) for party in ("ALP", "LIB_NAT", "GRN", "ONP", "OTH_IND"))
        assert abs(total - 1) < 1e-9


def test_2022_council_surface_covers_current_regions_without_target_outcomes():
    audit = json.loads((REPO / "metadata/historical-replay-2022-council-surface-audit.json").read_text())
    assert audit["regionCount"] == 8
    assert audit["direct2018RegionJoinRequired"] is False
    assert audit["regionalPollContribution"] == 0
    assert "COUNCIL_2022_TARGET" in audit["forbiddenInputs"]
