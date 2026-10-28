#!/usr/bin/env python3
"""Audit the physical-polling-place crosswalk against the repo's 2022 surface.

This is a method-validation test for the Phase B 2025 challenger.  It rebuilds a
2022 ONP district surface by assigning each AEC polling place to the Victorian
Assembly district containing the *physical voting-centre coordinate*, then
compares that result with the existing 2022 `allocated_ballots` ecological
surface already used by the forecast.

If the point-location method cannot reproduce the existing 2022 surface, it is
not methodologically matched and must not be promoted as a 2025 replacement.
No 2026 polling, Morgan seat polling, candidate effects or election outcomes are
read by this script.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_aec_2025_onp_geography import (
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
AEC_2022_RESULTS = "https://results.aec.gov.au/27966/website/Downloads/HouseStateFirstPrefsByPollingPlaceDownload-27966-VIC.csv"
AEC_2022_PLACES = "https://results.aec.gov.au/27966/website/Downloads/GeneralPollingPlacesDownload-27966.csv"
EXISTING = ROOT / "model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz"
OUTPUT = ROOT / "metadata/aec-2022-point-crosswalk-audit.json"


def _key(value: str) -> str:
    return str(value).strip().upper()


def _rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(float)


def _existing_surface() -> pd.DataFrame:
    frame = pd.read_csv(EXISTING, compression="gzip")
    frame = frame[frame.party_id.ne("INFORMAL")].copy()
    totals = frame.groupby("district_name", as_index=False).allocated_ballots.sum().rename(columns={"allocated_ballots": "existing_formal"})
    onp = (
        frame[frame.party_id.eq("ON")]
        .groupby("district_name", as_index=False)
        .allocated_ballots.sum()
        .rename(columns={"allocated_ballots": "existing_onp"})
    )
    out = totals.merge(onp, on="district_name", how="left").fillna({"existing_onp": 0.0})
    out["existing_share"] = out.existing_onp / out.existing_formal
    out["district_key"] = out.district_name.map(_key)
    state = float(out.existing_share.mean())
    out["existing_signal"] = np.log(np.clip(out.existing_share, .004, None) / max(state, .004))
    return out


def _point_surface() -> tuple[pd.DataFrame, dict]:
    results_payload = _get(AEC_2022_RESULTS)
    places_payload = _get(AEC_2022_PLACES)
    _, boundaries, _ = _boundaries()
    results = _csv(results_payload)
    places = _csv(places_payload)

    result_ids: set[str] = set()
    for row in results:
        try:
            result_ids.add(_field(row, "PollingPlaceID", "PollingPlaceId"))
        except KeyError:
            pass

    coords: dict[str, tuple[float, float, str]] = {}
    for row in places:
        try:
            state = _field(row, "StateAb", "State", "PremisesStateAb")
            if state.upper() not in {"VIC", "VICTORIA"}:
                continue
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            if pid not in result_ids:
                continue
            lon = _float(row, "Longitude")
            lat = _float(row, "Latitude")
            name = _field(row, "PollingPlace", "PollingPlaceName", "PollingPlaceNm")
            if np.isfinite(lon) and np.isfinite(lat):
                coords[pid] = (lon, lat, name)
        except (KeyError, ValueError):
            continue

    prepared = [(feature, _geometry_bbox(feature["geometry"])) for feature in boundaries]
    assignment: dict[str, str] = {}
    unmatched = []
    for pid, (lon, lat, name) in coords.items():
        candidates = [
            feature
            for feature, (xmin, ymin, xmax, ymax) in prepared
            if xmin <= lon <= xmax and ymin <= lat <= ymax
        ]
        matches = [feature for feature in candidates if _point_in_geometry(lon, lat, feature["geometry"])]
        if len(matches) == 1:
            assignment[pid] = _district_name(matches[0]["properties"])
        else:
            unmatched.append({"pollingPlaceId": pid, "pollingPlace": name, "matches": len(matches)})

    totals: dict[str, float] = {}
    onp: dict[str, float] = {}
    unlocated_candidate_votes = 0.0
    for row in results:
        try:
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            votes = _float(row, "OrdinaryVotes", "Votes")
        except (KeyError, ValueError):
            continue
        district = assignment.get(pid)
        if district is None:
            unlocated_candidate_votes += votes
            continue
        key = _key(district)
        totals[key] = totals.get(key, 0.0) + votes
        if _is_onp(row):
            onp[key] = onp.get(key, 0.0) + votes

    names = {_key(_district_name(feature["properties"])): _district_name(feature["properties"]) for feature in boundaries}
    rows = []
    for key, name in names.items():
        formal = totals.get(key, 0.0)
        if formal <= 0:
            raise ValueError(f"no located 2022 formal vote for {name}")
        votes = onp.get(key, 0.0)
        rows.append({
            "district_key": key,
            "point_district_name": name,
            "point_formal": formal,
            "point_onp": votes,
            "point_share": votes / formal,
        })
    point = pd.DataFrame(rows)
    state = float(point.point_share.mean())
    point["point_signal"] = np.log(np.clip(point.point_share, .004, None) / max(state, .004))
    return point, {
        "resultPollingPlaceIds": len(result_ids),
        "coordinatePlacesUsed": len(coords),
        "locatedPlaces": len(assignment),
        "unmatchedPlaces": unmatched,
        "unlocatedCandidateVotes": unlocated_candidate_votes,
    }


def build() -> dict:
    existing = _existing_surface()
    point, point_audit = _point_surface()
    merged = existing.merge(point, on="district_key", how="outer", indicator=True, validate="one_to_one")
    if len(merged) != 88 or not merged._merge.eq("both").all():
        bad = merged.loc[merged._merge.ne("both"), ["district_name", "point_district_name", "district_key", "_merge"]].to_dict("records")
        raise ValueError(f"2022 point/existing surface district mismatch: {bad}")

    x = merged.existing_signal.to_numpy(float)
    y = merged.point_signal.to_numpy(float)
    x -= x.mean(); y -= y.mean()
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(np.corrcoef(_rank(x), _rank(y))[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    merged["existing_signal_centered"] = x
    merged["point_signal_centered"] = y
    merged["point_minus_existing"] = y - x
    merged["fit_residual"] = y - fitted

    def records(column: str, n: int = 20) -> list[dict]:
        frame = merged.reindex(merged[column].abs().sort_values(ascending=False).index).head(n)
        return [{
            "district": row.district_name,
            "existingShare": float(row.existing_share),
            "pointShare": float(row.point_share),
            "existingSignalCentered": float(row.existing_signal_centered),
            "pointSignalCentered": float(row.point_signal_centered),
            column: float(row[column]),
        } for _, row in frame.iterrows()]

    return {
        "schemaVersion": 1,
        "status": "shadow-method-audit",
        "question": "Does physical polling-place assignment reproduce the existing 2022 allocated-ballot ecological surface?",
        "districts": 88,
        "pearsonSignalCorrelation": pearson,
        "spearmanRankCorrelation": spearman,
        "linearFitPointOnExisting": {
            "intercept": float(intercept),
            "slope": float(slope),
            "rSquared": pearson ** 2,
        },
        "meanAbsoluteCenteredSignalDifference": float(np.mean(np.abs(y - x))),
        "largestDifferences": records("point_minus_existing"),
        "largestFitResiduals": records("fit_residual"),
        "pointAssignmentAudit": point_audit,
        "interpretationRule": (
            "A materially imperfect reconstruction means the 2025 physical-point surface is not methodologically matched "
            "to the production AEC-2022 allocated-ballot surface. This audit is a diagnostic, not a model-selection target."
        ),
        "governance": {
            "productionInput": False,
            "2026PollingRead": False,
            "royMorganRead": False,
            "purpose": "crosswalk-method validation only",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "districts": report["districts"],
        "pearson": report["pearsonSignalCorrelation"],
        "spearman": report["spearmanRankCorrelation"],
        "slope": report["linearFitPointOnExisting"]["slope"],
        "rSquared": report["linearFitPointOnExisting"]["rSquared"],
        "meanAbsoluteDifference": report["meanAbsoluteCenteredSignalDifference"],
    }, indent=2))


if __name__ == "__main__":
    main()
