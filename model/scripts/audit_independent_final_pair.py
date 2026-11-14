"""Describe historical final-pair survival for the leading independent in each seat."""
import csv
import json
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data/processed"
RANKS = ("first", "second", "third", "fourth or lower")


def read(year, suffix):
    with (DATA / f"vec_{year}_assembly_{suffix}.csv").open() as stream:
        return list(csv.DictReader(stream))


def audit(year):
    seats = defaultdict(list)
    for row in read(year, "candidate_primaries"):
        if row["contest"] == "general-election":
            seats[row["district_id"]].append(row)
    final = {row["district_id"]: row for row in read(year, "final_pairs")}
    ranks = {key: dict(finalist=0, eliminated=0, unknown=0) for key in RANKS}
    for district, candidates in seats.items():
        independents = [row for row in candidates if row["independent_status"].lower() == "true"]
        if not independents:
            continue
        vote = lambda row: int(row["first_preference_votes"])
        leading = max(independents, key=vote)
        if sum(vote(row) == vote(leading) for row in candidates) > 1:
            raise ValueError(f"Tied rank requires manual review: {year} {district}")
        rank = min(3, sum(vote(row) > vote(leading) for row in candidates))
        result = final[district]
        pair = [result[f"finalist_{i}_candidate"] for i in (1, 2)]
        if result["outcome_table_kind"] == "final-pair-unavailable-early-majority":
            status = "unknown"
        elif not all(pair):
            raise ValueError(f"Missing finalists: {year} {district}")
        else:
            names = {row["candidate_name"].casefold() for row in candidates}
            if not all(name.casefold() in names for name in pair):
                raise ValueError(f"Unmatched historical finalist: {year} {district}: {pair}")
            status = "finalist" if leading["candidate_name"].casefold() in {name.casefold() for name in pair} else "eliminated"
        ranks[RANKS[rank]][status] += 1
    return ranks


if __name__ == "__main__":
    print(json.dumps({year: audit(year) for year in (2014, 2018, 2022)}, indent=2))
