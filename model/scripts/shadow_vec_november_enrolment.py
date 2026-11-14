#!/usr/bin/env python3
"""Read-only paired model sensitivity using official, validated 5 Nov VEC enrolment.

DO NOT alter the frozen October 31 model, poll inputs, sealed prediction,
admission metadata or historical validation. October VEC XLS bytes are retrieved
and reconciled by the separate audit; this script only reads their review CSVs.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "model/src"))
import vicforecast.forecast_2026 as forecast  # noqa: E402

SOURCE_SHA = {
    "district": "bd0cb3ceee05b9abbb2f507b0a0cb522e6c589a55e5a453cda600ef710420fb1",
    "region": "50f9d64690fe98b47cd0f6425aa40c8fe92f04f4b6453d7c884aea5bb40f7c8d",
}
CSV_SHA = {
    "district": "aea0784a3a18a85d57e2e42b265289aa7feaa9187e0a6ad3d7af56e10aac1e7d",
    "region": "c778a069dd0a171073a33c179e4c6cba98a7fab5e90e9ca5d16db998ac452f21",
}
SEPTEMBER = {
    "district": "model/data/processed/vec_enrolment_district_2026-09-04.csv",
    "region": "model/data/processed/vec_enrolment_region_2026-09-04.csv",
}
EXPECTED_SEPTEMBER_SHA = {
    "district": "d553eaa6a071794300ba83db551836f4b8f06d36b8084db97a28903ef3f8ea44",
    "region": "0c8b32460eba5078d05add48ebd17a9794c24dc77e471918e0299435223f986a",
}
EXPECTED_MEANS = {
    "ALP": 34.4074, "LIB_NAT": 35.7782, "ONP": 15.3608,
    "GRN": 2.4430, "OTH_IND": 0.0106,
}


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def inspect_official_review(root: Path, review_dir: Path):
    report = json.loads((review_dir / "enrolment-review.json").read_text())
    if (report["status"] != "OFFICIAL_RECONCILED_REVIEW_ONLY_NOT_ADMITTED"
        or report["workbookExtractedDate"] != "2026-11-05"
        or report["districtAndRegionTotal"] != 4_725_477
        or report["publishedStatewideTotal"] != 4_725_477
        or report["governance"]["automaticPromotion"] is not False
        or report["governance"]["canonicalForecastInputsChanged"] is not False):
        raise ValueError("VEC evidence vintage or provenance changed")
    replacement = {}
    evidence = {}
    for geography, count in (("district", 88), ("region", 8)):
        entry = report["sourceWorkbooks"][geography]
        if (entry["http"]["sha256"] != SOURCE_SHA[geography]
            or entry["rows"] != count
            or entry["effectiveDate"] != "2026-11-05"):
            raise ValueError("VEC official workbook does not match pre-acquisition receipt: " + geography)
        source_file = review_dir / entry["sourceName"]
        if digest(source_file.read_bytes()) != SOURCE_SHA[geography]:
            raise ValueError("Raw VEC workbook differs from source receipt")
        candidate = (review_dir / f"vec-enrolment-{geography}-october-2026.review.csv").read_bytes()
        if digest(candidate) != CSV_SHA[geography]:
            raise ValueError("Source-derived enrolment CSV checksum differs from validated artifact")
        baseline = (root / SEPTEMBER[geography]).read_bytes()
        if digest(baseline) != EXPECTED_SEPTEMBER_SHA[geography]:
            raise ValueError("Approved 4 September source bytes have drifted")
        frame = pd.read_csv(BytesIO(candidate))
        if len(frame) != count or frame.geography_name.nunique() != count:
            raise ValueError("Incomplete VEC geography universe: " + geography)
        existing = pd.read_csv(BytesIO(baseline))
        if set(frame.geography_name) != set(existing.geography_name):
            raise ValueError("VEC district/region identity mismatch")
        if (frame.enrolled_electors <= 0).any() or frame.enrolled_electors.isna().any():
            raise ValueError("Invalid new VEC enrolment counts")
        replacement[geography] = candidate
        evidence[geography] = {
            "rawWorkbookSha256": SOURCE_SHA[geography],
            "reviewCsvSha256": CSV_SHA[geography],
            "acceptedSeptemberSha256": EXPECTED_SEPTEMBER_SHA[geography],
            "rows": count,
            "previousTotal": int(existing.enrolled_electors.sum()),
            "newTotal": int(frame.enrolled_electors.sum()),
        }
    if replacement and sum(pd.read_csv(BytesIO(replacement["district"])).enrolled_electors) != 4_725_477:
        raise ValueError("District total changed")
    return replacement, evidence


@contextmanager
def review_enrolment_only(replacements: dict[str, bytes]):
    original = pd.read_csv
    paths = {Path(SEPTEMBER[k]).name: contents for k, contents in replacements.items()}
    substitutions = []

    def source_reader(path, *args, **kwargs):
        name = Path(path).name if isinstance(path, (str, Path)) else None
        if name in paths:
            substitutions.append(name)
            return original(BytesIO(paths[name]), *args, **kwargs)
        return original(path, *args, **kwargs)

    # Only two precisely named existing source CSVs can be replaced, in memory.
    with patch.object(forecast.pd, "read_csv", side_effect=source_reader):
        yield substitutions
    if sorted(substitutions) != sorted(paths):
        raise ValueError("Original model did not consume both expected VEC inputs")


def run_frozen(root: Path, *, simulations: int = 5000, seed: int = 20260826):
    return forecast.run_experimental_forecast(root / "model", simulations=simulations, seed=seed)


def chamber_summary(result):
    frame = result.chamber.set_index("party")
    if len(frame) != 5:
        raise ValueError("Not five party families")
    return {
        "means": {p: float(frame.loc[p,"mean"]) for p in forecast.PARTIES},
        "majority": {p: float(frame.loc[p, "majority_probability"]) for p in ("ALP","LIB_NAT")},
        "hung": float(frame.hung_probability.iloc[0]),
    }


def audit_delta(old, new):
    old_chamber, new_chamber = chamber_summary(old), chamber_summary(new)
    district_before = old.districts.set_index("district_name")
    district_after = new.districts.set_index("district_name")
    if (len(district_before) != 88 or len(district_after) != 88
        or set(district_before.index) != set(district_after.index)):
        raise ValueError("Changed Assembly district universe")
    rows = []
    for seat in sorted(district_before.index):
        a,b = district_before.loc[seat],district_after.loc[seat]
        winner_delta={p:float(b[f"win_{p.lower()}"]-a[f"win_{p.lower()}"]) for p in forecast.PARTIES}
        if abs(sum(winner_delta.values()))>1e-8:
            raise ValueError("District probabilities not normalised: " + seat)
        rows.append({
            "district":seat,
            "oldModalFamily":str(a.favoured_party),
            "newModalFamily":str(b.favoured_party),
            "modalChanged":str(a.favoured_party)!=str(b.favoured_party),
            "deltaWinnerFrequencies":winner_delta,
            "largestAbsoluteWinFrequencyDelta":max(abs(x) for x in winner_delta.values()),
            "oldEnrolment":int(a.enrolled_electors) if "enrolled_electors" in a else None,
            "newEnrolment":int(b.enrolled_electors) if "enrolled_electors" in b else None,
        })
    reg_a,reg_b=old.council_regions.set_index("region_name"),new.council_regions.set_index("region_name")
    if len(reg_a)!=8 or len(reg_b)!=8 or set(reg_a.index)!=set(reg_b.index):
        raise ValueError("Council region universe changed")
    council=[]
    for name in sorted(reg_a.index):
        a,b=reg_a.loc[name],reg_b.loc[name]
        council.append({"region":name,"deltaMeanSeats":{p:float(b[f"mean_{p.lower()}"]-a[f"mean_{p.lower()}"]) for p in forecast.PARTIES}})
    rows.sort(key=lambda d:(-d["largestAbsoluteWinFrequencyDelta"],d["district"]))
    return {
      "baseline":old_chamber,"reviewOnly":new_chamber,
      "deltaExpectedSeats":{p:new_chamber["means"][p]-old_chamber["means"][p] for p in forecast.PARTIES},
      "deltaHungFrequency":new_chamber["hung"]-old_chamber["hung"],
      "districtsWithAnyFivePointShift":sum(x["largestAbsoluteWinFrequencyDelta"]>=.05 for x in rows),
      "modalWinnerChanges":[x for x in rows if x["modalChanged"]],
      "maxDistrictWinFrequencyShift":rows[0]["largestAbsoluteWinFrequencyDelta"],
      "allDistrictDeltas":rows,"councilRegionDeltas":council,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--review-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    arguments=parser.parse_args()
    if arguments.output.resolve().is_relative_to((REPO/"model/data").resolve()) or \
       arguments.output.resolve().is_relative_to((REPO/"metadata").resolve()):
        raise ValueError("Cannot overwrite canonical forecast or admission metadata")
    config=yaml.safe_load((REPO/"model/config/experimental_forecast.yml").read_text())
    canonical=json.loads((REPO/"model/data/processed/experimental_forecast_2026.json").read_text())
    if (str(config["as_of"])!="2026-10-31" or canonical["as_of"]!="2026-10-31"
        or canonical["simulations"]!=5000 or canonical["seed"]!=20260826
        or canonical["production_compatible"] is not False):
        raise ValueError("Reference model changed: new experiment protocol needed")

    sources,evidence=inspect_official_review(REPO,arguments.review_dir)
    reference=run_frozen(REPO)
    baseline=chamber_summary(reference)
    for party, expected in EXPECTED_MEANS.items():
        if abs(baseline["means"][party]-expected)>1e-8:
            raise ValueError(f"Frozen reference no longer matches published canonical {party} seat mean")
    with review_enrolment_only(sources) as consumed:
        test=run_frozen(REPO)
    result=audit_delta(reference,test)
    output={
        "schemaVersion":1,"status":"REVIEW_ONLY_NOT_ADMITTED",
        "computedAtUtc":datetime.now(timezone.utc).isoformat(),
        "experimentalForecastAsOf":"2026-10-31",
        "newEnrolmentExtractedDate":"2026-11-05",
        "sameSeed":20260826,"simulationsPerCase":5000,
        "vintage":"All polls/coefficients/config/seed frozen at October 31",
        "sourceEvidence":evidence,
        "actualSubstitutedInputs":sorted(consumed),
        "method":"Exact same original forecast engine twice, 5000 draws each, with only the two explicitly sourced VEC enrolment CSV files replaced in memory for one run.",
        "interpretation":"Not a new dated 5 Nov forecast. A controlled 31 Oct reweighting sensitivity; not evidence of forecast improvement or approved input promotion.",
        "findings":result,
        "governance":{"ownerApproved":False,"canonicalInputsModified":False,"forecastRefreshed":False,
                      "criticalFreshnessGateChanged":False,"historicalBacktestChanged":False},
    }
    arguments.output.parent.mkdir(parents=True,exist_ok=True)
    arguments.output.write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps({
        "status":output["status"],
        "deltaMeanSeats":result["deltaExpectedSeats"],
        "deltaHungProbability":result["deltaHungFrequency"],
        "districtsOverFivePointChange":result["districtsWithAnyFivePointShift"],
        "modalWinnerChanges":result["modalWinnerChanges"],
        "topDistrictDeltas":result["allDistrictDeltas"][:8],
        "councilRegionDeltas":result["councilRegionDeltas"]
    }),flush=True)

if __name__=="__main__":
    main()
