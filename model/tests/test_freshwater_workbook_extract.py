from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/extract-freshwater-workbooks.py"
spec = importlib.util.spec_from_file_location("extract_freshwater_workbooks", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_extract_rows_finds_current_primary_and_main_tpp():
    sheets = {
        "Methodology": [
            ["Fieldwork dates: 31 July - 3 August 2026"],
            ["Sample: 1,020 Victorian voters"],
        ],
        "Tables": [
            [module.PRIMARY_QUESTION + " (Squeezed & Valid)"],
            ["Column %", "Total"],
            ["The Labor Party", 0.2466],
            ["Liberals & Nationals", 0.3030],
            ["One Nation", 0.2161],
            ["The Greens", 0.1447],
            ["Other", 0.0896],
            ["Unweighted n", 952],
            ["TPP (Squeezed & Valid)"],
            ["Column %", "Total"],
            ["Labor Party", 0.4816],
            ["Liberals & Nationals", 0.5184],
            ["Unweighted n", 928],
            ["TPP (Labor v One Nation) (Squeezed & Valid)"],
            ["Labor Party", 0.526],
            ["One Nation", 0.474],
        ],
    }
    result = module.extract_rows(sheets)
    assert result["sampleSize"] == 1020
    assert result["primaryVoteRounded"] == {"alp": 25, "coalition": 30, "oneNation": 22, "greens": 14, "otherParties": 9}
    assert result["twoPartyPreferredRounded"] == {"alp": 48, "coalition": 52}
    assert result["primaryVoteUnweightedBase"] == 952
    assert result["twoPartyPreferredUnweightedBase"] == 928


def test_extract_rows_rejects_incomplete_primary_table():
    sheets = {
        "Methodology": [["Fieldwork dates: 1-2 August 2026"], ["Sample: 1,000 Victorian voters"]],
        "Tables": [[module.PRIMARY_QUESTION], ["The Labor Party", 0.25], ["TPP (Valid)"], ["Labor Party", 0.48], ["Liberals & Nationals", 0.52]],
    }
    try:
        module.extract_rows(sheets)
    except ValueError as error:
        assert "incomplete primary-vote table" in str(error)
    else:
        raise AssertionError("incomplete table should fail closed")
