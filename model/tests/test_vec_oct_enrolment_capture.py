import importlib.util
from pathlib import Path
import csv
import sys

import pytest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT / "scripts/capture-vec-enrolment-oct-2026.py"
spec=importlib.util.spec_from_file_location("vec_oct_capture",SCRIPT)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

A="https://www.vec.vic.gov.au/-/media/abc123.xls"
B="https://www.vec.vic.gov.au/-/media/def456.xlsx"

def html(links=None):
    if links is None:
        links=(
            f'<a href="{A}">District statistics - October 2026 (xls, 91.0 kb)</a>'
            f'<a href="{B}">Region statistics - October 2026 (xlsx, 83.5 kb)</a>'
        )
    return f'<html><h2>October 2026</h2><p>There are 4,725,477 people on the Victorian electoral roll as of 5 November 2026.</p>{links}</html>'

def test_vetted_october_listing_discovers_exact_two_official_links():
    links,total=m.discover_urls(html())
    assert links == {"district":A,"region":B}
    assert total == 4_725_477

def test_october_listing_rejects_cached_july_page():
    with pytest.raises(ValueError,match="cached page"):
        m.discover_urls("<h2>June 2026</h2><a href='/file.xlsx'>District statistics - June 2026</a>")

def test_no_unvetted_secondary_host_can_be_injected():
    with pytest.raises(ValueError,match="Non-VEC"):
        m.discover_urls(html(
            '<a href="https://example.org/a.xls">District statistics - October 2026</a>'
            f'<a href="{B}">Region statistics - October 2026</a>'))

def test_duplicate_or_missing_links_fail_closed():
    with pytest.raises(ValueError,match="Duplicate"):
        m.discover_urls(html(
            f'<a href="{A}">District statistics - October 2026</a>'
            f'<a href="{A}">District statistics - October 2026</a>'
            f'<a href="{B}">Region statistics - October 2026</a>'))
    with pytest.raises(ValueError,match="Missing"):
        m.discover_urls(html(f'<a href="{A}">District statistics - October 2026</a>'))

def test_october_link_needs_explicit_xls_or_xlsx():
    with pytest.raises(ValueError,match="lacks .xls"):
        m.discover_urls(html(
            '<a href="https://www.vec.vic.gov.au/-/media/opaque">District statistics - October 2026</a>'
            f'<a href="{B}">Region statistics - October 2026</a>'))

def test_comparison_rejects_missing_area_and_reports_exact_seat_deltas(tmp_path):
    baseline=tmp_path/"baseline.csv"
    with baseline.open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=["geography_name","enrolled_electors"])
        w.writeheader()
        w.writerow({"geography_name":"Albert Park","enrolled_electors":50000})
        w.writerow({"geography_name":"Kalkallo","enrolled_electors":60000})
    rows=[{"geography_name":"Albert Park","enrolled_electors":50100},
          {"geography_name":"Kalkallo","enrolled_electors":60500}]
    result=m.comparison(rows,baseline)
    assert result["newTotal"]==110600
    assert result["totalChange"]==600
    assert result["topAbsoluteChanges"][0]["name"]=="Kalkallo"
    assert result["topAbsoluteChanges"][0]["change"]==500
    with pytest.raises(ValueError,match="Geography mismatch"):
        m.comparison(rows[:1],baseline)

def test_source_url_rejects_ports_credentials_and_http():
    for url in ("http://www.vec.vic.gov.au/a.xls",
                "https://wrong.vec.vic.gov.au/a.xls",
                "https://user:pass@www.vec.vic.gov.au/a.xls",
                "https://www.vec.vic.gov.au:8443/a.xls"):
        with pytest.raises(ValueError):
            m.validate_url(url)

def test_capture_script_does_not_automatically_change_governed_input_files():
    text=SCRIPT.read_text()
    assert "automaticPromotion" in text
    assert "ownerApprovalRecorded" in text
    assert "canonicalForecastInputsChanged" in text
    assert "model/data/processed/vec_enrolment_district_2026-09-04.csv" in text
    assert "model/data/processed/vec_enrolment_region_2026-09-04.csv" in text
