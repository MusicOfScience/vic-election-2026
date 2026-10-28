#!/usr/bin/env python3
"""Fit preregistered C1 Assembly preference rows without loading scoring outcomes.

Consumes only historical clean original-parcel transfer evidence.  It does not
open historical final-pair/winner artefacts and does not read any 2026 forecast
output.  The resulting JSON is intended to be hashed/frozen before C1 scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

PARTIES = ("ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND")
TARGETS = (2014, 2018, 2022)
CONCENTRATION_GRID = (2, 4, 8, 12, 18, 24, 36, 48, 72, 108, 144)
MIN_EVENTS = 12
MIN_ELECTIONS = 2
BROAD_CONCENTRATION = 2.0


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def broad_row(source: str) -> list[float]:
    return [0.0 if p == source else 0.25 for p in PARTIES]


def admissible(event: dict) -> tuple[bool, str]:
    source = event["source_family"]
    if source == "OTH_IND":
        return False, "heterogeneous-source-family"
    if int(event.get("within_source_family_transfer_votes", 0)) != 0:
        return False, "within-source-family-transfer"
    counts = event["destination_candidate_count"]
    if any(int(counts.get(p, 0)) > 1 for p in PARTIES):
        return False, "multiple-candidates-in-collapsed-destination-family"
    return True, "admissible"


def available(event: dict, source: str) -> list[str]:
    counts = event["destination_candidate_count"]
    return [p for p in PARTIES if p != source and int(counts.get(p, 0)) > 0]


def connected_choice_graph(events: list[dict], source: str) -> bool:
    nodes = [p for p in PARTIES if p != source]
    graph = {p: set() for p in nodes}
    for event in events:
        avail = available(event, source)
        for i, p in enumerate(avail):
            graph[p].update(avail[:i] + avail[i + 1:])
    if not nodes:
        return False
    seen = {nodes[0]}
    stack = [nodes[0]]
    while stack:
        node = stack.pop()
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == set(nodes)


def loglik(beta: np.ndarray, events: list[dict], source: str, dests: list[str]) -> float:
    total = 0.0
    b = {dests[0]: 0.0, **{d: float(beta[i - 1]) for i, d in enumerate(dests) if i > 0}}
    for event in events:
        avail = available(event, source)
        if len(avail) < 2:
            continue
        logits = np.array([b[p] for p in avail], dtype=float)
        logits -= logits.max()
        probs = np.exp(logits)
        probs /= probs.sum()
        counts = np.array([float(event["destination_votes"].get(p, 0)) for p in avail])
        total += float(np.dot(counts, np.log(np.clip(probs, 1e-15, None))))
    return total


def fit_attraction(events: list[dict], source: str) -> tuple[np.ndarray, dict]:
    dests = [p for p in PARTIES if p != source]
    if not connected_choice_graph(events, source):
        raise ValueError("continuing-family choice-set graph is not connected")
    beta = np.zeros(len(dests) - 1, dtype=float)
    current = loglik(beta, events, source, dests)
    for iteration in range(100):
        grad = np.zeros_like(beta)
        hess = np.zeros((len(beta), len(beta)))
        b = {dests[0]: 0.0, **{d: float(beta[i - 1]) for i, d in enumerate(dests) if i > 0}}
        for event in events:
            avail = available(event, source)
            if len(avail) < 2:
                continue
            logits = np.array([b[p] for p in avail], dtype=float)
            logits -= logits.max()
            probs = np.exp(logits); probs /= probs.sum()
            counts = np.array([float(event["destination_votes"].get(p, 0)) for p in avail])
            n = counts.sum()
            free = [p for p in avail if p != dests[0]]
            for a, pa in enumerate(free):
                ia = dests.index(pa) - 1
                posa = avail.index(pa)
                grad[ia] += counts[posa] - n * probs[posa]
                for pb in free:
                    ib = dests.index(pb) - 1
                    posb = avail.index(pb)
                    hess[ia, ib] -= n * probs[posa] * ((1.0 if pa == pb else 0.0) - probs[posb])
        if np.max(np.abs(grad)) < 1e-7:
            break
        try:
            step = np.linalg.solve(-hess, grad)
        except np.linalg.LinAlgError as exc:
            raise ValueError("conditional-attractiveness Hessian is singular") from exc
        scale = 1.0
        improved = False
        while scale >= 1e-6:
            candidate = beta + scale * step
            candidate_ll = loglik(candidate, events, source, dests)
            if candidate_ll >= current - 1e-10:
                beta = candidate
                current = candidate_ll
                improved = True
                break
            scale *= 0.5
        if not improved:
            raise ValueError("conditional-attractiveness Newton step failed line search")
        if np.max(np.abs(scale * step)) < 1e-9:
            break
    strengths = np.ones(len(dests), dtype=float)
    strengths[1:] = np.exp(np.clip(beta, -30, 30))
    strengths /= strengths.sum()
    row = np.zeros(len(PARTIES), dtype=float)
    for p, value in zip(dests, strengths):
        row[PARTIES.index(p)] = value
    return row, {"iterations": iteration + 1, "multinomial_log_likelihood": current}


def conditional_probability(row: np.ndarray, event: dict, source: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    avail = available(event, source)
    probs = np.array([row[PARTIES.index(p)] for p in avail], dtype=float)
    probs /= probs.sum()
    counts = np.array([float(event["destination_votes"].get(p, 0)) for p in avail], dtype=float)
    return avail, probs, counts


def dm_log_likelihood(row: np.ndarray, events: list[dict], source: str, concentration: float) -> float:
    score = 0.0
    for event in events:
        _avail, probs, counts = conditional_probability(row, event, source)
        n = float(counts.sum())
        if n <= 0 or len(probs) < 2:
            continue
        alpha = np.maximum(concentration * probs, 1e-12)
        score += math.lgamma(concentration) - math.lgamma(concentration + n)
        score += math.lgamma(n + 1.0) - sum(math.lgamma(float(y) + 1.0) for y in counts)
        score += sum(math.lgamma(float(a + y)) - math.lgamma(float(a)) for a, y in zip(alpha, counts))
    return float(score)


def fit_row(events: list[dict], source: str) -> dict:
    years = sorted({int(e["election_year"]) for e in events})
    if source == "OTH_IND":
        return {"status": "broad-fallback", "reason": "OTH_IND-is-semantically-heterogeneous", "mean": broad_row(source), "concentration": BROAD_CONCENTRATION, "training_events": len(events), "training_years": years}
    if len(events) < MIN_EVENTS:
        return {"status": "broad-fallback", "reason": f"fewer-than-{MIN_EVENTS}-admissible-events", "mean": broad_row(source), "concentration": BROAD_CONCENTRATION, "training_events": len(events), "training_years": years}
    if len(years) < MIN_ELECTIONS:
        return {"status": "broad-fallback", "reason": f"fewer-than-{MIN_ELECTIONS}-training-elections", "mean": broad_row(source), "concentration": BROAD_CONCENTRATION, "training_events": len(events), "training_years": years}
    try:
        row, fit = fit_attraction(events, source)
    except ValueError as exc:
        return {"status": "broad-fallback", "reason": f"not-identifiable:{exc}", "mean": broad_row(source), "concentration": BROAD_CONCENTRATION, "training_events": len(events), "training_years": years}
    scored = [(c, dm_log_likelihood(row, events, source, float(c))) for c in CONCENTRATION_GRID]
    best = max(value for _, value in scored)
    concentration = min(c for c, value in scored if abs(value - best) <= 1e-8)
    return {
        "status": "empirical-c1",
        "reason": "preregistered-eligibility-passed",
        "mean": [float(x) for x in row],
        "concentration": float(concentration),
        "training_events": len(events),
        "training_years": years,
        "fit": fit,
        "concentration_log_likelihood": {str(c): float(v) for c, v in scored},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    raw = args.evidence.read_bytes()
    evidence = json.loads(raw)
    events = evidence["events"]
    status_counts: dict[str, int] = {}
    excluded_reason_counts: dict[str, int] = {}
    admissible_events = []
    for event in events:
        ok, reason = admissible(event)
        status_counts[event["source_family"]] = status_counts.get(event["source_family"], 0) + 1
        if ok:
            admissible_events.append(event)
        else:
            excluded_reason_counts[reason] = excluded_reason_counts.get(reason, 0) + 1

    target_fits = {}
    for target in TARGETS:
        training = [e for e in admissible_events if int(e["election_year"]) < target]
        rows = {}
        for source in PARTIES:
            source_events = [e for e in training if e["source_family"] == source]
            rows[source] = fit_row(source_events, source)
        target_fits[str(target)] = {
            "training_event_count": len(training),
            "training_years": sorted({int(e["election_year"]) for e in training}),
            "rows": rows,
        }

    payload = {
        "schemaVersion": 1,
        "model": "C1-preregistered-clean-original-parcel-walk-forward",
        "party_order": list(PARTIES),
        "evidence_sha256": sha(raw),
        "guardrails": {
            "historical_final_pair_or_winner_outcomes_loaded": False,
            "uses_2026_forecast_output": False,
            "uses_target_cycle_transfer_events": False,
        },
        "rules": {
            "minimum_events": MIN_EVENTS,
            "minimum_training_elections": MIN_ELECTIONS,
            "OTH_IND_empirical_row_allowed": False,
            "broad_fallback_concentration": BROAD_CONCENTRATION,
            "concentration_grid": list(CONCENTRATION_GRID),
            "multiple_candidates_in_same_destination_family_allowed": False,
            "within_source_family_transfer_allowed": False,
        },
        "evidence_diagnostics": {
            "all_clean_events_by_source_family": dict(sorted(status_counts.items())),
            "admissible_event_count": len(admissible_events),
            "excluded_reason_counts": dict(sorted(excluded_reason_counts.items())),
        },
        "targets": target_fits,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["evidence_diagnostics"], sort_keys=True))
    for target, fit in target_fits.items():
        print(json.dumps({"target": target, "training_event_count": fit["training_event_count"], "training_years": fit["training_years"], "row_status": {p: r["status"] for p, r in fit["rows"].items()}, "row_events": {p: r["training_events"] for p, r in fit["rows"].items()}}, sort_keys=True))
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
