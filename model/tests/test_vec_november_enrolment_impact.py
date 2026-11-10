"""Synthetic non-mutation and delta arithmetic tests for the VEC reweighting shadow."""
from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("vec_nov_impact",ROOT/"model/scripts/shadow_vec_november_enrolment.py")
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)


def test_memory_patch_only_intercepts_two_precise_paths():
    baseline=pd.read_csv
    sources={
        "district":b"geography_name,enrolled_electors\nKalkallo,70346\n",
        "region":b"geography_name,enrolled_electors\nWestern Metropolitan,616247\n"
    }
    # Model uses both explicit September file paths, but no other CSV should be replaced.
    with module.review_enrolment_only(sources) as consumed:
        district=pd.read_csv(ROOT/module.SEPTEMBER["district"])
        region=pd.read_csv(ROOT/module.SEPTEMBER["region"])
        other=pd.read_csv(BytesIO(b"a,b\n2,3\n"))
        assert district.enrolled_electors.iloc[0]==70346
        assert region.enrolled_electors.iloc[0]==616247
        assert other.b.iloc[0]==3
    assert sorted(consumed)==sorted(Path(p).name for p in module.SEPTEMBER.values())
    assert pd.read_csv is baseline


def test_memory_patch_refuses_unconsumed_sources():
    with pytest.raises(ValueError,match="did not consume"):
        with module.review_enrolment_only({"district":b"a\n1\n","region":b"a\n2\n"}):
            pass


def sample_result(preferred="ALP",onp_delta=0):
    d=[]
    for i in range(88):
        alpv=.6-onp_delta
        onpv=.2+onp_delta
        data={"district_name":f"District {i}","favoured_party":preferred}
        for party in module.forecast.PARTIES:
            data[f"win_{party.lower()}"]={"ALP":alpv,"LIB_NAT":.2,"ONP":onpv,"GRN":0,"OTH_IND":0}[party]
        d.append(data)
    chamber=[]
    for party in module.forecast.PARTIES:
        chamber.append({"party":party,"mean":{"ALP":35,"LIB_NAT":36,"ONP":15,"GRN":2,"OTH_IND":0}[party],
                        "majority_probability":0.1 if party=="ALP" else 0.2 if party=="LIB_NAT" else 0,
                        "hung_probability":.7})
    council=[]
    for r in range(8):
        record={"region_name":f"Region {r}"}
        for party in module.forecast.PARTIES:
            record[f"mean_{party.lower()}"]=1.0 if party=="ALP" else .5
        council.append(record)
    return SimpleNamespace(districts=pd.DataFrame(d),chamber=pd.DataFrame(chamber),
                           council_regions=pd.DataFrame(council))


def test_paired_comparison_finds_88_district_changes_without_changing_party_totals():
    old=sample_result(onp_delta=0)
    new=sample_result(onp_delta=.1)
    value=module.audit_delta(old,new)
    assert value["districtsWithAnyFivePointShift"]==88
    assert len(value["allDistrictDeltas"])==88
    assert value["modalWinnerChanges"]==[]
    assert len(value["councilRegionDeltas"])==8
    assert np.isclose(value["maxDistrictWinFrequencyShift"],.1)
    assert value["deltaExpectedSeats"]["ALP"]==0


def test_mismatched_district_universe_is_fatal():
    old=sample_result()
    new=sample_result()
    new.districts=new.districts.iloc[:87]
    with pytest.raises(ValueError,match="district universe"):
        module.audit_delta(old,new)


def test_expected_workbook_and_csv_hashes_fixed():
    assert module.SOURCE_SHA["district"]=="bd0cb3ceee05b9abbb2f507b0a0cb522e6c589a55e5a453cda600ef710420fb1"
    assert module.CSV_SHA["region"]=="c778a069dd0a171073a33c179e4c6cba98a7fab5e90e9ca5d16db998ac452f21"
    assert sorted(module.SEPTEMBER)==["district","region"]
