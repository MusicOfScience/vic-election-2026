#!/usr/bin/env python3
"""Extract prediction-safe 2006 Assembly family primaries.

The 2006 results are prior-election evidence for the 2010 replay.  This
extractor deliberately reads only the official VEC 2006 first-preference
tables and emits a family-composition prior; it never reads the 2010
transition/swing artefact.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


SUMMARY_URL = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/state2006/state2006resultsummary.html"
BASE_URL = SUMMARY_URL.rsplit("/", 1)[0] + "/"
EVIDENCE_DATE = "2006-11-25"
FAMILIES = ("ALP", "LIB_NAT", "GRN", "OTH_IND")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "vic-election-2026 historical evidence extractor"})
    with urlopen(request, timeout=60) as response:
        return response.read()


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[tuple[str, list[list[str]]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "table":
            self._table = []
            self._title = attr.get("title") or ""
        elif self._table is not None and tag == "tr":
            self._row = []
        elif self._row is not None and tag in {"th", "td"}:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self._row is not None and self._cell is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._table is not None and self._row is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append((self._title, self._table))
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def party_family(raw: str) -> str:
    value = raw.strip().upper()
    if value in {"ALP", "AUSTRALIAN LABOR PARTY", "AUSTRALIAN LABOR PARTY - VICTORIAN BRANCH"}:
        return "ALP"
    if value in {"LIBERAL", "LIBERAL PARTY", "LIBERAL PARTY OF AUSTRALIA - VICTORIAN DIVISION", "NATIONALS", "THE NATIONALS", "NATIONAL PARTY"}:
        return "LIB_NAT"
    if "GREEN" in value:
        return "GRN"
    return "OTH_IND"


def summary_links(summary: bytes) -> list[tuple[str, str]]:
    text = summary.decode("utf-8", errors="replace")
    links = re.findall(r'href="(state2006result[^"/]+district\.html)"', text, flags=re.I)
    names = re.findall(r'>([^<>]+) District</a>', text, flags=re.I)
    if len(links) != 88 or len(names) != 88:
        raise ValueError(f"expected 88 2006 district links, found {len(links)} links/{len(names)} names")
    return [(name.strip(), BASE_URL + link) for name, link in zip(names, links)]


def parse_first_preferences(payload: bytes) -> list[tuple[str, str, int]]:
    parser = TableParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    tables = [rows for title, rows in parser.tables if title.lower() == "first preference votes"]
    if len(tables) != 1:
        raise ValueError(f"expected one first-preference table, found {len(tables)}")
    rows = tables[0]
    output: list[tuple[str, str, int]] = []
    for row in rows[1:]:
        if len(row) < 3 or not row[2].replace(",", "").isdigit():
            continue
        output.append((row[0], row[1], int(row[2].replace(",", ""))))
    if not output:
        raise ValueError("first-preference table had no candidate rows")
    return output


def extract(output_path: Path, manifest_path: Path) -> None:
    summary = fetch(SUMMARY_URL)
    districts = summary_links(summary)
    rows: list[dict[str, str | int | bool]] = []
    manifest = [{"url": SUMMARY_URL, "sha256": sha256_bytes(summary), "publishedDate": EVIDENCE_DATE, "role": "official-2006-district-index"}]
    seen: set[str] = set()
    for district_name, url in districts:
        payload = fetch(url)
        district_id = slug(district_name)
        if district_id in seen:
            raise ValueError(f"duplicate district {district_id}")
        seen.add(district_id)
        manifest.append({"url": url, "sha256": sha256_bytes(payload), "publishedDate": EVIDENCE_DATE, "role": "official-2006-assembly-first-preferences", "districtId": district_id})
        family_votes = {family: 0 for family in FAMILIES}
        formal = 0
        for candidate, raw_party, votes in parse_first_preferences(payload):
            family_votes[party_family(raw_party)] += votes
            formal += votes
        for family in FAMILIES:
            rows.append({
                "election_id": "vic_la_2006",
                "district_name": district_name,
                "district_id": district_id,
                "party_family": family,
                "first_preference_votes": family_votes[family],
                "formal_votes": formal,
                "source_url": url,
                "source_sha256": sha256_bytes(payload),
                "evidence_available_by": EVIDENCE_DATE,
                "district_reconciled": family_votes["ALP"] + family_votes["LIB_NAT"] + family_votes["GRN"] + family_votes["OTH_IND"] == formal,
            })
    if len(seen) != 88 or len(rows) != 352:
        raise ValueError(f"expected 88 districts/352 family rows, got {len(seen)}/{len(rows)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(__import__("json").dumps({"schemaVersion": 1, "cycleId": "vic_la_2010", "priorElection": "vic_la_2006", "boundaryAlignment": "same-boundary", "sourceAuthority": "Victorian Electoral Commission", "evidenceAvailableBy": EVIDENCE_DATE, "targetOutcomeDependency": False, "sources": manifest}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("model/data/processed/vec_2006_assembly_family_primaries.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("metadata/vec-2006-assembly-source-manifest.json"))
    args = parser.parse_args()
    extract(args.output, args.manifest)
