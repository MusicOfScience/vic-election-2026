#!/usr/bin/env python3
"""Admit the 2010 ballot mask from the fixed-fact candidate slate.

The slate is a structured extraction of candidate district/party facts from
Appendix 15 of the official VEC report.  This script never reads result,
winner, preference, or vote fields and only propagates ballot availability.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SLATE = ROOT / "model/data/validation/historical-replay-2010-fixed-fact-candidate-slate.csv"
OLD_MASK = ROOT / "model/data/validation/historical-replay-2010-ballot-mask.csv"
MASK = OLD_MASK
LOCAL = ROOT / "model/data/validation/historical-replay-2010-local-inputs.csv"

FAMILIES = ("ALP", "LIB_NAT", "GRN", "OTH_IND")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    slate = list(csv.DictReader(SLATE.open(encoding="utf-8")))
    if len(slate) != 502 or any(row["target_outcome_dependency"].lower() != "false" for row in slate):
        raise ValueError("fixed-fact candidate slate is not the governed 502-row source")
    districts = {}
    for row in slate:
        districts.setdefault(row["district_id"], {"district_name": row["district_name"], "families": set()})["families"].add(row["party_family"])
    if len(districts) != 88:
        raise ValueError("fixed-fact candidate slate must cover all 88 districts")
    old = {row["district_id"]: row for row in csv.DictReader(OLD_MASK.open(encoding="utf-8"))}
    rows = []
    for district_id in sorted(districts):
        if district_id not in old:
            raise ValueError(f"district missing from incumbent baseline: {district_id}")
        families = districts[district_id]["families"]
        if not {"ALP", "GRN"}.issubset(families):
            raise ValueError(f"required ALP/GRN ballot family missing: {district_id}")
        active = [family for family in FAMILIES if family in families]
        rows.append({
            "cycle_id": "vic_la_2010",
            "district_id": district_id,
            "district_name": old[district_id]["district_name"],
            "ballot_active_families": ";".join(active),
            "incumbent_party_family": old[district_id]["incumbent_party_family"],
            "source_evidence_status": "fixed-fact-reconstructed-from-official-vec-candidate-slate",
            "evidence_available_by": "2010-11-25",
            "target_outcome_dependency": "false",
        })
    with MASK.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    # Propagate only ballot fields into the already-frozen local vectors.
    local_rows = list(csv.DictReader(LOCAL.open(encoding="utf-8")))
    by_id = {row["district_id"]: row for row in rows}
    for row in local_rows:
        row["ballot_active_families"] = by_id[row["district_id"]]["ballot_active_families"]
        row["local_input_status"] = "prediction-safe-prior-composition-final-ballot-availability"
    with LOCAL.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(local_rows[0]))
        writer.writeheader()
        writer.writerows(local_rows)
    active_oth = sum("OTH_IND" in set(row["ballot_active_families"].split(";")) for row in rows)
    audit = {
        "schemaVersion": 2,
        "cycleId": "vic_la_2010",
        "status": "pass-fixed-fact-reconstruction",
        "districtCount": len(rows),
        "candidateCount": len(slate),
        "candidateSlate": str(SLATE.relative_to(ROOT)),
        "candidateSlateSha256": sha(SLATE),
        "ballotMask": str(MASK.relative_to(ROOT)),
        "ballotMaskSha256": sha(MASK),
        "localInput": str(LOCAL.relative_to(ROOT)),
        "localInputChangeReason": "final cutoff-safe ballot availability only",
        "othIndActiveDistricts": active_oth,
        "othIndInactiveDistricts": len(rows) - active_oth,
        "activeFamilies": list(FAMILIES),
        "oneNation": "verified-unavailable",
        "targetOutcomeDependency": False,
        "targetOutcomeFieldsRead": False,
        "reconstruction": {
            "policy": "metadata/historical-fixed-fact-reconstruction-policy.json",
            "sourceUrl": "https://www.vec.vic.gov.au/-/media/08680c0035b34af4b6ea2074edc763a4.pdf",
            "sourceSha256": "be2dbabd5735ff7128fa9ac5ab3e05e99d41c3d7a4502d33959b7c3464da7567",
            "sourceSection": "Appendix 15: List of Candidates (PDF pages 137-145)",
            "sourcePublicationTiming": "post-election reconstruction source; not used for availability timing",
            "factEffectiveBy": "2010-11-12",
            "availabilityEvidenceDate": "2010-11-25",
        },
        "previousProvisionalMask": {
            "path": str(MASK.relative_to(ROOT)),
            "sha256": "c1cb04195670b52c3fa4d7f5765bcfdd85df981674d1b6ffaec8fe1486a1a516",
            "status": "superseded-provisional-history",
        },
    }
    (ROOT / "metadata/historical-replay-2010-ballot-availability-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ballotMaskSha256": sha(MASK), "localInputSha256": sha(LOCAL), "othIndActiveDistricts": active_oth}, indent=2))


if __name__ == "__main__":
    main()
