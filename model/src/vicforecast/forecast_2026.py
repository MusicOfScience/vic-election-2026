"""End-to-end experimental 2026 Victorian election forecast.

This module connects the project's audited evidence to a reproducible joint
simulation. It is deliberately labelled experimental: the sealed demographic
ridge challenger failed promotion and therefore receives zero central weight.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

import numpy as np
import pandas as pd
import yaml

from .polling.latent import LatentPollState, fit_latent_poll_state


PARTIES = ("ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND")
ASSEMBLY_2022_TARGET = np.array([37.03, 34.37, 0.22, 11.50, 16.88])
COUNCIL_2022_TARGET = np.array([33.01, 29.44, 2.04, 10.32, 25.19])

# Rows are the excluded party; columns are the next available party family.
# These are documented priors, varied in every simulation, not asserted facts.
PREFERENCE_PRIOR = np.array([
    [0.00, 0.39, 0.14, 0.34, 0.13],
    [0.26, 0.00, 0.51, 0.07, 0.16],
    [0.22, 0.48, 0.00, 0.04, 0.26],
    [0.72, 0.09, 0.04, 0.00, 0.15],
    [0.30, 0.26, 0.31, 0.13, 0.00],
])


@dataclass(frozen=True)
class ExperimentalForecast:
    poll_state: LatentPollState
    poll_sensitivity: dict[str, dict[str, float]]
    assumptions: dict
    districts: pd.DataFrame
    chamber: pd.DataFrame
    seat_distribution: pd.DataFrame
    council_regions: pd.DataFrame
    council: pd.DataFrame
    simulations: int
    seed: int
    production_compatible: bool = False


def load_forecast_config(root: str | Path) -> dict:
    path = Path(root) / "config/experimental_forecast.yml"
    config = yaml.safe_load(path.read_text())
    required = {"as_of", "election_date", "polling", "assembly", "council"}
    if not isinstance(config, dict) or not required.issubset(config):
        raise ValueError(f"forecast config is missing required keys: {sorted(required)}")
    return config


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _family(value: str | None) -> str:
    value = "" if value is None else str(value).upper()
    if value in {"ALP"} or "LABOR" in value:
        return "ALP"
    if value in {"LP", "LIB", "NP", "NAT", "LIB_NAT"} or "LIBERAL" in value or "NATIONAL" in value:
        return "LIB_NAT"
    if value in {"ON", "ONP"} or "ONE NATION" in value:
        return "ONP"
    if value in {"GRN"} or "GREEN" in value:
        return "GRN"
    return "OTH_IND"


def _rake(frame: pd.DataFrame, targets: np.ndarray, weights: np.ndarray) -> pd.DataFrame:
    values = np.clip(frame.loc[:, PARTIES].to_numpy(float), 0.002, None)
    values /= values.sum(axis=1, keepdims=True)
    weights = weights / weights.sum()
    target = targets / targets.sum()
    for _ in range(100):
        current = (values * weights[:, None]).sum(axis=0)
        values *= target / np.clip(current, 1e-9, None)
        values /= values.sum(axis=1, keepdims=True)
    out = frame.copy()
    out.loc[:, PARTIES] = values
    return out


def build_assembly_seed(root: str | Path, config: dict | None = None) -> pd.DataFrame:
    root = Path(root)
    config = config or load_forecast_config(root)
    assembly = config["assembly"]
    surface = pd.read_csv(root / "data/processed/aec_2022_state_district_party_surface_vic.csv.gz")
    surface["family"] = surface.party_id.map(_family)
    surface = surface[surface.party_id.ne("INFORMAL")]
    grouped = surface.groupby(["district_id", "district_name", "family"], as_index=False).allocated_ballots.sum()
    pivot = grouped.pivot(index=["district_id", "district_name"], columns="family", values="allocated_ballots").fillna(0).reset_index()
    for party in PARTIES:
        if party not in pivot:
            pivot[party] = 0.0
    raw = pivot.loc[:, PARTIES].to_numpy(float)
    raw /= raw.sum(axis=1, keepdims=True)
    state = raw.mean(axis=0)
    pivot["onp_local_log"] = np.clip(np.log(np.clip(raw[:, 2], .004, None) / max(state[2], .004)), -1.20, 1.10)
    # Shrink an auxiliary federal-to-state surface toward the official VEC
    # statewide anchor before incorporating direct district evidence.
    local = np.log(np.clip(raw, .002, None)) - np.log(np.clip(state, .002, None))
    pivot.loc[:, PARTIES] = np.exp(np.log(ASSEMBLY_2022_TARGET / 100) + float(assembly["aec_local_pattern_shrinkage"]) * local)
    pivot.loc[:, PARTIES] = pivot.loc[:, PARTIES].div(pivot.loc[:, PARTIES].sum(axis=1), axis=0)

    evidence = pd.read_csv(root / "data/processed/vec_2022_indicative_candidate_evidence.csv")
    evidence["family"] = evidence.party_id.map(_family)
    direct = evidence.groupby(["district_id", "family"], as_index=False).result_page_primary_votes.sum()
    totals = direct.groupby("district_id").result_page_primary_votes.transform("sum")
    direct["share"] = direct.result_page_primary_votes / totals
    direct = direct.pivot(index="district_id", columns="family", values="share").fillna(0)
    for i, row in pivot.iterrows():
        did = row.district_id
        if did not in direct.index:
            continue
        observed = np.array([direct.loc[did].get(p, 0.0) for p in PARTIES])
        observed = np.maximum(observed, .002)
        observed /= observed.sum()
        auxiliary = pivot.loc[i, list(PARTIES)].to_numpy(float)
        direct_weight = float(assembly["direct_district_evidence_weight"])
        blended = direct_weight * observed + (1.0 - direct_weight) * auxiliary
        pivot.loc[i, list(PARTIES)] = blended / blended.sum()

    enrol = pd.read_csv(root / "data/processed/vec_enrolment_district_2026-06.csv")
    weights = dict(zip(enrol.geography_name.map(_slug), enrol.enrolled_electors))
    pivot["enrolled_electors"] = pivot.district_id.map(weights).fillna(enrol.enrolled_electors.mean())
    pivot = _rake(pivot, ASSEMBLY_2022_TARGET, pivot.enrolled_electors.to_numpy(float))
    membership = pd.read_csv(root / "data/processed/district_region_membership_2026.csv")
    pivot = pivot.merge(membership[["district_name", "region_name"]], on="district_name", how="left")
    return pivot.sort_values("district_name").reset_index(drop=True)


def build_council_seed(root: str | Path) -> pd.DataFrame:
    root = Path(root)
    surface = pd.read_csv(root / "data/processed/aec_2022_state_region_party_surface_vic.csv.gz")
    surface = surface[surface.party_id.ne("INFORMAL")].copy()
    surface["family"] = surface.party_id.map(_family)
    grouped = surface.groupby(["region_name", "family"], as_index=False).allocated_ballots.sum()
    pivot = grouped.pivot(index="region_name", columns="family", values="allocated_ballots").fillna(0).reset_index()
    for p in PARTIES:
        if p not in pivot:
            pivot[p] = 0.0
    vals = pivot.loc[:, PARTIES].to_numpy(float)
    vals /= vals.sum(axis=1, keepdims=True)
    state = vals.mean(axis=0)
    local = np.log(np.clip(vals, .002, None)) - np.log(np.clip(state, .002, None))
    pivot.loc[:, PARTIES] = np.exp(np.log(COUNCIL_2022_TARGET / 100) + .55 * local)
    pivot.loc[:, PARTIES] = pivot.loc[:, PARTIES].div(pivot.loc[:, PARTIES].sum(axis=1), axis=0)
    enrol = pd.read_csv(root / "data/processed/vec_enrolment_region_2026-06.csv")
    weights = dict(zip(enrol.geography_name, enrol.enrolled_electors))
    pivot["enrolled_electors"] = pivot.region_name.map(weights)
    pivot["region_id"] = pivot.region_name.map(_slug)
    return _rake(pivot, COUNCIL_2022_TARGET, pivot.enrolled_electors.to_numpy(float))


def _count_irv(primary: np.ndarray, preference: np.ndarray) -> tuple[int, tuple[int, int]]:
    votes = primary.copy()
    continuing = set(range(len(PARTIES)))
    while len(continuing) > 2:
        source = min(continuing, key=lambda x: (votes[x], x))
        continuing.remove(source)
        destinations = sorted(continuing)
        probs = preference[source, destinations]
        probs = probs / probs.sum()
        votes[destinations] += votes[source] * probs
        votes[source] = 0.0
    final = tuple(sorted(continuing, key=lambda x: votes[x], reverse=True))
    return final[0], final


def _count_group_stv(primary: np.ndarray, preference: np.ndarray) -> np.ndarray:
    """Five-member voter-directed group STV approximation.

    It models party-group vote pools and voter-directed transfers, including
    10% exhaustion. It is not a candidate-order claim.
    """
    votes = primary.copy() * 100000.0
    quota = 100000.0 / 6.0
    active = set(range(len(PARTIES)))
    seats = np.zeros(len(PARTIES), dtype=int)
    while seats.sum() < 5:
        winner = max(active, key=lambda x: votes[x])
        if votes[winner] >= quota:
            seats[winner] += 1
            surplus = max(votes[winner] - quota, 0.0)
            votes[winner] = surplus
            if seats[winner] >= 5:
                active.discard(winner)
            continue
        source = min(active, key=lambda x: votes[x])
        if len(active) == 1:
            seats[source] += 5 - seats.sum()
            break
        active.remove(source)
        dest = sorted(active)
        probs = preference[source, dest]
        probs = probs / probs.sum()
        votes[dest] += votes[source] * .90 * probs
        votes[source] = 0.0
    return seats


def _summary(values: np.ndarray) -> tuple[float, float, float, float]:
    return (float(values.mean()), float(np.median(values)), float(np.quantile(values, .1)), float(np.quantile(values, .9)))


def run_experimental_forecast(root: str | Path, *, simulations: int = 5000, seed: int = 20260826) -> ExperimentalForecast:
    root = Path(root)
    config = load_forecast_config(root)
    polling = config["polling"]
    assembly = config["assembly"]
    events = pd.read_csv(root / "data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(root / "data/processed/poll_estimates_seed.csv")
    poll = fit_latent_poll_state(
        events, estimates, as_of=config["as_of"], draws=simulations, seed=seed,
        half_life_days=float(polling["half_life_days"]),
        effective_sample_cap=int(polling["effective_sample_cap"]),
        systematic_floor=float(polling["systematic_floor"]),
    )
    sensitivity: dict[str, dict[str, float]] = {}
    for half_life in (21, int(polling["half_life_days"]), 90):
        if half_life == int(polling["half_life_days"]):
            sensitivity[str(half_life)] = poll.mean
            continue
        fitted = fit_latent_poll_state(
            events, estimates, as_of=config["as_of"], draws=min(max(simulations, 1000), 2000),
            seed=seed + half_life, half_life_days=half_life,
            effective_sample_cap=int(polling["effective_sample_cap"]),
            systematic_floor=float(polling["systematic_floor"]),
        )
        sensitivity[str(half_life)] = fitted.mean
    districts = build_assembly_seed(root, config)
    council_seed = build_council_seed(root)
    rng = np.random.default_rng(seed + 1)
    baseline_state = ASSEMBLY_2022_TARGET / 100.0
    wins = np.zeros((len(districts), len(PARTIES)), int)
    primary_sum = np.zeros_like(wins, float)
    pairs: list[dict[str, int]] = [dict() for _ in range(len(districts))]
    chamber_draws = np.zeros((simulations, len(PARTIES)), int)

    # By-election evidence is a small, time-decayed local incumbency signal.
    boosts = np.zeros((len(districts), len(PARTIES)))
    by_path = root / "data/seed/recent_state_by_elections.json"
    if by_path.exists():
        by = json.loads(by_path.read_text())["events"]
        index = {name: i for i, name in enumerate(districts.district_name)}
        for event in by:
            if event["district"] not in index:
                continue
            age = (pd.Timestamp(config["election_date"]) - pd.Timestamp(event["date"])).days
            strength = float(assembly["by_election_max_logit_boost"]) * np.exp(-age / float(assembly["by_election_decay_days"]))
            boosts[index[event["district"]], PARTIES.index(_family(event.get("elected_party_raw")))] += strength

    region_names = sorted(districts.region_name.dropna().unique())
    region_index = {name: i for i, name in enumerate(region_names)}
    district_regions = np.array([region_index.get(x, 0) for x in districts.region_name])
    base = districts.loc[:, PARTIES].to_numpy(float)
    local_pattern = np.log(np.clip(base, .002, None) / baseline_state)
    # The 2022 One Nation state result reflected very sparse contest coverage.
    # Its 2026 statewide rise must not be multiplied by that ballot-access
    # artefact. Preserve broad local tendency, but shrink the extreme ratios.
    local_limits = np.array([float(assembly["local_logit_limits"][party]) for party in PARTIES])
    local_pattern = np.clip(local_pattern, -local_limits, local_limits)
    # Unlike the sparse 2022 state ballot, the federal ecological surface gives
    # statewide contest coverage for One Nation's geographic propensity.
    local_pattern[:, 2] = districts.onp_local_log.to_numpy(float)
    greens_limit = float(assembly["greens_local_logit_limit"])
    local_pattern[:, 3] = np.clip(local_pattern[:, 3] * float(assembly["greens_local_pattern_multiplier"]), -greens_limit, greens_limit)
    for s in range(simulations):
        state = poll.draws[s] / 100.0
        region_shock = rng.normal(0, float(assembly["region_shock_sd"]), size=(len(region_names), len(PARTIES)))
        local_shock = rng.normal(0, float(assembly["district_shock_sd"]), size=(len(districts), len(PARTIES)))
        logits = np.log(np.clip(state, 1e-6, None)) + local_pattern + region_shock[district_regions] + local_shock + boosts
        primaries = np.exp(logits - logits.max(axis=1, keepdims=True))
        primaries /= primaries.sum(axis=1, keepdims=True)
        primary_sum += primaries
        pref = np.vstack([rng.dirichlet(np.maximum(row * float(assembly["preference_prior_concentration"]), .02)) for row in PREFERENCE_PRIOR])
        for d in range(len(districts)):
            winner, pair = _count_irv(primaries[d], pref)
            wins[d, winner] += 1
            chamber_draws[s, winner] += 1
            label = "–".join(PARTIES[x] for x in pair)
            pairs[d][label] = pairs[d].get(label, 0) + 1

    district_rows = []
    for i, row in districts.iterrows():
        pair = max(pairs[i], key=pairs[i].get)
        probabilities = wins[i] / simulations
        positive = probabilities[probabilities > 0]
        entropy = float(-(positive * np.log(positive)).sum())
        item = {"district_id": row.district_id, "district_name": row.district_name, "region_name": row.region_name,
                "likely_final_pair": pair, "final_pair_probability": pairs[i][pair] / simulations,
                "effective_contenders": float(np.exp(entropy)),
                "competitive_parties": int((probabilities >= .10).sum()),
                "win_entropy": entropy / np.log(len(PARTIES)),
                "by_election_signal_party": PARTIES[int(np.argmax(boosts[i]))] if boosts[i].max() > 0 else "",
                "by_election_signal_strength": float(boosts[i].max())}
        for j, party in enumerate(PARTIES):
            forecast_primary = primary_sum[i, j] / simulations * 100.0
            baseline_primary = float(row[party]) * 100.0
            item[f"win_{party.lower()}"] = probabilities[j]
            item[f"primary_{party.lower()}"] = forecast_primary
            item[f"baseline_{party.lower()}"] = baseline_primary
            item[f"change_{party.lower()}"] = forecast_primary - baseline_primary
        item["favoured_party"] = PARTIES[int(np.argmax(wins[i]))]
        item["favoured_probability"] = float(wins[i].max() / simulations)
        district_rows.append(item)

    chamber_rows = []
    for j, party in enumerate(PARTIES):
        mean, median, low, high = _summary(chamber_draws[:, j])
        chamber_rows.append({"party": party, "mean": mean, "median": median, "lower80": low, "upper80": high,
                             "majority_probability": float((chamber_draws[:, j] >= 45).mean())})
    hung = 1.0 - float((chamber_draws.max(axis=1) >= 45).mean())
    chamber = pd.DataFrame(chamber_rows)
    chamber["hung_probability"] = hung
    seat_dist = pd.DataFrame({"seats": np.arange(89), "probability": [float((chamber_draws[:, 0] == x).mean()) for x in range(89)]})

    # Council uses the same statewide latent draw but a separate regional model
    # and voter-directed five-member counting process.
    council_draws = np.zeros((simulations, len(council_seed), len(PARTIES)), int)
    cbase = council_seed.loc[:, PARTIES].to_numpy(float)
    council_anchor = COUNCIL_2022_TARGET / 100.0
    council_local = np.log(np.clip(cbase, .002, None) / council_anchor)
    council_local = np.clip(council_local, -np.array([.8, .8, .4, .8, .8]), np.array([.8, .8, .4, .8, .8]))
    for s in range(simulations):
        state = poll.draws[s] / 100.0
        pref = np.vstack([rng.dirichlet(np.maximum(row * 42.0, .02)) for row in PREFERENCE_PRIOR])
        for r in range(len(council_seed)):
            logits = np.log(np.clip(state, 1e-6, None)) + council_local[r] + rng.normal(0, .10, len(PARTIES))
            primary = np.exp(logits - logits.max()); primary /= primary.sum()
            council_draws[s, r] = _count_group_stv(primary, pref)
    council_region_rows = []
    for r, row in council_seed.iterrows():
        patterns, counts = np.unique(council_draws[:, r, :], axis=0, return_counts=True)
        modal = patterns[counts.argmax()]
        item = {"region_id": row.region_id, "region_name": row.region_name,
                "modal_probability": float(counts.max() / simulations)}
        for j, party in enumerate(PARTIES):
            item[f"seats_{party.lower()}"] = int(modal[j])
            item[f"mean_{party.lower()}"] = float(council_draws[:, r, j].mean())
        council_region_rows.append(item)
    total_council = council_draws.sum(axis=1)
    council_rows = []
    for j, party in enumerate(PARTIES):
        mean, median, low, high = _summary(total_council[:, j])
        council_rows.append({"party": party, "mean": mean, "median": median, "lower80": low, "upper80": high})
    return ExperimentalForecast(poll, sensitivity, config, pd.DataFrame(district_rows), chamber, seat_dist,
                                pd.DataFrame(council_region_rows), pd.DataFrame(council_rows), simulations, seed)
