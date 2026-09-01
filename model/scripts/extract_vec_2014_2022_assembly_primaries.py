#!/usr/bin/env python3
"""Extract complete 2014, 2018 and 2022 VEC Assembly primary results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ARCHIVE_ROOT = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results"
ARCHIVE_SUMMARIES = {
    2014: f"{ARCHIVE_ROOT}/state2014/summary.html",
    2018: f"{ARCHIVE_ROOT}/state2018/summary.html",
}
MODERN_2022_INDEX = "https://www.vec.vic.gov.au/results/state-election-results/2022-state-election-results"
NARRACAN_2022_URL = (
    "https://www.vec.vic.gov.au/results/state-election-results/state-by-elections-timeline/"
    "narracan-district-supplementary-election-results"
)
TARGET_FAMILIES = ["ALP", "Coalition", "Greens", "One Nation", "Other/Independent"]
EXPECTED_DISTRICTS = {2014: 88, 2018: 88, 2022: 88}
EXPECTED_MAIN_ELECTION_FORMAL = {2014: 3_355_707, 2018: 3_514_474, 2022: 3_617_000}
EXPECTED_NARRACAN_2022_FORMAL = 37_205


def normalise(value: str) -> str:
    return " ".join(value.split()).strip().casefold()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def plain_text(source: str) -> str:
    source = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", source)
    return " ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", source)).split())


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self.table is None:
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            if any(self.row):
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


@dataclass(frozen=True)
class SourcePage:
    year: int
    district_name: str
    url: str
    cache_name: str
    contest: str = "general-election"


def fetch(url: str, path: Path, offline: bool, retries: int = 4) -> bytes:
    if path.exists():
        return path.read_bytes()
    if offline:
        raise FileNotFoundError(f"offline cache miss: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": "vic-election-2026-evidence/1.0"})
            with urlopen(request, timeout=90) as response:
                payload = response.read()
            if not payload:
                raise ValueError(f"empty response from {url}")
            path.write_bytes(payload)
            return payload
        except Exception as exc:  # pragma: no cover - network retry path
            error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {error}")


def archive_sources(year: int, summary: str) -> list[SourcePage]:
    links = re.findall(
        r'(?is)<a\s+[^>]*href=["\']([^"\']*district\.html)["\'][^>]*>(.*?)</a>', summary
    )
    sources: list[SourcePage] = []
    seen: set[str] = set()
    for href, label in links:
        name = re.sub(r"\s+District\s*$", "", plain_text(label), flags=re.I)
        if not name or name in seen:
            continue
        seen.add(name)
        sources.append(SourcePage(year, name, urljoin(ARCHIVE_SUMMARIES[year], href), Path(href).name))
    return sources


def modern_2022_sources(index: str) -> list[SourcePage]:
    links = re.findall(
        r'(?is)<a\s+[^>]*href=["\']([^"\']*/results-by-district/[^"\']+-district-results)["\'][^>]*>(.*?)</a>',
        index,
    )
    sources: list[SourcePage] = []
    seen: set[str] = set()
    for href, label in links:
        name = re.sub(r"\s+District results\s*$", "", plain_text(label), flags=re.I)
        if not name or name in seen:
            continue
        seen.add(name)
        sources.append(SourcePage(2022, name, urljoin(MODERN_2022_INDEX, href), f"{slugify(name)}.html"))
    sources.append(SourcePage(2022, "Narracan", NARRACAN_2022_URL, "narracan-supplementary.html", "supplementary-election"))
    return sources


def first_preference_table(source: str, district_name: str) -> list[tuple[str, str, int]]:
    parser = TableParser()
    parser.feed(source)
    for table in parser.tables:
        if not table:
            continue
        headers = [normalise(cell) for cell in table[0]]
        if len(headers) < 3 or headers[0] != "candidate" or headers[1] != "party" or not headers[2].startswith("1st pref"):
            continue
        rows: list[tuple[str, str, int]] = []
        for row in table[1:]:
            if len(row) < 3 or not row[0].strip():
                continue
            vote_text = row[2].replace(",", "").strip()
            if not vote_text.isdigit():
                raise ValueError(f"{district_name}: invalid primary vote {row[2]!r}")
            rows.append((row[0].strip(), " ".join(row[1].split()), int(vote_text)))
        if rows:
            return rows
    raise ValueError(f"{district_name}: no candidate first-preference table found")


def displayed_formal_votes(source: str, district_name: str) -> int:
    match = re.search(r"Formal Votes?:\s*([0-9][0-9,]*)", plain_text(source), flags=re.I)
    if not match:
        raise ValueError(f"{district_name}: displayed formal-vote total not found")
    return int(match.group(1).replace(",", ""))


def summary_formal_votes(source: str) -> int:
    match = re.search(r"Total Formal Votes\s*([0-9][0-9,]*)", plain_text(source), flags=re.I)
    if not match:
        match = re.search(r"Total formal votes\s*([0-9][0-9,]*)", plain_text(source), flags=re.I)
    if not match:
        raise ValueError("summary formal-vote total not found")
    return int(match.group(1).replace(",", ""))


def alias_map(crosswalk: dict[str, Any]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for family, aliases in crosswalk["aliases"].items():
        for alias in aliases:
            key = normalise(alias)
            if key in mapped and mapped[key] != family:
                raise ValueError(f"crosswalk collision for {alias!r}")
            mapped[key] = family
    return mapped


def extract_page(page: SourcePage, payload: bytes) -> dict[str, Any]:
    source = payload.decode("utf-8", "replace")
    candidates = first_preference_table(source, page.district_name)
    formal = displayed_formal_votes(source, page.district_name)
    if sum(votes for _, _, votes in candidates) != formal:
        raise ValueError(f"{page.year} {page.district_name}: candidate votes do not reconcile to {formal}")
    return {"page": page, "payload": payload, "formal": formal, "candidates": candidates}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_2022_overlap(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        existing = list(csv.DictReader(handle))
    indexed = {
        (normalise(row["district_name"]), normalise(row["candidate_name"])): int(row["first_preference_votes"])
        for row in rows
    }
    mismatches = []
    for row in existing:
        key = (normalise(row["district_name"]), normalise(row["candidate_name"]))
        actual = indexed.get(key)
        expected = int(row["result_page_primary_votes"])
        if actual != expected:
            mismatches.append({"district": row["district_name"], "candidate": row["candidate_name"], "expected": expected, "actual": actual})
    if mismatches:
        raise ValueError(f"2022 indicative overlap mismatch: {mismatches[:5]}")
    return {"rowsChecked": len(existing), "districtsChecked": len({row["district_name"] for row in existing}), "mismatches": 0}


def build(args: argparse.Namespace) -> dict[str, Any]:
    crosswalk = json.loads(args.crosswalk.read_text(encoding="utf-8"))
    mapped_aliases = alias_map(crosswalk)
    cache = args.cache_dir
    summary_payloads: dict[int, bytes] = {}
    source_pages: list[SourcePage] = []
    source_manifest: list[dict[str, Any]] = []

    for year, url in ARCHIVE_SUMMARIES.items():
        payload = fetch(url, cache / str(year) / "summary.html", args.offline)
        summary_payloads[year] = payload
        source_manifest.append({"election_year": year, "district_name": "[summary]", "contest": "general-election", "source_url": url, "sha256": sha256_bytes(payload)})
        source_pages.extend(archive_sources(year, payload.decode("utf-8", "replace")))
    index_payload = fetch(MODERN_2022_INDEX, cache / "2022" / "index.html", args.offline)
    summary_payloads[2022] = index_payload
    source_manifest.append({"election_year": 2022, "district_name": "[summary]", "contest": "general-election", "source_url": MODERN_2022_INDEX, "sha256": sha256_bytes(index_payload)})
    source_pages.extend(modern_2022_sources(index_payload.decode("utf-8", "replace")))

    by_year = Counter(page.year for page in source_pages)
    if dict(by_year) != EXPECTED_DISTRICTS:
        raise ValueError(f"district discovery mismatch: expected {EXPECTED_DISTRICTS}, found {dict(by_year)}")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch, page.url, cache / str(page.year) / page.cache_name, args.offline): page
            for page in source_pages
        }
        for future in as_completed(futures):
            page = futures[future]
            results.append(extract_page(page, future.result()))
    results.sort(key=lambda item: (item["page"].year, item["page"].district_name))

    party_labels = sorted({party for result in results for _, party, _ in result["candidates"] if party}, key=normalise)
    unknown = [label for label in party_labels if normalise(label) not in mapped_aliases]
    if args.list_party_labels:
        print(json.dumps({"partyLabels": party_labels, "unknownPartyLabels": unknown}, indent=2, ensure_ascii=False))
        raise SystemExit(0)
    if unknown:
        raise ValueError(f"unadjudicated official party labels: {unknown}")

    candidate_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    for result in results:
        page: SourcePage = result["page"]
        page_hash = sha256_bytes(result["payload"])
        source_manifest.append({"election_year": page.year, "district_name": page.district_name, "contest": page.contest, "source_url": page.url, "sha256": page_hash})
        district_candidates: list[dict[str, Any]] = []
        for order, (candidate_name, party, votes) in enumerate(result["candidates"], start=1):
            independent = party == ""
            family = "Other/Independent" if independent else mapped_aliases[normalise(party)]
            row = {
                "election_id": f"vic_la_{page.year}", "district_name": page.district_name,
                "district_id": slugify(page.district_name), "contest": page.contest,
                "source_url": page.url, "source_sha256": page_hash, "candidate_order": order,
                "candidate_name": candidate_name, "party_raw": party, "independent_status": independent,
                "party_family": family, "first_preference_votes": votes, "formal_votes": result["formal"],
                "district_reconciled": True,
            }
            candidate_rows.append(row)
            district_candidates.append(row)
        for family in TARGET_FAMILIES:
            matching = [row for row in district_candidates if row["party_family"] == family]
            family_rows.append({
                "election_id": f"vic_la_{page.year}", "district_name": page.district_name,
                "district_id": slugify(page.district_name), "contest": page.contest,
                "party_family": family, "contest_status": "contested" if matching else "verified_no_contest",
                "candidate_count": len(matching),
                "first_preference_votes": sum(row["first_preference_votes"] for row in matching),
                "formal_votes": result["formal"], "district_reconciled": True,
            })

    totals = {
        year: sum(result["formal"] for result in results if result["page"].year == year and result["page"].contest == "general-election")
        for year in EXPECTED_DISTRICTS
    }
    official_summary_totals = {
        year: summary_formal_votes(summary_payloads[year].decode("utf-8", "replace"))
        for year in EXPECTED_DISTRICTS
    }
    if official_summary_totals != EXPECTED_MAIN_ELECTION_FORMAL:
        raise ValueError(f"official summary totals changed: {official_summary_totals}")
    if totals != EXPECTED_MAIN_ELECTION_FORMAL:
        raise ValueError(f"district totals do not match official summaries: {totals}")
    narracan_total = sum(result["formal"] for result in results if result["page"].contest == "supplementary-election")
    if narracan_total != EXPECTED_NARRACAN_2022_FORMAL:
        raise ValueError(f"Narracan supplementary total mismatch: {narracan_total}")

    overlap = validate_2022_overlap(args.indicative_2022, [row for row in candidate_rows if row["election_id"] == "vic_la_2022"])
    audit: dict[str, Any] = {
        "schemaVersion": 1, "reviewedAt": "2026-09-01",
        "status": "complete-2014-2022-assembly-primary-evidence",
        "authority": "Victorian Electoral Commission", "cycles": {},
        "sourceManifest": "metadata/vec-historical-assembly-primary-source-manifest.csv",
        "checks": {
            "allDistrictsDiscovered": True, "allCandidateTotalsReconciled": True,
            "allFamilyTotalsReconciled": True, "allPartyLabelsAdjudicated": True,
            "mainElectionStatewideTotalsReconciled": True,
            "narracanSupplementaryTotalReconciled": True,
            "existing2022IndicativeOverlap": overlap,
        },
        "use": {
            "historicalOutcomeScoring": "eligible", "currentForecast": "excluded",
            "historicalReplayInput": "outcome-only-not-pre-election-information",
            "automaticGateOpening": False, "productionAuthorisation": False,
        },
    }
    for year in EXPECTED_DISTRICTS:
        cycle_candidates = [row for row in candidate_rows if row["election_id"] == f"vic_la_{year}"]
        cycle_families = [row for row in family_rows if row["election_id"] == f"vic_la_{year}"]
        audit["cycles"][str(year)] = {
            "districts": len({row["district_id"] for row in cycle_candidates}),
            "candidateRows": len(cycle_candidates), "familyRows": len(cycle_families),
            "generalElectionFormalVotes": totals[year],
            "supplementaryFormalVotes": narracan_total if year == 2022 else 0,
            "allDistrictFormalVotes": sum(
                formal for _, formal in {(row["district_id"], row["formal_votes"]) for row in cycle_candidates}
            ),
        }
    return {"audit": audit, "manifest": source_manifest, "candidateRows": candidate_rows, "familyRows": family_rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--crosswalk", type=Path, default=Path("model/config/historical-party-family-crosswalk.json"))
    parser.add_argument("--indicative-2022", type=Path, default=Path("model/data/processed/vec_2022_indicative_candidate_evidence.csv"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--list-party-labels", action="store_true")
    args = parser.parse_args()
    built = build(args)

    candidate_fields = ["election_id", "district_name", "district_id", "contest", "source_url", "source_sha256", "candidate_order", "candidate_name", "party_raw", "independent_status", "party_family", "first_preference_votes", "formal_votes", "district_reconciled"]
    family_fields = ["election_id", "district_name", "district_id", "contest", "party_family", "contest_status", "candidate_count", "first_preference_votes", "formal_votes", "district_reconciled"]
    outputs = []
    for year in EXPECTED_DISTRICTS:
        candidates = [row for row in built["candidateRows"] if row["election_id"] == f"vic_la_{year}"]
        families = [row for row in built["familyRows"] if row["election_id"] == f"vic_la_{year}"]
        candidate_path = args.output_root / f"model/data/processed/vec_{year}_assembly_candidate_primaries.csv"
        family_path = args.output_root / f"model/data/processed/vec_{year}_assembly_family_primaries.csv"
        write_csv(candidate_path, candidates, candidate_fields)
        write_csv(family_path, families, family_fields)
        outputs.extend([
            {"path": str(candidate_path.relative_to(args.output_root)), "sha256": sha256_file(candidate_path), "rows": len(candidates)},
            {"path": str(family_path.relative_to(args.output_root)), "sha256": sha256_file(family_path), "rows": len(families)},
        ])
    manifest_path = args.output_root / "metadata/vec-historical-assembly-primary-source-manifest.csv"
    write_csv(manifest_path, sorted(built["manifest"], key=lambda row: (row["election_year"], row["district_name"])), ["election_year", "district_name", "contest", "source_url", "sha256"])
    outputs.append({"path": str(manifest_path.relative_to(args.output_root)), "sha256": sha256_file(manifest_path), "rows": len(built["manifest"])})
    built["audit"]["outputs"] = outputs
    audit_path = args.output_root / "metadata/vec-2014-2022-assembly-primary-audit.json"
    audit_path.write_text(json.dumps(built["audit"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    candidate_total = sum(output["rows"] for output in outputs if "candidate_primaries" in output["path"])
    print(f"Extracted {candidate_total} candidate rows across 264 district-cycle contests.")


if __name__ == "__main__":
    main()
