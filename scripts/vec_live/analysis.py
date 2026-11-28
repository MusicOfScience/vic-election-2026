"""Conservative historical comparisons and compact private location results."""
import csv
from pathlib import Path

FAMILIES = {"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "One Nation": "ONP"}
BASE = Path(__file__).resolve().parents[2] / "model/data/processed"


def district_key(name):
    return " ".join(name.casefold().removesuffix(" district").split())


def baselines():
    primary, pair = {}, {}
    with (BASE / "vec_2022_assembly_family_primaries.csv").open() as source:
        for row in csv.DictReader(source):
            family = FAMILIES.get(row["party_family"])
            if (family and row["contest"] == "general-election" and row["contest_status"] == "contested"
                    and row["district_reconciled"] == "True" and int(row["formal_votes"]) > 0):
                primary.setdefault(district_key(row["district_name"]), {})[family] = (
                    100 * int(row["first_preference_votes"]) / int(row["formal_votes"]))
    with (BASE / "vec_2022_assembly_final_pairs.csv").open() as source:
        for row in csv.DictReader(source):
            if row["final_pair_available"] != "True" or row["outcome_table_kind"] != "results-after-distribution":
                continue
            a = FAMILIES.get(row["finalist_1_party_family"])
            b = FAMILIES.get(row["finalist_2_party_family"])
            if a and b and a != b:
                votes = [int(row["finalist_1_votes"]), int(row["finalist_2_votes"])]
                total = sum(votes)
                if total:
                    pair[district_key(row["district_name"])] = {
                        a: 100 * votes[0] / total, b: 100 * votes[1] / total}
    return primary, pair


def compare(contest, count, history):
    if not count:
        return None
    primary, pair = history
    district = district_key(contest["name"])
    families = {
        key: (((candidate.get("affiliation") or {}).get("register") or {}).get("modelFamily"))
        for key, candidate in contest["candidates"].items()
    }

    def changes(tallies, formal, baseline):
        changes = {}
        if formal:
            for key, tally in tallies.items():
                family = families.get(key)
                if family in baseline:
                    changes[family] = changes.get(family, 0) + tally["votes"]
        return [{"family": family, "prior": baseline[family], "current": 100 * votes / formal}
                for family, votes in changes.items()]

    first = count["first"] or {}
    preferred = count["pair"] or {}
    primary_rows = changes(first["candidates"], first["formal"]["votes"], primary.get(district, {})) \
        if first.get("status") == "reported" else []
    pair_rows = []
    if preferred.get("status") == "reported":
        tallies = preferred["candidates"]
        baseline = pair.get(district, {})
        if len(tallies) == len(baseline) == 2 and {families.get(k) for k in tallies} == baseline.keys():
            pair_rows = changes(tallies, sum(item["votes"] for item in tallies.values()), baseline)
    return {"primary": primary_rows, "pair": pair_rows} if primary_rows or pair_rows else None


def polling_locations(count, references):
    rows = []
    for location_id, parcel in (count or {}).get("places", {}).items():
        reference = references[location_id]
        first, pair = parcel["first"] or {}, parcel["pair"] or {}
        if first.get("status") != "reported" and pair.get("status") not in ("reported", "withheld", "incompatible"):
            continue
        reported = first.get("status") == "reported"
        rows.append({
            "id": location_id, "name": reference.get("name") or location_id,
            "classification": reference.get("classification"),
            "formal": first["formal"]["votes"] if reported else None,
            "informal": first["informal"]["votes"] if reported else None,
            "firstVotes": {
                **{key: item["votes"] for key, item in first.get("candidates", {}).items()},
                **{f"group-{key}": item["votes"] for key, item in first.get("groups", {}).items()},
            } if reported else {},
            "pairStatus": pair.get("status"),
            "pairVotes": {key: item["votes"] for key, item in pair.get("candidates", {}).items()},
        })
    return sorted(rows, key=lambda item: item["name"].casefold())
