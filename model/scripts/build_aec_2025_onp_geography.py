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
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
AEC_RESULTS = "https://results.aec.gov.au/31496/Website/Downloads/HouseStateFirstPrefsByPollingPlaceDownload-31496-VIC.csv"
AEC_PLACES = "https://results.aec.gov.au/31496/Website/Downloads/GeneralPollingPlacesDownload-31496.csv"
VICMAP_QUERY = "https://services-ap1.arcgis.com/P744lA0wf4LlBZ84/arcgis/rest/services/Vicmap_Admin/FeatureServer/15/query"
OUTPUT = ROOT / "model/data/validation/aec_2025_onp_state_district_surface.csv"
AUDIT = ROOT / "metadata/aec-2025-onp-geography-audit.json"


def _get(url: str, *, attempts: int = 4) -> bytes:
    req = Request(url, headers={"User-Agent": "vic-election-2026-research/1.0"})
    for attempt in range(attempts):
        try:
            with urlopen(req, timeout=90) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                raise
        except URLError:
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable retry state")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv(payload: bytes) -> list[dict[str, str]]:
    """Parse AEC downloads that may include a one-line metadata preamble."""
    text = payload.decode("utf-8-sig")
    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines[:10]):
        folded = line.lower().replace("_", "")
        if "pollingplaceid" in folded and "," in line:
            header_index = index
            break
    if header_index is None:
        raise ValueError("could not identify AEC CSV header containing PollingPlaceID")
    return list(csv.DictReader(io.StringIO("\n".join(lines[header_index:]))))


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


def _iter_points(coords):
    if (
        isinstance(coords, (list, tuple))
        and len(coords) >= 2
        and isinstance(coords[0], (int, float))
        and isinstance(coords[1], (int, float))
    ):
        yield float(coords[0]), float(coords[1])
        return
    for child in coords:
        yield from _iter_points(child)


def _geometry_bbox(geometry: dict) -> tuple[float, float, float, float]:
    points = list(_iter_points(geometry["coordinates"]))
    if not points:
        raise ValueError("empty boundary geometry")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def _district_name(properties: dict) -> str:
    preferred = (
        "district_name", "districtname", "electorate_name", "electoratename",
        "state_district", "statedistrict", "name",
    )
    folded = {str(k).lower().replace("_", ""): k for k in properties}
    for candidate in preferred:
        key = folded.get(candidate.replace("_", ""))
        if key is not None and properties[key]:
            return str(properties[key]).strip()
    for key, value in properties.items():
        key_text = str(key).lower()
        if ("district" in key_text or "electorate" in key_text) and "name" in key_text and value:
            return str(value).strip()
    raise KeyError(f"cannot identify district-name field from {list(properties)}")


def _boundaries() -> tuple[bytes, list[dict], int]:
    """Fetch Vicmap in small pages so the public ArcGIS service does not time out."""
    page_size = 5
    offset = 0
    features: list[dict] = []
    payloads: list[bytes] = []
    while True:
        query = urlencode({
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "orderByFields": "OBJECTID",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        })
        payload = _get(f"{VICMAP_QUERY}?{query}")
        payloads.append(payload)
        geo = json.loads(payload)
        page = geo.get("features", [])
        if not page:
            break
        features.extend(page)
        offset += len(page)
        if len(page) < page_size:
            break
        if offset > 200:
            raise ValueError("Vicmap pagination exceeded defensive limit")
    if len(features) != 88:
        raise ValueError(f"expected 88 Assembly polygons, got {len(features)}")
    combined = b"\n".join(payloads)
    return combined, features, len(payloads)


def _is_onp(row: dict[str, str]) -> bool:
    values = " ".join(str(value) for value in row.values()).upper()
    if "ONE NATION" in values or "PAULINE HANSON" in values:
        return True
    try:
        return _field(row, "PartyAb", "PartyAbbreviation").upper() in {"ON", "ONP"}
    except KeyError:
        return False


def build() -> tuple[list[dict], dict]:
    results_payload = _get(AEC_RESULTS)
    places_payload = _get(AEC_PLACES)
    boundary_payload, boundaries, boundary_requests = _boundaries()
    results = _csv(results_payload)
    places = _csv(places_payload)

    result_place_ids: set[str] = set()
    for row in results:
        try:
            result_place_ids.add(_field(row, "PollingPlaceID", "PollingPlaceId"))
        except KeyError:
            continue

    # Polling-place IDs are stable join keys; filter to Victoria and to IDs
    # actually present in the VIC House result before doing spatial work.
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
            if math.isfinite(lon) and math.isfinite(lat):
                coords[pid] = (lon, lat, name)
        except (KeyError, ValueError):
            continue

    prepared = [(feature, _geometry_bbox(feature["geometry"])) for feature in boundaries]
    assignment: dict[str, str] = {}
    unmatched_places: list[dict] = []
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
            unmatched_places.append({
                "pollingPlaceId": pid,
                "pollingPlace": name,
                "longitude": lon,
                "latitude": lat,
                "bboxCandidates": len(candidates),
                "matches": len(matches),
            })

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
        rows.append({
            "district_name": name,
            "located_formal_votes": round(formal),
            "onp_votes": round(votes),
            "onp_share": votes / formal,
        })

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
            "aecHousePollingPlaceFirstPreferences": {
                "url": AEC_RESULTS,
                "sha256": _sha(results_payload),
                "status": "final",
            },
            "aecPollingPlaces": {"url": AEC_PLACES, "sha256": _sha(places_payload)},
            "vicmapAssemblyGeoJSON": {
                "url": VICMAP_QUERY,
                "sha256CombinedPagedResponses": _sha(boundary_payload),
                "featureCount": len(boundaries),
                "requestCount": boundary_requests,
            },
        },
        "districtCount": len(rows),
        "resultPollingPlaceIds": len(result_place_ids),
        "coordinatePollingPlacesInVictoriaUsedForJoin": len(coords),
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
        writer.writeheader()
        writer.writerows(rows)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({
        "districts": len(rows),
        "locatedStateOnpShare": audit["locatedStateOnpShare"],
        "locatedPollingPlaces": audit["locatedPollingPlaces"],
        "unmatchedCoordinatePlaces": len(audit["unmatchedCoordinatePlaces"]),
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
