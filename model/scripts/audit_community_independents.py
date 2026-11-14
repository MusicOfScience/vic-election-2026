"""Compare verified nominees, historical candidate results and pooled projections."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "model/data/processed"
# Climate 200's October briefing names its four supported campaigns.
# Benambra and Shepparton are separate regional succession cases.
CONTESTS = [
    ("Kew", "TORNEY, Sophie", "TORNEY, Sophie"),
    ("Hawthorn", "IBUKI, Shima", "LOWE, Melissa"),
    ("Mornington", "GOFFIN, Melissa", "LARDNER, Kate"),
    ("Footscray", "MARSH, Jess", None),
    ("Benambra", "McKEEMAN, Lachie", "HAWKINS, Jacqui"),
    ("Shepparton", "COSTA, Lou", "SHEED, Suzanna"),
    ("Caulfield", None, "KALTMANN, Nomi"),
]


def records(name):
    with (DATA / name).open() as stream:
        return list(csv.DictReader(stream))


def audit():
    history = records("vec_2022_assembly_candidate_primaries.csv")
    final = {row["district_name"]: row for row in records("vec_2022_assembly_final_pairs.csv")}
    forecast = {row["district_name"]: row for row in records("experimental_forecast_2026_districts.csv")}
    roster = json.loads((ROOT / "app/vec-official-candidates-2026.review.json").read_text())["rows"]
    for seat, nominee, predecessor in CONTESTS:
        if nominee and sum(row[0] == "Assembly" and row[1] == seat and row[3] == nominee and row[4] is None
                           for row in roster) != 1:
            raise ValueError(f"Could not verify nominee in {seat}")
        primary = sorted((row for row in history if row["district_name"] == seat),
                         key=lambda row: -int(row["first_preference_votes"]))
        prior = next((row for row in primary if row["candidate_name"] == predecessor), None)
        if predecessor is not None and prior is None:
            raise ValueError(f"Missing historical comparator for {seat}")
        final_share = next((float(final[seat][f"finalist_{i}_percent"]) for i in (1, 2)
                            if final[seat][f"finalist_{i}_candidate"] == predecessor), None)
        yield {
            "seat": seat, "nominee": nominee, "comparator2022": predecessor,
            "primary2022Pct": round(100 * int(prior["first_preference_votes"]) / int(prior["formal_votes"]), 2) if prior else None,
            "primary2022Rank": primary.index(prior) + 1 if prior else None,
            "final2022Pct": final_share,
            "pooledModelPrimaryPct": round(float(forecast[seat]["primary_oth_ind"]), 2),
            "pooledModelWinPct": round(100 * float(forecast[seat]["win_oth_ind"]), 2),
        }


if __name__ == "__main__":
    print(json.dumps(list(audit()), indent=2))
