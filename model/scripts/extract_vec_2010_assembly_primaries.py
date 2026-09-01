#!/usr/bin/env python3
"""Extract 2010 Victorian Assembly candidate primaries from the VEC report.

The supplied VEC Report to Parliament is a 1,088-page PDF with one bookmarked
first-preference table for each of the 88 Assembly districts.  This extractor
uses those bookmarks and the printed table geometry; it fails closed if the
source fingerprint, district count, candidate headers, party labels or formal
vote reconciliations differ from the audited source.

Runtime dependencies are intentionally extraction-only: ``pypdf`` and
``pdfplumber``.  The committed outputs are independently fingerprinted by the
repository's normal evidence validator, so CI does not need to parse the PDF.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pdfplumber
from pypdf import PdfReader


SOURCE_URL = "https://www.vec.vic.gov.au/-/media/08680c0035b34af4b6ea2074edc763a4.pdf"
SOURCE_SHA256 = "be2dbabd5735ff7128fa9ac5ab3e05e99d41c3d7a4502d33959b7c3464da7567"
ELECTION_ID = "vic_la_2010"
EXPECTED_DISTRICTS = 88
EXPECTED_CANDIDATES = 502
EXPECTED_STATEWIDE_FORMAL_VOTES = 3_164_729
TARGET_FAMILIES = ("ALP", "Coalition", "Greens", "One Nation", "Other/Independent")

# Exact affiliation strings printed in the audited report.  Longer phrases
# precede their substrings so the geometry matcher cannot select a partial label.
PARTY_PHRASES = (
    "D.L.P. - DEMOCRATIC LABOR PARTY",
    "D.L.P. DEMOCRATIC LABOR PARTY",
    "AUSTRALIAN LABOR PARTY",
    "AUSTRALIAN GREENS",
    "SOCIALIST ALLIANCE",
    "COUNTRY ALLIANCE",
    "FAMILY FIRST",
    "CHRISTIAN PARTY",
    "AUSTRALIAN PARTY",
    "SEX PARTY",
    "THE NATIONALS",
    "NATIONALS",
    "LIBERAL",
)

PARTY_FAMILY = {
    "AUSTRALIAN LABOR PARTY": "ALP",
    "LIBERAL": "Coalition",
    "THE NATIONALS": "Coalition",
    "NATIONALS": "Coalition",
    "AUSTRALIAN GREENS": "Greens",
    "D.L.P. - DEMOCRATIC LABOR PARTY": "Other/Independent",
    "D.L.P. DEMOCRATIC LABOR PARTY": "Other/Independent",
    "SOCIALIST ALLIANCE": "Other/Independent",
    "COUNTRY ALLIANCE": "Other/Independent",
    "FAMILY FIRST": "Other/Independent",
    "CHRISTIAN PARTY": "Other/Independent",
    "AUSTRALIAN PARTY": "Other/Independent",
    "SEX PARTY": "Other/Independent",
    "": "Other/Independent",
}

REGION_PREFIXES = (
    "Eastern Metropolitan",
    "Eastern Victoria",
    "Northern Metropolitan",
    "Northern Victoria",
    "South Eastern Metropolitan",
    "Southern Metropolitan",
    "Western Metropolitan",
    "Western Victoria",
)

NUMBER = re.compile(r"^\d[\d,]*$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def flatten_outline(items: Iterable[Any]) -> Iterable[Any]:
    for item in items:
        if isinstance(item, list):
            yield from flatten_outline(item)
        else:
            yield item


def district_bookmarks(reader: PdfReader) -> list[tuple[str, int]]:
    bookmarks: list[tuple[str, int]] = []
    for item in flatten_outline(reader.outline):
        title = getattr(item, "title", "")
        if not title.endswith("_1") or title.startswith(REGION_PREFIXES):
            continue
        bookmarks.append((title[:-2], reader.get_destination_page_number(item) + 1))
    if len(bookmarks) != EXPECTED_DISTRICTS:
        raise ValueError(f"expected {EXPECTED_DISTRICTS} district bookmarks, found {len(bookmarks)}")
    if len({name for name, _ in bookmarks}) != EXPECTED_DISTRICTS:
        raise ValueError("district bookmark names are not unique")
    if any(a[1] >= b[1] for a, b in zip(bookmarks, bookmarks[1:])):
        raise ValueError("district bookmarks are not in strictly increasing page order")
    return bookmarks


def word_rows(words: list[dict[str, Any]], tolerance: float = 0.8) -> list[list[dict[str, Any]]]:
    rows: list[list[dict[str, Any]]] = []
    for word in sorted(words, key=lambda value: (value["top"], value["x0"])):
        for row in rows:
            if abs(row[0]["top"] - word["top"]) < tolerance:
                row.append(word)
                break
        else:
            rows.append([word])
    return [sorted(row, key=lambda value: value["x0"]) for row in rows]


def word_centre(word: dict[str, Any]) -> float:
    return (word["x0"] + word["x1"]) / 2


def phrase_match(
    centre: float,
    candidate_top: float,
    header: list[dict[str, Any]],
    phrase: str,
) -> tuple[float, tuple[dict[str, Any], ...]] | None:
    pools: list[list[dict[str, Any]]] = []
    for token in phrase.split():
        matches = [
            word
            for word in header
            if word["text"] == token
            and word["top"] > candidate_top + 4
            and abs(word_centre(word) - centre) < 60
        ]
        if not matches:
            return None
        pools.append(matches)

    best: tuple[float, tuple[dict[str, Any], ...]] | None = None
    for combination in itertools.product(*pools):
        if len({id(word) for word in combination}) != len(combination):
            continue
        tops = [word["top"] for word in combination]
        if any(first > second + 1 for first, second in zip(tops, tops[1:])):
            continue
        centres = [word_centre(word) for word in combination]
        if max(centres) - min(centres) > 90:
            continue
        score = sum(abs(value - centre) for value in centres) / len(centres)
        score += 0.05 * (max(tops) - min(tops))
        if best is None or score < best[0]:
            best = (score, combination)
    return best


def parse_district(page: Any, district_name: str, source_page: int) -> tuple[int, list[dict[str, Any]]]:
    words = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=False)
    rows = word_rows(words)
    formal_votes: int | None = None
    heading_top: float | None = None
    total_row: list[dict[str, Any]] | None = None

    for row in rows:
        text = " ".join(word["text"] for word in row)
        if text.startswith("FORMAL VOTES"):
            values = [word for word in row if NUMBER.match(word["text"])]
            if values:
                formal_votes = int(values[-1]["text"].replace(",", ""))
        if "NUMBER OF FIRST PREFERENCE VOTES POLLED BY EACH CANDIDATE" in text:
            heading_top = row[0]["top"]
        if text.startswith("TOTAL ALL VOTE TYPES"):
            total_row = row

    if formal_votes is None or heading_top is None or total_row is None:
        raise ValueError(f"{district_name}: required table markers were not found on page {source_page}")

    numeric_words = [word for word in total_row if NUMBER.match(word["text"])]
    values = [int(word["text"].replace(",", "")) for word in numeric_words]
    candidate_count = len(values) - 2  # informal votes and total votes polled
    if candidate_count < 2:
        raise ValueError(f"{district_name}: invalid candidate-column count")
    candidate_votes = values[:candidate_count]
    informal_votes, total_votes = values[-2:]
    if sum(candidate_votes) != formal_votes:
        raise ValueError(f"{district_name}: candidate votes do not equal formal votes")
    if formal_votes + informal_votes != total_votes:
        raise ValueError(f"{district_name}: formal plus informal votes do not equal total votes")

    centres = [word_centre(word) for word in numeric_words]
    first_data_top = min(
        row[0]["top"]
        for row in rows
        if row[0]["top"] > heading_top
        and len([word for word in row if NUMBER.match(word["text"])]) >= candidate_count + 2
    )
    raw_header = [word for word in words if heading_top + 2 < word["top"] < first_data_top - 1]

    # Discard the printed Informal/Total column headings before candidate parsing.
    header: list[dict[str, Any]] = []
    for word in raw_header:
        nearest = min(range(len(centres)), key=lambda index: abs(word_centre(word) - centres[index]))
        if nearest < candidate_count:
            header.append(word)

    anchors = sorted((word for word in header if "," in word["text"]), key=word_centre)
    if len(anchors) != candidate_count:
        raise ValueError(
            f"{district_name}: expected {candidate_count} comma-anchored candidate names, found {len(anchors)}"
        )

    # Detect affiliation phrases globally, then allocate each physical phrase to
    # only one candidate.  This handles narrow columns where e.g. "THE" and
    # "NATIONALS" sit either side of the candidate's numeric column centre.
    options: list[tuple[float, int, int, str, tuple[dict[str, Any], ...]]] = []
    for index, (centre, anchor) in enumerate(zip(centres[:candidate_count], anchors)):
        for phrase in PARTY_PHRASES:
            match = phrase_match(centre, anchor["top"], header, phrase)
            if match:
                score, physical_words = match
                options.append((score, -len(phrase.split()), index, phrase, physical_words))
    options.sort(key=lambda value: (value[1], value[0]))

    affiliations: dict[int, str] = {}
    used_party_words: set[int] = set()
    for _score, _negative_length, index, phrase, physical_words in options:
        word_ids = {id(word) for word in physical_words}
        if index in affiliations or word_ids & used_party_words:
            continue
        affiliations[index] = phrase
        used_party_words.update(word_ids)

    # Party words are now removed.  Assign all remaining name fragments to the
    # nearest comma anchor, which preserves wrapped surnames and given names.
    anchor_centres = [word_centre(word) for word in anchors]
    name_words = [word for word in header if id(word) not in used_party_words]
    forced_owner: dict[int, int] = {}

    # When two comma anchors share a line, any intervening given-name token
    # belongs to the left-hand anchor.  A pure midpoint rule would misallocate
    # ASBURY, Lisa / WALIA, Harpreet in Keilor because "Lisa" is centred almost
    # exactly between their vote columns.
    for index, (left, right) in enumerate(zip(anchors, anchors[1:])):
        if abs(left["top"] - right["top"]) >= 0.8:
            continue
        for word in name_words:
            if (
                abs(word["top"] - left["top"]) < 0.8
                and left["x1"] <= word["x0"]
                and word["x1"] <= right["x0"]
                and "," not in word["text"]
            ):
                forced_owner[id(word)] = index

    # Preserve visibly hyphenated continuations on the next printed line, such
    # as McCOLL, Karen- / Joy in Bundoora.
    for index, word in enumerate(name_words):
        if not word["text"].endswith("-"):
            continue
        owner = min(range(candidate_count), key=lambda value: abs(word_centre(word) - anchor_centres[value]))
        for continuation in name_words:
            if (
                1 < continuation["top"] - word["top"] < 13
                and continuation["x0"] < word["x1"] + 2
                and continuation["x1"] > word["x0"] - 2
                and "," not in continuation["text"]
            ):
                forced_owner[id(continuation)] = owner

    name_groups: list[list[dict[str, Any]]] = [[] for _ in anchors]
    for word in name_words:
        index = forced_owner.get(
            id(word),
            min(range(candidate_count), key=lambda value: abs(word_centre(word) - anchor_centres[value])),
        )
        name_groups[index].append(word)

    candidates: list[dict[str, Any]] = []
    for index, (group, votes) in enumerate(zip(name_groups, candidate_votes), start=1):
        name = " ".join(word["text"] for word in sorted(group, key=lambda value: (value["top"], value["x0"])))
        name = re.sub(r"-\s+", "-", name)
        if name.count(",") != 1:
            raise ValueError(f"{district_name}: malformed candidate name {name!r}")
        party = affiliations.get(index - 1, "")
        if party not in PARTY_FAMILY:
            raise ValueError(f"{district_name}: unadjudicated party label {party!r}")
        independent = party == ""
        candidates.append(
            {
                "election_id": ELECTION_ID,
                "district_name": district_name,
                "district_id": slugify(district_name),
                "source_page": source_page,
                "source_url": SOURCE_URL,
                "source_sha256": SOURCE_SHA256,
                "candidate_order": index,
                "candidate_name": name,
                "party_raw": party,
                "independent_status": independent,
                "party_family": PARTY_FAMILY[party],
                "first_preference_votes": votes,
                "formal_votes": formal_votes,
                "district_reconciled": True,
            }
        )
    return formal_votes, candidates


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def extract(pdf_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source_hash = sha256(pdf_path)
    if source_hash != SOURCE_SHA256:
        raise ValueError(f"source SHA-256 mismatch: expected {SOURCE_SHA256}, found {source_hash}")

    reader = PdfReader(pdf_path)
    if len(reader.pages) != 1088:
        raise ValueError(f"expected 1088 source pages, found {len(reader.pages)}")
    bookmarks = district_bookmarks(reader)

    candidate_rows: list[dict[str, Any]] = []
    district_formal: dict[str, int] = {}
    with pdfplumber.open(pdf_path) as document:
        for district_name, page_number in bookmarks:
            formal_votes, candidates = parse_district(document.pages[page_number - 1], district_name, page_number)
            district_formal[district_name] = formal_votes
            candidate_rows.extend(candidates)

    if len(candidate_rows) != EXPECTED_CANDIDATES:
        raise ValueError(f"expected {EXPECTED_CANDIDATES} candidates, found {len(candidate_rows)}")
    if len({row["district_id"] for row in candidate_rows}) != EXPECTED_DISTRICTS:
        raise ValueError("candidate output does not cover 88 unique districts")
    if sum(district_formal.values()) != EXPECTED_STATEWIDE_FORMAL_VOTES:
        raise ValueError(
            "district formal votes do not reconcile to the report's statewide total "
            f"of {EXPECTED_STATEWIDE_FORMAL_VOTES:,}"
        )

    family_rows: list[dict[str, Any]] = []
    for district_name, page_number in bookmarks:
        district_candidates = [row for row in candidate_rows if row["district_name"] == district_name]
        for family in TARGET_FAMILIES:
            matching = [row for row in district_candidates if row["party_family"] == family]
            family_rows.append(
                {
                    "election_id": ELECTION_ID,
                    "district_name": district_name,
                    "district_id": slugify(district_name),
                    "source_page": page_number,
                    "party_family": family,
                    "contest_status": "contested" if matching else "verified_no_contest",
                    "candidate_count": len(matching),
                    "first_preference_votes": sum(row["first_preference_votes"] for row in matching),
                    "formal_votes": district_formal[district_name],
                    "district_reconciled": True,
                }
            )
        if sum(row["first_preference_votes"] for row in family_rows[-len(TARGET_FAMILIES) :]) != district_formal[district_name]:
            raise ValueError(f"{district_name}: five-family votes do not reconcile")

    party_counts = Counter(row["party_raw"] or "[blank-independent]" for row in candidate_rows)
    family_totals = Counter()
    for row in candidate_rows:
        family_totals[row["party_family"]] += row["first_preference_votes"]
    audit = {
        "schemaVersion": 1,
        "reviewedAt": "2026-09-01",
        "status": "complete-2010-outcome-evidence",
        "source": {
            "authority": "Victorian Electoral Commission",
            "document": "Report to Parliament on the 2010 Victorian State Election",
            "url": SOURCE_URL,
            "suppliedFilename": "08680c0035b34af4b6ea2074edc763a4(1).pdf",
            "sha256": source_hash,
            "pages": len(reader.pages),
            "assemblyDistrictTablePages": {name: page for name, page in bookmarks},
            "reuseTerms": "not-separately-stated-in-supplied-report",
        },
        "extraction": {
            "method": "bookmarked district pages plus printed table geometry",
            "extractor": "model/scripts/extract_vec_2010_assembly_primaries.py",
            "districts": len(bookmarks),
            "candidateRows": len(candidate_rows),
            "familyRows": len(family_rows),
            "statewideFormalVotes": sum(district_formal.values()),
            "partyLabelCounts": dict(sorted(party_counts.items())),
            "familyVoteTotals": {family: family_totals.get(family, 0) for family in TARGET_FAMILIES},
        },
        "checks": {
            "sourceFingerprintMatched": True,
            "districtBookmarks": EXPECTED_DISTRICTS,
            "districtPrimaryTables": EXPECTED_DISTRICTS,
            "uniqueDistricts": EXPECTED_DISTRICTS,
            "candidateNamesStructurallyValid": True,
            "allPartyLabelsAdjudicated": True,
            "allCandidateRowsNonNegative": all(row["first_preference_votes"] >= 0 for row in candidate_rows),
            "allDistrictCandidateTotalsReconciled": True,
            "allDistrictFamilyTotalsReconciled": True,
            "absentFamiliesMarkedVerifiedNoContest": True,
        },
        "use": {
            "historicalOutcomeScoring": "eligible",
            "currentForecast": "excluded",
            "historicalReplayInput": "outcome-only-not-pre-election-information",
            "automaticGateOpening": False,
            "productionAuthorisation": False,
        },
    }
    return candidate_rows, family_rows, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument(
        "--candidate-output",
        type=Path,
        default=Path("model/data/processed/vec_2010_assembly_candidate_primaries.csv"),
    )
    parser.add_argument(
        "--family-output",
        type=Path,
        default=Path("model/data/processed/vec_2010_assembly_family_primaries.csv"),
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=Path("metadata/vec-2010-assembly-primary-audit.json"),
    )
    args = parser.parse_args()

    candidates, families, audit = extract(args.pdf)
    candidate_fields = [
        "election_id",
        "district_name",
        "district_id",
        "source_page",
        "source_url",
        "source_sha256",
        "candidate_order",
        "candidate_name",
        "party_raw",
        "independent_status",
        "party_family",
        "first_preference_votes",
        "formal_votes",
        "district_reconciled",
    ]
    family_fields = [
        "election_id",
        "district_name",
        "district_id",
        "source_page",
        "party_family",
        "contest_status",
        "candidate_count",
        "first_preference_votes",
        "formal_votes",
        "district_reconciled",
    ]
    write_csv(args.candidate_output, candidates, candidate_fields)
    write_csv(args.family_output, families, family_fields)
    audit["outputs"] = [
        {
            "path": "model/data/processed/vec_2010_assembly_candidate_primaries.csv",
            "sha256": sha256(args.candidate_output),
            "rows": len(candidates),
        },
        {
            "path": "model/data/processed/vec_2010_assembly_family_primaries.csv",
            "sha256": sha256(args.family_output),
            "rows": len(families),
        },
    ]
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Extracted {len(candidates)} candidates across {EXPECTED_DISTRICTS} districts; "
        "all candidate and family totals reconcile."
    )


if __name__ == "__main__":
    main()
