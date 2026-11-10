#!/usr/bin/env python3
"""Official VEC October 2026 enrolment capture: strictly read-only review.

This script does NOT update the registered forecast, metadata/sources.json,
model/config, dashboard generated enrolment, poll registry or prospective seals.
It preserves source bytes and prepares a reconciled evidence review for approval.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model/scripts"))
import extract_vec_enrolment as existing  # noqa: E402

LISTING = "https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics"
OCTOBER = re.compile(r"(District|Region) statistics\s*[-–]\s*October 2026", re.I)
MAX_BYTES = 2_500_000
BASELINES = {
    "district": ROOT / "model/data/processed/vec_enrolment_district_2026-09-04.csv",
    "region": ROOT / "model/data/processed/vec_enrolment_region_2026-09-04.csv",
}
EXPECTED = {"district": 88, "region": 8}
HEADER = existing.EXPECTED_COLUMNS
COLUMNS = existing.CSV_COLUMNS


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ListingLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.all_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data):
        self.all_text.append(data)
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            if self.href:
                self.links.append((" ".join(self.parts).strip(), self.href))
            self.href, self.parts = None, []


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("www.vec.vic.gov.au", "vec.vic.gov.au"):
        raise ValueError("Non-VEC, non-HTTPS or third-party enrolment URL rejected")
    if parsed.username or parsed.password or parsed.port is not None:
        raise ValueError("Unexpected URL credentials or port")
    return url


def discover_urls(html: str):
    parser = ListingLinks()
    parser.feed(html)
    if not re.search(r"October\s+2026", " ".join(parser.all_text), re.I):
        raise ValueError("Current official listing does not expose October 2026; cached page rejected")
    result = {}
    for label, href in parser.links:
        match = OCTOBER.search(" ".join(label.split()))
        if match is None:
            continue
        kind = match.group(1).lower()
        if kind in result:
            raise ValueError(f"Duplicate October {kind} link: listing ambiguous")
        url = validate_url(urljoin(LISTING, href))
        if not urlparse(url).path.lower().endswith((".xls", ".xlsx")):
            # VEC content-hashed /-/media/ files can have spreadsheet extensions;
            # refuse a content-like API endpoint without a verified file name.
            raise ValueError(f"October {kind} link lacks .xls/.xlsx file extension: {url}")
        result[kind] = url
    if set(result) != {"district", "region"}:
        raise ValueError(f"Missing official October district/region spreadsheet links; got {sorted(result)}")
    text = " ".join(parser.all_text)
    total = re.search(r"There are\s+([\d, ]+)\s+people on the Victorian electoral roll", text, re.I)
    return result, int(total.group(1).replace(",", "").replace(" ", "")) if total else None


def fetch(url: str) -> tuple[bytes, dict]:
    validate_url(url)
    request = Request(url, headers={"User-Agent": "VictorianElectionResearch/2026 (public VEC enrolment validation)", "Accept": "text/html,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"})
    with urlopen(request, timeout=25) as response:
        final = response.geturl()
        validate_url(final)
        content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("Unexpectedly large official source file")
        status = response.status
        metadata = {
            "url": url, "finalUrl": final, "httpStatus": status,
            "contentType": response.headers.get("Content-Type"),
            "lastModified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "size": len(content), "sha256": sha(content)
        }
    if status != 200 or len(content) < 200:
        raise ValueError(f"Unexpected official source HTTP status/length: {status}, {len(content)}")
    return content, metadata


def xls_data(path: Path, kind: str):
    """Read legacy OLE2/BIFF source; never guess format solely by extension."""
    import xlrd
    data = path.read_bytes()
    if not data.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        raise ValueError("Neither a true XLS nor a ZIP XLSX workbook")
    workbook = xlrd.open_workbook(file_contents=data, on_demand=True)
    sheet = workbook.sheet_by_index(0)

    def get(row, col):
        return sheet.cell_value(row-1, col-1) if row <= sheet.nrows else None

    if str(get(5, 2)).strip().lower() != kind:
        raise ValueError("Unexpected workbook geography type")
    for col_letter, name in HEADER.items():
        col_idx = sum((ord(x) - 64)*26**i for i, x in enumerate(reversed(col_letter)))
        if get(10, col_idx) != name:
            raise ValueError(f"Unexpected XLS header {col_letter}10: {get(10,col_idx)!r}")
    serial = get(7, 2)
    if not isinstance(serial, (int, float)):
        raise ValueError("VEC XLS extraction date is not an Excel serial")
    date = xlrd.xldate_as_datetime(serial, workbook.datemode).date().isoformat()
    rows = []
    for row in range(11, sheet.nrows + 1):
        area = get(row, 1)
        if not isinstance(area, (int,float)) or int(area) != area:
            continue
        name = get(row, 2)
        electors, variance, properties = get(row, 6), get(row, 7), get(row, 9)
        if (not isinstance(name, str) or
            not isinstance(electors,(int,float)) or int(electors) != electors or
            not isinstance(properties,(int,float)) or int(properties) != properties or
            not isinstance(variance,(int,float))):
            raise ValueError(f"XLS incomplete enrolment at row {row}")
        rows.append({
            "Area No": int(area), "geography_name": name.strip(),
            "unnamed_2": "", "unnamed_3": "", "unnamed_4": "",
            "enrolled_electors": int(electors), "Variance to Average (%)": variance,
            "unnamed_7": "", "Property Count": int(properties), "geography_type": kind,
        })
    if len(rows) != EXPECTED[kind] or [r["Area No"] for r in rows] != list(range(1, EXPECTED[kind]+1)):
        raise ValueError(f"XLS {kind} roster count/sequence incomplete: {len(rows)}")
    if len({r["geography_name"] for r in rows}) != EXPECTED[kind]:
        raise ValueError("Duplicate geography in VEC XLS")
    return existing.WorkbookData(path, kind, date, rows)


def read_source(path: Path, kind: str):
    data = path.read_bytes()
    if data.startswith(b"PK\x03\x04"):
        result = existing.read_workbook(path, kind)
        fmt = "xlsx-zip"
    else:
        result = xls_data(path,kind)
        fmt = "xls-biff"
    return result, fmt


def rows_by_name(rows):
    return {r["geography_name"]: int(r["enrolled_electors"]) for r in rows}


def comparison(current, baseline):
    with baseline.open(newline="", encoding="utf8") as f:
        old_rows = list(csv.DictReader(f))
    old, new = rows_by_name(old_rows), rows_by_name(current)
    if set(old) != set(new):
        raise ValueError(f"Geography mismatch: lost={sorted(set(old)-set(new))}, gained={sorted(set(new)-set(old))}")
    deltas = [{"name": name, "old": old[name], "new": new[name],
               "change": new[name] - old[name],
               "changePercent": round(100*(new[name]/old[name]-1),4)}
              for name in sorted(new)]
    return {"baselineSha256": sha(baseline.read_bytes()), "baselineCount": len(old),
            "newCount": len(new), "baselineTotal": sum(old.values()),
            "newTotal": sum(new.values()), "totalChange": sum(new.values())-sum(old.values()),
            "topAbsoluteChanges": sorted(deltas,key=lambda x:-abs(x["change"]))[:12],
            "allChanges": deltas}


def build_review(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    page, meta = fetch(LISTING)
    page_html = page.decode("utf-8",errors="replace")
    (output / "vec-source-listing.html").write_bytes(page)
    links, page_total = discover_urls(page_html)
    sources = {}
    records = {}
    for kind in ("district","region"):
        url = links[kind]
        data, http = fetch(url)
        extension = ".xlsx" if data.startswith(b"PK\x03\x04") else ".xls"
        path = output / f"vec-enrolment-{kind}-october-2026{extension}"
        path.write_bytes(data)
        rows, fmt = read_source(path,kind)
        if len(rows.records) != EXPECTED[kind]:
            raise ValueError(f"Unexpected {kind} row count")
        sources[kind] = {"http": http, "format": fmt, "effectiveDate": rows.effective_date,
                         "sourceName": path.name, "rows": len(rows.records)}
        records[kind] = rows
    dates={rec.effective_date for rec in records.values()}
    if len(dates)!=1:
        raise ValueError(f"District and region extracted on different dates: {dates}")
    effective=dates.pop()
    if effective < "2026-10-01" or effective > "2026-11-11":
        raise ValueError(f"October listing gives unexpected workbook extracted date: {effective}")
    changes={kind: comparison(records[kind].records, BASELINES[kind]) for kind in records}
    if changes["district"]["newTotal"] != changes["region"]["newTotal"]:
        raise ValueError("Official district and region enrolment totals do not reconcile")
    total=changes["district"]["newTotal"]
    if page_total is not None and total != page_total:
        raise ValueError(f"Workbook total {total} does not match VEC page statewide total {page_total}")
    for kind in ("district","region"):
        filename = output / f"vec-enrolment-{kind}-october-2026.review.csv"
        with filename.open("w",newline="",encoding="utf8") as f:
            writer=csv.DictWriter(f,fieldnames=COLUMNS,lineterminator="\n")
            writer.writeheader()
            writer.writerows(records[kind].records)
        sources[kind]["reviewCsv"]={"path":filename.name,"sha256":sha(filename.read_bytes())}
    report={
        "schemaVersion":1, "status":"OFFICIAL_RECONCILED_REVIEW_ONLY_NOT_ADMITTED",
        "sourceAuthority":"Victorian Electoral Commission", "listing":meta,
        "listingMonth":"October 2026", "workbookExtractedDate":effective,
        "retrievedAtUtc":datetime.now(timezone.utc).isoformat(),
        "publishedStatewideTotal":page_total,
        "districtAndRegionTotal":total, "sourceWorkbooks":sources,
        "baselineSeptemberReconciliation":changes,
        "governance":{"automaticPromotion":False,"ownerApprovalRecorded":False,
                      "canonicalForecastInputsChanged":False,"forecastRefreshed":False,
                      "criticalSourceFreshnessGateRestored":False},
        "limitations":"Official page update may be later than original XLS extraction. Original bytes and exact hashes retained in run artifact; no model parameter impact tested."
    }
    (output / "enrolment-review.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":report["status"],"date":effective,
                      "total":total,"districtChange":changes["district"]["totalChange"],
                      "regionChange":changes["region"]["totalChange"]},indent=2),flush=True)
    return report


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    try:
        build_review(args.output)
    except Exception as exc:
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output / "acquisition-failure.json").write_text(json.dumps({
            "status":"SOURCE_CAPTURE_OR_VALIDATION_FAILED_NOT_ADMITTED",
            "errorType":type(exc).__name__,"reason":str(exc),
            "canonicalForecastInputsChanged":False},indent=2)+"\n")
        raise
