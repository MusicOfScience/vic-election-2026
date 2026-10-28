#!/usr/bin/env python3
"""Build a 2025 Senate ONP district surface as a robustness check on House geography.

This is validation-only.  It maps final AEC Senate polling-place first
preferences to the same current Victorian Assembly polygons used by the House
challenger, then compares the resulting ONP spatial signal with the 2025 House
surface.  It is not a second independent observation in any likelihood and is
never injected into the forecast.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from build_aec_2025_onp_geography import (
    AEC_PLACES,
    _boundaries,
    _csv,
    _district_name,
    _field,
    _float,
    _geometry_bbox,
    _get,
    _is_onp,
    _point_in_geometry,
)


ROOT = Path(__file__).resolve().parents[2]
MENU = "https://results.aec.gov.au/31496/Website/SenateDivisionDownloadMenu-31496-VIC-Csv.htm"
DOWNLOAD_BASE = "https://results.aec.gov.au/31496/Website/Downloads/"
HOUSE = ROOT / "model/data/validation/aec_2025_onp_state_district_surface.csv"
SENATE_OUTPUT = ROOT / "model/data/validation/aec_2025_onp_senate_state_district_surface.csv"
AUDIT_OUTPUT = ROOT / "metadata/onp-geography-2025-house-senate-robustness.json"


def _key(value: str) -> str:
    return str(value).strip().upper()


def _rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(float)


def _senate_urls() -> list[str]:
    html = _get(MENU).decode("utf-8", errors="replace")
    names = sorted(set(re.findall(r"SenateDivisionFirstPrefsByPollingPlaceDownload-31496-\d+\.csv", html)))
    if len(names) != 38:
        raise ValueError(f"expected 38 Victorian Senate division CSVs, found {len(names)}")
    return [DOWNLOAD_BASE + name for name in names]


def _assignment(result_place_ids: set[str]) -> tuple[dict[str, str], dict]:
    places = _csv(_get(AEC_PLACES))
    _, boundaries, boundary_requests = _boundaries()
    coords: dict[str, tuple[float, float, str]] = {}
    for row in places:
        try:
            state = _field(row, "StateAb", "State", "PremisesStateAb")
            if state.upper() not in {"VIC", "VICTORIA"}:
                continue
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            if pid not in result_place_ids:
                continue
            lon = _float(row, "Longitude")
            lat = _float(row, "Latitude")
            name = _field(row, "PollingPlace", "PollingPlaceName", "PollingPlaceNm")
            if np.isfinite(lon) and np.isfinite(lat):
                coords[pid] = (lon, lat, name)
        except (KeyError, ValueError):
            continue
    prepared = [(feature, _geometry_bbox(feature["geometry"])) for feature in boundaries]
    assigned: dict[str, str] = {}
    unmatched = []
    for pid, (lon, lat, name) in coords.items():
        candidates = [
            feature
            for feature, (xmin, ymin, xmax, ymax) in prepared
            if xmin <= lon <= xmax and ymin <= lat <= ymax
        ]
        matches = [feature for feature in candidates if _point_in_geometry(lon, lat, feature["geometry"])]
        if len(matches) == 1:
            assigned[pid] = _district_name(matches[0]["properties"])
        else:
            unmatched.append({"pollingPlaceId": pid, "pollingPlace": name, "matches": len(matches)})
    return assigned, {
        "coordinatePlaces": len(coords),
        "locatedPlaces": len(assigned),
        "unmatchedPlaces": unmatched,
        "boundaryRequests": boundary_requests,
    }


def build() -> tuple[pd.DataFrame, dict]:
    urls = _senate_urls()
    result_rows: list[dict[str, str]] = []
    for url in urls:
        result_rows.extend(_csv(_get(url)))
    result_ids = set()
    for row in result_rows:
        try:
            result_ids.add(_field(row, "PollingPlaceID", "PollingPlaceId"))
        except KeyError:
            pass
    assigned, assignment_audit = _assignment(result_ids)

    totals: dict[str, float] = {}
    onp: dict[str, float] = {}
    used_rows = 0
    unlocated_votes = 0.0
    for row in result_rows:
        try:
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            votes = _float(row, "Votes", "OrdinaryVotes")
        except (KeyError, ValueError):
            continue
        district = assigned.get(pid)
        if district is None:
            unlocated_votes += votes
            continue
        key = _key(district)
        totals[key] = totals.get(key, 0.0) + votes
        if _is_onp(row):
            onp[key] = onp.get(key, 0.0) + votes
        used_rows += 1

    if len(totals) != 88:
        raise ValueError(f"Senate mapping produced {len(totals)} state districts, expected 88")
    rows = []
    for key in sorted(totals):
        formal = totals[key]
        votes = onp.get(key, 0.0)
        rows.append({
            "district_key": key,
            "located_formal_votes": formal,
            "onp_votes": votes,
            "onp_share": votes / formal,
        })
    senate = pd.DataFrame(rows)
    senate_state = senate.onp_votes.sum() / senate.located_formal_votes.sum()
    senate["senate_log_ratio_to_located_state"] = np.log(np.clip(senate.onp_share, .0005, None) / senate_state)

    house = pd.read_csv(HOUSE)
    house["district_key"] = house.district_name.map(_key)
    merged = house.merge(senate, on="district_key", how="outer", validate="one_to_one", indicator=True)
    if len(merged) != 88 or not merged._merge.eq("both").all():
        bad = merged.loc[merged._merge.ne("both"), ["district_name", "district_key", "_merge"]].to_dict("records")
        raise ValueError(f"House/Senate district mismatch: {bad}")

    x = merged.onp_log_ratio_to_located_state.to_numpy(float)
    y = merged.senate_log_ratio_to_located_state.to_numpy(float)
    x -= x.mean(); y -= y.mean()
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(np.corrcoef(_rank(x), _rank(y))[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    residual = y - (intercept + slope * x)
    merged["house_signal_centered"] = x
    merged["senate_signal_centered"] = y
    merged["senate_minus_house"] = y - x
    merged["fit_residual"] = residual

    def records(column: str, n: int = 20) -> list[dict]:
        frame = merged.reindex(merged[column].abs().sort_values(ascending=False).index).head(n)
        return [{
            "district": row.district_name,
            "houseOnpShare": float(row.onp_share_x),
            "senateOnpShare": float(row.onp_share_y),
            "houseSignalCentered": float(row.house_signal_centered),
            "senateSignalCentered": float(row.senate_signal_centered),
            column: float(row[column]),
        } for _, row in frame.iterrows()]

    senate_out = merged[["district_name", "located_formal_votes_y", "onp_votes_y", "onp_share_y", "senate_log_ratio_to_located_state"]].rename(columns={
        "located_formal_votes_y": "located_formal_votes",
        "onp_votes_y": "onp_votes",
        "onp_share_y": "onp_share",
    })
    audit = {
        "schemaVersion": 1,
        "status": "shadow-robustness-only",
        "source": "final AEC 2025 Senate first preferences by polling place, Victoria",
        "districts": 88,
        "senateDivisionFiles": len(urls),
        "locatedStateOnpShare": float(senate_state),
        "pearsonHouseSenateSignalCorrelation": pearson,
        "spearmanHouseSenateRankCorrelation": spearman,
        "linearFitSenateOnHouse": {"intercept": float(intercept), "slope": float(slope), "rSquared": pearson ** 2},
        "meanAbsoluteCenteredSignalDifference": float(np.mean(np.abs(y - x))),
        "largestHouseSenateDifferences": records("senate_minus_house"),
        "largestFitResiduals": records("fit_residual"),
        "assignment": assignment_audit,
        "usedResultRows": used_rows,
        "unlocatedResultVotesAcrossRows": unlocated_votes,
        "interpretationRule": (
            "House and Senate are overlapping electoral evidence from the same election and are not independent observations. "
            "High spatial agreement reduces concern that House candidate fields alone drive the 2025 challenger; disagreement identifies seats needing candidate/context review."
        ),
        "governance": {"productionInput": False, "forecastWeight": 0, "royMorganRead": False},
    }
    return senate_out, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--surface-output", type=Path, default=SENATE_OUTPUT)
    parser.add_argument("--audit-output", type=Path, default=AUDIT_OUTPUT)
    args = parser.parse_args()
    senate, audit = build()
    args.surface_output.parent.mkdir(parents=True, exist_ok=True)
    senate.to_csv(args.surface_output, index=False)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({
        "districts": audit["districts"],
        "locatedStateOnpShare": audit["locatedStateOnpShare"],
        "pearsonHouseSenate": audit["pearsonHouseSenateSignalCorrelation"],
        "spearmanHouseSenate": audit["spearmanHouseSenateRankCorrelation"],
        "slope": audit["linearFitSenateOnHouse"]["slope"],
    }, indent=2))


if __name__ == "__main__":
    main()
