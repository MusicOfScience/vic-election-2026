#!/usr/bin/env python3
"""Reconcile VEC 2026 Council ballot groups against the verified 303-row roster.

Read-only official-source audit. Never publish the original VEC HTML: the
source pages include candidate contact names, telephone numbers and emails.
Only candidate, group letter and order are exported in a 7-day review artifact.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
VEC_HOSTS = {"www.vec.vic.gov.au", "vec.vic.gov.au"}
REGIONS = {
    "Eastern Victoria": "eastern-victoria",
    "North-Eastern Metropolitan": "north-eastern-metropolitan",
    "Northern Metropolitan": "northern-metropolitan",
    "Northern Victoria": "northern-victoria",
    "South-Eastern Metropolitan": "south-eastern-metropolitan",
    "Southern Metropolitan": "southern-metropolitan",
    "Western Metropolitan": "western-metropolitan",
    "Western Victoria": "western-victoria",
}
MARKER = "the groups and candidates for this region election"
GROUP_RE = re.compile(r"(?m)^[ \t]*([A-Z])\.[ \t]+([^\n]+)[ \t]*$")
UNGROUPED_RE = re.compile(r"(?mi)^[ \t]*(Ungrouped)[ \t]*$")


def clean(text: str) -> str:
    """NFKC preserves known VEC names and offsets for ordered regex search."""
    return unicodedata.normalize("NFKC", str(text)).casefold()


def text_of_page(html: bytes, region: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()
    title = soup.get_text("\n", strip=True)
    if f"candidates for {region}".casefold() not in title.casefold():
        raise ValueError("Wrong region page or missing candidate-list heading")
    normalized = clean(title).replace("\u00a0", " ")
    start = normalized.find(MARKER)
    if start < 0:
        raise ValueError("No VEC final ballot-order declaration")
    return normalized[start:]


def headings_from_text(text: str) -> list[tuple[int, str, str]]:
    found = []
    for m in GROUP_RE.finditer(text):
        letter, label = m.group(1).upper(), m.group(2).strip()
        if "group voting tickets" in label or len(label) > 120:
            continue
        found.append((m.start(), letter, label))
    for m in UNGROUPED_RE.finditer(text):
        found.append((m.start(), "Ungrouped", "Ungrouped"))
    found.sort(key=lambda item: item[0])
    if not found or found[0][1] != "A":
        raise ValueError("Missing or non-alphabetic first Council group heading")
    return found


def match_candidate(text: str, name: str, cursor: int):
    pattern = re.escape(clean(name).replace("\u00a0", " "))
    pattern = pattern.replace(r"\ ", r"\s+")
    result = re.search(pattern, text[cursor:], flags=re.IGNORECASE)
    if result is None:
        raise ValueError("Candidate not found after previous nominee: " + name)
    return cursor + result.start(), cursor + result.end()


def reconcile_region(html: bytes, region: str, expected: list[list]):
    text = text_of_page(html, region)
    headings = headings_from_text(text)
    mapped = []
    cursor = 0
    for row in expected:
        # Tuple schema is [chamber, contest, workbook row ordinal, candidate, RPP].
        _, contest, source_ordinal, name, _ = row
        if contest != region:
            raise ValueError("Workbook region mismatch")
        at, cursor = match_candidate(text, name, cursor)
        earlier = [item for item in headings if item[0] < at]
        if not earlier:
            raise ValueError("Nominee has no preceding VEC group heading: " + name)
        _, letter, label = earlier[-1]
        mapped.append({
            "region": region,
            "candidate": name,
            "sourceOrdinal": source_ordinal,
            "group": letter,
            "groupLabel": label,
        })
    if len(mapped) != len(expected):
        raise ValueError("Missing Council nominees")
    # Candidates in each letter must be contiguous, and grouped columns must
    # advance from A sequentially. "Ungrouped" may appear only at the end.
    sequence = [entry["group"] for entry in mapped]
    blocks = []
    for group in sequence:
        if not blocks or blocks[-1] != group:
            blocks.append(group)
    letters = [letter for letter in blocks if letter != "Ungrouped"]
    if letters != [chr(65 + x) for x in range(len(letters))]:
        raise ValueError("Non-contiguous or out-of-order Council group letters")
    if "Ungrouped" in blocks and blocks[-1] != "Ungrouped":
        raise ValueError("Ungrouped nominees must follow all lettered groups")
    if any(letter == "Ungrouped" for letter in blocks[:-1]):
        raise ValueError("Ungrouped nominees appeared before last block")
    # Each group label must be invariant throughout the consecutive group.
    labels = {}
    within_group = Counter()
    for entry in mapped:
        group = entry["group"]
        if group in labels and labels[group] != entry["groupLabel"]:
            raise ValueError("Same Council group letter has conflicting labels")
        labels[group] = entry["groupLabel"]
        within_group[group] += 1
        entry["withinGroupOrdinal"] = within_group[group]
    return {
        "region": region,
        "candidateCount": len(mapped),
        "letteredGroups": len(letters),
        "ungroupedCandidates": within_group.get("Ungrouped", 0),
        "groups": [{"letter": g, "label": labels[g], "candidateCount": within_group[g]} for g in blocks],
        "candidates": mapped,
    }


def fetch_vec(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in VEC_HOSTS:
        raise ValueError("Only named VEC HTTPS endpoints allowed")
    request = Request(url, headers={
        "User-Agent": "vic-election-2026-group-evidence/1.0",
        "Accept": "text/html",
    })
    with urlopen(request, timeout=25) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname not in VEC_HOSTS:
            raise ValueError("VEC region endpoint redirected off authorised host")
        if response.status != 200:
            raise ValueError("VEC HTTP status " + str(response.status))
        if "html" not in response.headers.get("content-type", ""):
            raise ValueError("VEC region response is not HTML")
        raw = response.read(2_000_001)
    if not raw or len(raw) > 2_000_000:
        raise ValueError("Empty or oversized VEC region page")
    return raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", required=True)
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    roster_bytes = Path(options.roster).read_bytes()
    roster = json.loads(roster_bytes)
    if roster.get("sourceFileSha256") != (
        "f5c9505d01abb39bfd4e20cd389c6adea2e524a26423c7c82a51084e21d95c16"
    ):
        raise ValueError("Unverified VEC workbook source")
    council_rows = [r for r in roster["rows"] if r[0] == "Council"]
    if len(council_rows) != 303 or len(REGIONS) != 8:
        raise ValueError("Council candidate count or region universe changed")
    review = {
        "schemaVersion": 1,
        "status": "review-only-requires-human-approval",
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "candidateWorkbookSha256": roster["sourceFileSha256"],
        "candidateRosterSha256": hashlib.sha256(roster_bytes).hexdigest(),
        "privacy": "Only official candidate names and group assignments; source contact details excluded.",
        "forecastInputsChanged": False,
        "registryChanged": False,
        "regions": [],
    }
    output = Path(options.output)
    output.mkdir(parents=True, exist_ok=True)
    errors = []
    for region, slug in REGIONS.items():
        url = f"https://www.vec.vic.gov.au/electoral-boundaries/state-regions/{slug}-region/nominations"
        expected = [r for r in council_rows if r[1] == region]
        if not expected:
            raise ValueError("Missing official roster region: " + region)
        try:
            raw = fetch_vec(url)
            result = reconcile_region(raw, region, expected)
            result["sourceUrl"] = url
            result["sourceHtmlSha256"] = hashlib.sha256(raw).hexdigest()
            review["regions"].append(result)
            print(json.dumps({"region": region, "status": "matched",
                "candidates": len(expected), "groups": result["letteredGroups"],
                "ungrouped": result["ungroupedCandidates"]}))
        except Exception as exc:
            # Never log or persist source HTML, contact-person data or other
            # private fields; candidate names alone may appear in diagnostics.
            message = str(exc)
            errors.append({"region": region, "error": message})
            print(json.dumps({"region": region, "status": "REVIEW_REQUIRED", "reason": message}))
    review["allRegionsVerified"] = len(review["regions"]) == 8 and not errors
    review["verifiedCandidateCount"] = sum(x["candidateCount"] for x in review["regions"])
    review["errors"] = errors
    review["status"] = "review-ready-not-model-admitted" if review["allRegionsVerified"] and review["verifiedCandidateCount"] == 303 else "INCOMPLETE_SOURCE_REVIEW"
    (output / "vec-council-groups-review.json").write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": review["status"], "regionsMatched": len(review["regions"]),
        "candidateCount": review["verifiedCandidateCount"], "errors": len(errors)}))
    if review["status"] != "review-ready-not-model-admitted":
        raise SystemExit("Council ballot-group review incomplete; the report remains quarantined")


if __name__ == "__main__":
    main()
