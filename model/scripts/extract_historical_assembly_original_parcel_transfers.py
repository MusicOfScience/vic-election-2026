#!/usr/bin/env python3
"""Extract clean first-exclusion Assembly transfer events from official VEC pages.

Only the first exclusion is treated as a source-party preference observation.
At that point the excluded candidate's parcel consists of original first-
preference ballots; later exclusions contain mixed transferred parcels and are
therefore not silently attributed to the later candidate's party.

This script is historical evidence construction for PR #138. It does not read
2026 forecast outputs and does not fit any preference parameters.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CYCLES = (2010, 2014, 2018, 2022)
FAMILY_TO_MODEL = {
    "ALP": "ALP",
    "Coalition": "LIB_NAT",
    "One Nation": "ONP",
    "Greens": "GRN",
    "Other/Independent": "OTH_IND",
    "LIB_NAT": "LIB_NAT",
    "ONP": "ONP",
    "GRN": "GRN",
    "OTH_IND": "OTH_IND",
}
MODEL_PARTIES = ("ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND")


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join(html.unescape("".join(self._cell)).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(cell.strip() for cell in self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def norm(value: str) -> str:
    return " ".join(value.casefold().split())


def surname(value: str) -> str:
    """Return the surname token used by VEC's `SURNAME, Given` tables.

    The 2010 PDF-derived candidate registry contains a handful of damaged given
    names (for example `COLTMAN,` and `ELLIOTT,`) while the official HTML
    distribution pages contain the full names. A surname fallback is therefore
    allowed only when the surname identifies exactly one governed candidate in
    the same district. Ambiguity remains a hard failure.
    """
    text = norm(value)
    return text.split(",", 1)[0].strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def integer(value: str) -> int:
    text = value.replace(",", "").strip()
    return int(text) if text else 0


def fetch(url: str, cache_dir: Path, retries: int = 4) -> bytes:
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    cache = cache_dir / f"{key}.html"
    if cache.exists():
        return cache.read_bytes()
    cache.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "vic-election-2026-original-parcel-evidence/1.0"})
            with urlopen(req, timeout=90) as response:
                payload = response.read()
            if not payload:
                raise ValueError(f"empty response: {url}")
            cache.write_bytes(payload)
            return payload
        except Exception as exc:  # bounded retries for VEC's intermittent 999
            last = exc
            if attempt + 1 == retries:
                raise
    raise RuntimeError(last)


def distribution_link(source: str, base_url: str) -> str | None:
    for pattern in (
        r'href=["\']([^"\']*distribution[^"\']*district\.html)["\']',
        r'href=["\']([^"\']*distribution[^"\']*\.html)["\']',
    ):
        match = re.search(pattern, source, flags=re.I)
        if match:
            return urljoin(base_url, match.group(1))
    return None


def candidate_registry(year: int) -> dict[tuple[str, str], str]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_candidate_primaries.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    registry: dict[tuple[str, str], str] = {}
    for row in rows:
        district = norm(row["district_name"])
        candidate = norm(row["candidate_name"])
        family = FAMILY_TO_MODEL.get(row["party_family"])
        if family is None:
            raise ValueError(f"{year} {row['district_name']}: unmodelled family {row['party_family']!r}")
        registry[(district, candidate)] = family
    return registry


def resolve_candidate_family(
    registry: dict[tuple[str, str], str], district_key: str, candidate: str
) -> tuple[str, str]:
    """Resolve exact name first, then a unique same-district surname only."""
    candidate_key = norm(candidate)
    exact = registry.get((district_key, candidate_key))
    if exact is not None:
        return exact, "exact"
    target_surname = surname(candidate)
    matches = [
        (name, family)
        for (district, name), family in registry.items()
        if district == district_key and surname(name) == target_surname
    ]
    if len(matches) == 1:
        return matches[0][1], "unique-district-surname"
    if not matches:
        raise ValueError(f"candidate missing from governed registry: {candidate!r}")
    raise ValueError(
        f"candidate surname is ambiguous in governed registry: {candidate!r} -> {[name for name, _ in matches]!r}"
    )


def find_distribution_table(source: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(source)
    for table in parser.tables:
        if len(table) < 3 or not table[0] or table[0][0].strip():
            continue
        labels = [norm(row[0]) for row in table[1:] if row]
        if any("first preference" in x or "first pref" in x for x in labels) and any(x.startswith("transfer of ") for x in labels):
            return table
    raise ValueError("distribution page has no recognised preference table")


def source_from_transfer_label(label: str) -> tuple[int, str]:
    match = re.search(
        r"transfer of\s+([0-9,]+)\s+ballot[- ]papers\s+of\s+(.+?)\s*\(\s*(?:1st|first)\s+excluded candidate\s*\)",
        label,
        flags=re.I,
    )
    if not match:
        raise ValueError(f"first transfer label is not an original-parcel exclusion: {label!r}")
    return integer(match.group(1)), match.group(2).strip()


def extract_one(row: dict[str, str], year: int, registry: dict[tuple[str, str], str], cache_dir: Path) -> dict:
    district = row["district_name"]
    source_url = row.get("source_url") or row.get("outcome_source_url")
    if not source_url:
        return {"district_name": district, "status": "no-source-url"}
    try:
        source_payload = fetch(source_url, cache_dir / str(year))
        source = source_payload.decode("utf-8", "replace")
        dist_url = distribution_link(source, source_url)
        # Some governed outcome rows, notably 2022, already point directly to
        # the official distribution page. In that case there is no parent-page
        # hyperlink to discover; reuse the governed outcome URL itself.
        outcome_url = row.get("outcome_source_url") or ""
        if dist_url is None and "distribution" in outcome_url.casefold():
            dist_url = outcome_url
        if dist_url is None:
            return {"district_name": district, "status": "no-distribution-link", "source_url": source_url, "source_sha256": sha(source_payload)}
        dist_payload = fetch(dist_url, cache_dir / str(year))
        table = find_distribution_table(dist_payload.decode("utf-8", "replace"))
        headers = table[0]
        if len(headers) < 4 or norm(headers[-1]) != "total":
            raise ValueError(f"unexpected distribution header: {headers!r}")
        candidates = headers[1:-1]
        first = next(row for row in table[1:] if row and ("first preference" in norm(row[0]) or "first pref" in norm(row[0])))
        transfer = next(row for row in table[1:] if row and norm(row[0]).startswith("transfer of "))
        label_total, source_candidate = source_from_transfer_label(transfer[0])
        if len(first) < len(headers) or len(transfer) < len(headers):
            raise ValueError("ragged first-preference/transfer row")
        first_votes = [integer(value) for value in first[1:1 + len(candidates)]]
        transfer_votes = [integer(value) for value in transfer[1:1 + len(candidates)]]
        row_total = integer(transfer[-1])
        try:
            source_index = next(i for i, candidate in enumerate(candidates) if norm(candidate) == norm(source_candidate))
        except StopIteration as exc:
            raise ValueError(f"excluded candidate {source_candidate!r} not found in header") from exc
        source_first = first_votes[source_index]
        if source_first != label_total or row_total != label_total:
            raise ValueError(
                f"original parcel does not reconcile: first={source_first}, label={label_total}, row={row_total}"
            )
        if transfer_votes[source_index] != 0:
            raise ValueError("excluded candidate received votes in own transfer row")
        if sum(transfer_votes) != source_first:
            raise ValueError(f"destination transfers do not sum to original parcel ({sum(transfer_votes)} vs {source_first})")

        district_key = norm(district)
        source_family, source_match_method = resolve_candidate_family(registry, district_key, source_candidate)

        family_votes = {party: 0 for party in MODEL_PARTIES}
        family_candidate_count = {party: 0 for party in MODEL_PARTIES}
        candidate_destinations = []
        fallback_match_count = int(source_match_method != "exact")
        for index, candidate in enumerate(candidates):
            if index == source_index:
                continue
            family, match_method = resolve_candidate_family(registry, district_key, candidate)
            fallback_match_count += int(match_method != "exact")
            family_votes[family] += transfer_votes[index]
            family_candidate_count[family] += 1
            candidate_destinations.append({
                "candidate": candidate,
                "family": family,
                "votes": transfer_votes[index],
                "registry_match_method": match_method,
            })

        within_family_votes = family_votes[source_family]
        return {
            "status": "clean-original-parcel",
            "election_year": year,
            "election_id": f"vic_la_{year}",
            "district_id": slug(district),
            "district_name": district,
            "source_candidate": source_candidate,
            "source_family": source_family,
            "source_registry_match_method": source_match_method,
            "registry_surname_fallback_matches": fallback_match_count,
            "source_votes": source_first,
            "destination_votes": family_votes,
            "destination_candidate_count": family_candidate_count,
            "within_source_family_transfer_votes": within_family_votes,
            "within_source_family_transfer_share": within_family_votes / source_first if source_first else 0.0,
            "candidate_destinations": candidate_destinations,
            "source_url": source_url,
            "source_sha256": sha(source_payload),
            "distribution_url": dist_url,
            "distribution_sha256": sha(dist_payload),
            "first_transfer_label": transfer[0],
        }
    except Exception as exc:
        return {"district_name": district, "status": "failure", "error": f"{type(exc).__name__}: {exc}", "source_url": source_url}


def load_cycle_rows(year: int) -> list[dict[str, str]]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_final_pairs.csv"
    return list(csv.DictReader(path.open(encoding="utf-8")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/irv-original-parcel")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    events = []
    cycle_summaries = []
    for year in CYCLES:
        registry = candidate_registry(year)
        rows = load_cycle_rows(year)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda row: extract_one(row, year, registry, args.cache_dir), rows))
        clean = [row for row in results if row["status"] == "clean-original-parcel"]
        failures = [row for row in results if row["status"] == "failure"]
        events.extend(clean)
        source_counts: dict[str, int] = {}
        for event in clean:
            source_counts[event["source_family"]] = source_counts.get(event["source_family"], 0) + 1
        cycle_summaries.append({
            "year": year,
            "district_rows": len(rows),
            "clean_original_parcel_events": len(clean),
            "no_distribution_link": sum(row["status"] == "no-distribution-link" for row in results),
            "failures": len(failures),
            "registry_surname_fallback_matches": sum(int(row.get("registry_surname_fallback_matches", 0)) for row in clean),
            "source_family_event_counts": dict(sorted(source_counts.items())),
            "failure_details": failures,
        })

    within_family_events = [e for e in events if e["within_source_family_transfer_votes"] > 0]
    payload = {
        "schemaVersion": 2,
        "purpose": "clean first-exclusion/original-parcel Assembly preference evidence for PR #138",
        "guardrails": {
            "uses_2026_forecast_output": False,
            "fits_preference_parameters": False,
            "later_mixed_parcel_exclusions_used": False,
            "official_vec_only": True,
            "candidate_name_fallback": "unique surname within district only; ambiguous surnames fail closed",
        },
        "summary": {
            "clean_original_parcel_events": len(events),
            "within_source_family_transfer_events": len(within_family_events),
            "within_source_family_transfer_votes": sum(e["within_source_family_transfer_votes"] for e in events),
            "registry_surname_fallback_matches": sum(int(e.get("registry_surname_fallback_matches", 0)) for e in events),
        },
        "cycles": cycle_summaries,
        "events": sorted(events, key=lambda e: (e["election_year"], e["district_name"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    for cycle in cycle_summaries:
        print(json.dumps({k: v for k, v in cycle.items() if k != "failure_details"}, sort_keys=True))
    if any(cycle["failures"] for cycle in cycle_summaries):
        print(json.dumps({"failure_details": {str(c["year"]): c["failure_details"] for c in cycle_summaries if c["failures"]}}, sort_keys=True))
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
