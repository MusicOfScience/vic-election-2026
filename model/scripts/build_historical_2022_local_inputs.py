"""Build the leakage-safe 2022 local-pattern input from pre-cutoff surfaces.

This deliberately produces relative local composition only.  It never reads
Victorian 2022 state-election outcomes or the production target anchors.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARTIES = ("ALP", "LIB_NAT", "GRN", "ONP", "OTH_IND")
SHRINKAGE = 0.62
AEC_DISTRICT = ROOT / "model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz"
VEC_BASELINE = ROOT / "model/data/processed/vec_2018_estimated_2022_boundary_2cp.csv"
FAMILY_ROWS = ROOT / "model/data/processed/vec_2022_assembly_family_primaries.csv"
MEMBERSHIP = ROOT / "model/data/processed/district_region_membership_2026.csv"
OUTPUT = ROOT / "model/data/validation/historical-replay-2022-local-inputs.csv"
AUDIT = ROOT / "metadata/historical-replay-2022-local-input-audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family(party_id: str) -> str:
    if party_id == "ALP": return "ALP"
    if party_id in {"LP", "NP"}: return "LIB_NAT"
    if party_id == "GRN": return "GRN"
    if party_id == "ON": return "ONP"
    return "OTH_IND"


def build() -> list[dict[str, str]]:
    with gzip.open(AEC_DISTRICT, "rt", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with VEC_BASELINE.open(newline="") as handle:
        baseline = {row["district_id"]: row for row in csv.DictReader(handle)}
    with MEMBERSHIP.open(newline="") as handle:
        region = {row["district_name"]: row["region_name"] for row in csv.DictReader(handle)}
    active: dict[str, set[str]] = {}
    with FAMILY_ROWS.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["district_name"] == "Narracan": continue
            if row["contest_status"] == "contested":
                active.setdefault(row["district_id"], set()).add({"ALP": "ALP", "Coalition": "LIB_NAT", "Greens": "GRN", "One Nation": "ONP", "Other/Independent": "OTH_IND"}[row["party_family"]])
    grouped: dict[tuple[str, str], float] = {}
    names: dict[str, str] = {}
    for row in rows:
        if row["district_name"] == "Narracan" or row["party_id"] == "INFORMAL": continue
        key = (row["district_id"], family(row["party_id"]))
        grouped[key] = grouped.get(key, 0.0) + float(row["allocated_ballots"])
        names[row["district_id"]] = row["district_name"]
    states = {party: 0.0 for party in PARTIES}
    raw: dict[str, dict[str, float]] = {}
    for district in names:
        values = {party: grouped.get((district, party), 0.0) for party in PARTIES}
        total = sum(values.values())
        if total <= 0: raise ValueError(f"empty AEC surface for {district}")
        raw[district] = {party: values[party] / total for party in PARTIES}
        for party in PARTIES: states[party] += raw[district][party]
    state = {party: states[party] / len(raw) for party in PARTIES}
    output: list[dict[str, str]] = []
    for district, values in sorted(raw.items(), key=lambda item: names[item[0]]):
        if district not in baseline: raise ValueError(f"missing VEC baseline for {district}")
        local = {party: math.exp(SHRINKAGE * (math.log(max(values[party], 0.002)) - math.log(max(state[party], 0.002)))) for party in PARTIES}
        norm = sum(local.values())
        local = {party: local[party] / norm for party in PARTIES}
        row = {
            "cycle_id": "vic_la_2022", "district_id": district, "district_name": names[district],
            "region_name": region.get(names[district], ""),
            "vec_2018_alp_tpp": baseline[district]["estimated_2018_alp_tpp_share"],
            "vec_2018_coalition_tpp": baseline[district]["estimated_2018_coalition_tpp_share"],
            "ballot_active_families": ";".join(sorted(active.get(district, set()))),
            "source_cutoff": "2022-11-25", "transformation_version": "historical_replay_v2_aec_relative_pattern_0.62",
        }
        row.update({f"aec_local_{party.lower()}": f"{local[party]:.12f}" for party in PARTIES})
        output.append(row)
    if len(output) != 87 or any(row["district_name"] == "Narracan" for row in output): raise ValueError("2022 local input must contain exactly 87 general-election districts")
    return output


def main() -> None:
    rows = build()
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    AUDIT.write_text(json.dumps({
        "cycleId": "vic_la_2022", "status": "pass-relative-surface-only-multipart-anchor-pending",
        "rows": len(rows), "excludedDistrict": "Narracan", "shrinkage": SHRINKAGE,
        "sources": {
            "aecDistrictSurface": {"path": str(AEC_DISTRICT.relative_to(ROOT)), "sha256": sha256(AEC_DISTRICT), "effectiveDate": "2022-05-21", "role": "relative contextual pattern only"},
            "vecBoundaryTpp": {"path": str(VEC_BASELINE.relative_to(ROOT)), "sha256": sha256(VEC_BASELINE), "effectiveDate": "2022-08-05", "role": "pre-cutoff ALP/Coalition TPP local anchor"},
            "boundaryMembership": {"path": str(MEMBERSHIP.relative_to(ROOT)), "sha256": sha256(MEMBERSHIP), "effectiveDate": "2022-11-01", "role": "2022 geography only"},
        },
        "forbiddenInputs": ["ASSEMBLY_2022_TARGET", "COUNCIL_2022_TARGET", "vec_2022_indicative_candidate_evidence.csv", "2022 Victorian state-election outcomes", "2018-2022 outcome-transition files"],
        "limitations": ["AEC shares are relative spatial signals, not Victorian state-election levels", "statewide poll anchor and ballot-aware simulation remain separate downstream inputs"],
    }, indent=2) + "\n")


if __name__ == "__main__": main()
