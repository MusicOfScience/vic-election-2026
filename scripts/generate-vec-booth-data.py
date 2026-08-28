#!/usr/bin/env python3
"""Build the dashboard's official VEC 2022 voting-centre dataset.

The script intentionally scrapes the VEC's state-election pages rather than
substituting the AEC's federal polling-place files. It retains ordinary voting
centres only; early, postal, absent and provisional votes remain district-wide
vote modes and are not presented as physical booths.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.vec.vic.gov.au/results/state-election-results/2022-state-election-results/results-by-district"
PARTIES = ("ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND")


def load_districts() -> list[dict]:
    text = (ROOT / "app/model-output.generated.ts").read_text(encoding="utf-8")
    match = re.search(r"export const modelOutput = (.*) as const;\s*$", text, re.S)
    if not match:
        raise RuntimeError("could not parse app/model-output.generated.ts")
    return json.loads(match.group(1))["districts"]


def party_group(raw: object) -> str:
    value = "" if pd.isna(raw) else str(raw).casefold()
    if "australian labor party" in value:
        return "ALP"
    if "liberal" in value or "the nationals" in value:
        return "LIB_NAT"
    if "one nation" in value:
        return "ONP"
    if "australian greens" in value:
        return "GRN"
    return "OTH_IND"


def as_int(value: object) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    return 0 if pd.isna(numeric) else int(numeric)


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Victorian-Election-Forecasting-Laboratory/2026 (public research dashboard)"})
    with urlopen(request, timeout=35) as response:
        return response.read().decode("utf-8")


def ordinary_rows(frame: pd.DataFrame, label_column: object) -> pd.DataFrame:
    labels = frame[label_column].astype("string")
    matches = labels[labels.str.casefold() == "ordinary votes total"].index
    if matches.empty:
        raise RuntimeError("ordinary-vote boundary missing")
    return frame.loc[: matches[0] - 1].copy()


def parse_primary(html: str) -> tuple[list[dict], dict[str, str]]:
    frame = pd.read_html(StringIO(html), flavor="lxml")[0]
    label_column = frame.columns[0]
    candidate_columns = list(frame.columns[1:-2])
    frame = ordinary_rows(frame, label_column)
    candidates = {}
    for column in candidate_columns:
        candidate, party = column if isinstance(column, tuple) else (column, "")
        candidates[str(candidate)] = party_group(party)

    booths = []
    for _, row in frame.iterrows():
        name = str(row[label_column]).strip()
        grouped = {party: 0 for party in PARTIES}
        for column in candidate_columns:
            _, party = column if isinstance(column, tuple) else (column, "")
            grouped[party_group(party)] += as_int(row[column])
        informal = as_int(row.iloc[-2])
        total = as_int(row.iloc[-1])
        formal = sum(grouped.values())
        booths.append({
            "name": name,
            "formal": formal,
            "informal": informal,
            "total": total,
            "primaryVotes": grouped,
            "primaryPct": {party: round(100 * votes / formal, 2) if formal else 0 for party, votes in grouped.items()},
        })
    return booths, candidates


def parse_two_candidate(html: str) -> tuple[dict[str, dict], list[dict]]:
    frame = pd.read_html(StringIO(html), flavor="lxml", header=None)[0]
    if len(frame) < 3 or frame.shape[1] < 4:
        raise RuntimeError("unexpected 2CP table")
    candidates = [
        {"name": str(frame.iloc[0, index]), "party": str(frame.iloc[1, index])}
        for index in (1, 2)
    ]
    data = frame.iloc[2:].copy()
    data.columns = range(data.shape[1])
    data = ordinary_rows(data, 0)
    by_booth = {}
    for _, row in data.iterrows():
        name = str(row.iloc[0]).strip()
        votes = [as_int(row.iloc[index]) for index in (1, 2)]
        formal = sum(votes)
        by_booth[name] = {
            "votes": votes,
            "pct": [round(100 * value / formal, 2) if formal else 0 for value in votes],
        }
    return by_booth, candidates


def build_district(district: dict) -> dict:
    district_id = district["district_id"]
    if district_id == "narracan":
        return {"districtId": district_id, "districtName": district["district_name"], "booths": [], "status": "supplementary-election-source-required"}
    root = f"{BASE}/{district_id}-district-results"
    primary_html = fetch(f"{root}/{district_id}-district-results-by-voting-centre")
    two_candidate_html = fetch(f"{root}/{district_id}-2cp-results-by-voting-centre")
    booths, candidate_groups = parse_primary(primary_html)
    two_candidate, final_two = parse_two_candidate(two_candidate_html)
    for booth in booths:
        booth["twoCandidate"] = two_candidate.get(booth["name"])
    return {
        "districtId": district_id,
        "districtName": district["district_name"],
        "status": "official-vec-2022",
        "source": f"{root}/{district_id}-district-results-by-voting-centre",
        "twoCandidateSource": f"{root}/{district_id}-2cp-results-by-voting-centre",
        "candidateGroups": candidate_groups,
        "finalTwo": final_two,
        "booths": booths,
    }


def main() -> int:
    districts = load_districts()
    output = []
    failures = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(build_district, district): district for district in districts}
        for future in as_completed(futures):
            district = futures[future]
            try:
                output.append(future.result())
                print(f"ok {district['district_name']}", file=sys.stderr)
            except Exception as error:
                failures.append({"districtId": district["district_id"], "districtName": district["district_name"], "error": str(error)})
                print(f"failed {district['district_name']}: {error}", file=sys.stderr)
    output.sort(key=lambda row: row["districtName"])
    payload = {"source": "Victorian Electoral Commission 2022 state election", "districts": output, "failures": failures}
    target = ROOT / "app/booth-data.generated.ts"
    target.write_text(f"// Generated by scripts/generate-vec-booth-data.py\nexport const boothData = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))} as const;\n", encoding="utf-8")
    print(json.dumps({"districts": len(output), "booths": sum(len(row.get("booths", [])) for row in output), "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
