#!/usr/bin/env python3
"""Build the cutoff-safe 2010 notional Assembly baseline from ABC's pendulum."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_URL = "https://www.abc.net.au/news/2010-01-25/pendulum-for-2010-victorian-election/9389340"
PUBLISHED = "2010-01-25"


def fetch() -> bytes:
    req = Request(SOURCE_URL, headers={"User-Agent": "vic-election-2026 historical evidence extractor"})
    with urlopen(req, timeout=60) as response:
        return response.read()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def extract(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8", errors="replace")
    pattern = re.compile(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", re.S | re.I)
    rows: list[dict[str, str]] = []
    for district, comparison in pattern.findall(text):
        district = html.unescape(re.sub(r"<[^>]+>", "", district)).strip()
        comparison = html.unescape(re.sub(r"<[^>]+>", "", comparison)).strip()
        if "%" not in comparison and " v " not in comparison:
            continue
        contest_note = re.search(r"\(([^)]*\bv\s+[^)]*)\)", district)
        district = re.sub(r"\s*\([^)]*\)$", "", district).replace(" (*)", "")
        match = re.match(r"(ALP|LIB|NAT|IND)\s+([0-9.]+)%?(?:\s+v\s+(LIB|ALP))?$", comparison)
        if not match:
            raise ValueError(f"unparsed ABC comparison: {district!r} {comparison!r}")
        holder = {"ALP": "ALP", "LIB": "LIB_NAT", "NAT": "LIB_NAT", "IND": "OTH_IND"}[match.group(1)]
        contest = "non-major" if match.group(3) or contest_note else "major-party"
        rows.append({"district_name": district, "district_id": slug(district), "notional_holder_family": holder, "comparison_type": contest, "notional_margin_pp": match.group(2), "published_comparison": comparison})
    if len(rows) != 88 or len({row["district_id"] for row in rows}) != 88:
        raise ValueError(f"expected 88 unique districts, found {len(rows)}")
    return rows


def main() -> None:
    payload = fetch()
    rows = extract(payload)
    out = Path("model/data/validation/historical-replay-2010-assembly-notional-baseline.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        fields = ["cycle_id", "district_id", "district_name", "notional_holder_family", "comparison_type", "notional_margin_pp", "published_comparison", "source_url", "source_sha256", "evidence_available_by", "target_outcome_dependency"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"cycle_id": "vic_la_2010", **row, "source_url": SOURCE_URL, "source_sha256": sha256(payload), "evidence_available_by": PUBLISHED, "target_outcome_dependency": "false"})
    manifest = {"schemaVersion": 1, "cycleId": "vic_la_2010", "sourceAuthority": "ABC News / Antony Green", "sourceUrl": SOURCE_URL, "publishedAt": PUBLISHED, "retrievedSha256": sha256(payload), "targetOutcomeDependency": False, "districtCount": len(rows), "nonMajorContestCount": sum(row["comparison_type"] == "non-major" for row in rows)}
    Path("metadata/historical-replay-2010-notional-baseline-audit.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
