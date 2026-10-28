#!/usr/bin/env python3
"""Audit all candidate-level Assembly exclusion parcels on official VEC pages.

Unlike the C1 original-parcel extractor, this records later mixed parcels too.
Those later rows are *not* interpreted as original voter preference by the
excluded candidate's party. They are recorded only as the effective parcel
transferred at that elimination stage, which is potentially relevant to a
candidate-level operational IRV model.

No preference parameter is fitted and no 2026 forecast output is read.
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
    return norm(value).split(",", 1)[0].strip()


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
            req = Request(url, headers={"User-Agent": "vic-election-2026-effective-transfer-audit/1.0"})
            with urlopen(req, timeout=90) as response:
                payload = response.read()
            if not payload:
                raise ValueError(f"empty response: {url}")
            cache.write_bytes(payload)
            return payload
        except Exception as exc:
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


def candidate_registry(year: int) -> dict[tuple[str, str], dict]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_candidate_primaries.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    registry: dict[tuple[str, str], dict] = {}
    for row in rows:
        family = FAMILY_TO_MODEL.get(row["party_family"])
        if family is None:
            raise ValueError(f"{year} {row['district_name']}: unmodelled family {row['party_family']!r}")
        registry[(norm(row["district_name"]), norm(row["candidate_name"]))] = {
            "family": family,
            "party_raw": row.get("party_raw") or "",
            "independent": str(row.get("independent_status", "")).casefold() == "true",
            "registry_name": row["candidate_name"],
        }
    return registry


def resolve_candidate(registry: dict[tuple[str, str], dict], district_key: str, candidate: str) -> tuple[dict, str]:
    exact = registry.get((district_key, norm(candidate)))
    if exact is not None:
        return exact, "exact"
    target = surname(candidate)
    matches = [
        meta for (district, name), meta in registry.items()
        if district == district_key and surname(name) == target
    ]
    if len(matches) == 1:
        return matches[0], "unique-district-surname"
    if not matches:
        raise ValueError(f"candidate missing from governed registry: {candidate!r}")
    raise ValueError(f"candidate surname ambiguous in governed registry: {candidate!r}")


def find_distribution_table(source: str) -> list[list[str]]:
    parser = TableParser(); parser.feed(source)
    for table in parser.tables:
        if len(table) < 3 or not table[0] or table[0][0].strip():
            continue
        labels = [norm(row[0]) for row in table[1:] if row]
        if any("first preference" in x or "first pref" in x for x in labels) and any(x.startswith("transfer of ") for x in labels):
            return table
    raise ValueError("no recognised distribution table")


def parse_transfer_label(label: str) -> tuple[int, str, int]:
    match = re.search(
        r"transfer of\s+([0-9,]+)\s+ballot[- ]papers\s+of\s+(.+?)\s*\(\s*(\d+)(?:st|nd|rd|th)\s+excluded candidate\s*\)",
        label,
        flags=re.I,
    )
    if not match:
        raise ValueError(f"unrecognised exclusion label: {label!r}")
    return integer(match.group(1)), match.group(2).strip(), int(match.group(3))


def extract_district(row: dict[str, str], year: int, registry: dict[tuple[str, str], dict], cache_dir: Path) -> dict:
    district = row["district_name"]
    source_url = row.get("source_url") or row.get("outcome_source_url")
    if not source_url:
        return {"district_name": district, "status": "no-source-url"}
    try:
        source_payload = fetch(source_url, cache_dir / str(year))
        source = source_payload.decode("utf-8", "replace")
        dist_url = distribution_link(source, source_url)
        outcome_url = row.get("outcome_source_url") or ""
        if dist_url is None and "distribution" in outcome_url.casefold():
            dist_url = outcome_url
        if dist_url is None:
            return {"district_name": district, "status": "no-distribution-link"}
        dist_payload = fetch(dist_url, cache_dir / str(year))
        table = find_distribution_table(dist_payload.decode("utf-8", "replace"))
        headers = table[0]
        candidates = headers[1:-1]
        if len(candidates) < 2 or norm(headers[-1]) != "total":
            raise ValueError(f"unexpected distribution header: {headers!r}")
        district_key = norm(district)
        candidate_meta = []
        fallback_matches = 0
        for candidate in candidates:
            meta, method = resolve_candidate(registry, district_key, candidate)
            fallback_matches += int(method != "exact")
            candidate_meta.append({**meta, "display_name": candidate, "match_method": method})

        first = next(r for r in table[1:] if r and ("first preference" in norm(r[0]) or "first pref" in norm(r[0])))
        running = [integer(v) for v in first[1:1 + len(candidates)]]
        events = []
        pending_expected = None
        for table_row in table[2:]:
            if not table_row:
                continue
            label = norm(table_row[0])
            values = [integer(v) for v in table_row[1:1 + len(candidates)]]
            if label.startswith("transfer of "):
                parcel, source_candidate, ordinal = parse_transfer_label(table_row[0])
                source_index = next((i for i, c in enumerate(candidates) if norm(c) == norm(source_candidate)), None)
                if source_index is None:
                    raise ValueError(f"excluded candidate {source_candidate!r} not in header")
                if running[source_index] != parcel:
                    raise ValueError(f"parcel/current total mismatch for {source_candidate}: {parcel} vs {running[source_index]}")
                if values[source_index] != 0 or sum(values) != parcel:
                    raise ValueError(f"transfer row does not reconcile for {source_candidate}")
                continuing = [i for i, value in enumerate(running) if value > 0 and i != source_index]
                if any(values[i] and i not in continuing for i in range(len(values))):
                    raise ValueError(f"transfer sent votes to non-continuing candidate for {source_candidate}")
                source_meta = candidate_meta[source_index]
                destination_rows = []
                family_votes = {p: 0 for p in MODEL_PARTIES}
                family_candidate_count = {p: 0 for p in MODEL_PARTIES}
                for i in continuing:
                    meta = candidate_meta[i]
                    family_votes[meta["family"]] += values[i]
                    family_candidate_count[meta["family"]] += 1
                    destination_rows.append({
                        "candidate": candidates[i],
                        "family": meta["family"],
                        "party_raw": meta["party_raw"],
                        "independent": meta["independent"],
                        "votes": values[i],
                        "pre_transfer_total": running[i],
                    })
                next_running = [running[i] + values[i] for i in range(len(running))]
                next_running[source_index] = 0
                pending_expected = next_running
                events.append({
                    "election_year": year,
                    "election_id": f"vic_la_{year}",
                    "district_id": slug(district),
                    "district_name": district,
                    "elimination_ordinal": ordinal,
                    "is_original_parcel": ordinal == 1,
                    "source_candidate": source_candidate,
                    "source_family": source_meta["family"],
                    "source_party_raw": source_meta["party_raw"],
                    "source_independent": source_meta["independent"],
                    "parcel_votes": parcel,
                    "continuing_candidates": len(continuing),
                    "destination_votes": family_votes,
                    "destination_candidate_count": family_candidate_count,
                    "within_source_family_votes": family_votes[source_meta["family"]],
                    "destinations": destination_rows,
                })
            elif label.startswith("progressive total") or label.startswith("final total"):
                if pending_expected is not None and values != pending_expected:
                    raise ValueError(f"progressive total does not reconcile after exclusion in {district}")
                running = values
                pending_expected = None
        if pending_expected is not None:
            raise ValueError("distribution ended before progressive/final total reconciliation")
        return {
            "district_name": district,
            "status": "ok",
            "events": events,
            "registry_surname_fallback_matches": fallback_matches,
            "distribution_url": dist_url,
            "distribution_sha256": sha(dist_payload),
        }
    except Exception as exc:
        return {"district_name": district, "status": "failure", "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/irv-effective-transfer-audit")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    all_events = []
    cycles = []
    for year in CYCLES:
        path = ROOT / f"model/data/processed/vec_{year}_assembly_final_pairs.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        registry = candidate_registry(year)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(lambda row: extract_district(row, year, registry, args.cache_dir), rows))
        ok = [r for r in results if r["status"] == "ok"]
        failures = [r for r in results if r["status"] == "failure"]
        events = [event for district in ok for event in district["events"]]
        all_events.extend(events)
        source_family_counts = {p: sum(e["source_family"] == p for e in events) for p in MODEL_PARTIES}
        cycles.append({
            "year": year,
            "district_rows": len(rows),
            "distribution_districts": len(ok),
            "no_distribution_link": sum(r["status"] == "no-distribution-link" for r in results),
            "failures": len(failures),
            "exclusion_events": len(events),
            "original_parcel_events": sum(e["is_original_parcel"] for e in events),
            "mixed_parcel_events": sum(not e["is_original_parcel"] for e in events),
            "same_family_transfer_events": sum(e["within_source_family_votes"] > 0 for e in events),
            "source_family_event_counts": source_family_counts,
            "registry_surname_fallback_matches": sum(int(r.get("registry_surname_fallback_matches", 0)) for r in ok),
            "failure_details": failures,
        })

    payload = {
        "schemaVersion": 1,
        "purpose": "candidate-level effective IRV exclusion-parcel audit for PR #138",
        "interpretation": "Later mixed parcels describe operational transfers at elimination; they are not labelled as original voter preference by the excluded candidate's party.",
        "guardrails": {
            "uses_2026_forecast_output": False,
            "fits_preference_parameters": False,
            "official_vec_only": True,
        },
        "summary": {
            "exclusion_events": len(all_events),
            "original_parcel_events": sum(e["is_original_parcel"] for e in all_events),
            "mixed_parcel_events": sum(not e["is_original_parcel"] for e in all_events),
            "same_family_transfer_events": sum(e["within_source_family_votes"] > 0 for e in all_events),
            "source_family_event_counts": {p: sum(e["source_family"] == p for e in all_events) for p in MODEL_PARTIES},
        },
        "cycles": cycles,
        "events": sorted(all_events, key=lambda e: (e["election_year"], e["district_name"], e["elimination_ordinal"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    for cycle in cycles:
        print(json.dumps({k: v for k, v in cycle.items() if k != "failure_details"}, sort_keys=True))
    if any(c["failures"] for c in cycles):
        print(json.dumps({"failure_details": {str(c["year"]): c["failure_details"] for c in cycles if c["failures"]}}, sort_keys=True))
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
