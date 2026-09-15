#!/usr/bin/env python3
"""Validate and extract VEC enrolment workbooks without mutating model inputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXPECTED_COLUMNS = {
    "A": "Area No",
    "B": "Area Name",
    "F": "Elector Count",
    "G": "Variance to Average (%)",
    "I": "Property Count",
}
EXPECTED_ROWS = {"district": 88, "region": 8}
SOURCE_URLS = {
    "district": "https://www.vec.vic.gov.au/-/media/9a3266f985484f069c25b00618da2deb.xlsx",
    "region": "https://www.vec.vic.gov.au/-/media/019821e1781940c38b1735fb0d6c1f96.xlsx",
}
CSV_COLUMNS = [
    "Area No",
    "geography_name",
    "unnamed_2",
    "unnamed_3",
    "unnamed_4",
    "enrolled_electors",
    "Variance to Average (%)",
    "unnamed_7",
    "Property Count",
    "geography_type",
]


@dataclass(frozen=True)
class WorkbookData:
    path: Path
    area_type: str
    effective_date: str
    records: list[dict[str, object]]


def _cell_column(reference: str) -> str:
    match = re.match(r"[A-Z]+", reference)
    if not match:
        raise ValueError(f"invalid cell reference: {reference}")
    return match.group(0)


def _shared_strings(archive: ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.text or "" for node in item.findall(".//x:t", NS)) for item in root.findall("x:si", NS)]


def _cell_value(cell: ET.Element, strings: list[str]) -> object | None:
    value = cell.find("x:v", NS)
    if value is None or value.text is None:
        return None
    if cell.attrib.get("t") == "s":
        return strings[int(value.text)]
    number = float(value.text)
    return int(number) if number.is_integer() else number


def _read_cells(path: Path) -> dict[str, object]:
    with ZipFile(path) as archive:
        strings = _shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    cells: dict[str, object] = {}
    for cell in sheet.findall(".//x:sheetData/x:row/x:c", NS):
        value = _cell_value(cell, strings)
        if value is not None:
            cells[cell.attrib["r"]] = value
    return cells


def _excel_date(value: object) -> str:
    if not isinstance(value, (int, float)):
        raise ValueError("Date Extracted must be an Excel serial date")
    return (datetime(1899, 12, 30) + timedelta(days=float(value))).date().isoformat()


def read_workbook(path: Path, expected_type: str) -> WorkbookData:
    cells = _read_cells(path)
    area_type = str(cells.get("B5", "")).strip().lower()
    if area_type != expected_type:
        raise ValueError(f"{path.name}: expected {expected_type.title()} workbook, found {area_type or 'missing type'}")
    for column, expected in EXPECTED_COLUMNS.items():
        actual = cells.get(f"{column}10")
        if actual != expected:
            raise ValueError(f"{path.name}: expected {expected!r} in {column}10, found {actual!r}")

    records = []
    for row_number in range(11, 751):
        area_number = cells.get(f"A{row_number}")
        if not isinstance(area_number, int):
            continue
        name = cells.get(f"B{row_number}")
        electors = cells.get(f"F{row_number}")
        variance = cells.get(f"G{row_number}")
        properties = cells.get(f"I{row_number}")
        if not isinstance(name, str) or not isinstance(electors, int) or not isinstance(variance, (int, float)) or not isinstance(properties, int):
            raise ValueError(f"{path.name}: incomplete data row {row_number}")
        records.append({
            "Area No": area_number,
            "geography_name": name.strip(),
            "unnamed_2": "",
            "unnamed_3": "",
            "unnamed_4": "",
            "enrolled_electors": electors,
            "Variance to Average (%)": variance,
            "unnamed_7": "",
            "Property Count": properties,
            "geography_type": expected_type,
        })

    expected_rows = EXPECTED_ROWS[expected_type]
    if len(records) != expected_rows:
        raise ValueError(f"{path.name}: expected {expected_rows} records, found {len(records)}")
    if [record["Area No"] for record in records] != list(range(1, expected_rows + 1)):
        raise ValueError(f"{path.name}: area numbers are not a complete 1-{expected_rows} sequence")
    if len({record["geography_name"] for record in records}) != expected_rows:
        raise ValueError(f"{path.name}: geography names are not unique")
    return WorkbookData(path, expected_type, _excel_date(cells.get("B7")), records)


def _read_baseline(path: Path) -> dict[str, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["geography_name"]: int(row["enrolled_electors"]) for row in csv.DictReader(handle)}


def _write_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bundle(
    district_path: Path,
    region_path: Path,
    output_dir: Path,
    baseline_district_path: Path,
    baseline_region_path: Path,
    report_path: Path,
) -> dict[str, object]:
    district = read_workbook(district_path, "district")
    region = read_workbook(region_path, "region")
    if district.effective_date != region.effective_date:
        raise ValueError("district and region workbooks have different extraction dates")
    district_total = sum(int(record["enrolled_electors"]) for record in district.records)
    region_total = sum(int(record["enrolled_electors"]) for record in region.records)
    if district_total != region_total:
        raise ValueError(f"district total {district_total} does not match region total {region_total}")

    baselines = {
        "district": _read_baseline(baseline_district_path),
        "region": _read_baseline(baseline_region_path),
    }
    current = {
        "district": {str(record["geography_name"]): int(record["enrolled_electors"]) for record in district.records},
        "region": {str(record["geography_name"]): int(record["enrolled_electors"]) for record in region.records},
    }
    for area_type in ("district", "region"):
        if baselines[area_type].keys() != current[area_type].keys():
            missing = sorted(baselines[area_type].keys() - current[area_type].keys())
            added = sorted(current[area_type].keys() - baselines[area_type].keys())
            raise ValueError(f"{area_type} names changed; missing={missing}, added={added}")

    output_dir.mkdir(parents=True, exist_ok=True)
    effective_date = district.effective_date
    outputs = {
        "district": output_dir / f"vec_enrolment_district_{effective_date}.csv",
        "region": output_dir / f"vec_enrolment_region_{effective_date}.csv",
    }
    _write_csv(outputs["district"], district.records)
    _write_csv(outputs["region"], region.records)

    old_total = sum(baselines["district"].values())
    district_changes = {name: current["district"][name] - old for name, old in baselines["district"].items()}
    report = {
        "schemaVersion": 1,
        "validationStatus": "passed",
        "automaticPromotion": False,
        "publisher": "Victorian Electoral Commission",
        "canonicalListingUrl": "https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics",
        "effectiveDate": effective_date,
        "workbooks": {
            area_type: {
                "sourceUrl": SOURCE_URLS[area_type],
                "sha256": _sha256(data.path),
                "rows": len(data.records),
            }
            for area_type, data in (("district", district), ("region", region))
        },
        "baselines": {
            "district": {"path": str(baseline_district_path), "sha256": _sha256(baseline_district_path), "rows": len(baselines["district"])},
            "region": {"path": str(baseline_region_path), "sha256": _sha256(baseline_region_path), "rows": len(baselines["region"])},
        },
        "outputs": {
            area_type: {
                "path": str(path),
                "sha256": _sha256(path),
                "rows": len(data.records),
            }
            for area_type, path, data in (
                ("district", outputs["district"], district),
                ("region", outputs["region"], region),
            )
        },
        "reconciliation": {
            "districtTotal": district_total,
            "regionTotal": region_total,
            "previousDistrictTotal": old_total,
            "electorChange": district_total - old_total,
            "electorChangePercent": round((district_total / old_total - 1) * 100, 4),
            "districtNamesUnchanged": True,
            "regionNamesUnchanged": True,
            "smallestDistrictChange": min(district_changes.items(), key=lambda item: item[1]),
            "largestDistrictChange": max(district_changes.items(), key=lambda item: item[1]),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district-workbook", type=Path, required=True)
    parser.add_argument("--region-workbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-district", type=Path, required=True)
    parser.add_argument("--baseline-region", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = build_bundle(
        args.district_workbook,
        args.region_workbook,
        args.output_dir,
        args.baseline_district,
        args.baseline_region,
        args.report,
    )
    print(json.dumps({"validationStatus": report["validationStatus"], "effectiveDate": report["effectiveDate"], "reconciliation": report["reconciliation"]}, indent=2))


if __name__ == "__main__":
    main()
