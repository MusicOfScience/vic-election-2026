#!/usr/bin/env python3
"""Combine same-boundary 2006 family shares with the pre-election 2010 anchor."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


FAMILIES = ("ALP", "LIB_NAT", "GRN", "OTH_IND")
PRIMARY = Path("model/data/processed/vec_2006_assembly_family_primaries.csv")
BASELINE = Path("model/data/validation/historical-replay-2010-assembly-notional-baseline.csv")
MASK = Path("model/data/validation/historical-replay-2010-ballot-mask.csv")
OUT = Path("model/data/validation/historical-replay-2010-local-inputs.csv")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    primary = list(csv.DictReader(PRIMARY.open(encoding="utf-8")))
    baseline = {row["district_id"]: row for row in csv.DictReader(BASELINE.open(encoding="utf-8"))}
    if len(baseline) != 88 or len(primary) != 352:
        raise ValueError("2010 local input requires 88 baseline districts and 352 prior family rows")
    rows = []
    mask_rows = []
    for district_id in sorted(baseline):
        prior = {row["party_family"]: int(row["first_preference_votes"]) for row in primary if row["district_id"] == district_id}
        formal = int(next(row["formal_votes"] for row in primary if row["district_id"] == district_id))
        if set(prior) != set(FAMILIES) or sum(prior.values()) != formal or formal <= 0:
            raise ValueError(f"prior family composition failed for {district_id}")
        shares = {family: prior[family] / formal for family in FAMILIES}
        # The prior-election pages prove family structure, but do not prove the
        # final 2010 nomination list.  Keep that distinction explicit.
        active = ";".join(family for family in FAMILIES if prior[family] > 0)
        mask_rows.append({"cycle_id": "vic_la_2010", "district_id": district_id, "district_name": baseline[district_id]["district_name"], "ballot_active_families": active, "incumbent_party_family": baseline[district_id]["notional_holder_family"], "source_evidence_status": "pending-cutoff-final-nomination-verification", "evidence_available_by": "unknown-pending-verification", "target_outcome_dependency": "false"})
        rows.append({"cycle_id": "vic_la_2010", "district_id": district_id, "district_name": baseline[district_id]["district_name"], "ballot_active_families": active, "incumbent_party_family": baseline[district_id]["notional_holder_family"], "comparison_type": baseline[district_id]["comparison_type"], "notional_margin_pp": baseline[district_id]["notional_margin_pp"], **{f"prior_{family.lower()}_share": f"{shares[family]:.12f}" for family in FAMILIES}, "local_input_status": "prediction-safe-prior-composition-pending-final-ballot-audit", "source_primary_sha256": sha(PRIMARY), "source_baseline_sha256": sha(BASELINE), "target_outcome_dependency": "false"})
    MASK.parent.mkdir(parents=True, exist_ok=True)
    with MASK.open("w", newline="", encoding="utf-8") as handle:
        fields = list(mask_rows[0]); writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(mask_rows)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        fields = list(rows[0]); writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    Path("metadata/historical-replay-2010-local-input-audit.json").write_text(json.dumps({"schemaVersion": 1, "cycleId": "vic_la_2010", "status": "blocked-pending-cutoff-final-ballot-verification", "districtCount": 88, "sameBoundaryPrior": True, "priorFamilyArtefact": str(PRIMARY), "notionalBaseline": str(BASELINE), "ballotMask": str(MASK), "targetOutcomeDependency": False, "forbiddenPredictionInputs": ["model/data/processed/vec_2006_2010_same_boundary_tpp_swing.csv", "model/data/processed/vec_2010_assembly_candidate_primaries.csv", "any 2010 winner/primary/swing artefact"], "demographicChallengerCentralWeight": 0}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": main()
