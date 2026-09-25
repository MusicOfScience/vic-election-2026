"""Extract the scoring-only 2010 Assembly winner/final-pair artefact.

This script is intentionally separate from prediction construction.  It may
only be run after the sealed 2010 prediction/comparator verification event.
It reads official VEC result pages and emits no model-input artefact.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from urllib.parse import urljoin
from pathlib import Path
from urllib.request import Request, urlopen

from extract_vec_2022_assembly_final_pairs import TableParser, elected_member, normalise
from extract_vec_2018_final_pairs import parse_distribution

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ROOT / "model/data/processed/vec_2010_assembly_candidate_primaries.csv"
OUT = ROOT / "model/data/processed/vec_2010_assembly_final_pairs.csv"
CACHE = ROOT / ".cache/vec-2010-assembly-final-pairs"
CROSSWALK = ROOT / "model/config/historical-party-family-crosswalk.json"
BASE_URL = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/state2010/"
FAMILIES = {"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "Other/Independent": "OTH_IND"}


def normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def slug(value: str) -> str:
    # The VEC's historical blob preserves the hyphen in South-West Coast but
    # removes spaces from ordinary district names.
    return re.sub(r"[^a-z0-9-]+", "", value.casefold())


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    path = CACHE / (slug(url.rsplit("/", 1)[-1]) + ".html")
    if path.exists():
        return path.read_bytes()
    CACHE.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "vic-election-2026-outcome-scoring/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
    if not payload:
        raise ValueError(f"empty VEC response: {url}")
    path.write_bytes(payload)
    return payload


def parse_number(value: str) -> int:
    value = value.replace(",", "").strip()
    if not value.isdigit():
        raise ValueError(f"invalid vote total {value!r}")
    return int(value)


def parse_percent(value: str) -> float:
    return float(value.replace("%", "").strip())


def final_distribution_table(source: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(source)
    for table in parser.tables:
        if not table:
            continue
        headers = [normalise(cell) for cell in table[0]]
        if headers[:3] == ["candidate", "party", "votes after distribution"]:
            return [row[:4] for row in table[1:] if len(row) >= 4 and row[0].strip()]
    return []


def main() -> None:
    aliases = json.loads(CROSSWALK.read_text())["aliases"]
    alias_map = {normalise(name): family for family, names in aliases.items() for name in names}
    primary = list(csv.DictReader(PRIMARY.open(encoding="utf-8")))
    districts = {}
    family_by_candidate = {}
    family_by_name = {}
    party_by_candidate = {}
    for row in primary:
        districts.setdefault(row["district_id"], row)
        family_by_candidate[(row["district_id"], normalise(row["candidate_name"]))] = row["party_family"]
        family_by_name[normalise(row["candidate_name"])] = row["party_family"]
        party_by_candidate[normalise(row["candidate_name"])] = row["party_raw"]
        surname = normalise(row["candidate_name"]).split(",", 1)[0].strip()
        family_by_name.setdefault(surname, row["party_family"])
        party_by_candidate.setdefault(surname, row["party_raw"])
        for token in surname.split():
            if len(token) >= 3:
                family_by_name.setdefault(token, row["party_family"])
                party_by_candidate.setdefault(token, row["party_raw"])
    if len(districts) != 88:
        raise ValueError(f"expected 88 primary districts, found {len(districts)}")
    fields = [
        "election_id", "district_id", "district_name", "source_url", "source_sha256", "outcome_source_url", "outcome_source_sha256",
        "elected_candidate", "elected_party_raw", "elected_party_family",
        "finalist_1_candidate", "finalist_1_party_raw", "finalist_1_party_family", "finalist_1_votes", "finalist_1_percent",
        "finalist_2_candidate", "finalist_2_party_raw", "finalist_2_party_family", "finalist_2_votes", "finalist_2_percent",
        "winner_party_family", "final_pair_family_label", "final_pair_available", "final_pair_reason", "outcome_table_kind", "target_outcome_dependency",
    ]
    results = []
    for district_id, first in sorted(districts.items()):
        name = first["district_name"]
        url = BASE_URL + f"state2010result{slug(name)}district.html"
        payload = fetch(url)
        source = payload.decode("utf-8", "replace")
        # The official page's Results after distribution table is the source of
        # truth. No primary-only or TCP/2CP fallback is permitted.
        finalists = final_distribution_table(source)
        outcome_url = url
        outcome_sha = sha(payload)
        table_kind = "results-after-distribution"
        if len(finalists) != 2:
            link = re.search(r'href=["\']([^"\']*distribution[^"\']*district\.html)["\']', source, flags=re.I)
            if link:
                outcome_url = urljoin(url, link.group(1))
                distribution_payload = fetch(outcome_url)
                outcome_sha = sha(distribution_payload)
                distribution_source = distribution_payload.decode("utf-8", "replace")
                table_parser = TableParser()
                table_parser.feed(distribution_source)
                for table in table_parser.tables:
                    if table and table[0] and table[0][0].strip() == "":
                        for candidate in table[0][1:-1]:
                            surname = normalise(candidate).split(",", 1)[0].strip()
                            if surname in party_by_candidate:
                                party_by_candidate[normalise(candidate)] = party_by_candidate[surname]
                                family_by_name[normalise(candidate)] = family_by_name[surname]
                parsed, table_kind, _ = parse_distribution(distribution_source, outcome_url, party_by_candidate, family_by_name, alias_map)
                finalists = [[candidate, party or party_by_candidate.get(normalise(candidate), ""), str(votes), f"{percent:.2f}%"] for candidate, party, votes, percent, _family in parsed]
            else:
                finalists = []
                table_kind = "final-pair-unavailable-early-majority"
        candidate_names = [row[0].strip() for row in finalists]
        elected_name, elected_party = elected_member(source, name, candidate_names)
        mapped = []
        for candidate, party, votes, percent in finalists:
            raw = party.strip()
            family = alias_map.get(normalise(raw))
            if family is None:
                # The official table may use ALP/Liberal shorthand; resolve it
                # through the governed candidate-primary family identity.
                family = family_by_candidate.get((district_id, normalise(candidate)))
            if family is None:
                raise ValueError(f"{name}: unknown final-pair party {raw!r}")
            mapped.append((candidate.strip(), raw, family, parse_number(votes), parse_percent(percent)))
        if len(mapped) > 2:
            raise ValueError(f"{name}: official final-pair table has more than two rows")
        elected_family = family_by_candidate.get((district_id, normalise(elected_name)))
        if elected_family is None:
            elected_family = alias_map.get(normalise(elected_party))
        if elected_family is None:
            raise ValueError(f"{name}: unknown elected family {elected_party!r}")
        if len(mapped) == 2:
            if elected_name not in {mapped[0][0], mapped[1][0]}:
                raise ValueError(f"{name}: elected member is absent from final pair")
            if max(mapped[0][3], mapped[1][3]) == min(mapped[0][3], mapped[1][3]):
                raise ValueError(f"{name}: tied final-pair totals")
            winner = mapped[0] if mapped[0][3] > mapped[1][3] else mapped[1]
            if winner[0] != elected_name:
                raise ValueError(f"{name}: final-pair leader is not elected member")
            if abs(mapped[0][4] + mapped[1][4] - 100.0) > 0.25:
                raise ValueError(f"{name}: final-pair percentages do not reconcile")
        elif mapped:
            raise ValueError(f"{name}: malformed final-distribution table")
        pair_available = len(mapped) == 2
        results.append({
            "election_id": "vic_la_2010", "district_id": district_id, "district_name": name,
            "source_url": url, "source_sha256": sha(payload), "outcome_source_url": outcome_url, "outcome_source_sha256": outcome_sha,
            "elected_candidate": elected_name, "elected_party_raw": elected_party, "elected_party_family": elected_family,
            "finalist_1_candidate": mapped[0][0] if pair_available else "", "finalist_1_party_raw": mapped[0][1] if pair_available else "", "finalist_1_party_family": mapped[0][2] if pair_available else "", "finalist_1_votes": mapped[0][3] if pair_available else "", "finalist_1_percent": mapped[0][4] if pair_available else "",
            "finalist_2_candidate": mapped[1][0] if pair_available else "", "finalist_2_party_raw": mapped[1][1] if pair_available else "", "finalist_2_party_family": mapped[1][2] if pair_available else "", "finalist_2_votes": mapped[1][3] if pair_available else "", "finalist_2_percent": mapped[1][4] if pair_available else "",
            "winner_party_family": elected_family, "final_pair_family_label": f"{mapped[0][2]}-{mapped[1][2]}" if pair_available else "", "final_pair_available": pair_available, "final_pair_reason": "official-results-after-distribution-of-preferences" if pair_available else "official-page-exposes-only-two-candidate-preferred-or-early-majority", "outcome_table_kind": table_kind, "target_outcome_dependency": False,
        })
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "rows": len(results), "sha256": sha(OUT.read_bytes()), "finalPairAvailable": sum(bool(row["final_pair_available"]) for row in results), "finalPairUnavailable": sum(not bool(row["final_pair_available"]) for row in results)}))


if __name__ == "__main__":
    main()
