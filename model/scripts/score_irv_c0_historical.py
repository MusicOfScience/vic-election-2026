#!/usr/bin/env python3
"""Score the current 2026 Assembly IRV preference mechanism on historical outcomes.

C0 is deliberately the production mechanism under test: the current fixed 5x5
PREFERENCE_PRIOR, Dirichlet concentration 72, one preference draw shared by all
districts in a simulated election, and the production `_count_irv` function.

The replay is conditional on observed historical five-family primaries. This
isolates preference/elimination/family-aggregation performance from polling and
primary-vote forecast error. Historical final-pair and winner outcomes are
scoring-only and never enter the simulated preferences.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(ROOT / "model/src"))
from vicforecast.forecast_2026 import PARTIES, PREFERENCE_PRIOR, _count_irv  # noqa: E402

CYCLES = (2010, 2014, 2018, 2022)
FAMILY_MAP = {
    "ALP": "ALP",
    "Coalition": "LIB_NAT",
    "LIB_NAT": "LIB_NAT",
    "One Nation": "ONP",
    "ONP": "ONP",
    "Greens": "GRN",
    "GRN": "GRN",
    "Other/Independent": "OTH_IND",
    "OTH_IND": "OTH_IND",
}
PAIR_CATEGORIES = tuple(itertools.combinations_with_replacement(range(len(PARTIES)), 2))
EPS = 1e-6

# These represent genuine observed IRV final-two evidence.  In particular,
# 2018's `two-candidate-preferred-final-page` fallback is deliberately excluded:
# a VEC 2CP pair is useful reporting, but it is not necessarily the actual IRV
# final pair and therefore cannot score the elimination model.
OBSERVED_IRV_PAIR_KINDS = {
    "results-after-distribution",
    "distribution-page-final-total",
}


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def truthy(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes"}


def load_primaries(year: int) -> dict[str, dict]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_family_primaries.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, dict] = {}
    for row in rows:
        # The legacy 2010 family artefact predates the `contest` column. Treat
        # a missing value as the general-election universe; later artefacts
        # still explicitly exclude supplementary/post-cycle contests.
        contest = row.get("contest") or ""
        if contest not in {"general-election", "general_election", ""}:
            continue
        did = row["district_id"]
        fam = FAMILY_MAP.get(row["party_family"])
        if fam is None:
            raise ValueError(f"{year} {did}: unknown family {row['party_family']!r}")
        rec = out.setdefault(
            did,
            {
                "district_name": row["district_name"],
                "votes": {p: 0.0 for p in PARTIES},
                "formal": float(row["formal_votes"]),
            },
        )
        if not math.isclose(rec["formal"], float(row["formal_votes"])):
            raise ValueError(f"{year} {did}: inconsistent formal vote total")
        rec["votes"][fam] += float(row["first_preference_votes"])
    for did, rec in out.items():
        total = sum(rec["votes"].values())
        if not math.isclose(total, rec["formal"], rel_tol=0, abs_tol=0.5):
            raise ValueError(f"{year} {did}: family primaries do not reconcile ({total} vs {rec['formal']})")
        rec["primary"] = np.array([rec["votes"][p] / rec["formal"] for p in PARTIES], dtype=float)
    return out


def load_outcomes(year: int) -> dict[str, dict]:
    path = ROOT / f"model/data/processed/vec_{year}_assembly_final_pairs.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = {}
    for row in rows:
        did = row["district_id"]
        winner = FAMILY_MAP.get(row.get("winner_party_family") or row.get("elected_party_family") or "")
        if winner is None:
            raise ValueError(f"{year} {did}: unknown winner family")

        table_kind = (row.get("outcome_table_kind") or "").strip()
        final_pair_flag = row.get("final_pair_available")
        pair_is_observed_irv = (
            table_kind in OBSERVED_IRV_PAIR_KINDS
            and (final_pair_flag in (None, "") or truthy(final_pair_flag))
        )
        f1 = FAMILY_MAP.get(row.get("finalist_1_party_family") or "")
        f2 = FAMILY_MAP.get(row.get("finalist_2_party_family") or "")
        pair = None
        if pair_is_observed_irv and f1 is not None and f2 is not None:
            pair = tuple(sorted((PARTIES.index(f1), PARTIES.index(f2))))

        if table_kind == "two-candidate-preferred-final-page" and pair is not None:
            raise AssertionError(f"{year} {did}: 2CP fallback leaked into IRV final-pair scoring")

        out[did] = {
            "district_name": row["district_name"],
            "winner": PARTIES.index(winner),
            "pair": pair,
            "pair_raw": [row.get("finalist_1_party_family"), row.get("finalist_2_party_family")],
            "pair_table_kind": table_kind or None,
            "pair_scoring_status": "observed-irv-final-pair" if pair is not None else "not-scored-as-irv-final-pair",
        }
    return out


def brier(prob: np.ndarray, observed: int) -> float:
    target = np.zeros_like(prob)
    target[observed] = 1.0
    return float(np.sum((prob - target) ** 2))


def score_cycle(year: int, simulations: int, concentration: float, seed: int) -> dict:
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
            rng.dirichlet(np.maximum(row * concentration, .02))
            for row in PREFERENCE_PRIOR
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
    ap.add_argument("--simulations", type=int, default=5000)
    ap.add_argument("--concentration", type=float, default=72.0)
    ap.add_argument("--seed", type=int, default=20261028)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    cycles = [score_cycle(y, args.simulations, args.concentration, args.seed) for y in CYCLES]
    all_districts = [d for c in cycles for d in c["districts"]]
    pair_rows = [d for d in all_districts if d["pair_observed"] is not None]
    summary = {
        "schemaVersion": 2,
        "model": "C0-current-production-preference-mechanism",
        "conditional_on": "observed historical five-family first preferences",
        "pair_scoring_rule": "official observed IRV final pairs only; indicative 2CP fallbacks excluded",
        "simulations_per_cycle": args.simulations,
        "preference_prior_concentration": args.concentration,
        "seed": args.seed,
        "guardrails": {
            "uses_2026_forecast_output": False,
            "uses_2026_seat_polling": False,
            "historical_outcomes_are_scoring_only": True,
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
