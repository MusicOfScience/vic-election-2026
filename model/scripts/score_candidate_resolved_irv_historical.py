#!/usr/bin/env python3
"""Score the preregistered OTH/Independent candidate-resolution IRV challenger.

R1 resolves only OTH_IND candidates.  ALP, Coalition, One Nation and Greens
remain family aggregates.  The script refuses to run unless the regenerated
walk-forward q_oth fit matches the pre-outcome freeze committed before this
historical outcome score.

No 2026 forecast output is read or written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "model/src"))

from score_irv_c0_historical import (  # noqa: E402
    EPS,
    FAMILY_MAP,
    OBSERVED_IRV_PAIR_KINDS,
    PAIR_CATEGORIES,
    PARTIES,
    brier,
    load_outcomes,
    load_primaries,
    truthy,
)
from vicforecast.forecast_2026 import PREFERENCE_PRIOR, _count_irv  # noqa: E402

TARGETS = (2014, 2018, 2022)
OTH_INDEX = PARTIES.index("OTH_IND")
NAMED_INDICES = tuple(i for i, party in enumerate(PARTIES) if party != "OTH_IND")
DEFAULT_PREREG = ROOT / "metadata/candidate-resolution-irv-preregistration-2026-10-29.json"
DEFAULT_FREEZE = ROOT / "metadata/candidate-resolution-irv-qoth-freeze-2026-10-29.json"
DEFAULT_C0_ADJUDICATION = ROOT / "metadata/irv-final-pair-calibration-adjudication-2026-10-28.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm_name(value: str) -> str:
    return " ".join(str(value).casefold().split())


def candidate_signature(family: str, candidate: str) -> str:
    if family == "OTH_IND":
        return f"OTH_IND::{norm_name(candidate)}"
    return family


def load_candidate_states(year: int, family_primaries: dict[str, dict]) -> dict[str, dict]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_candidate_primaries.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, dict] = {}
    for row in rows:
        contest = row.get("contest") or ""
        if contest not in {"general-election", "general_election", ""}:
            continue
        did = row["district_id"]
        family = FAMILY_MAP.get(row["party_family"])
        if family is None:
            raise ValueError(f"{year} {did}: unknown candidate family {row['party_family']!r}")
        formal = float(row["formal_votes"])
        rec = out.setdefault(
            did,
            {
                "district_name": row["district_name"],
                "formal": formal,
                "named_votes": {PARTIES[i]: 0.0 for i in NAMED_INDICES},
                "oth_candidates": [],
            },
        )
        if not math.isclose(rec["formal"], formal, rel_tol=0, abs_tol=0.5):
            raise ValueError(f"{year} {did}: inconsistent formal votes in candidate file")
        votes = float(row["first_preference_votes"])
        if family == "OTH_IND":
            rec["oth_candidates"].append({
                "candidate": row["candidate_name"],
                "candidate_order": int(row.get("candidate_order") or 9999),
                "votes": votes,
                "party_raw": row.get("party_raw") or "",
                "independent": str(row.get("independent_status") or "").casefold() == "true",
            })
        else:
            rec["named_votes"][family] += votes

    for did, rec in out.items():
        rec["oth_candidates"].sort(key=lambda row: (row["candidate_order"], norm_name(row["candidate"])))
        candidate_total = sum(rec["named_votes"].values()) + sum(c["votes"] for c in rec["oth_candidates"])
        if not math.isclose(candidate_total, rec["formal"], rel_tol=0, abs_tol=0.5):
            raise ValueError(f"{year} {did}: candidate primaries do not reconcile ({candidate_total} vs {rec['formal']})")
        if did not in family_primaries:
            raise ValueError(f"{year} {did}: candidate district missing from C0 family primaries")
        c0 = family_primaries[did]
        if not math.isclose(rec["formal"], c0["formal"], rel_tol=0, abs_tol=0.5):
            raise ValueError(f"{year} {did}: candidate/C0 formal totals differ")
        family_votes = [
            rec["named_votes"][PARTIES[i]] if i in NAMED_INDICES else sum(c["votes"] for c in rec["oth_candidates"])
            for i in range(len(PARTIES))
        ]
        for i, votes in enumerate(family_votes):
            expected = float(c0["primary"][i]) * float(c0["formal"])
            if not math.isclose(votes, expected, rel_tol=0, abs_tol=0.5):
                raise ValueError(
                    f"{year} {did}: candidate-resolved {PARTIES[i]} total {votes} != C0 family total {expected}"
                )

        node_families = list(NAMED_INDICES) + [OTH_INDEX] * len(rec["oth_candidates"])
        node_labels = [PARTIES[i] for i in NAMED_INDICES] + [
            candidate_signature("OTH_IND", c["candidate"]) for c in rec["oth_candidates"]
        ]
        node_votes = [rec["named_votes"][PARTIES[i]] for i in NAMED_INDICES] + [
            c["votes"] for c in rec["oth_candidates"]
        ]
        rec["node_families"] = np.asarray(node_families, dtype=int)
        rec["node_labels"] = node_labels
        rec["primary"] = np.asarray(node_votes, dtype=float) / rec["formal"]
    return out


def load_exact_pair_signatures(year: int, outcomes: dict[str, dict]) -> dict[str, tuple[str, str] | None]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_final_pairs.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, tuple[str, str] | None] = {}
    for row in rows:
        did = row["district_id"]
        if did not in outcomes or outcomes[did]["pair"] is None:
            out[did] = None
            continue
        f1 = FAMILY_MAP.get(row.get("finalist_1_party_family") or "")
        f2 = FAMILY_MAP.get(row.get("finalist_2_party_family") or "")
        if f1 is None or f2 is None:
            out[did] = None
            continue
        sig = (
            candidate_signature(f1, row.get("finalist_1_candidate") or ""),
            candidate_signature(f2, row.get("finalist_2_candidate") or ""),
        )
        out[did] = tuple(sorted(sig))
    return out


def split_oth_mass(indices: list[int], votes: np.ndarray, mode: str) -> np.ndarray:
    if not indices:
        return np.asarray([], dtype=float)
    if mode == "equal":
        return np.full(len(indices), 1.0 / len(indices), dtype=float)
    if mode != "proportional":
        raise ValueError(f"unknown OTH allocation mode {mode!r}")
    current = np.asarray([max(float(votes[i]), 0.0) for i in indices], dtype=float)
    total = float(current.sum())
    if total <= 0:
        return np.full(len(indices), 1.0 / len(indices), dtype=float)
    return current / total


def count_r1(
    primary: np.ndarray,
    node_families: np.ndarray,
    node_labels: list[str],
    preference: np.ndarray,
    q_oth: float,
    allocation: str,
) -> tuple[int, tuple[int, int], tuple[str, str], int]:
    votes = primary.copy()
    continuing = set(range(len(votes)))
    oth_to_oth_steps = 0
    while len(continuing) > 2:
        source = min(continuing, key=lambda x: (votes[x], x))
        continuing.remove(source)
        source_family = int(node_families[source])
        named = sorted(i for i in continuing if int(node_families[i]) != OTH_INDEX)
        oth = sorted(i for i in continuing if int(node_families[i]) == OTH_INDEX)
        probs: dict[int, float] = {}

        if source_family != OTH_INDEX:
            active_families = [int(node_families[i]) for i in named]
            raw_named = np.asarray([preference[source_family, fam] for fam in active_families], dtype=float)
            raw_oth = float(preference[source_family, OTH_INDEX]) if oth else 0.0
            denom = float(raw_named.sum() + raw_oth)
            if denom <= 0:
                raise ValueError("named-family transfer has no continuing destination mass")
            for idx, raw in zip(named, raw_named):
                probs[idx] = float(raw / denom)
            if oth:
                shares = split_oth_mass(oth, votes, allocation)
                for idx, share in zip(oth, shares):
                    probs[idx] = float((raw_oth / denom) * share)
        else:
            if oth and named:
                q = min(max(float(q_oth), 0.0), 1.0)
                shares = split_oth_mass(oth, votes, allocation)
                for idx, share in zip(oth, shares):
                    probs[idx] = float(q * share)
                raw_named = np.asarray(
                    [preference[OTH_INDEX, int(node_families[i])] for i in named], dtype=float
                )
                denom = float(raw_named.sum())
                if denom <= 0:
                    raise ValueError("OTH cross-family transfer has no continuing named-family mass")
                for idx, raw in zip(named, raw_named):
                    probs[idx] = float((1.0 - q) * raw / denom)
                oth_to_oth_steps += 1
            elif oth:
                shares = split_oth_mass(oth, votes, allocation)
                for idx, share in zip(oth, shares):
                    probs[idx] = float(share)
                oth_to_oth_steps += 1
            elif named:
                raw_named = np.asarray(
                    [preference[OTH_INDEX, int(node_families[i])] for i in named], dtype=float
                )
                denom = float(raw_named.sum())
                if denom <= 0:
                    raise ValueError("OTH transfer has no continuing named-family mass")
                for idx, raw in zip(named, raw_named):
                    probs[idx] = float(raw / denom)
            else:
                raise ValueError("IRV elimination left no destination")

        total_prob = sum(probs.values())
        if not math.isclose(total_prob, 1.0, rel_tol=0, abs_tol=1e-10):
            raise ValueError(f"candidate-level transfer probabilities sum to {total_prob}")
        source_votes = float(votes[source])
        for idx, prob in probs.items():
            votes[idx] += source_votes * prob
        votes[source] = 0.0

    final = tuple(sorted(continuing, key=lambda x: (-votes[x], x)))
    winner_family = int(node_families[final[0]])
    pair_families = tuple(sorted((int(node_families[final[0]]), int(node_families[final[1]]))))
    exact_pair = tuple(sorted((node_labels[final[0]], node_labels[final[1]])))
    return winner_family, pair_families, exact_pair, oth_to_oth_steps


def init_counts(ids: list[str]) -> dict:
    return {
        "winner": {did: np.zeros(len(PARTIES), dtype=int) for did in ids},
        "pair": {did: Counter() for did in ids},
        "exact_pair": {did: Counter() for did in ids},
        "oth_to_oth_steps": 0,
        "simulations_with_oth_to_oth": 0,
    }


def district_records(
    counts: dict,
    ids: list[str],
    outcomes: dict[str, dict],
    exact_observed: dict[str, tuple[str, str] | None],
    simulations: int,
    include_exact: bool,
) -> list[dict]:
    records = []
    for did in ids:
        outcome = outcomes[did]
        wp = counts["winner"][did] / simulations
        winner_obs = int(outcome["winner"])
        winner_modal = int(np.argmax(wp))
        rec = {
            "district_id": did,
            "district_name": outcome["district_name"],
            "winner_observed": PARTIES[winner_obs],
            "winner_modal": PARTIES[winner_modal],
            "winner_observed_probability": float(wp[winner_obs]),
            "winner_correct": winner_modal == winner_obs,
            "winner_brier": brier(wp, winner_obs),
            "winner_log_loss": float(-math.log(max(float(wp[winner_obs]), EPS))),
            "pair_observed": None,
            "pair_modal": None,
            "pair_observed_probability": None,
            "pair_correct": None,
            "pair_brier": None,
            "pair_log_loss": None,
            "phantom_oth_modal_pair_error": False,
            "exact_oth_pair_observed": None,
            "exact_oth_pair_modal": None,
            "exact_oth_pair_observed_probability": None,
            "exact_oth_pair_correct": None,
        }
        pair_obs = outcome["pair"]
        if pair_obs is not None:
            pp = np.asarray([counts["pair"][did][cat] / simulations for cat in PAIR_CATEGORIES], dtype=float)
            obs_index = PAIR_CATEGORIES.index(pair_obs)
            modal_index = int(np.argmax(pp))
            pair_modal = PAIR_CATEGORIES[modal_index]
            obs_prob = float(pp[obs_index])
            rec.update({
                "pair_observed": [PARTIES[pair_obs[0]], PARTIES[pair_obs[1]]],
                "pair_modal": [PARTIES[pair_modal[0]], PARTIES[pair_modal[1]]],
                "pair_observed_probability": obs_prob,
                "pair_correct": pair_modal == pair_obs,
                "pair_brier": brier(pp, obs_index),
                "pair_log_loss": float(-math.log(max(obs_prob, EPS))),
                "phantom_oth_modal_pair_error": (
                    OTH_INDEX in pair_modal and OTH_INDEX not in pair_obs
                ),
            })
            if include_exact and exact_observed.get(did) is not None and OTH_INDEX in pair_obs:
                exact_counter = counts["exact_pair"][did]
                exact_obs = exact_observed[did]
                exact_modal = exact_counter.most_common(1)[0][0] if exact_counter else None
                exact_prob = exact_counter[exact_obs] / simulations
                rec.update({
                    "exact_oth_pair_observed": list(exact_obs),
                    "exact_oth_pair_modal": list(exact_modal) if exact_modal else None,
                    "exact_oth_pair_observed_probability": float(exact_prob),
                    "exact_oth_pair_correct": exact_modal == exact_obs,
                })
        records.append(rec)
    return records


def aggregate(records: list[dict]) -> dict:
    pair_rows = [row for row in records if row["pair_observed"] is not None]
    exact_rows = [row for row in records if row["exact_oth_pair_observed"] is not None]
    return {
        "winnerDistricts": len(records),
        "finalPairDistricts": len(pair_rows),
        "winnerModalAccuracy": float(np.mean([r["winner_correct"] for r in records])),
        "winnerMeanBrier": float(np.mean([r["winner_brier"] for r in records])),
        "winnerMeanLogLoss": float(np.mean([r["winner_log_loss"] for r in records])),
        "pairModalAccuracy": float(np.mean([r["pair_correct"] for r in pair_rows])) if pair_rows else None,
        "pairMeanBrier": float(np.mean([r["pair_brier"] for r in pair_rows])) if pair_rows else None,
        "pairMeanLogLoss": float(np.mean([r["pair_log_loss"] for r in pair_rows])) if pair_rows else None,
        "zeroProbabilityObservedPairs": sum(float(r["pair_observed_probability"]) == 0.0 for r in pair_rows),
        "phantomOthModalPairErrors": sum(bool(r["phantom_oth_modal_pair_error"]) for r in pair_rows),
        "exactOthPairDistricts": len(exact_rows),
        "exactOthPairModalAccuracy": (
            float(np.mean([r["exact_oth_pair_correct"] for r in exact_rows])) if exact_rows else None
        ),
        "exactOthPairMeanObservedProbability": (
            float(np.mean([r["exact_oth_pair_observed_probability"] for r in exact_rows])) if exact_rows else None
        ),
    }


def assert_c0_reproduction(actual: dict, adjudication: dict) -> None:
    expected = adjudication["c0"]["matched2014To2022"]
    pairs = {
        "winnerDistricts": "winnerDistricts",
        "finalPairDistricts": "finalPairDistricts",
        "winnerModalAccuracy": "winnerModalAccuracy",
        "winnerMeanBrier": "winnerMeanBrier",
        "winnerMeanLogLoss": "winnerMeanLogLoss",
        "pairModalAccuracy": "pairModalAccuracy",
        "pairMeanBrier": "pairMeanBrier",
        "pairMeanLogLoss": "pairMeanLogLoss",
    }
    for actual_key, expected_key in pairs.items():
        a = actual[actual_key]
        e = expected[expected_key]
        if isinstance(e, int):
            if a != e:
                raise AssertionError(f"C0 reproduction failed for {actual_key}: {a} != {e}")
        elif not math.isclose(float(a), float(e), rel_tol=0, abs_tol=1e-12):
            raise AssertionError(f"C0 reproduction failed for {actual_key}: {a} != {e}")


def support_checks(r0: dict, challenger: dict, prereg: dict) -> dict:
    rule = prereg["supportRule"]
    improvement = float(r0["pairMeanLogLoss"] - challenger["pairMeanLogLoss"])
    winner_brier_change = float(challenger["winnerMeanBrier"] - r0["winnerMeanBrier"])
    checks = {
        "pairLogLossImprovement": improvement,
        "minimumPairLogLossImprovementPassed": improvement >= float(rule["minimumPairLogLossImprovement"]),
        "pairBrierNonWorseningPassed": challenger["pairMeanBrier"] <= r0["pairMeanBrier"],
        "winnerBrierChange": winner_brier_change,
        "winnerBrierTolerancePassed": winner_brier_change <= float(rule["maximumAbsoluteWinnerBrierWorsening"]),
        "phantomOthModalPairErrorsChange": int(challenger["phantomOthModalPairErrors"] - r0["phantomOthModalPairErrors"]),
        "phantomOthModalPairErrorsFallPassed": challenger["phantomOthModalPairErrors"] < r0["phantomOthModalPairErrors"],
    }
    checks["allMetricChecksPassed"] = all(
        value for key, value in checks.items() if key.endswith("Passed")
    )
    return checks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", type=Path, required=True)
    ap.add_argument("--preregistration", type=Path, default=DEFAULT_PREREG)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    ap.add_argument("--c0-adjudication", type=Path, default=DEFAULT_C0_ADJUDICATION)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    fit = json.loads(args.fit.read_text(encoding="utf-8"))
    c0_adjudication = json.loads(args.c0_adjudication.read_text(encoding="utf-8"))
    if freeze.get("status") != "frozen-before-r1-historical-outcome-score":
        raise ValueError("q_oth freeze is not marked pre-score frozen")
    if sha256(args.fit) != freeze["qOthFitSha256"]:
        raise ValueError("regenerated q_oth fit does not match the frozen pre-score SHA-256")
    if fit.get("guardrails", {}).get("historicalOutcomesRead") is not False:
        raise ValueError("q_oth fit is not outcome-isolated")

    simulations = int(prereg["r0"]["simulationsPerTarget"])
    concentration = float(prereg["r0"]["preferenceConcentration"])
    seed = int(prereg["r0"]["electionSeed"])
    fit_by_target = {int(item["targetYear"]): item for item in fit["targets"]}

    cycle_outputs = []
    pooled_records = {"r0": [], "r1_equal": [], "r1_proportional": []}
    for year in TARGETS:
        family_primaries = load_primaries(year)
        outcomes = load_outcomes(year)
        candidate_states = load_candidate_states(year, family_primaries)
        exact_observed = load_exact_pair_signatures(year, outcomes)
        ids = sorted(set(family_primaries) & set(outcomes) & set(candidate_states))
        q_target = fit_by_target[year]
        if not q_target["identified"]:
            raise ValueError(f"{year}: q_oth identification gate failed")
        q_draws = np.asarray(q_target["bootstrapDraws"], dtype=float)
        if len(q_draws) != simulations:
            raise ValueError(f"{year}: expected {simulations} frozen q_oth draws, got {len(q_draws)}")

        counts = {
            "r0": init_counts(ids),
            "r1_equal": init_counts(ids),
            "r1_proportional": init_counts(ids),
        }
        rng = np.random.default_rng(seed + year)
        for simulation in range(simulations):
            pref = np.vstack([
                rng.dirichlet(np.maximum(row * concentration, .02))
                for row in PREFERENCE_PRIOR
            ])
            q_oth = float(q_draws[simulation])
            any_oth_step = {"r1_equal": False, "r1_proportional": False}
            for did in ids:
                winner, pair = _count_irv(family_primaries[did]["primary"], pref)
                counts["r0"]["winner"][did][winner] += 1
                counts["r0"]["pair"][did][tuple(sorted(pair))] += 1

                state = candidate_states[did]
                for method, allocation in (("r1_equal", "equal"), ("r1_proportional", "proportional")):
                    r1_winner, r1_pair, exact_pair, oth_steps = count_r1(
                        state["primary"], state["node_families"], state["node_labels"],
                        pref, q_oth, allocation,
                    )
                    counts[method]["winner"][did][r1_winner] += 1
                    counts[method]["pair"][did][r1_pair] += 1
                    counts[method]["exact_pair"][did][exact_pair] += 1
                    counts[method]["oth_to_oth_steps"] += oth_steps
                    any_oth_step[method] = any_oth_step[method] or oth_steps > 0
            for method in any_oth_step:
                counts[method]["simulations_with_oth_to_oth"] += int(any_oth_step[method])

        method_outputs = {}
        for method in counts:
            records = district_records(
                counts[method], ids, outcomes, exact_observed, simulations,
                include_exact=method != "r0",
            )
            pooled_records[method].extend(records)
            method_outputs[method] = {
                "summary": aggregate(records),
                "othToOthTransferSteps": counts[method]["oth_to_oth_steps"],
                "simulationsWithAnyOthToOthTransfer": counts[method]["simulations_with_oth_to_oth"],
                "districts": records,
            }
        cycle_outputs.append({
            "cycle": f"vic_la_{year}",
            "qOth": q_target["summary"],
            "districtsWithMultipleOthCandidates": sum(
                len(candidate_states[did]["oth_candidates"]) > 1 for did in ids
            ),
            "methods": method_outputs,
        })

    pooled = {method: aggregate(records) for method, records in pooled_records.items()}
    assert_c0_reproduction(pooled["r0"], c0_adjudication)
    equal_checks = support_checks(pooled["r0"], pooled["r1_equal"], prereg)
    proportional_checks = support_checks(pooled["r0"], pooled["r1_proportional"], prereg)
    same_direction = bool(equal_checks["allMetricChecksPassed"] == proportional_checks["allMetricChecksPassed"])
    supported = bool(
        equal_checks["allMetricChecksPassed"]
        and proportional_checks["allMetricChecksPassed"]
        and same_direction
    )
    if not same_direction:
        adjudication = "allocation-sensitive-unresolved"
    elif supported:
        adjudication = "historically-supported-architecture-only"
    else:
        adjudication = "historically-not-supported-under-frozen-rule"

    payload = {
        "schemaVersion": 1,
        "status": "historical-r1-candidate-resolution-score",
        "model": "R1-OTH_IND-candidate-resolved-operational-IRV",
        "simulationsPerTarget": simulations,
        "familyPreferenceConcentration": concentration,
        "electionSeed": seed,
        "qOthFitSha256": sha256(args.fit),
        "qOthFreeze": str(args.freeze.relative_to(ROOT)),
        "guardrails": {
            "uses2026ForecastOutput": False,
            "uses2026SeatPolling": False,
            "fitsNewCrossFamilyMeans": False,
            "c0ReproducedToMachineTolerance": True,
        },
        "pooled2014To2022": pooled,
        "supportChecks": {
            "r1Equal": equal_checks,
            "r1Proportional": proportional_checks,
            "allocationSensitivityPreservesConclusionDirection": same_direction,
            "r1HistoricallySupported": supported,
            "adjudication": adjudication,
        },
        "cycles": cycle_outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "pooled2014To2022": pooled,
        "supportChecks": payload["supportChecks"],
        "output": str(args.output),
        "sha256": sha256(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
