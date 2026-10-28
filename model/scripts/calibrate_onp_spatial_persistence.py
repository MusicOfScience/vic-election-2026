#!/usr/bin/env python3
"""Calibrate ONP spatial persistence from historical AEC Senate geography.

This script implements docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_PROTOCOL.md.
It does not import or execute the 2026 Assembly simulator and must not read 2026
seat outputs. All calibration evidence is official AEC election data plus fixed
2026 VEC enrolment weights and current Vicmap Assembly polygons.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from build_aec_2025_onp_geography import (
    _boundaries,
    _district_name,
    _field,
    _float,
    _geometry_bbox,
    _get,
    _is_onp,
    _point_in_geometry,
)


ROOT = Path(__file__).resolve().parents[2]
EVENTS = {
    2016: {"id": 20499, "date": "2016-07-02"},
    2019: {"id": 24310, "date": "2019-05-18"},
    2022: {"id": 27966, "date": "2022-05-21"},
    2025: {"id": 31496, "date": "2025-05-03"},
}
TARGET_DATE = date.fromisoformat("2026-11-28")
TARGET_START = date.fromisoformat("2025-05-03")
EPSILON_SHARE = 0.0005
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 20261028
SURFACE_OUTPUT = ROOT / "model/data/validation/onp-senate-spatial-surfaces-2016-2025.csv"
CALIBRATION_OUTPUT = ROOT / "metadata/onp-spatial-persistence-calibration-2026-10-28.json"
ENROLMENT_PATH = ROOT / "model/data/processed/vec_enrolment_district_2026-09-04.csv"
MEMBERSHIP_PATH = ROOT / "model/data/processed/district_region_membership_2026.csv"


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _parse_aec_csv(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines[:12]):
        folded = line.lower().replace("_", "")
        if "pollingplaceid" in folded and "," in line:
            header_index = index
            break
    if header_index is None:
        raise ValueError("could not identify AEC CSV header containing PollingPlaceID")
    return list(csv.DictReader(io.StringIO("\n".join(lines[header_index:]))))


def _senate_zip_url(event_id: int) -> str:
    return (
        f"https://results.aec.gov.au/{event_id}/Website/External/"
        f"SenateStateFirstPrefsByPollingPlaceDownload-{event_id}-VIC.zip"
    )


def _places_url(event_id: int) -> str:
    return (
        f"https://results.aec.gov.au/{event_id}/Website/Downloads/"
        f"GeneralPollingPlacesDownload-{event_id}.csv"
    )


def _rows_from_zip(payload: bytes) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not names:
            raise ValueError("AEC Senate archive contains no CSV")
        for name in names:
            rows.extend(_parse_aec_csv(archive.read(name)))
    return rows


def _normalise_name(value: str) -> str:
    return str(value).strip().upper()


def _load_weights() -> pd.DataFrame:
    enrolment = pd.read_csv(ENROLMENT_PATH)
    enrolment = enrolment.loc[enrolment.geography_type.eq("district"), ["geography_name", "enrolled_electors"]].copy()
    enrolment["district_key"] = enrolment.geography_name.map(_normalise_name)
    membership = pd.read_csv(MEMBERSHIP_PATH)[["district_name", "region_name"]].copy()
    membership["district_key"] = membership.district_name.map(_normalise_name)
    merged = membership.merge(
        enrolment[["district_key", "enrolled_electors"]],
        on="district_key",
        how="left",
        validate="one_to_one",
    )
    if len(merged) != 88 or merged.enrolled_electors.isna().any():
        raise ValueError("could not build 88-district fixed 2026 weight table")
    merged["weight"] = merged.enrolled_electors / merged.enrolled_electors.sum()
    return merged[["district_name", "district_key", "region_name", "enrolled_electors", "weight"]]


def _assign_places(
    rows: list[dict[str, str]], places_payload: bytes, boundaries: list[dict]
) -> tuple[dict[str, str], dict]:
    result_ids: set[str] = set()
    for row in rows:
        try:
            result_ids.add(_field(row, "PollingPlaceID", "PollingPlaceId"))
        except KeyError:
            continue
    places = _parse_aec_csv(places_payload)
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
            if math.isfinite(lon) and math.isfinite(lat):
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
    return assignment, {
        "resultPlaceIds": len(result_ids),
        "coordinatePlaces": len(coords),
        "locatedPlaces": len(assignment),
        "unmatchedPlaces": unmatched,
    }


def _surface_for_event(year: int, boundaries: list[dict], weights: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    event_id = EVENTS[year]["id"]
    zip_url = _senate_zip_url(event_id)
    places_url = _places_url(event_id)
    senate_payload = _get(zip_url)
    places_payload = _get(places_url)
    rows = _rows_from_zip(senate_payload)
    assignment, assignment_audit = _assign_places(rows, places_payload, boundaries)

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
        key = _normalise_name(district)
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
    frame["raw_log_ratio"] = np.log(np.clip(frame.onp_share, EPSILON_SHARE, None) / state_share)
    centre = float(np.sum(frame.weight * frame.raw_log_ratio))
    frame["delta"] = frame.raw_log_ratio - centre
    frame["year"] = year

    audit = {
        "year": year,
        "eventId": event_id,
        "electionDate": EVENTS[year]["date"],
        "senateUrl": zip_url,
        "senateSha256": _sha(senate_payload),
        "placesUrl": places_url,
        "placesSha256": _sha(places_payload),
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


def _weighted_slope(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    denom = float(np.sum(w * x * x))
    if denom <= 1e-15:
        raise ValueError("degenerate weighted slope denominator")
    return float(np.sum(w * x * y) / denom)


def _weighted_r2(x: np.ndarray, y: np.ndarray, w: np.ndarray, slope: float) -> float:
    residual = y - slope * x
    sse = float(np.sum(w * residual * residual))
    centre = float(np.sum(w * y) / np.sum(w))
    sst = float(np.sum(w * (y - centre) ** 2))
    return 1.0 - sse / sst if sst > 0 else float("nan")


def _bounded_two_component_fit(p: np.ndarray, r: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float, float]:
    """Exact bounded WLS solution for two coefficients constrained to [0,1]."""
    X = np.column_stack([p, r])
    sw = np.sqrt(w)[:, None]
    coef = np.linalg.lstsq(X * sw, y * sw[:, 0], rcond=None)[0]
    candidates: list[tuple[float, float]] = []
    if np.all((coef >= 0.0) & (coef <= 1.0)):
        candidates.append((float(coef[0]), float(coef[1])))
    rr = float(np.sum(w * r * r))
    pp = float(np.sum(w * p * p))
    for a in (0.0, 1.0):
        k = 0.0 if rr <= 1e-15 else float(np.sum(w * r * (y - a * p)) / rr)
        candidates.append((a, float(np.clip(k, 0.0, 1.0))))
    for k in (0.0, 1.0):
        a = 0.0 if pp <= 1e-15 else float(np.sum(w * p * (y - k * r)) / pp)
        candidates.append((float(np.clip(a, 0.0, 1.0)), k))
    best = None
    for a, k in candidates:
        sse = float(np.sum(w * (y - a * p - k * r) ** 2))
        if best is None or sse < best[2]:
            best = (a, k, sse)
    assert best is not None
    return best


def _target_retention(value: float, interval_days: int) -> float:
    target_days = (TARGET_DATE - TARGET_START).days
    if value <= 0.0:
        return 0.0
    return float(math.exp(math.log(value) * target_days / interval_days))


def _fit_triplet(data: pd.DataFrame, years: tuple[int, int, int]) -> dict:
    t0, t1, t2 = years
    x = data[f"delta_{t0}"].to_numpy(float)
    middle = data[f"delta_{t1}"].to_numpy(float)
    y = data[f"delta_{t2}"].to_numpy(float)
    w = data["fit_weight"].to_numpy(float)
    beta01 = _weighted_slope(x, middle, w)
    persistent = beta01 * x
    innovation = middle - persistent
    a, kappa, sse = _bounded_two_component_fit(persistent, innovation, y, w)
    interval_days = (date.fromisoformat(EVENTS[t2]["date"]) - date.fromisoformat(EVENTS[t1]["date"])).days
    return {
        "years": [t0, t1, t2],
        "beta01": beta01,
        "middlePersistentSd": float(np.sqrt(np.average(persistent ** 2, weights=w))),
        "middleInnovationSd": float(np.sqrt(np.average(innovation ** 2, weights=w))),
        "a": a,
        "kappa": kappa,
        "weightedSse": sse,
        "intervalDays": interval_days,
        "aTarget": _target_retention(a, interval_days),
        "kappaTarget": _target_retention(kappa, interval_days),
    }


def _pairwise_diagnostics(wide: pd.DataFrame, years: list[int]) -> list[dict]:
    out = []
    w = wide.weight.to_numpy(float)
    for left, right in zip(years[:-1], years[1:]):
        x = wide[f"delta_{left}"].to_numpy(float)
        y = wide[f"delta_{right}"].to_numpy(float)
        slope = _weighted_slope(x, y, w)
        out.append({
            "from": left,
            "to": right,
            "pearson": float(np.corrcoef(x, y)[0, 1]),
            "spearman": float(pd.Series(x).rank().corr(pd.Series(y).rank())),
            "weightedSlope": slope,
            "weightedR2": _weighted_r2(x, y, w, slope),
        })
    return out


def _bootstrap(wide: pd.DataFrame, draws: int, seed: int) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(seed)
    regions = sorted(wide.region_name.unique())
    rows = []
    for draw in range(draws):
        sampled = rng.choice(regions, size=len(regions), replace=True)
        parts = []
        for index, region in enumerate(sampled):
            part = wide.loc[wide.region_name.eq(region)].copy()
            part["bootstrap_block"] = index
            parts.append(part)
        sample = pd.concat(parts, ignore_index=True)
        sample["fit_weight"] = sample.enrolled_electors.astype(float)
        t1 = _fit_triplet(sample, (2016, 2019, 2022))
        t2 = _fit_triplet(sample, (2019, 2022, 2025))
        rows.append({
            "draw": draw,
            "aTarget": (t1["aTarget"] + t2["aTarget"]) / 2.0,
            "kappaTarget": (t1["kappaTarget"] + t2["kappaTarget"]) / 2.0,
            "aTargetTriplet1": t1["aTarget"],
            "aTargetTriplet2": t2["aTarget"],
            "kappaTargetTriplet1": t1["kappaTarget"],
            "kappaTargetTriplet2": t2["kappaTarget"],
        })
    frame = pd.DataFrame(rows)

    def summary(column: str) -> dict:
        values = frame[column].to_numpy(float)
        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "q05": float(np.quantile(values, 0.05)),
            "q10": float(np.quantile(values, 0.10)),
            "q25": float(np.quantile(values, 0.25)),
            "q75": float(np.quantile(values, 0.75)),
            "q90": float(np.quantile(values, 0.90)),
            "q95": float(np.quantile(values, 0.95)),
        }

    return frame, {column: summary(column) for column in frame.columns if column != "draw"}


def _leave_one_region_out(wide: pd.DataFrame) -> list[dict]:
    rows = []
    for region in sorted(wide.region_name.unique()):
        sample = wide.loc[~wide.region_name.eq(region)].copy()
        sample["fit_weight"] = sample.enrolled_electors.astype(float)
        t1 = _fit_triplet(sample, (2016, 2019, 2022))
        t2 = _fit_triplet(sample, (2019, 2022, 2025))
        rows.append({
            "omittedRegion": region,
            "aTarget": (t1["aTarget"] + t2["aTarget"]) / 2.0,
            "kappaTarget": (t1["kappaTarget"] + t2["kappaTarget"]) / 2.0,
        })
    return rows


def calibrate(draws: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    boundary_payload, boundaries, boundary_requests = _boundaries()
    weights = _load_weights()
    surfaces = []
    audits = []
    for year in sorted(EVENTS):
        surface, audit = _surface_for_event(year, boundaries, weights)
        surfaces.append(surface)
        audits.append(audit)

    long = pd.concat(surfaces, ignore_index=True)
    wide = weights.copy()
    for year, surface in zip(sorted(EVENTS), surfaces):
        delta = surface[["district_key", "delta"]].rename(columns={"delta": f"delta_{year}"})
        wide = wide.merge(delta, on="district_key", how="left", validate="one_to_one")
    if wide.filter(regex=r"^delta_").isna().any().any():
        raise ValueError("missing historical surface after merge")
    wide["fit_weight"] = wide.enrolled_electors.astype(float)

    triplets = [
        _fit_triplet(wide, (2016, 2019, 2022)),
        _fit_triplet(wide, (2019, 2022, 2025)),
    ]
    point = {
        "aTarget": float(np.mean([row["aTarget"] for row in triplets])),
        "kappaTarget": float(np.mean([row["kappaTarget"] for row in triplets])),
    }
    bootstrap, bootstrap_summary = _bootstrap(wide, draws, seed)

    unweighted = wide.copy()
    unweighted["fit_weight"] = 1.0
    unweighted_triplets = [
        _fit_triplet(unweighted, (2016, 2019, 2022)),
        _fit_triplet(unweighted, (2019, 2022, 2025)),
    ]

    report = {
        "schemaVersion": 1,
        "status": "frozen-pre-2026-seat-run",
        "protocol": "docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_PROTOCOL.md",
        "primaryEvidence": "AEC Senate first preferences by physical polling place, Victoria, 2016/2019/2022/2025",
        "targetHorizon": {
            "from": TARGET_START.isoformat(),
            "to": TARGET_DATE.isoformat(),
            "days": (TARGET_DATE - TARGET_START).days,
        },
        "fixedWeights": "VEC district enrolment 2026-09-04",
        "boundarySource": "Vicmap Admin current Assembly polygons",
        "boundarySha256": _sha(boundary_payload),
        "boundaryRequests": boundary_requests,
        "events": audits,
        "pairwiseDiagnostics": _pairwise_diagnostics(wide, sorted(EVENTS)),
        "tripletPointFits": triplets,
        "pooledPointEstimate": point,
        "bootstrap": {
            "draws": draws,
            "seed": seed,
            "block": "eight Victorian Legislative Council regions, sampled with replacement",
            "jointEmpiricalDistribution": True,
            "summary": bootstrap_summary,
            "drawsSha256": hashlib.sha256(bootstrap.to_csv(index=False).encode()).hexdigest(),
        },
        "leaveOneRegionOut": _leave_one_region_out(wide),
        "unweightedDiagnosticTriplets": unweighted_triplets,
        "governance": {
            "productionInput": False,
            "assembly2026SimulatorExecuted": False,
            "assembly2026OutputsRead": False,
            "royMorganRead": False,
            "campaignSeatClaimsRead": False,
            "analystSeatCallsRead": False,
        },
        "interpretation": (
            "This artefact freezes the external-data persistence calibration before any new 2026 Assembly run. "
            "The empirical joint bootstrap distribution of aTarget and kappaTarget is the allowed input to a later shadow simulation; "
            "it is not itself a production promotion."
        ),
    }
    return long, report, bootstrap


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    parser.add_argument("--surface-output", type=Path, default=SURFACE_OUTPUT)
    parser.add_argument("--calibration-output", type=Path, default=CALIBRATION_OUTPUT)
    parser.add_argument("--bootstrap-output", type=Path, default=ROOT / "model/data/validation/onp-spatial-persistence-bootstrap.csv")
    args = parser.parse_args()
    surfaces, report, bootstrap = calibrate(args.draws, args.seed)
    args.surface_output.parent.mkdir(parents=True, exist_ok=True)
    surfaces.to_csv(args.surface_output, index=False)
    args.calibration_output.parent.mkdir(parents=True, exist_ok=True)
    args.calibration_output.write_text(json.dumps(report, indent=2) + "\n")
    args.bootstrap_output.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.to_csv(args.bootstrap_output, index=False)
    print(json.dumps({
        "status": report["status"],
        "targetDays": report["targetHorizon"]["days"],
        "pooledPointEstimate": report["pooledPointEstimate"],
        "bootstrapSummary": {
            "aTarget": report["bootstrap"]["summary"]["aTarget"],
            "kappaTarget": report["bootstrap"]["summary"]["kappaTarget"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
