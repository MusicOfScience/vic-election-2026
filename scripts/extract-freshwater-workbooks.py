#!/usr/bin/env python3
"""Extract governed Victorian polling evidence from Freshwater XLSX workbooks.

Uses only the Python standard library. It reads the OOXML package directly,
checks the methodology metadata, and extracts the first current-leadership
primary-vote and Coalition-Labor TPP tables. It never writes model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
OFFICE_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
PRIMARY_QUESTION = "If a Victorian State Election were held today, who would receive your first, or Primary Vote?"
PARTIES = {
    "The Labor Party": "alp",
    "Labor Party": "alp",
    "Liberals & Nationals": "coalition",
    "Liberal & Nationals": "coalition",
    "One Nation": "oneNation",
    "The Greens": "greens",
    "Other": "otherParties",
}


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference).group(0)
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - 64
    return value - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(node.text or "" for node in item.findall(".//m:t", NS)) for item in root.findall("m:si", NS)]


def _sheet_rows(archive: zipfile.ZipFile) -> dict[str, list[list[object]]]:
    shared = _shared_strings(archive)
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("r:Relationship", REL_NS)}
    result: dict[str, list[list[object]]] = {}
    for sheet in workbook.findall(".//m:sheets/m:sheet", NS):
        name = sheet.attrib["name"]
        target = targets[sheet.attrib[OFFICE_REL]].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        root = ET.fromstring(archive.read(target))
        rows: list[list[object]] = []
        for row in root.findall(".//m:sheetData/m:row", NS):
            values: list[object] = []
            for cell in row.findall("m:c", NS):
                index = _column_index(cell.attrib["r"])
                while len(values) <= index:
                    values.append(None)
                cell_type = cell.attrib.get("t")
                raw = cell.findtext("m:v", default="", namespaces=NS)
                if cell_type == "s" and raw:
                    value: object = shared[int(raw)]
                elif cell_type == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//m:t", NS))
                elif raw:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
                else:
                    value = None
                values[index] = value
            rows.append(values)
        result[name] = rows
    return result


def _value(row: list[object], index: int = 0) -> object | None:
    return row[index] if index < len(row) else None


def _percent(value: object) -> float:
    number = float(value)
    return number * 100 if abs(number) <= 1 else number


def _extract_table(rows: list[list[object]], start: int, labels: dict[str, str], limit: int = 15) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in rows[start + 1 : start + limit]:
        label = str(_value(row) or "").strip()
        if label in {"Unweighted n", "Weighted n", "Back to TOC"}:
            break
        if label in labels and _value(row, 1) is not None:
            values[labels[label]] = _percent(_value(row, 1))
    return values


def extract_rows(sheets: dict[str, list[list[object]]]) -> dict:
    methodology = next((rows for name, rows in sheets.items() if "method" in name.lower()), None)
    if methodology is None:
        raise ValueError("methodology sheet missing")
    methodology_text = "\n".join(str(_value(row) or "") for row in methodology)
    fieldwork = re.search(r"Fieldwork dates:\s*(.+)", methodology_text, re.I)
    sample = re.search(r"Sample:\s*([\d,]+)\s+Victorian voters", methodology_text, re.I)
    if not fieldwork or not sample:
        raise ValueError("fieldwork or sample metadata missing")

    primary = None
    tpp = None
    primary_base = None
    tpp_base = None
    for rows in sheets.values():
        for index, row in enumerate(rows):
            heading = str(_value(row) or "").strip()
            if primary is None and heading.startswith(PRIMARY_QUESTION):
                primary = _extract_table(rows, index, PARTIES)
                base_rows = rows[index + 1 : index + 15]
                primary_base = next((int(_value(item, 1)) for item in base_rows if str(_value(item) or "") == "Unweighted n"), None)
            if tpp is None and heading.startswith("TPP (") and "One Nation" not in heading and "Leader Change" not in heading:
                tpp = _extract_table(rows, index, {"Labor Party": "alp", "Liberals & Nationals": "coalition", "Liberal & Nationals": "coalition"})
                base_rows = rows[index + 1 : index + 12]
                tpp_base = next((int(_value(item, 1)) for item in base_rows if str(_value(item) or "") == "Unweighted n"), None)
    if set(primary or {}) != {"alp", "coalition", "oneNation", "greens", "otherParties"}:
        raise ValueError(f"incomplete primary-vote table: {primary}")
    if set(tpp or {}) != {"alp", "coalition"}:
        raise ValueError(f"incomplete Coalition-Labor TPP table: {tpp}")
    if abs(sum(primary.values()) - 100) > 0.02 or abs(sum(tpp.values()) - 100) > 0.02:
        raise ValueError("extracted percentages do not sum to 100")
    return {
        "fieldworkLabel": fieldwork.group(1).strip(),
        "sampleSize": int(sample.group(1).replace(",", "")),
        "primaryVoteExact": {key: round(value, 4) for key, value in primary.items()},
        "primaryVoteRounded": {key: round(value) for key, value in primary.items()},
        "primaryVoteUnweightedBase": primary_base,
        "twoPartyPreferredExact": {key: round(value, 4) for key, value in tpp.items()},
        "twoPartyPreferredRounded": {key: round(value) for key, value in tpp.items()},
        "twoPartyPreferredUnweightedBase": tpp_base,
    }


def extract_workbook(content: bytes) -> dict:
    with zipfile.ZipFile(BytesIO(content)) as archive:
        return extract_rows(_sheet_rows(archive))


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "vic-election-forecast-source-adapter/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def build_report(config: dict) -> dict:
    records = []
    for source in config["workbooks"]:
        content = fetch(source["url"])
        extracted = extract_workbook(content)
        checks = {
            "sampleMatches": extracted["sampleSize"] == source["expectedSampleSize"],
            "primaryRoundedMatches": extracted["primaryVoteRounded"] == source["expectedPrimaryVoteRounded"],
            "twoPartyRoundedMatches": extracted["twoPartyPreferredRounded"] == source["expectedTwoPartyPreferredRounded"],
        }
        records.append({**source, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content), **extracted, "checks": checks, "valid": all(checks.values())})
    return {
        "schemaVersion": 1,
        "mode": "primary-workbook-extraction-review-only",
        "automaticPromotion": False,
        "allValid": all(record["valid"] for record in records),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--config", default=root / "metadata/freshwater-workbooks-2026.json", type=Path)
    parser.add_argument("--output", default=root / "freshwater-primary-report.json", type=Path)
    args = parser.parse_args()
    report = build_report(json.loads(args.config.read_text()))
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Freshwater primary workbooks: {len(report['records'])} parsed; valid={report['allValid']}; automatic promotion disabled.")
    if not report["allValid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
