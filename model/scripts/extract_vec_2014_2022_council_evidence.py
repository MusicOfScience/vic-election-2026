#!/usr/bin/env python3
"""Extract official VEC Council primaries and published count-total sequences.

The script downloads (or replays from a cache) the eight region result pages and
distribution workbooks for the 2014, 2018 and 2022 Victorian state elections.
Election results remain scoring-only evidence and are not forecast inputs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from lxml import html


USER_AGENT = "vic-election-2026 historical evidence audit"
OLD_REGION_SLUGS = (
    "easternmetropolitanregion",
    "easternvictoriaregion",
    "northernmetropolitanregion",
    "northernvictoriaregion",
    "south-easternmetropolitanregion",
    "southernmetropolitanregion",
    "westernmetropolitanregion",
    "westernvictoriaregion",
)
REGION_SLUGS_2022 = (
    "eastern-victoria-region-results",
    "north-eastern-metropolitan-region-results",
    "northern-metropolitan-region-results",
    "northern-victoria-region-results",
    "south-eastern-metropolitan-region-results",
    "southern-metropolitan-region-results",
    "western-metropolitan-region-results",
    "western-victoria-region-results",
)


@dataclass(frozen=True)
class Source:
    year: int
    region_slug: str
    page_url: str


def sources() -> list[Source]:
    result: list[Source] = []
    for year in (2014, 2018):
        base = f"https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/state{year}/"
        result.extend(Source(year, slug, urllib.parse.urljoin(base, f"{slug}.html")) for slug in OLD_REGION_SLUGS)
    base_2022 = "https://www.vec.vic.gov.au/results/state-election-results/2022-state-election-results/results-by-region/"
    result.extend(Source(2022, slug, urllib.parse.urljoin(base_2022, slug)) for slug in REGION_SLUGS_2022)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalise_name(value: object) -> str:
    return compact(value).casefold().replace("’", "'").replace("–", "-")


def download(url: str, path: Path, offline: bool) -> None:
    if path.exists():
        return
    if offline:
        raise RuntimeError(f"offline replay missing cached source: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(urllib.parse.quote(url, safe=":/%?=&"), headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                path.write_bytes(response.read())
            return
        except Exception as error:  # pragma: no cover - exercised only on transient network errors
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}")


def parse_page(page_path: Path) -> dict[str, object]:
    raw = page_path.read_bytes()
    document = html.fromstring(raw)
    text = compact(document.text_content())
    tables = pd.read_html(page_path, flavor="lxml")
    candidate_table = next(table for table in tables if "Candidate" in table.columns and "Party" in table.columns)
    vote_column = next(column for column in candidate_table.columns if "1st pref" in str(column))
    primaries = []
    for _, row in candidate_table.iterrows():
        raw_votes = str(row[vote_column]).replace(",", "").strip()
        if not re.fullmatch(r"\d+(?:\.0)?", raw_votes):
            continue
        primaries.append({
            "candidate_name": compact(row["Candidate"]),
            "party_name": compact(row["Party"]),
            "first_preference_votes": int(float(raw_votes)),
        })
    formal_match = re.search(r"Formal votes?:\s*([0-9,]+)", text, re.IGNORECASE)
    if not formal_match:
        raise RuntimeError(f"formal-vote total not found in {page_path}")
    formal_votes = int(formal_match.group(1).replace(",", ""))
    elected_nodes = document.xpath(
        "//*[self::span or self::b][contains(translate(normalize-space(.), 'ELECTED', 'elected'), 'elected:')]"
    )
    elected = []
    for node in elected_nodes:
        match = re.search(r"(?:1st|2nd|3rd|4th|5th) elected:\s*(.+)", compact(node.text_content()), re.IGNORECASE)
        if match:
            elected.append(match.group(1).strip())
    if len(elected) != 5:
        raise RuntimeError(f"expected five elected members in {page_path}, found {len(elected)}")
    links = document.xpath("//a[contains(translate(normalize-space(.), 'DISTRIBUTIONS', 'distributions'), 'distribution')]/@href")
    if len(links) != 1:
        raise RuntimeError(f"expected one distribution workbook link in {page_path}, found {len(links)}")
    return {
        "formal_votes": formal_votes,
        "primaries": primaries,
        "elected": elected,
        "distribution_href": links[0],
    }


def region_name_from_workbook(frame: pd.DataFrame) -> str:
    for value in frame.iloc[:12, 0].tolist():
        text = compact(value)
        if text.endswith(" Region"):
            return text
    raise RuntimeError("region name not found in distribution workbook")


def metadata_number(frame: pd.DataFrame, label: str) -> int:
    for value in frame.iloc[:15, 0].tolist():
        match = re.search(rf"{re.escape(label)}[^:]*:\s*([0-9,]+)", compact(value), re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    raise RuntimeError(f"{label} not found in distribution workbook")


def parse_workbook(path: Path) -> dict[str, object]:
    frame = pd.read_excel(path, sheet_name="Results-PRDistribution", header=None)
    header_row = next(i for i in range(len(frame)) if compact(frame.iloc[i, 0]).startswith("Count"))
    headers = [compact(value) for value in frame.iloc[header_row].tolist()]
    total_index = next(i for i, value in enumerate(headers) if value.upper() == "TOTAL")
    candidate_positions = [i for i in range(4, total_index - 2) if headers[i]]
    candidate_headers = [headers[i] for i in candidate_positions]
    special_headers = headers[total_index - 2 : total_index + 1]
    if special_headers != ["Gain/Loss", "Exhausted", "TOTAL"]:
        raise RuntimeError(f"unexpected balance columns in {path}: {special_headers}")
    if not candidate_headers or len(set(candidate_headers)) != len(candidate_headers):
        raise RuntimeError(f"candidate columns are empty or duplicated in {path}")

    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for row_index in range(header_row + 1, len(frame)):
        row = frame.iloc[row_index]
        count_value = row.iloc[0]
        if pd.notna(count_value):
            try:
                count_number = int(float(count_value))
            except (TypeError, ValueError):
                continue
            current = {
                "count_number": count_number,
                "count_detail": compact(row.iloc[1]),
                "transfer_value": compact(row.iloc[2]),
                "elected_at_count": compact(row.iloc[total_index + 1]) if total_index + 1 < len(row) else "",
            }
            if count_number == 1:
                current["totals"] = [row.iloc[i] for i in candidate_positions + list(range(total_index - 2, total_index + 1))]
                events.append(current)
            continue
        if current is not None and compact(row.iloc[3]).upper() == "PTOTAL":
            current["totals"] = [row.iloc[i] for i in candidate_positions + list(range(total_index - 2, total_index + 1))]
            if not events or events[-1]["count_number"] != current["count_number"]:
                events.append(current)

    if not events or events[0]["count_number"] != 1:
        raise RuntimeError(f"count-one totals missing in {path}")
    expected_counts = list(range(1, int(events[-1]["count_number"]) + 1))
    actual_counts = [int(event["count_number"]) for event in events]
    if actual_counts != expected_counts:
        raise RuntimeError(f"count sequence is not contiguous in {path}")
    return {
        "region_name": region_name_from_workbook(frame),
        "formal_votes": metadata_number(frame, "Formal Ballot Papers included in count"),
        "informal_votes": metadata_number(frame, "Informal Ballot Papers"),
        "quota": metadata_number(frame, "Quota"),
        "candidate_headers": candidate_headers,
        "entity_headers": candidate_headers + special_headers,
        "events": events,
    }


def page_distribution_url(source: Source, page_path: Path, href: str) -> str:
    if href.startswith("http"):
        return href
    return urllib.parse.urljoin(source.page_url, href)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        handle = io.StringIO(newline="")
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_bytes(gzip.compress(handle.getvalue().encode("utf-8"), compresslevel=9, mtime=0))
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    primary_rows: dict[int, list[dict[str, object]]] = {2014: [], 2018: [], 2022: []}
    count_rows: dict[int, list[dict[str, object]]] = {2014: [], 2018: [], 2022: []}
    manifest_rows: list[dict[str, object]] = []
    region_audits: list[dict[str, object]] = []

    for source in sources():
        year_cache = args.cache_dir / str(source.year)
        page_path = year_cache / f"{source.region_slug}.html"
        download(source.page_url, page_path, args.offline)
        page = parse_page(page_path)
        distribution_url = page_distribution_url(source, page_path, str(page["distribution_href"]))
        workbook_path = year_cache / f"{source.region_slug}-distribution.xls"
        download(distribution_url, workbook_path, args.offline)
        workbook = parse_workbook(workbook_path)
        region_name = str(workbook["region_name"])
        region_id = re.sub(r"[^a-z0-9]+", "-", region_name.casefold()).strip("-")
        page_primaries = list(page["primaries"])
        workbook_names = list(workbook["candidate_headers"])
        count_one = list(workbook["events"])[0]["totals"]
        page_by_name = {normalise_name(row["candidate_name"]): row for row in page_primaries}
        if set(page_by_name) != {normalise_name(name) for name in workbook_names}:
            raise RuntimeError(f"candidate identities do not reconcile for {source.year} {region_name}")
        for index, name in enumerate(workbook_names):
            page_row = page_by_name[normalise_name(name)]
            workbook_votes = int(float(count_one[index]))
            if workbook_votes != page_row["first_preference_votes"]:
                raise RuntimeError(f"count-one primary mismatch for {source.year} {region_name}: {name}")
        formal_votes = int(page["formal_votes"])
        if formal_votes != int(workbook["formal_votes"]):
            raise RuntimeError(f"formal-vote total mismatch for {source.year} {region_name}")
        if sum(int(row["first_preference_votes"]) for row in page_primaries) != formal_votes:
            raise RuntimeError(f"candidate primaries do not sum to formal votes for {source.year} {region_name}")
        quota = int(workbook["quota"])
        if quota != formal_votes // 6 + 1:
            raise RuntimeError(f"invalid quota for {source.year} {region_name}")

        page_hash = sha256(page_path)
        workbook_hash = sha256(workbook_path)
        election_id = f"vic_lc_{source.year}"
        for row in page_primaries:
            primary_rows[source.year].append({
                "election_id": election_id,
                "region_id": region_id,
                "region_name": region_name,
                "candidate_name": row["candidate_name"],
                "party_name": row["party_name"],
                "first_preference_votes": row["first_preference_votes"],
                "formal_votes": formal_votes,
                "quota": quota,
                "source_url": source.page_url,
                "source_sha256": page_hash,
            })
        entity_headers = list(workbook["entity_headers"])
        for event in workbook["events"]:
            totals = list(event["totals"])
            if len(totals) != len(entity_headers):
                raise RuntimeError(f"count width mismatch for {source.year} {region_name} count {event['count_number']}")
            for entity_index, entity_name in enumerate(entity_headers):
                value = totals[entity_index]
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    continue
                numeric = float(value)
                count_rows[source.year].append({
                    "election_id": election_id,
                    "region_id": region_id,
                    "region_name": region_name,
                    "count_number": event["count_number"],
                    "count_detail": event["count_detail"],
                    "transfer_value": event["transfer_value"],
                    "entity_type": "candidate" if entity_index < len(workbook_names) else "balance",
                    "entity_name": entity_name,
                    "total_votes": format(numeric, ".12g"),
                    "elected_at_count": event["elected_at_count"],
                    "source_url": distribution_url,
                    "source_sha256": workbook_hash,
                })
        for source_type, url, path in (
            ("region-result-page", source.page_url, page_path),
            ("distribution-workbook", distribution_url, workbook_path),
        ):
            manifest_rows.append({
                "election_id": election_id,
                "region_id": region_id,
                "region_name": region_name,
                "source_type": source_type,
                "source_url": url,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            })
        region_audits.append({
            "electionId": election_id,
            "regionId": region_id,
            "regionName": region_name,
            "formalVotes": formal_votes,
            "informalVotes": workbook["informal_votes"],
            "quota": quota,
            "candidateRows": len(page_primaries),
            "countEvents": len(workbook["events"]),
            "countTotalRows": sum(1 for row in count_rows[source.year] if row["region_id"] == region_id),
            "electedCandidates": len(page["elected"]),
            "elected": page["elected"],
            "pagePrimaryMatchesWorkbookCountOne": True,
        })

    primary_fields = [
        "election_id", "region_id", "region_name", "candidate_name", "party_name",
        "first_preference_votes", "formal_votes", "quota", "source_url", "source_sha256",
    ]
    count_fields = [
        "election_id", "region_id", "region_name", "count_number", "count_detail",
        "transfer_value", "entity_type", "entity_name", "total_votes", "elected_at_count",
        "source_url", "source_sha256",
    ]
    for year in (2014, 2018, 2022):
        write_csv(args.output_root / f"model/data/processed/vec_{year}_council_candidate_primaries.csv", primary_rows[year], primary_fields)
        write_csv(args.output_root / f"model/data/processed/vec_{year}_council_preference_counts.csv.gz", count_rows[year], count_fields)
    manifest_path = args.output_root / "metadata/vec-2014-2022-council-source-manifest.csv"
    write_csv(manifest_path, manifest_rows, ["election_id", "region_id", "region_name", "source_type", "source_url", "sha256", "bytes"])

    audit = {
        "schemaVersion": 1,
        "reviewedAt": "2026-09-01",
        "status": "partial-three-cycle-official-council-evidence",
        "scope": "Official VEC Legislative Council result pages and preference-distribution workbooks for 2014, 2018 and 2022",
        "coverage": {
            "cycles": ["vic_lc_2014", "vic_lc_2018", "vic_lc_2022"],
            "regionCycleContests": len(region_audits),
            "regionsPerCycle": 8,
            "electedCandidates": sum(int(row["electedCandidates"]) for row in region_audits),
            "candidateRows": sum(len(rows) for rows in primary_rows.values()),
            "countEvents": sum(int(row["countEvents"]) for row in region_audits),
            "countTotalRows": sum(len(rows) for rows in count_rows.values()),
            "fingerprintedSources": len(manifest_rows),
        },
        "acceptance": {
            "allRegionPagesPresent": len(region_audits) == 24,
            "fiveMembersPerRegion": all(row["electedCandidates"] == 5 for row in region_audits),
            "candidatePrimariesReconcileToFormalVotes": True,
            "pagePrimariesMatchWorkbookCountOne": True,
            "quotaFormulaReconciles": True,
            "countSequencesContiguous": True,
            "allSourcesFingerprinted": len(manifest_rows) == 48,
        },
        "regions": region_audits,
        "limitations": [
            "The 2010 Legislative Council cycle is not included in this harvest.",
            "Cycle-specific electoral-rule configuration remains unresolved.",
            "These election outcomes are scoring-only and cannot enter a pre-election information set.",
        ],
        "modelImpact": {
            "changesCurrentForecast": False,
            "historicalReplayEligible": False,
            "probabilityCalibrationReady": False,
            "automaticGateOpening": False,
        },
    }
    audit_path = args.output_root / "metadata/vec-2014-2022-council-evidence-audit.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["coverage"], indent=2))


if __name__ == "__main__":
    main()
