#!/usr/bin/env python3
"""Extract a VEC candidate *review packet* from its 2026 legacy Excel workbook.

No public contact names, phone numbers or email fields are exported. This
parser neither promotes candidate records nor modifies forecast inputs.
Requires xlrd==2.0.1 for legacy BIFF8 XLS (not xlsx).
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

EXPECTED = {"Assembly": (88, 734), "Council": (8, 303)}
HEADER = "Candidate Contact Persons' Details Summary Report"
REQUIRED_FIELDS = ("chamber", "contest", "rowOrdinal", "candidate", "registeredParty")


def cell(sheet, row, col):
    if row >= sheet.nrows or col >= sheet.ncols:
        return ""
    return str(sheet.cell_value(row, col)).strip()


def norm(text):
    text = unicodedata.normalize("NFKD", str(text)).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def identity(name):
    name = str(name).strip()
    if "," in name:
        family, given = name.split(",", 1)
        name = given.strip() + " " + family.strip()
    return norm(name)


def candidates_from_sheet(sheet, source, receipt, expected=EXPECTED):
    if cell(sheet, 0, 0) != HEADER or cell(sheet, 1, 0) != "State Election 2026":
        raise ValueError("Unexpected VEC candidate report or election")
    as_at = cell(sheet, 3, 0)
    if not as_at.startswith("As at 09 Nov 2026"):
        raise ValueError("Source publication date does not match the audited VEC report")
    sections = []
    for r in range(sheet.nrows):
        label = cell(sheet, r, 0)
        if label.endswith((" District", " Region")) and all(
            not cell(sheet, r, c) for c in range(1, min(sheet.ncols, 5))
        ):
            sections.append((r, label))
    if len(sections) != sum(t[0] for t in expected.values()):
        raise ValueError("Unexpected number of VEC contest sections")
    names = set()
    rows, contests, seen = [], [], set()
    for i, (begin, name) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else sheet.nrows
        chamber = "Assembly" if name.endswith(" District") else "Council"
        contest = name.removesuffix(" District").removesuffix(" Region")
        key = (chamber, contest.casefold())
        if key in names:
            raise ValueError("Duplicate contest " + contest)
        names.add(key)
        match = re.fullmatch(r"\((1|5) vacanc(?:y|ies), (\d+) candidates\)", cell(sheet, begin + 1, 0))
        if not match or int(match[1]) != (1 if chamber == "Assembly" else 5):
            raise ValueError("Missing or malformed VEC declared contest count: " + contest)
        declared = int(match[2])
        if cell(sheet, begin + 2, 0) != "Candidates" or cell(sheet, begin + 2, 4) != "RPP Name":
            raise ValueError("Unexpected worksheet candidate column layout: " + contest)
        candidate_rows = []
        for r in range(begin + 3, end):
            if not any(cell(sheet, r, c) for c in range(min(sheet.ncols, 5))):
                continue
            candidate = cell(sheet, r, 0)
            if not candidate:
                raise ValueError("Non-candidate detail row in " + contest)
            ident = (chamber, contest.casefold(), identity(candidate))
            if ident in seen:
                raise ValueError("Duplicate candidate within " + contest)
            seen.add(ident)
            candidate_rows.append({
                "chamber": chamber,
                "contest": contest,
                "rowOrdinal": len(candidate_rows) + 1,
                "candidate": candidate,
                # Intentionally select ONLY columns 0 and 4. Columns 1-3
                # contain contact-person names, phones and email addresses.
                "registeredParty": cell(sheet, r, 4) or None,
            })
        if len(candidate_rows) != declared:
            raise ValueError(f"{contest}: expected {declared}, found {len(candidate_rows)}")
        contests.append({"chamber": chamber, "contest": contest, "declared": declared, "extracted": len(candidate_rows)})
        rows.extend(candidate_rows)
    for chamber, (num_contests, num_candidates) in expected.items():
        if sum(c["chamber"] == chamber for c in contests) != num_contests:
            raise ValueError("Wrong " + chamber + " contest count")
        if sum(r["chamber"] == chamber for r in rows) != num_candidates:
            raise ValueError("Wrong " + chamber + " candidate count")
    return {
        "schemaVersion": 1,
        "mode": "vec-2026-official-roster-review-only",
        "sourceUrl": receipt["sourceFileUrl"],
        "capturedAt": receipt["capturedAt"],
        "sourceSha256": source,
        "sourceReportAsAt": as_at,
        "candidateCount": len(rows),
        "contestCount": len(contests),
        "assemblyCount": sum(r["chamber"] == "Assembly" for r in rows),
        "councilCount": sum(r["chamber"] == "Council" for r in rows),
        "contactDetailsIncluded": False,
        "officialNominationAdmitted": False,
        "forecastInputsChanged": False,
        "ballotOrderPolicy": "Row ordinal only; Council group/column membership requires separate VEC region-page verification",
        "unaffiliatedLabelPolicy": "Blank VEC RPP label is not automatic evidence of independent or ungrouped classification",
        "contests": contests,
        "candidates": rows,
    }


def review_against_provisional(data, registry):
    prior = registry["candidates"]
    indexed = {}
    for p in prior:
        key = (norm(p["contest"]), identity(p["name"]))
        indexed.setdefault(key, []).append(p)
    matched = set()
    found, missing = [], []
    for row in data["candidates"]:
        key = (norm(row["contest"]), identity(row["candidate"]))
        candidates = indexed.get(key, [])
        if len(candidates) == 1:
            match = candidates[0]
            matched.add((norm(match["contest"]), identity(match["name"])))
            found.append({"chamber": row["chamber"], "contest": row["contest"],
                          "officialName": row["candidate"], "officialRegisteredParty": row["registeredParty"],
                          "provisionalName": match["name"], "provisionalParty": match.get("party"),
                          "reviewStatus": "identity-string-match-party-label-not-adjudicated"})
        elif not candidates:
            missing.append({"chamber": row["chamber"], "contest": row["contest"],
                            "officialName": row["candidate"], "registeredParty": row["registeredParty"],
                            "reviewStatus": "no-exact-normalized-provisional-name"})
        else:
            raise ValueError("Ambiguous previous candidate name: " + row["contest"])
    old_missing = [
        {"name": p["name"], "contest": p["contest"], "party": p.get("party"),
         "reviewStatus": "not-exact-normalized-in-official-list-not-proof-of-withdrawal"}
        for p in prior if (norm(p["contest"]), identity(p["name"])) not in matched
    ]
    if len(found) + len(missing) != data["candidateCount"]:
        raise ValueError("Reconciliation count mismatch")
    return {
        "schemaVersion": 1, "sourceSha256": data["sourceSha256"],
        "policy": "Review only. Name matches do not prove party continuity; unmatched names are not automatic replacements or withdrawals.",
        "priorCandidateCount": len(prior), "officialCandidateCount": data["candidateCount"],
        "exactNormalizedNameMatches": len(found),
        "newOrIdentityReviewNeeded": len(missing),
        "provisionalNotExactNameMatched": len(old_missing),
        "matchingNames": found, "officialNotMatched": missing,
        "provisionalNotMatched": old_missing,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--audit", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    raw = Path(args.file).read_bytes()
    receipt = json.loads(Path(args.receipt).read_text())
    digest = hashlib.sha256(raw).hexdigest()
    audit = json.loads(Path(args.audit).read_text())
    if (audit.get("sourceSha256") != digest or audit.get("sourceSizeBytes") != len(raw)):
        raise ValueError("Current VEC carrier does not match independently reviewed 10 November source audit")
    if (receipt.get("sourceFormat") != "xls"
            or receipt.get("captureStatus") != "REVIEW_REQUIRED"
            or receipt.get("sourceFileSha256") != digest):
        raise ValueError("Missing or non-matching audited XLS evidence receipt")
    import xlrd  # legacy .xls only; installed by the review-only workflow
    book = xlrd.open_workbook(file_contents=raw)
    if book.nsheets != 1:
        raise ValueError("Expected exactly one VEC candidate-report worksheet")
    data = candidates_from_sheet(book.sheet_by_index(0), digest, receipt)
    packet = review_against_provisional(data, json.loads(Path(args.registry).read_text()))
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    (target / "official-candidates-review.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    (target / "candidate-reconciliation-review.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n")
    with (target / "official-candidates-review.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        writer.writerows(data["candidates"])
    summary = {
        "sourceSha256": digest, "candidates": data["candidateCount"],
        "assembly": data["assemblyCount"], "council": data["councilCount"],
        "contests": data["contestCount"], "provisionalMatches": packet["exactNormalizedNameMatches"],
        "needsIdentityReview": packet["newOrIdentityReviewNeeded"],
        "oldRecordsNotNameMatched": packet["provisionalNotExactNameMatched"],
        "status": "REVIEW_ONLY_NO_REGISTRY_OR_MODEL_CHANGES",
    }
    (target / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
