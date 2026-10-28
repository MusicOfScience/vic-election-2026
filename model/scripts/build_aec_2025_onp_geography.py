#!/usr/bin/env python3
"""Build a 2025 federal ONP polling-place surface on Victorian Assembly districts.

Shadow research only. Downloads final official AEC 2025 House polling-place
first preferences and polling-place coordinates, then assigns ordinary polling
places to the current 88 Victorian Assembly polygons from Vicmap Admin.

The output is a *relative spatial signal*, not a 2026 vote forecast. Declaration
votes that cannot be located to a physical polling place are excluded from the
seat surface and reported in the audit. No Roy Morgan or 2026 seat polling is
read by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
AEC_RESULTS = "https://results.aec.gov.au/31496/Website/Downloads/HouseStateFirstPrefsByPollingPlaceDownload-31496-VIC.csv"
AEC_PLACES = "https://results.aec.gov.au/31496/Website/Downloads/GeneralPollingPlacesDownload-31496.csv"
VICMAP_QUERY = "https://services-ap1.arcgis.com/P744lA0wf4LlBZ84/arcgis/rest/services/Vicmap_Admin/FeatureServer/15/query"
OUTPUT = ROOT / "model/data/validation/aec_2025_onp_state_district_surface.csv"
AUDIT = ROOT / "metadata/aec-2025-onp-geography-audit.json"


def _get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "vic-election-2026-research/1.0"})
    with urlopen(req, timeout=90) as response:
        return response.read()


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _field(row: dict[str, str], *candidates: str) -> str:
    folded = {key.lower().replace("_", ""): key for key in row}
    for candidate in candidates:
        key = folded.get(candidate.lower().replace("_", ""))
        if key is not None:
            return row[key]
    raise KeyError(f"none of {candidates!r} found in {list(row)}")


def _float(row: dict[str, str], *names: str) -> float:
    return float(_field(row, *names))


def _point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_geometry(x: float, y: float, geometry: dict) -> bool:
    coords = geometry["coordinates"]
    polygons = [coords] if geometry["type"] == "Polygon" else coords
    for polygon in polygons:
        if not polygon or not _point_in_ring(x, y, polygon[0]):
            continue
        if any(_point_in_ring(x, y, hole) for hole in polygon[1:]):
            continue
        return True
    return False


def _district_name(properties: dict) -> str:
    preferred = ("district_name", "districtname", "electorate_name", "electoratename", "name")
    folded = {str(k).lower().replace("_", ""): k for k in properties}
    for candidate in preferred:
        key = folded.get(candidate.replace("_", ""))
        if key is not None and properties[key]:
            return str(properties[key]).strip()
    for key, value in properties.items():
        if "name" in str(key).lower() and value:
            return str(value).strip()
    raise KeyError(f"cannot identify district-name field from {list(properties)}")


def _boundaries() -> tuple[bytes, list[dict]]:
    query = urlencode({
        "where": "1=1", "outFields": "*", "returnGeometry": "true",
        "outSR": "4326", "f": "geojson",
    })
    payload = _get(f"{VICMAP_QUERY}?{query}")
    geo = json.loads(payload)
    features = geo.get("features", [])
    if len(features) != 88:
        raise ValueError(f"expected 88 Assembly polygons, got {len(features)}")
    return payload, features


def _is_onp(row: dict[str, str]) -> bool:
    values = " ".join(str(value) for value in row.values()).upper()
    return "ONE NATION" in values or "PAULINE HANSON" in values or _field(row, "PartyAb", "PartyAbbreviation").upper() in {"ON", "ONP"}


def build() -> tuple[list[dict], dict]:
    results_payload = _get(AEC_RESULTS)
    places_payload = _get(AEC_PLACES)
    boundary_payload, boundaries = _boundaries()
    results = _csv(results_payload)
    places = _csv(places_payload)

    # Polling-place IDs are stable join keys; filter to Victoria before mapping.
    coords: dict[str, tuple[float, float, str]] = {}
    for row in places:
        try:
            state = _field(row, "StateAb", "State")
            if state.upper() != "VIC":
                continue
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            lon = _float(row, "Longitude")
            lat = _float(row, "Latitude")
            name = _field(row, "PollingPlace", "PollingPlaceName")
            if math.isfinite(lon) and math.isfinite(lat):
                coords[pid] = (lon, lat, name)
        except (KeyError, ValueError):
            continue

    assignment: dict[str, str] = {}
    unmatched_places: list[dict] = []
    for pid, (lon, lat, name) in coords.items():
        matches = [feature for feature in boundaries if _point_in_geometry(lon, lat, feature["geometry"])]
        if len(matches) == 1:
            assignment[pid] = _district_name(matches[0]["properties"])
        else:
            unmatched_places.append({"pollingPlaceId": pid, "pollingPlace": name, "longitude": lon, "latitude": lat, "matches": len(matches)})

    totals: dict[str, float] = {}
    onp: dict[str, float] = {}
    used_rows = 0
    unlocated_votes = 0.0
    for row in results:
        try:
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            votes = _float(row, "OrdinaryVotes", "Votes")
        except (KeyError, ValueError):
            continue
        district = assignment.get(pid)
        if district is None:
            unlocated_votes += votes
            continue
        totals[district] = totals.get(district, 0.0) + votes
        if _is_onp(row):
            onp[district] = onp.get(district, 0.0) + votes
        used_rows += 1

    names = sorted({_district_name(feature["properties"]) for feature in boundaries})
    if len(names) != 88:
        raise ValueError("boundary district names are not unique")
    rows = []
    for name in names:
        formal = totals.get(name, 0.0)
        if formal <= 0:
            raise ValueError(f"no located House first-preference votes for {name}")
        votes = onp.get(name, 0.0)
        rows.append({"district_name": name, "located_formal_votes": round(formal), "onp_votes": round(votes), "onp_share": votes / formal})

    weighted_state = sum(row["onp_votes"] for row in rows) / sum(row["located_formal_votes"] for row in rows)
    for row in rows:
        share = max(float(row["onp_share"]), 0.0005)
        row["onp_log_ratio_to_located_state"] = math.log(share / weighted_state)

    audit = {
        "schemaVersion": 1,
        "status": "shadow-only-relative-geography",
        "sourceElection": "2025 Australian federal election",
        "sourceElectionDate": "2025-05-03",
        "targetGeography": "Victorian Assembly STATE_ASSEMBLY_2022 (88 districts)",
        "method": "AEC House ordinary polling-place first preferences spatially assigned by AEC polling-place coordinates to Vicmap Assembly polygons",
        "sources": {
            "aecHousePollingPlaceFirstPreferences": {"url": AEC_RESULTS, "sha256": _sha(results_payload), "status": "final"},
            "aecPollingPlaces": {"url": AEC_PLACES, "sha256": _sha(places_payload)},
            "vicmapAssemblyGeoJSON": {"url": VICMAP_QUERY, "sha256": _sha(boundary_payload), "featureCount": len(boundaries)},
        },
        "districtCount": len(rows),
        "locatedPollingPlaces": len(assignment),
        "unmatchedCoordinatePlaces": unmatched_places,
        "usedResultRows": used_rows,
        "unlocatedResultVotesAcrossCandidateRows": unlocated_votes,
        "locatedStateOnpShare": weighted_state,
        "governance": {
            "forecastLevel": False,
            "royMorganRead": False,
            "statewide2026PollingRead": False,
            "candidateEffectsRead": False,
            "purpose": "relative 2025 spatial challenger only",
        },
        "limitations": [
            "Physical polling-place assignment excludes declaration votes that cannot be geolocated to a home district.",
            "Polling-place location is an ecological approximation: electors can vote outside their exact state district, especially at early voting centres.",
            "Federal House candidate fields can create local candidate effects; this surface must be compared with 2022 and independent mappings before model promotion.",
        ],
    }
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--audit", type=Path, default=AUDIT)
    args = parser.parse_args()
    rows, audit = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"districts": len(rows), "locatedStateOnpShare": audit["locatedStateOnpShare"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
