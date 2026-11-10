"""Privacy and reconciliation tests for the VEC 2026 candidate-review extractor."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("extract_vec_nominations", ROOT / "scripts" / "extract_vec_nominations.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Sheet:
    def __init__(self, data):
        self.data = data
        self.nrows = max(data) + 1
        self.ncols = 5

    def cell_value(self, row, col):
        return self.data.get(row, {}).get(col, "")


def sample():
    return Sheet({
        0: {0: "Candidate Contact Persons' Details Summary Report"},
        1: {0: "State Election 2026"},
        3: {0: "As at 09 Nov 2026 07:58 PM"},
        6: {0: "Melbourne District"},
        7: {0: "(1 vacancy, 2 candidates) "},
        8: {0: "Candidates", 1: "Contact Person Name", 2: "Phone Contact", 3: "Email Address", 4: "RPP Name"},
        9: {0: "COURTIS, Phillip", 1: "private contact", 2: "0499 888 777",
            3: "private@example.com", 4: "One Nation Victoria"},
        10: {0: "SANDELL, Ellen", 1: "private manager", 2: "0400 123 456",
             3: "another@example.com", 4: "Australian Greens Victoria"},
        12: {0: "Eastern Victoria Region"},
        13: {0: "(5 vacancies, 2 candidates)"},
        14: {0: "Candidates", 1: "Contact Person Name", 2: "Phone Contact", 3: "Email Address", 4: "RPP Name"},
        15: {0: "FORWARD, Max", 1: "private contact", 3: "hidden@example.com", 4: "Victorian Socialists"},
        16: {0: "PERSON, Another", 1: "private person", 2: "0488 111 111"},
    })


def receipt():
    return {"sourceFileUrl": "https://www.vec.vic.gov.au/source.xls",
            "capturedAt": "2026-11-10T13:05:01Z"}


def test_whitelisted_official_fields_and_complete_counts():
    result = module.candidates_from_sheet(sample(), "a" * 64, receipt(),
                    expected={"Assembly": (1, 2), "Council": (1, 2)})
    assert result["candidateCount"] == 4
    assert result["assemblyCount"] == 2 and result["councilCount"] == 2
    assert result["contactDetailsIncluded"] is False
    assert all(set(x) == set(module.REQUIRED_FIELDS) for x in result["candidates"])
    assert result["candidates"][0]["candidate"] == "COURTIS, Phillip"
    assert result["candidates"][-1]["registeredParty"] is None
    text = json.dumps(result)
    assert "private@example.com" not in text
    assert "0499" not in text
    assert "private contact" not in text
    assert result["officialNominationAdmitted"] is False


def test_name_normalisation_does_not_decide_party_identity():
    data = module.candidates_from_sheet(sample(), "a" * 64, receipt(),
                 expected={"Assembly": (1, 2), "Council": (1, 2)})
    old = {"candidates": [
        {"contest": "Melbourne", "name": "Phillip Courtis", "party": "Something different"},
        {"contest": "Melbourne", "name": "Matthew Collins", "party": "One Nation"},
    ]}
    diff = module.review_against_provisional(data, old)
    assert diff["exactNormalizedNameMatches"] == 1
    assert diff["newOrIdentityReviewNeeded"] == 3
    assert diff["provisionalNotExactNameMatched"] == 1
    assert diff["matchingNames"][0]["reviewStatus"] == "identity-string-match-party-label-not-adjudicated"
    assert diff["provisionalNotMatched"][0]["name"] == "Matthew Collins"


def test_declared_count_mismatch_rejected():
    sheet = sample()
    sheet.data[7][0] = "(1 vacancy, 3 candidates)"
    with pytest.raises(ValueError, match="expected 3"):
        module.candidates_from_sheet(sheet, "a" * 64, receipt(),
                 expected={"Assembly": (1, 2), "Council": (1, 2)})


def test_duplicate_official_candidate_rejected():
    sheet = sample()
    sheet.data[10][0] = "COURTIS, Phillip"
    with pytest.raises(ValueError, match="Duplicate candidate"):
        module.candidates_from_sheet(sheet, "a" * 64, receipt(),
                 expected={"Assembly": (1, 2), "Council": (1, 2)})


def test_source_date_mismatch_rejected():
    sheet = sample()
    sheet.data[3][0] = "As at 03 Nov 2026"
    with pytest.raises(ValueError, match="publication date"):
        module.candidates_from_sheet(sheet, "a" * 64, receipt(),
                 expected={"Assembly": (1, 2), "Council": (1, 2)})
