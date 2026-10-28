#!/usr/bin/env python3
"""Score frozen candidate-resolved preference-concentration selections on 2018/2022.

Gate B for PR #142. The selected concentrations must already be frozen by SHA-256.
No 2026 forecast output is read or generated.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "model/src"))

from score_candidate_resolved_irv_historical import (  # noqa: E402
    PREFERENCE_PRIOR,
    _count_irv,
    aggregate,
    count_r1,
    district_records,
    init_counts,
    load_candidate_states,
    load_exact_pair_signatures,
    load_outcomes,
    load_primaries,
    sha256,
)

DEFAULT_PREREG = ROOT / "metadata/candidate-resolution-preference-uncertainty-preregistration-2026-10-29.json"
DEFAULT_QOTH_FREEZE = ROOT / "metadata/candidate-resolution-irv-qoth-freeze-2026-10-29.json"
DEFAULT_R1_PREREG = ROOT / "metadata/candidate-resolution-irv-preregistration-2026-10-29.json"
TARGETS = (2018, 2022)


def simulate_r0(year: int, simulations: int, seed: int) -> tuple[dict, list[dict]]:
    primaries = load_primaries(year)
    outcomes = load_outcomes(year)
    ids = sorted(set(primaries) & set(outcomes))
    counts = init_counts(ids)
    rng = np.random.default_rng(seed + year)
    for _ in range(simulations):
        pref = np.vstack([rng.dirichlet(np.maximum(row * 72.0, .02)) for row in PREFERENCE_PRIOR])
        for did in ids:
            winner, pair = _count_irv(primaries[did]["primary"], pref)
            counts["winner"][did][winner] += 1
            counts["pair"][did][tuple(sorted(pair))] += 1
    records = district_records(counts, ids, outcomes, {}, simulations, include_exact=False)
    return aggregate(records), records


def simulate_r1(
    year: int,
    concentration: float,
    allocation: str,
    q_draws: np.ndarray,
    simulations: int,
    seed: int,
) -> tuple[dict, list[dict]]:
    family_primaries = load_primaries(year)
    outcomes = load_outcomes(year)
    candidate_states = load_candidate_states(year, family_primaries)
    exact_observed = load_exact_pair_signatures(year, outcomes)
    ids = sorted(set(family_primaries) & set(outcomes) & set(candidate_states))
    if len(q_draws) != simulations:
        raise ValueError(f"{year}: expected {simulations} q_oth draws, got {len(q_draws)}")
    counts = init_counts(ids)
    rng = np.random.default_rng(seed + year)
    for simulation in range(simulations):
        pref = np.vstack([
            rng.dirichlet(np.maximum(row * concentration, .02))
            for row in PREFERENCE_PRIOR
        ])
        q_oth = float(q_draws[simulation])
        any_oth = False
        for did in ids:
            state = candidate_states[did]
            winner, pair, exact_pair, oth_steps = count_r1(
                state["primary"], state["node_families"], state["node_labels"],
                pref, q_oth, allocation,
            )
            counts["winner"][did][winner] += 1
            counts["pair"][did][pair] += 1
            counts["exact_pair"][did][exact_pair] += 1
            counts["oth_to_oth_steps"] += oth_steps
            any_oth = any_oth or oth_steps > 0
        counts["simulations_with_oth_to_oth"] += int(any_oth)
    records = district_records(counts, ids, outcomes, exact_observed, simulations, include_exact=True)
    return aggregate(records), records


def pooled(records: dict[int, list[dict]]) -> dict:
    rows: list[dict] = []
    for year in TARGETS:
        rows.extend(records[year])
    return aggregate(rows)


def per_target_catastrophic(u1: dict[int, dict], r1: dict[int, dict], limit: float) -> dict:
    detail = {}
    any_fail = False
    for year in TARGETS:
        winner_delta = float(u1[year]["winnerMeanLogLoss"] - r1[year]["winnerMeanLogLoss"])
        pair_delta = float(u1[year]["pairMeanLogLoss"] - r1[year]["pairMeanLogLoss"])
        fail = winner_delta > limit or pair_delta > limit
        detail[str(year)] = {
            "winnerLogLossChangeVsR1_72": winner_delta,
            "pairLogLossChangeVsR1_72": pair_delta,
            "catastrophicReversal": fail,
        }
        any_fail = any_fail or fail
    return {"targets": detail, "anyCatastrophicReversal": any_fail}


def research_checks(u1: dict, r1: dict, r0: dict, target_check: dict, gate: dict) -> dict:
    winner_improvement = float(r1["winnerMeanLogLoss"] - u1["winnerMeanLogLoss"])
    pair_advantage = float(r0["pairMeanLogLoss"] - u1["pairMeanLogLoss"])
    pair_brier_change = float(u1["pairMeanBrier"] - r1["pairMeanBrier"])
    winner_brier_change = float(u1["winnerMeanBrier"] - r1["winnerMeanBrier"])
    pair_accuracy_drop_pp = 100.0 * float(r1["pairModalAccuracy"] - u1["pairModalAccuracy"])
    checks = {
        "winnerLogLossImprovementVsR1_72": winner_improvement,
        "winnerLogLossImprovementPassed": winner_improvement >= float(gate["winnerLogLossImprovementVsR1_72Min"]),
        "pairLogLossAdvantageVsR0_C0": pair_advantage,
        "pairLogLossAdvantagePassed": pair_advantage >= float(gate["pairLogLossAdvantageVsR0_C0Min"]),
        "pairBrierChangeVsR1_72": pair_brier_change,
        "pairBrierTolerancePassed": pair_brier_change <= float(gate["pairBrierMaxWorseningVsR1_72"]),
        "winnerBrierChangeVsR1_72": winner_brier_change,
        "winnerBrierNonWorseningPassed": winner_brier_change <= 0.0,
        "pairModalAccuracyDropPpVsR1_72": pair_accuracy_drop_pp,
        "pairModalAccuracyTolerancePassed": pair_accuracy_drop_pp <= float(gate["pairModalAccuracyMaxDropPpVsR1_72"]),
        "perTargetCatastrophicCheck": target_check,
        "noCatastrophicTargetReversalPassed": not bool(target_check["anyCatastrophicReversal"]),
    }
    checks["allMetricChecksPassed"] = all(
        value for key, value in checks.items() if key.endswith("Passed")
    )
    return checks


def production_checks(u1: dict, r1: dict, r0: dict, gate: dict) -> dict:
    checks = {
        "winnerLogLossNoWorseThanR0Passed": u1["winnerMeanLogLoss"] <= r0["winnerMeanLogLoss"],
        "winnerBrierVsR0Margin": float(u1["winnerMeanBrier"] - r0["winnerMeanBrier"]),
        "winnerBrierTolerancePassed": u1["winnerMeanBrier"] <= r0["winnerMeanBrier"] + float(gate["winnerBrierMaxAboveR0_C0"]),
        "pairLogLossBetterThanR0Passed": u1["pairMeanLogLoss"] < r0["pairMeanLogLoss"],
        "pairBrierBetterThanR0Passed": u1["pairMeanBrier"] < r0["pairMeanBrier"],
        "zeroProbabilityObservedPairsChangeVsR1_72": int(u1["zeroProbabilityObservedPairs"] - r1["zeroProbabilityObservedPairs"]),
        "zeroProbabilityObservedPairsNonIncreasingPassed": u1["zeroProbabilityObservedPairs"] <= r1["zeroProbabilityObservedPairs"],
    }
    checks["allMetricChecksPassed"] = all(
        value for key, value in checks.items() if key.endswith("Passed")
    )
    return checks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", type=Path, required=True)
    ap.add_argument("--selection", type=Path, required=True)
    ap.add_argument("--selection-freeze", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--preregistration", type=Path, default=DEFAULT_PREREG)
    ap.add_argument("--qoth-freeze", type=Path, default=DEFAULT_QOTH_FREEZE)
    ap.add_argument("--r1-preregistration", type=Path, default=DEFAULT_R1_PREREG)
    args = ap.parse_args()

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    qfreeze = json.loads(args.qoth_freeze.read_text(encoding="utf-8"))
    r1_prereg = json.loads(args.r1_preregistration.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    sfreeze = json.loads(args.selection_freeze.read_text(encoding="utf-8"))

    if sfreeze.get("status") != "frozen-before-heldout-2018-2022-score":
        raise ValueError("selection freeze is not marked pre-held-out")
    if sha256(args.selection) != sfreeze["selectionArtifactSha256"]:
        raise ValueError("regenerated selection artifact does not match committed pre-held-out SHA-256")
    if sha256(args.fit) != qfreeze["qOthFitSha256"]:
        raise ValueError("q_oth fit does not match PR #140 freeze")
    if selection["selections"] != sfreeze["selections"]:
        raise ValueError("selected concentrations differ from committed freeze")
    if selection["trainingEvidenceHashes"] != sfreeze["trainingEvidenceHashes"]:
        raise ValueError("training evidence hashes differ from committed freeze")

    simulations = int(r1_prereg["r0"]["simulationsPerTarget"])
    seed = int(r1_prereg["r0"]["electionSeed"])
    fit_by_target = {int(item["targetYear"]): item for item in fit["targets"]}

    records: dict[str, dict[int, list[dict]]] = {
        "r0": {}, "r1_72_equal": {}, "u1_equal": {}, "r1_72_proportional": {}, "u1_proportional": {}
    }
    summaries: dict[str, dict[int, dict]] = {key: {} for key in records}

    for year in TARGETS:
        q_target = fit_by_target[year]
        if not q_target["identified"]:
            raise ValueError(f"{year}: q_oth identification gate failed")
        q_draws = np.asarray(q_target["bootstrapDraws"], dtype=float)

        summary, recs = simulate_r0(year, simulations, seed)
        summaries["r0"][year], records["r0"][year] = summary, recs

        for allocation in ("equal", "proportional"):
            key72 = f"r1_72_{allocation}"
            summary72, recs72 = simulate_r1(year, 72.0, allocation, q_draws, simulations, seed)
            summaries[key72][year], records[key72][year] = summary72, recs72

            selected = float(selection["selections"][allocation][str(year)]["concentration"])
            keyu1 = f"u1_{allocation}"
            summaryu1, recsu1 = simulate_r1(year, selected, allocation, q_draws, simulations, seed)
            summaries[keyu1][year], records[keyu1][year] = summaryu1, recsu1

    pooled_metrics = {key: pooled(value) for key, value in records.items()}
    catastrophic_equal = per_target_catastrophic(
        summaries["u1_equal"], summaries["r1_72_equal"],
        float(prereg["researchSupportGate"]["perTargetCatastrophicLogLossWorseningMax"]),
    )
    catastrophic_prop = per_target_catastrophic(
        summaries["u1_proportional"], summaries["r1_72_proportional"],
        float(prereg["researchSupportGate"]["perTargetCatastrophicLogLossWorseningMax"]),
    )
    equal_checks = research_checks(
        pooled_metrics["u1_equal"], pooled_metrics["r1_72_equal"], pooled_metrics["r0"],
        catastrophic_equal, prereg["researchSupportGate"],
    )
    prop_checks = research_checks(
        pooled_metrics["u1_proportional"], pooled_metrics["r1_72_proportional"], pooled_metrics["r0"],
        catastrophic_prop, prereg["researchSupportGate"],
    )
    same_qualitative = bool(equal_checks["allMetricChecksPassed"] == prop_checks["allMetricChecksPassed"])
    research_supported = bool(equal_checks["allMetricChecksPassed"] and prop_checks["allMetricChecksPassed"] and same_qualitative)
    prod_checks = production_checks(
        pooled_metrics["u1_equal"], pooled_metrics["r1_72_equal"], pooled_metrics["r0"],
        prereg["productionCandidateGate"],
    )
    shadow_authorised = bool(research_supported and prod_checks["allMetricChecksPassed"])
    adjudication = "historically-supported-uncertainty-correction" if research_supported else "historically-inconclusive"

    payload = {
        "schemaVersion": 1,
        "status": "heldout-candidate-resolved-preference-uncertainty-score",
        "selectionArtifactSha256": sha256(args.selection),
        "qOthFitSha256": sha256(args.fit),
        "selections": selection["selections"],
        "perTarget": {
            str(year): {key: summaries[key][year] for key in summaries}
            for year in TARGETS
        },
        "pooled2018To2022": pooled_metrics,
        "researchSupportChecks": {
            "equal": equal_checks,
            "proportional": prop_checks,
            "sameQualitativeConclusionUnderSensitivity": same_qualitative,
            "historicallySupported": research_supported,
        },
        "productionCandidateChecks": {
            **prod_checks,
            "separateGoverned2026ShadowAuthorised": shadow_authorised,
        },
        "adjudication": adjudication,
        "guardrails": {
            "uses2026ForecastOutput": False,
            "uses2026SeatPolling": False,
            "modifiesCanonicalForecast": False,
            "modifiesPreferenceMeans": False,
            "modifiesCandidateResolutionArchitecture": False,
            "productionPromotionAuthorised": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selections": payload["selections"],
        "pooled2018To2022": pooled_metrics,
        "researchSupportChecks": payload["researchSupportChecks"],
        "productionCandidateChecks": payload["productionCandidateChecks"],
        "adjudication": adjudication,
        "sha256": sha256(args.output),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
