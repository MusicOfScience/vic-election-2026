"""Build the scoring-only 2022 Assembly final-pair outcome artefact.

The source universe is the already fingerprinted VEC district manifest.  This
script reads only official result pages and deliberately excludes Narracan's
later supplementary contest.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_vec_2014_2022_assembly_primaries import TableParser, alias_map, normalise, sha256_bytes  # noqa: E402
from extract_vec_2018_final_pairs import parse_distribution  # noqa: E402


REPO = SCRIPT_DIR.parents[1]
MANIFEST = REPO / "metadata/vec-historical-assembly-primary-source-manifest.csv"
CROSSWALK = REPO / "model/config/historical-party-family-crosswalk.json"
DEFAULT_OUT = REPO / "model/data/processed/vec_2022_assembly_final_pairs.csv"
PRIMARY_INPUT = REPO / "model/data/processed/vec_2022_assembly_candidate_primaries.csv"


def plain_text(source: str) -> str:
    source = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", source)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", source)).split())


def fetch(url: str, cache: Path) -> bytes:
    if cache.exists():
        return cache.read_bytes()
    cache.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "vic-election-2026-outcome-scoring/1.0"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
    if not payload:
        raise ValueError(f"empty VEC response: {url}")
    cache.write_bytes(payload)
    return payload


def final_table(source: str, district: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(source)
    for table in parser.tables:
        if not table:
            continue
        headers = [normalise(cell) for cell in table[0]]
        if len(headers) >= 4 and headers[:3] == ["candidate", "party", "votes after distribution"]:
            rows = [row[:4] for row in table[1:] if len(row) >= 4 and row[0].strip()]
            if len(rows) >= 2:
                return rows
    raise ValueError(f"{district}: exactly two final-distribution rows not found")


def distribution_final(source: str, district: str) -> tuple[list[list[str]], str]:
    parser = TableParser()
    parser.feed(source)
    for table in parser.tables:
        if not table or not table[0] or normalise(table[0][0]) != "":
            continue
        final = next((row for row in table[1:] if row and normalise(row[0]) == "final total"), None)
        if final is None:
            continue
        names = table[0][1:-1]
        values = final[1:1 + len(names)]
        rows = [[name, "", value, ""] for name, value in zip(names, values) if value.strip()]
        if len(rows) >= 2:
            return rows, "distribution-page-final-total"
    raise ValueError(f"{district}: distribution page has no FINAL TOTAL row")


def elected_member(source: str, district: str, candidates: list[str]) -> tuple[str, str]:
    elected_block = re.search(r"<h3>\s*Elected member\s*</h3>.*?</table>", source, flags=re.I | re.S)
    if elected_block:
        candidate_match = re.search(r"class=[\"'][^\"']*bold-text[^\"']*[\"'][^>]*>\s*([^<]+)", elected_block.group(0), flags=re.I)
        party_match = re.search(r"class=[\"'][^\"']*italic[^\"']*[\"'][^>]*>\s*([^<]*)", elected_block.group(0), flags=re.I)
        if candidate_match and party_match:
            return candidate_match.group(1).strip(), party_match.group(1).strip()
    text = plain_text(source)
    for candidate in candidates:
        match = re.search(r"Elected member\s+" + re.escape(candidate) + r"\s+(.+?)\s+Re(?:check|count) votes", text, flags=re.I)
        if match:
            return candidate, match.group(1).strip()
    match = re.search(r"Elected member.*?\b([A-Z][A-Z ,.'-]+)\s+([A-Z][A-Z .&'-]+)\s+(?:Recheck|Recount) votes", text, flags=re.I | re.S)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    raise ValueError(f"{district}: elected member block not found")


def parse_number(value: str) -> int:
    value = value.replace(",", "").strip()
    if not value.isdigit():
        raise ValueError(f"invalid final vote value: {value!r}")
    return int(value)


def parse_percent(value: str) -> float:
    value = value.replace("%", "").strip()
    return float(value)


def build(cache_dir: Path, refreshed_manifest: Path | None = None, refresh_output: Path | None = None, workbook_dir: Path | None = None, workbook_index: Path | None = None, *, election_year: str = "2022", expected_count: int = 87, exclude_district: str | None = "Narracan", primary_input: Path = PRIMARY_INPUT, election_id: str = "vic_la_2022") -> list[dict[str, object]]:
    crosswalk = json.loads(CROSSWALK.read_text())
    aliases = alias_map(crosswalk)
    primary_rows = list(csv.DictReader(primary_input.open(encoding="utf-8")))
    known_independents = {
        (normalise(row["district_name"]), normalise(row["candidate_name"]))
        for row in primary_rows
        if row["party_family"] == "Other/Independent" and row["independent_status"].casefold() == "true"
    }
    party_by_candidate = {normalise(row["candidate_name"]): row["party_raw"] for row in primary_rows}
    family_by_candidate = {normalise(row["candidate_name"]): row["party_family"] for row in primary_rows}
    workbook_sources: dict[str, tuple[str, Path]] = {}
    if workbook_dir and workbook_index:
        index_text = workbook_index.read_text(encoding="utf-8")
        for match in re.finditer(r'href=["\']([^"\']+\.(?:xls|xlsx))["\'][^>]*>(.*?)</a>', index_text, flags=re.I | re.S):
            label = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", match.group(2))).split())
            if "District - indicative distribution" not in label or "Narracan" in label:
                continue
            district = label.split(" District - indicative", 1)[0]
            ext = match.group(1).rsplit(".", 1)[-1]
            workbook = workbook_dir / (district.lower().replace(" ", "-") + "." + ext)
            if workbook.exists():
                workbook_sources[district] = ("https://www.vec.vic.gov.au" + match.group(1), workbook)
    manifest = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    pages = [row for row in manifest if row["election_year"] == election_year and row["contest"] == "general-election" and row["district_name"] != "[summary]" and row["district_name"] != exclude_district]
    if len(pages) != expected_count or (exclude_district and any(row["district_name"] == exclude_district for row in pages)):
        raise ValueError(f"VEC {election_year} general-election source universe must be exactly {expected_count} districts")
    refreshed_rows: list[dict[str, str]] = []
    refreshed_by_url = {}
    if refreshed_manifest and refreshed_manifest.exists():
        refreshed_by_url = {row["source_url"]: row for row in csv.DictReader(refreshed_manifest.open(encoding="utf-8"))}
    results: list[dict[str, object]] = []
    for source in pages:
        district = source["district_name"]
        payload = fetch(source["source_url"], cache_dir / f"{source['district_name'].lower().replace(' ', '-')}.html")
        actual_sha = sha256_bytes(payload)
        if actual_sha != source["sha256"] and source["source_url"] not in refreshed_by_url and refresh_output is None:
            raise ValueError(f"{district}: source fingerprint differs from governed manifest; refresh must be explicit")
        governed_sha = refreshed_by_url.get(source["source_url"], {}).get("sha256", actual_sha if refresh_output else source["sha256"])
        if governed_sha != actual_sha:
            raise ValueError(f"{district}: refreshed source fingerprint does not match retrieved bytes")
        refreshed_rows.append({**source, "sha256": actual_sha})
        text = payload.decode("utf-8", "replace")
        try:
            finalists = final_table(text, district)
        except ValueError:
            finalists = []
        outcome_url = source["source_url"]
        outcome_sha = actual_sha
        if len(finalists) != 2:
            link = re.search(r'href=["\']([^"\']*distribution[^"\']*district\.html)["\']', text, flags=re.I)
            if link:
                outcome_url = urljoin(source["source_url"], link.group(1))
                distribution_payload = fetch(outcome_url, cache_dir / f"{source['district_name'].lower().replace(' ', '-')}-distribution.html")
                outcome_sha = sha256_bytes(distribution_payload)
                parsed, table_kind, _ = parse_distribution(distribution_payload.decode("utf-8", "replace"), outcome_url, party_by_candidate, family_by_candidate, aliases)
                finalists = [[candidate, party, str(votes), f"{percent:.2f}%"] for candidate, party, votes, percent, _family in parsed]
            else:
                # The page may expose only a 2CP table because the winner
                # reached an absolute majority.  That is not an official
                # final-pair outcome and is deliberately not substituted.
                finalists = []
                table_kind = "final-pair-unavailable-early-majority"
        else:
            table_kind = "results-after-distribution"
        candidate_names = [row[0].strip() for row in finalists] or [row["candidate_name"] for row in primary_rows if normalise(row["district_name"]) == normalise(district)]
        elected_name, elected_party = elected_member(text, district, candidate_names)
        mapped = []
        for candidate, party, votes, percent in finalists:
            raw = party.strip()
            if not raw:
                # VEC leaves independent-party cells blank.  This is accepted
                # only when the governed candidate-primary artefact explicitly
                # identifies the same district/candidate as an independent.
                if (normalise(district), normalise(candidate)) not in known_independents:
                    raise ValueError(f"{district}: blank final-pair party lacks governed independent identity for {candidate!r}")
                family = "Other/Independent"
            else:
                family = aliases.get(normalise(raw))
            if family is None:
                raise ValueError(f"{district}: unadjudicated final-pair party {raw!r}")
            mapped.append({"candidate": candidate.strip(), "party": raw, "family": family, "votes": parse_number(votes), "percent": parse_percent(percent) if percent else 0.0})
        if len(mapped) > 2:
            raise ValueError(f"{district}: unprocessed multi-row final table")
        elected_family = family_by_candidate.get(normalise(elected_name))
        if elected_family is None:
            elected_family = aliases.get(normalise(elected_party))
        if elected_family is None:
            raise ValueError(f"{district}: elected party is not in the governed crosswalk")
        if mapped:
            elected = [item for item in mapped if normalise(item["candidate"]) == normalise(elected_name)]
            if len(elected) != 1:
                raise ValueError(f"{district}: elected member is not exactly one final-pair candidate")
            if mapped[0]["votes"] == mapped[1]["votes"] or max(item["votes"] for item in mapped) != elected[0]["votes"]:
                raise ValueError(f"{district}: final-pair winner does not have the greater final vote total")
            if abs(sum(item["percent"] for item in mapped) - 100.0) > 0.02:
                raise ValueError(f"{district}: final-pair percentages do not reconcile")
        results.append({
            "election_id": election_id, "district_id": re.sub(r"[^a-z0-9]+", "-", district.casefold()).strip("-"), "district_name": district,
            "source_url": source["source_url"], "source_sha256": governed_sha, "retrieved_sha256": actual_sha, "outcome_source_url": outcome_url, "outcome_source_sha256": outcome_sha,
            "elected_candidate": elected_name, "elected_party_raw": elected_party, "elected_party_family": elected_family,
            "finalist_1_candidate": mapped[0]["candidate"] if mapped else None, "finalist_1_party_raw": mapped[0]["party"] if mapped else None, "finalist_1_party_family": mapped[0]["family"] if mapped else None, "finalist_1_votes": mapped[0]["votes"] if mapped else None, "finalist_1_percent": mapped[0]["percent"] if mapped else None,
            "finalist_2_candidate": mapped[1]["candidate"] if mapped else None, "finalist_2_party_raw": mapped[1]["party"] if mapped else None, "finalist_2_party_family": mapped[1]["family"] if mapped else None, "finalist_2_votes": mapped[1]["votes"] if mapped else None, "finalist_2_percent": mapped[1]["percent"] if mapped else None,
            "winner_party_family": elected_family, "final_pair_family_label": f"{mapped[0]['family']}-{mapped[1]['family']}" if mapped else None, "final_pair_available": bool(mapped), "final_pair_selection_rule": "governed-vec-final-total-parser" if mapped else "not-available-on-official-early-majority-page", "outcome_table_kind": table_kind, "alp_won": int(elected_family == "ALP"),
        })
    if len({row["district_id"] for row in results}) != expected_count:
        raise ValueError(f"duplicate or missing {election_year} Assembly district IDs")
    if refresh_output is not None:
        refresh_output.parent.mkdir(parents=True, exist_ok=True)
        with refresh_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["election_year", "district_name", "contest", "source_url", "sha256"], lineterminator="\n")
            writer.writeheader(); writer.writerows(sorted(refreshed_rows, key=lambda row: row["district_name"]))
    return sorted(results, key=lambda row: str(row["district_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--refreshed-manifest", type=Path)
    parser.add_argument("--refresh-manifest", type=Path)
    parser.add_argument("--workbook-dir", type=Path)
    parser.add_argument("--workbook-index", type=Path)
    parser.add_argument("--election-year", default="2022")
    parser.add_argument("--expected-count", type=int, default=87)
    parser.add_argument("--exclude-district", default="Narracan")
    parser.add_argument("--primary-input", type=Path, default=PRIMARY_INPUT)
    parser.add_argument("--election-id", default="vic_la_2022")
    args = parser.parse_args()
    rows = build(args.cache_dir, args.refreshed_manifest, args.refresh_manifest, args.workbook_dir, args.workbook_index, election_year=args.election_year, expected_count=args.expected_count, exclude_district=args.exclude_district, primary_input=args.primary_input, election_id=args.election_id)
    fields = list(rows[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"path": str(args.output.resolve().relative_to(REPO)), "rows": len(rows), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "excludedDistrict": args.exclude_district, "finalPairUnavailable": sum(1 for row in rows if not row["final_pair_available"])}))


if __name__ == "__main__":
    main()
