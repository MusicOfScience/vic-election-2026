#!/usr/bin/env python3
"""Score the frozen preregistered C1 preference challenger on historical outcomes.

C1 was fitted and frozen before historical winner/final-pair outcomes were loaded.
Because no source-family row passed the preregistered evidence thresholds, every
row is the broad fallback. This scorer does not relax those thresholds after the
fact. It evaluates that frozen consequence on the same genuine-IRV outcome
universe used by the corrected C0 benchmark.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from score_irv_c0_historical import (
    EPS,
    PAIR_CATEGORIES,
    PARTIES,
    _count_irv,
    brier,
    load_outcomes,
    load_primaries,
)

TARGETS = (2014, 2018, 2022)
EXPECTED_FREEZE_CANDIDATE_SHA256 = "056127783aebb1bea4ed0f5ab20b0685ece4c98d3e82b1ecacd620c0f8b6e78c"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_frozen_target(freeze: dict, year: int) -> tuple[np.ndarray, np.ndarray, dict]:
    if freeze.get("model") != "C1-preregistered-clean-original-parcel-walk-forward":
        raise ValueError("unexpected C1 freeze model")
    source_freeze = freeze.get("source_freeze", {})
    if source_freeze.get("freeze_candidate_sha256") != EXPECTED_FREEZE_CANDIDATE_SHA256:
        raise ValueError("C1 freeze does not reference the preregistered pre-outcome candidate hash")
    if freeze.get("guardrails", {}).get("historical_final_pair_or_winner_outcomes_loaded") is not False:
        raise ValueError("C1 freeze must predate historical scoring outcomes")
    target = freeze["targets"][str(year)]
    rows = target["rows"]
    means = np.array([rows[p]["mean"] for p in PARTIES], dtype=float)
    concentrations = np.array([float(rows[p]["concentration"]) for p in PARTIES], dtype=float)
    for i, party in enumerate(PARTIES):
        row = rows[party]
        if row["status"] != "broad-fallback":
            raise ValueError(f"{year} {party}: C1 row unexpectedly escaped broad fallback")
        if not math.isclose(means[i].sum(), 1.0, abs_tol=1e-12):
            raise ValueError(f"{year} {party}: frozen mean row does not sum to one")
        if not math.isclose(means[i, i], 0.0, abs_tol=1e-12):
            raise ValueError(f"{year} {party}: frozen mean has diagonal mass")
    return means, concentrations, target


def score_cycle(year: int, freeze: dict, simulations: int, seed: int) -> dict:
    means, concentrations, frozen_target = load_frozen_target(freeze, year)
    primaries = load_primaries(year)
    outcomes = load_outcomes(year)
    ids = sorted(set(primaries) & set(outcomes))
    if not ids:
        raise ValueError(f"{year}: no overlapping historical primary/outcome districts")

    rng = np.random.default_rng(seed + year)
    winner_counts = {did: np.zeros(len(PARTIES), dtype=int) for did in ids}
    pair_counts = {did: Counter() for did in ids}

    for _ in range(simulations):
        pref = np.vstack([
            rng.dirichlet(np.maximum(means[i] * concentrations[i], .02))
            for i in range(len(PARTIES))
        ])
        for did in ids:
            winner, pair = _count_irv(primaries[did]["primary"], pref)
            winner_counts[did][winner] += 1
            pair_counts[did][tuple(sorted(pair))] += 1

    district_scores = []
    impossible_observed_pairs = 0
    excluded_pair_kinds: Counter[str] = Counter()
    for did in ids:
        outcome = outcomes[did]
        wp = winner_counts[did] / simulations
        winner_obs = outcome["winner"]
        pair_obs = outcome["pair"]
        winner_modal = int(np.argmax(wp))
        if pair_obs is None:
            excluded_pair_kinds[outcome.get("pair_table_kind") or "missing-kind"] += 1
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
            "pair_structurally_impossible": False,
            "pair_outcome_table_kind": outcome.get("pair_table_kind"),
        }
        if pair_obs is not None:
            pp = np.array([pair_counts[did][cat] / simulations for cat in PAIR_CATEGORIES], dtype=float)
            obs_index = PAIR_CATEGORIES.index(pair_obs)
            modal_index = int(np.argmax(pp))
            pair_modal = PAIR_CATEGORIES[modal_index]
            obs_prob = float(pp[obs_index])
            structurally_impossible = pair_obs[0] == pair_obs[1]
            impossible_observed_pairs += int(structurally_impossible)
            rec.update({
                "pair_observed": [PARTIES[pair_obs[0]], PARTIES[pair_obs[1]]],
                "pair_modal": [PARTIES[pair_modal[0]], PARTIES[pair_modal[1]]],
                "pair_observed_probability": obs_prob,
                "pair_correct": pair_modal == pair_obs,
                "pair_brier": brier(pp, obs_index),
                "pair_log_loss": float(-math.log(max(obs_prob, EPS))),
                "pair_structurally_impossible": structurally_impossible,
            })
        district_scores.append(rec)

    pair_rows = [r for r in district_scores if r["pair_observed"] is not None]
    return {
        "cycle": f"vic_la_{year}",
        "training_event_count": int(frozen_target["training_event_count"]),
        "training_years": list(frozen_target["training_years"]),
        "row_status": {p: frozen_target["rows"][p]["status"] for p in PARTIES},
        "districts_scored_winner": len(district_scores),
        "districts_scored_final_pair": len(pair_rows),
        "districts_excluded_from_pair_scoring_by_kind": dict(sorted(excluded_pair_kinds.items())),
        "observed_same_family_final_pairs": impossible_observed_pairs,
        "winner_modal_accuracy": float(np.mean([r["winner_correct"] for r in district_scores])),
        "winner_mean_brier": float(np.mean([r["winner_brier"] for r in district_scores])),
        "winner_mean_log_loss": float(np.mean([r["winner_log_loss"] for r in district_scores])),
        "pair_modal_accuracy": float(np.mean([r["pair_correct"] for r in pair_rows])) if pair_rows else None,
        "pair_mean_brier": float(np.mean([r["pair_brier"] for r in pair_rows])) if pair_rows else None,
        "pair_mean_log_loss": float(np.mean([r["pair_log_loss"] for r in pair_rows])) if pair_rows else None,
        "districts": district_scores,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--simulations", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261028)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    cycles = [score_cycle(year, freeze, args.simulations, args.seed) for year in TARGETS]
    all_districts = [d for c in cycles for d in c["districts"]]
    pair_rows = [d for d in all_districts if d["pair_observed"] is not None]
    summary = {
        "schemaVersion": 1,
        "model": "C1-frozen-preregistered-broad-fallback-consequence",
        "conditional_on": "observed historical five-family first preferences",
        "freeze_path": str(args.freeze),
        "freeze_file_sha256": sha(freeze_bytes),
        "freeze_candidate_sha256": EXPECTED_FREEZE_CANDIDATE_SHA256,
        "simulations_per_cycle": args.simulations,
        "seed": args.seed,
        "guardrails": {
            "uses_2026_forecast_output": False,
            "historical_outcomes_are_scoring_only": True,
            "thresholds_relaxed_after_evidence_inspection": False,
            "two_candidate_preferred_fallbacks_score_as_irv_pairs": False,
        },
        "overall": {
            "districts_scored_winner": len(all_districts),
            "districts_scored_final_pair": len(pair_rows),
            "observed_same_family_final_pairs": sum(c["observed_same_family_final_pairs"] for c in cycles),
            "winner_modal_accuracy": float(np.mean([d["winner_correct"] for d in all_districts])),
            "winner_mean_brier": float(np.mean([d["winner_brier"] for d in all_districts])),
            "winner_mean_log_loss": float(np.mean([d["winner_log_loss"] for d in all_districts])),
            "pair_modal_accuracy": float(np.mean([d["pair_correct"] for d in pair_rows])) if pair_rows else None,
            "pair_mean_brier": float(np.mean([d["pair_brier"] for d in pair_rows])) if pair_rows else None,
            "pair_mean_log_loss": float(np.mean([d["pair_log_loss"] for d in pair_rows])) if pair_rows else None,
        },
        "cycles": cycles,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary["overall"], sort_keys=True))
    for cycle in cycles:
        print(json.dumps({k: v for k, v in cycle.items() if k != "districts"}, sort_keys=True))
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
