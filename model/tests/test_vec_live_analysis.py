"""Private analysis export tests with no production feed dependency."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from vec_live.analysis import baselines, compare, polling_locations  # noqa: E402


def mapped(family):
    return {"affiliation": {"register": {"modelFamily": family}}}


def test_compares_assembly_primaries_and_only_compatible_party_pairings():
    primary, pairs = baselines()
    assert len(primary) == 87
    assert "narracan" not in primary
    contest = {"name": "Albert Park District",
               "candidates": {"a": mapped("ALP"), "c": mapped("LIB_NAT"), "g": mapped("GRN")}}
    count = {"first": {"status": "reported", "formal": {"votes": 100}, "candidates": {
        "a": {"votes": 42}, "c": {"votes": 26}, "g": {"votes": 32}}},
        "pair": {"status": "reported", "candidates": {"a": {"votes": 62}, "c": {"votes": 38}}}}
    output = compare(contest, count, (primary, pairs))
    assert {row["family"]: row["current"] for row in output["primary"]} == {"ALP": 42, "LIB_NAT": 26, "GRN": 32}
    assert {row["family"]: row["current"] for row in output["pair"]} == {"ALP": 62, "LIB_NAT": 38}
    count["pair"]["candidates"] = {"a": {"votes": 62}, "g": {"votes": 38}}
    assert compare(contest, count, (primary, pairs))["pair"] == []
    count["first"]["status"] = "unavailable"
    assert compare(contest, count, (primary, pairs)) is None


def test_location_results_keep_missing_and_withheld_votes_distinct_from_zero():
    values = {"places": {
        "1": {"first": {"status": "reported", "formal": {"votes": 0}, "informal": {"votes": 0},
                        "groups": {"a": {"votes": 0}}, "candidates": {"a": {"votes": 0}}},
              "pair": {"status": "withheld", "candidates": {}}},
        "2": {"first": None, "pair": {"status": "withheld", "candidates": {}}},
        "3": {"first": None, "pair": {"status": "unavailable", "candidates": {}}},
    }}
    rows = polling_locations(values, {key: {"name": key, "classification": None} for key in values["places"]})
    assert [row["id"] for row in rows] == ["1", "2"]
    assert rows[0]["firstVotes"] == {"a": 0, "group-a": 0}
    assert rows[0]["formal"] == 0
    assert rows[1]["formal"] is None and rows[1]["pairStatus"] == "withheld"
