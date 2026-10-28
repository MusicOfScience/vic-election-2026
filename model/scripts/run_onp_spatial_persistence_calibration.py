#!/usr/bin/env python3
"""Run preregistered ONP persistence calibration using durable AEC division CSVs.

Older AEC state-level ZIP endpoints can return 404 to automated clients even
when linked from archived tally-room pages. This acquisition adapter discovers
and downloads the official per-division Senate polling-place CSVs instead, then
hands the identical district surfaces to the preregistered estimator in
calibrate_onp_spatial_persistence.py.
"""
from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

import numpy as np

import calibrate_onp_spatial_persistence as calibration
from build_aec_2025_onp_geography import _field, _float, _is_onp


def _division_rows(event_id: int) -> tuple[list[dict[str, str]], dict]:
    menu = f"https://results.aec.gov.au/{event_id}/Website/SenateDivisionDownloadMenu-{event_id}-VIC-Csv.htm"
    base = f"https://results.aec.gov.au/{event_id}/Website/Downloads/"
    html_payload = calibration._get(menu)
    html = html_payload.decode("utf-8", errors="replace")
    pattern = rf"SenateDivisionFirstPrefsByPollingPlaceDownload-{event_id}-\d+\.csv"
    names = sorted(set(re.findall(pattern, html)))
    if len(names) < 35:
        raise ValueError(f"event {event_id}: expected at least 35 Victorian division CSVs, found {len(names)}")

    def fetch(name: str) -> tuple[str, bytes]:
        return name, calibration._get(base + name)

    with ThreadPoolExecutor(max_workers=8) as pool:
        fetched = list(pool.map(fetch, names))

    rows: list[dict[str, str]] = []
    digest = hashlib.sha256()
    for name, payload in sorted(fetched):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        rows.extend(calibration._parse_aec_csv(payload))
    return rows, {
        "menuUrl": menu,
        "menuSha256": hashlib.sha256(html_payload).hexdigest(),
        "divisionFileCount": len(names),
        "divisionPayloadSetSha256": digest.hexdigest(),
        "downloadBase": base,
    }


def _surface_for_event(year: int, boundaries: list[dict], weights):
    event_id = calibration.EVENTS[year]["id"]
    places_url = calibration._places_url(event_id)
    rows, source_audit = _division_rows(event_id)
    places_payload = calibration._get(places_url)
    assignment, assignment_audit = calibration._assign_places(rows, places_payload, boundaries)

    totals: dict[str, float] = {}
    onp: dict[str, float] = {}
    unlocated_votes = 0.0
    used_rows = 0
    for row in rows:
        try:
            pid = _field(row, "PollingPlaceID", "PollingPlaceId")
            votes = _float(row, "Votes", "OrdinaryVotes")
        except (KeyError, ValueError):
            continue
        district = assignment.get(pid)
        if district is None:
            unlocated_votes += votes
            continue
        key = calibration._normalise_name(district)
        totals[key] = totals.get(key, 0.0) + votes
        if _is_onp(row):
            onp[key] = onp.get(key, 0.0) + votes
        used_rows += 1

    frame = weights.copy()
    frame["located_formal_votes"] = frame.district_key.map(totals).fillna(0.0)
    frame["onp_votes"] = frame.district_key.map(onp).fillna(0.0)
    if frame.located_formal_votes.le(0).any():
        missing = frame.loc[frame.located_formal_votes.le(0), "district_name"].tolist()
        raise ValueError(f"{year} mapping has no located formal vote for districts: {missing}")
    frame["onp_share"] = frame.onp_votes / frame.located_formal_votes
    state_share = float(frame.onp_votes.sum() / frame.located_formal_votes.sum())
    if state_share <= 0:
        raise ValueError(f"{year}: ONP was not detected in Senate polling-place rows")
    frame["raw_log_ratio"] = np.log(np.clip(frame.onp_share, calibration.EPSILON_SHARE, None) / state_share)
    centre = float(np.sum(frame.weight * frame.raw_log_ratio))
    frame["delta"] = frame.raw_log_ratio - centre
    frame["year"] = year

    audit = {
        "year": year,
        "eventId": event_id,
        "electionDate": calibration.EVENTS[year]["date"],
        "senateAcquisition": source_audit,
        "placesUrl": places_url,
        "placesSha256": calibration._sha(places_payload),
        "rowCount": len(rows),
        "districtCount": int(len(frame)),
        "locatedStateOnpShare": state_share,
        "locatedFormalVotes": float(frame.located_formal_votes.sum()),
        "locatedOnpVotes": float(frame.onp_votes.sum()),
        "usedRows": used_rows,
        "unlocatedVotesAcrossRows": unlocated_votes,
        "assignment": assignment_audit,
    }
    return frame, audit


def main() -> None:
    calibration._surface_for_event = _surface_for_event
    calibration.main()


if __name__ == "__main__":
    main()
