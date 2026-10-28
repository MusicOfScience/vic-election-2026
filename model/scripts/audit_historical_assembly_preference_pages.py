#!/usr/bin/env python3
"""Audit official VEC Assembly preference-distribution page structure across 2010–2022.

This is a discovery/audit step for PR #138. It does not estimate preference
parameters and does not read any 2026 forecast output. The goal is to establish
which historical district pages expose count-by-count distribution evidence and
whether their HTML schemas are sufficiently regular for a governed extractor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CYCLES = (2010, 2014, 2018, 2022)


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


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch(url: str, cache: Path) -> bytes:
    key = hashlib.sha256(url.encode()).hexdigest()[:20]
    path = cache / f"{key}.html"
    if path.exists():
        return path.read_bytes()
    cache.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "vic-election-2026-preference-audit/1.0"})
    with urlopen(req, timeout=90) as response:
        payload = response.read()
    if not payload:
        raise ValueError(f"empty response: {url}")
    path.write_bytes(payload)
    return payload


def distribution_link(source: str, base_url: str) -> str | None:
    for pattern in (
        r'href=["\']([^"\']*distribution[^"\']*district\.html)["\']',
        r'href=["\']([^"\']*distribution[^"\']*\.html)["\']',
    ):
        match = re.search(pattern, source, flags=re.I)
        if match:
            return urljoin(base_url, match.group(1))
    return None


def classify_label(value: str) -> str:
    text = norm(value)
    if not text:
        return "blank"
    if ("first" in text or "1st" in text) and "pref" in text:
        return "first-preference"
    if "final total" in text:
        return "final-total"
    if "total" in text:
        return "total"
    if "transfer" in text:
        return "transfer"
    if "count" in text:
        return "count"
    if re.fullmatch(r"\d+", text):
        return "number"
    return "other"


def audit_one(row: dict[str, str], year: int, cache: Path) -> dict:
    district = row["district_name"]
    source_url = row.get("source_url") or row.get("outcome_source_url")
    if not source_url:
        return {"district": district, "status": "failure", "stage": "source-url", "error": "missing source URL"}
    try:
        source_payload = fetch(source_url, cache / str(year))
        source = source_payload.decode("utf-8", "replace")
        link = distribution_link(source, source_url)
        outcome_url = row.get("outcome_source_url") or ""
        if link is None and "distribution" in outcome_url.casefold():
            link = outcome_url
        if link is None:
            return {
                "district": district,
                "source_url": source_url,
                "source_sha256": sha(source_payload),
                "distribution_url": None,
                "status": "no-distribution-link",
            }
        dist_payload = fetch(link, cache / str(year))
        parser = TableParser()
        parser.feed(dist_payload.decode("utf-8", "replace"))
        candidates = []
        for table_index, table in enumerate(parser.tables):
            if len(table) < 2:
                continue
            width = max(len(r) for r in table)
            first = table[0]
            first_cell = first[0] if first else ""
            labels = [r[0] if r else "" for r in table[1:]]
            classes = [classify_label(x) for x in labels]
            score = int((not first_cell.strip()) and width >= 3) + int("final-total" in classes) + int(len(table) >= 4)
            if score >= 2:
                candidates.append({
                    "table_index": table_index,
                    "width": width,
                    "rows": len(table),
                    "header_cells": first,
                    "row_labels": labels,
                    "row_label_classes": classes,
                    "signature": f"w{width}:rows{len(table)}:first={classify_label(first_cell)}:labels={','.join(classes)}",
                })
        return {
            "district": district,
            "source_url": source_url,
            "source_sha256": sha(source_payload),
            "distribution_url": link,
            "distribution_sha256": sha(dist_payload),
            "status": "distribution-fetched",
            "tables_total": len(parser.tables),
            "candidate_distribution_tables": candidates,
        }
    except Exception as exc:
        return {"district": district, "status": "failure", "stage": "fetch-or-parse", "error": f"{type(exc).__name__}: {exc}"}


def audit_cycle(year: int, cache: Path, workers: int) -> tuple[list[dict], dict]:
    final_path = ROOT / f"model/data/processed/vec_{year}_assembly_final_pairs.csv"
    rows = list(csv.DictReader(final_path.open(encoding="utf-8")))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        district_rows = list(pool.map(lambda row: audit_one(row, year, cache), rows))
    district_rows.sort(key=lambda row: row["district"])

    template_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    for row in district_rows:
        for table in row.get("candidate_distribution_tables", []):
            template_counts[table["signature"]] += 1
            label_counts.update(table["row_label_classes"])
    failures = [r for r in district_rows if r.get("status") == "failure"]
    summary = {
        "year": year,
        "district_rows": len(rows),
        "distribution_fetched": sum(r.get("status") == "distribution-fetched" for r in district_rows),
        "no_distribution_link": sum(r.get("status") == "no-distribution-link" for r in district_rows),
        "failures": len(failures),
        "districts_with_candidate_distribution_table": sum(bool(r.get("candidate_distribution_tables")) for r in district_rows),
        "template_counts": dict(template_counts.most_common()),
        "row_label_class_counts": dict(label_counts),
        "failure_details": failures,
    }
    return district_rows, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/irv-preference-audit")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    all_rows: dict[str, list[dict]] = {}
    summaries = []
    for year in CYCLES:
        rows, summary = audit_cycle(year, args.cache_dir, args.workers)
        all_rows[str(year)] = rows
        summaries.append(summary)
        print(json.dumps(summary, sort_keys=True))

    payload = {
        "schemaVersion": 1,
        "purpose": "historical Assembly preference-distribution schema audit for PR #138",
        "guardrails": {
            "reads_2026_forecast_output": False,
            "fits_preference_parameters": False,
            "uses_only_official_vec_historical_result_pages": True,
        },
        "cycles": summaries,
        "districts": all_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
