#!/usr/bin/env python3
"""Extract official VEC 2010 Council primaries and count-total sequences.

The archived VEC region pages provide candidate identities, parties, first
preferences and elected members. Their linked distribution workbooks provide
the complete published count sequence. Election results are scoring-only
evidence and are never forecast inputs.
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
PAGE_BASE = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/state2010/"
FILE_BASE = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/files/"
REGION_SLUGS = (
    "easternmetropolitan",
    "easternvictoria",
    "northernmetropolitan",
    "northernvictoria",
    "southeasternmetropolitan",
    "southernmetropolitan",
    "westernmetropolitan",
    "westernvictoria",
)


@dataclass(frozen=True)
class Source:
    region_slug: str
    page_url: str
    workbook_url: str

    @property
    def page_filename(self) -> str:
        return urllib.parse.urlparse(self.page_url).path.rsplit("/", 1)[-1]

    @property
    def workbook_filename(self) -> str:
        return urllib.parse.urlparse(self.workbook_url).path.rsplit("/", 1)[-1]


def sources() -> list[Source]:
    return [
        Source(
            slug,
            urllib.parse.urljoin(PAGE_BASE, f"state2010result{slug}region.html"),
            urllib.parse.urljoin(FILE_BASE, f"state2010{slug}regiondistributions.xls"),
        )
        for slug in REGION_SLUGS
    ]


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
    request = urllib.request.Request(
        urllib.parse.quote(url, safe=":/%?=&"),
        headers={"User-Agent": USER_AGENT},
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                path.write_bytes(response.read())
            return
        except Exception as error:  # pragma: no cover - transient network path
            last_error = error
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to download {url}: {last_error}")


def parse_page(path: Path) -> dict[str, object]:
    document = html.fromstring(path.read_bytes())
    tables = pd.read_html(path, flavor="lxml")
    candidate_table = next(table for table in tables if "Candidate" in table.columns)
    vote_column = next(column for column in candidate_table.columns if "1st pref" in str(column))
    primaries = []
    for _, row in candidate_table.iterrows():
        raw_votes = compact(row[vote_column]).replace(",", "")
        if not re.fullmatch(r"\d+(?:\.0)?", raw_votes):
            raw_votes = next(
                (
                    compact(value).replace(",", "")
                    for value in row.iloc[1:].tolist()
                    if re.fullmatch(r"\d+(?:\.0)?", compact(value).replace(",", ""))
                ),
                "",
            )
        if not re.fullmatch(r"\d+(?:\.0)?", raw_votes):
            continue
        primaries.append(
            {
                "candidate_name": compact(row["Candidate"]),
                "party_name": compact(row["Party"]),
                "first_preference_votes": int(float(raw_votes)),
            }
        )

    text = compact(document.text_content())
    formal_match = re.search(r"Formal Votes:\s*([0-9,]+)", text, re.IGNORECASE)
    informal_match = re.search(r"Informal Votes:\s*([0-9,]+)", text, re.IGNORECASE)
    quota_match = re.search(r"Quota:\s*([0-9,]+)", text, re.IGNORECASE)
    if not (formal_match and informal_match and quota_match):
        raise RuntimeError(f"vote metadata missing in {path}")
    elected = []
    for node in document.xpath("//span[contains(concat(' ', normalize-space(@class), ' '), ' bold-text ')]"):
        match = re.search(
            r"(?:1st|2nd|3rd|4th|5th) elected:\s*(.+)",
            compact(node.text_content()),
            re.IGNORECASE,
        )
        if match:
            elected.append(compact(match.group(1)))
    if len(elected) != 5:
        summary = compact(tables[0].iloc[0, 0])
        elected = [
            compact(name)
            for name in re.findall(
                r"(?:1st|2nd|3rd|4th|5th) elected:\s*(.+?)(?=\s+(?:1st|2nd|3rd|4th|5th) elected:|$)",
                summary,
                re.IGNORECASE,
            )
        ]
    if len(elected) != 5:
        raise RuntimeError(f"expected five elected members in {path}, found {len(elected)}")
    return {
        "formal_votes": int(formal_match.group(1).replace(",", "")),
        "informal_votes": int(informal_match.group(1).replace(",", "")),
        "quota": int(quota_match.group(1).replace(",", "")),
        "primaries": primaries,
        "elected": elected,
    }


def metadata_number(frame: pd.DataFrame, label: str) -> int:
    for value in frame.iloc[:15, 0].tolist():
        match = re.search(rf"{re.escape(label)}[^:]*:\s*([0-9,]+)", compact(value), re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    raise RuntimeError(f"{label} not found in distribution workbook")


def parse_workbook(path: Path) -> dict[str, object]:
    frame = pd.read_excel(path, sheet_name="Sheet1", header=None)
    region_name = next(
        compact(value)
        for value in frame.iloc[:12, 0].tolist()
        if compact(value).endswith(" Region")
    )
    header_row = next(
        index
        for index in range(len(frame))
        if compact(frame.iloc[index, 0]).startswith("Count")
    )
    headers = [compact(value) for value in frame.iloc[header_row].tolist()]
    total_index = next(index for index, value in enumerate(headers) if value.upper() == "TOTAL")
    candidate_positions = [index for index in range(4, total_index - 2) if headers[index]]
    candidate_headers = [headers[index] for index in candidate_positions]
    special_headers = headers[total_index - 2 : total_index + 1]
    if special_headers != ["Gain/Loss", "Exhausted", "TOTAL"]:
        raise RuntimeError(f"unexpected balance columns in {path}: {special_headers}")
    if not candidate_headers or len(set(candidate_headers)) != len(candidate_headers):
        raise RuntimeError(f"candidate columns are empty or duplicated in {path}")

    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    positions = candidate_positions + list(range(total_index - 2, total_index + 1))
    for row_index in range(header_row + 1, len(frame)):
        row = frame.iloc[row_index]
        if pd.notna(row.iloc[0]):
            try:
                count_number = int(float(row.iloc[0]))
            except (TypeError, ValueError):
                continue
            current = {
                "count_number": count_number,
                "count_detail": compact(row.iloc[1]),
                "transfer_value": compact(row.iloc[2]),
                "elected_at_count": compact(row.iloc[total_index + 1]),
            }
            if count_number == 1:
                current["totals"] = [row.iloc[index] for index in positions]
                events.append(current)
            continue
        if current is not None and compact(row.iloc[3]).upper() == "PTOTAL":
            current["totals"] = [row.iloc[index] for index in positions]
            if not events or events[-1]["count_number"] != current["count_number"]:
                events.append(current)

    actual_counts = [int(event["count_number"]) for event in events]
    expected_counts = list(range(1, actual_counts[-1] + 1))
    if actual_counts != expected_counts:
        raise RuntimeError(f"count sequence is not contiguous in {path}")
    return {
        "region_name": region_name,
        "formal_votes": metadata_number(frame, "Formal Ballot Papers included in count"),
        "informal_votes": metadata_number(frame, "Informal Ballot Papers"),
        "quota": metadata_number(frame, "Quota"),
        "candidate_headers": candidate_headers,
        "entity_headers": candidate_headers + special_headers,
        "events": events,
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        handle = io.StringIO(newline="")
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_bytes(gzip.compress(handle.getvalue().encode("utf-8"), compresslevel=9, mtime=0))
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("."))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    primary_rows: list[dict[str, object]] = []
    count_rows: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []
    region_audits: list[dict[str, object]] = []

    for source in sources():
        page_path = args.cache_dir / source.page_filename
        workbook_path = args.cache_dir / source.workbook_filename
        download(source.page_url, page_path, args.offline)
        download(source.workbook_url, workbook_path, args.offline)
        page = parse_page(page_path)
        workbook = parse_workbook(workbook_path)
        region_name = str(workbook["region_name"])
        region_id = re.sub(r"[^a-z0-9]+", "-", region_name.casefold()).strip("-")

        page_primaries = list(page["primaries"])
        workbook_names = list(workbook["candidate_headers"])
        count_one = list(workbook["events"])[0]["totals"]
        page_by_name = {normalise_name(row["candidate_name"]): row for row in page_primaries}
        if set(page_by_name) != {normalise_name(name) for name in workbook_names}:
            raise RuntimeError(f"candidate identities do not reconcile for {region_name}")
        for index, name in enumerate(workbook_names):
            page_row = page_by_name[normalise_name(name)]
            if int(float(count_one[index])) != int(page_row["first_preference_votes"]):
                raise RuntimeError(f"count-one primary mismatch for {region_name}: {name}")

        formal_votes = int(page["formal_votes"])
        quota = int(page["quota"])
        if formal_votes != int(workbook["formal_votes"]):
            raise RuntimeError(f"formal-vote total mismatch for {region_name}")
        if int(page["informal_votes"]) != int(workbook["informal_votes"]):
            raise RuntimeError(f"informal-vote total mismatch for {region_name}")
        if quota != int(workbook["quota"]) or quota != formal_votes // 6 + 1:
            raise RuntimeError(f"quota mismatch for {region_name}")
        if sum(int(row["first_preference_votes"]) for row in page_primaries) != formal_votes:
            raise RuntimeError(f"candidate primaries do not reconcile for {region_name}")

        page_hash = sha256(page_path)
        workbook_hash = sha256(workbook_path)
        for row in page_primaries:
            primary_rows.append(
                {
                    "election_id": "vic_lc_2010",
                    "region_id": region_id,
                    "region_name": region_name,
                    "candidate_name": row["candidate_name"],
                    "party_name": row["party_name"],
                    "first_preference_votes": row["first_preference_votes"],
                    "formal_votes": formal_votes,
                    "quota": quota,
                    "source_url": source.page_url,
                    "source_sha256": page_hash,
                }
            )

        entity_headers = list(workbook["entity_headers"])
        region_count_rows = 0
        for event in workbook["events"]:
            totals = list(event["totals"])
            if len(totals) != len(entity_headers):
                raise RuntimeError(f"count width mismatch for {region_name} count {event['count_number']}")
            for entity_index, entity_name in enumerate(entity_headers):
                value = totals[entity_index]
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    continue
                count_rows.append(
                    {
                        "election_id": "vic_lc_2010",
                        "region_id": region_id,
                        "region_name": region_name,
                        "count_number": event["count_number"],
                        "count_detail": event["count_detail"],
                        "transfer_value": event["transfer_value"],
                        "entity_type": "candidate" if entity_index < len(workbook_names) else "balance",
                        "entity_name": entity_name,
                        "total_votes": format(float(value), ".12g"),
                        "elected_at_count": event["elected_at_count"],
                        "source_url": source.workbook_url,
                        "source_sha256": workbook_hash,
                    }
                )
                region_count_rows += 1

        for source_type, url, path in (
            ("region-result-page", source.page_url, page_path),
            ("distribution-workbook", source.workbook_url, workbook_path),
        ):
            manifest_rows.append(
                {
                    "election_id": "vic_lc_2010",
                    "region_id": region_id,
                    "region_name": region_name,
                    "source_type": source_type,
                    "source_url": url,
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
        region_audits.append(
            {
                "electionId": "vic_lc_2010",
                "regionId": region_id,
                "regionName": region_name,
                "formalVotes": formal_votes,
                "informalVotes": page["informal_votes"],
                "quota": quota,
                "candidateRows": len(page_primaries),
                "countEvents": len(workbook["events"]),
                "countTotalRows": region_count_rows,
                "electedCandidates": len(page["elected"]),
                "elected": page["elected"],
                "pagePrimaryMatchesWorkbookCountOne": True,
            }
        )

    primary_fields = [
        "election_id", "region_id", "region_name", "candidate_name", "party_name",
        "first_preference_votes", "formal_votes", "quota", "source_url", "source_sha256",
    ]
    count_fields = [
        "election_id", "region_id", "region_name", "count_number", "count_detail",
        "transfer_value", "entity_type", "entity_name", "total_votes", "elected_at_count",
        "source_url", "source_sha256",
    ]
    write_csv(
        args.output_root / "model/data/processed/vec_2010_council_candidate_primaries.csv",
        primary_rows,
        primary_fields,
    )
    write_csv(
        args.output_root / "model/data/processed/vec_2010_council_preference_counts.csv.gz",
        count_rows,
        count_fields,
    )
    write_csv(
        args.output_root / "metadata/vec-2010-council-source-manifest.csv",
        manifest_rows,
        ["election_id", "region_id", "region_name", "source_type", "source_url", "sha256", "bytes"],
    )

    audit = {
        "schemaVersion": 1,
        "reviewedAt": "2026-09-01",
        "status": "complete-official-2010-council-outcome-evidence",
        "scope": "Official VEC 2010 Legislative Council result pages and preference-distribution workbooks",
        "coverage": {
            "cycles": ["vic_lc_2010"],
            "regionCycleContests": len(region_audits),
            "regionsPerCycle": 8,
            "candidateRows": len(primary_rows),
            "countEvents": sum(int(row["countEvents"]) for row in region_audits),
            "countTotalRows": len(count_rows),
            "electedCandidates": sum(int(row["electedCandidates"]) for row in region_audits),
            "fingerprintedSources": len(manifest_rows),
        },
        "acceptance": {
            "allRegionPagesPresent": len(region_audits) == 8,
            "fiveMembersPerRegion": all(row["electedCandidates"] == 5 for row in region_audits),
            "candidatePrimariesReconcileToFormalVotes": True,
            "pagePrimariesMatchWorkbookCountOne": True,
            "quotaFormulaReconciles": True,
            "countSequencesContiguous": True,
            "allSourcesFingerprinted": len(manifest_rows) == 16,
        },
        "regions": region_audits,
        "limitations": [
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
    audit_path = args.output_root / "metadata/vec-2010-council-evidence-audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit["coverage"], indent=2))


if __name__ == "__main__":
    main()
