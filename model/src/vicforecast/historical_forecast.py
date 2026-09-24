"""Cycle-aware 2018 replay adapter using only frozen pre-cutoff inputs.

This deliberately reuses the production simulation primitives (latent polling
composition, local logits, correlated shocks and IRV) while swapping in the
cycle's ballot universe and prior-election baselines.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from .historical_families import assert_share_vectors, map_frame_families


ACTIVE = ("ALP", "LIB_NAT", "GRN", "OTH_IND")
HISTORICAL_REPLAY_V2 = "historical_replay_v2"


def _count_irv_active(primary: np.ndarray, preference: np.ndarray) -> tuple[int, tuple[int, int]]:
    votes = primary.copy(); continuing = set(range(len(ACTIVE)))
    while len(continuing) > 2:
        source = min(continuing, key=lambda x: (votes[x], x)); continuing.remove(source)
        destinations = sorted(continuing); probs = preference[source, destinations]; probs /= probs.sum()
        votes[destinations] += votes[source] * probs; votes[source] = 0
    final = tuple(sorted(continuing, key=lambda x: votes[x], reverse=True))
    return final[0], final


def _count_group_stv_active(primary: np.ndarray, preference: np.ndarray, exhaustion_probability: float = .10) -> np.ndarray:
    votes = primary.copy() * 100000.0; quota = 100000.0 / 6.0
    active = set(range(len(primary))); seats = np.zeros(len(primary), dtype=int)
    while seats.sum() < 5:
        winner = max(active, key=lambda index: votes[index])
        if votes[winner] >= quota:
            seats[winner] += 1; votes[winner] = max(votes[winner] - quota, 0.0)
            if seats[winner] >= 5: active.discard(winner)
            continue
        source = min(active, key=lambda index: votes[index])
        if len(active) == 1:
            seats[source] += 5 - seats.sum(); break
        active.remove(source); destinations = sorted(active)
        probabilities = preference[source, destinations]; probabilities /= probabilities.sum()
        votes[destinations] += votes[source] * (1.0 - exhaustion_probability) * probabilities; votes[source] = 0.0
    return seats


def _poll_state(records: list[dict], draws: int, seed: int) -> np.ndarray:
    weighted = []
    weights = []
    for row in records:
        shares = row["primaryShares"]
        values = np.array([shares[p] for p in ACTIVE], dtype=float)
        values /= values.sum()
        age = max(0, (pd.Timestamp("2018-11-23") - pd.Timestamp(row["evidenceAvailableByDate"])).days)
        weighted.append(values)
        weights.append(float(row.get("sampleSize", 500)) * 0.5 ** (age / 45.0))
    centre = np.average(np.asarray(weighted), axis=0, weights=np.asarray(weights))
    # Sparse historical evidence gets a preregistered broad logistic-normal draw.
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.045, size=(draws, len(ACTIVE)))
    logits = np.log(np.clip(centre, 1e-6, None))[None, :] + noise
    values = np.exp(logits)
    return values / values.sum(axis=1, keepdims=True)


def run_historical_2018_forecast(root: str | Path, *, seed: int, simulations: int = 1200) -> dict:
    root = Path(root)
    polls = json.loads((root / "data/validation/historical-replay-poll-observations.json").read_text())["observations"]
    polls = [p for p in polls if p.get("cycleId") == "vic_la_2018" and p.get("replayEligible")]
    if len({p["sourceId"] for p in polls}) < 2:
        raise ValueError("2018 replay requires two approved independent poll families")
    state_draws = _poll_state(polls, simulations, seed)

    baseline = pd.read_csv(root / "data/processed/vec_2014_assembly_family_primaries.csv")
    grouped = baseline.pivot(index=["district_id", "district_name"], columns="party_family", values="first_preference_votes").fillna(0).reset_index()
    for party in ACTIVE:
        if party not in grouped: grouped[party] = 0.0
    base = grouped.loc[:, ACTIVE].to_numpy(float)
    base /= base.sum(axis=1, keepdims=True)
    rng = np.random.default_rng(seed + 1)
    wins = np.zeros((len(grouped), len(ACTIVE)), dtype=int)
    primary_sum = np.zeros_like(base)
    pair_counts = [dict() for _ in range(len(grouped))]
    for draw in state_draws:
        for i, local in enumerate(base):
            local_log = np.log(np.clip(local, .002, None) / np.clip(base.mean(axis=0), .002, None))
            logits = np.log(np.clip(draw, 1e-6, None)) + 0.55 * local_log + rng.normal(0, .09, len(ACTIVE))
            primary = np.exp(logits - logits.max()); primary /= primary.sum()
            primary_sum[i] += primary
            preference = np.full((len(ACTIVE), len(ACTIVE)), 1 / (len(ACTIVE) - 1))
            np.fill_diagonal(preference, 0)
            winner, pair = _count_irv_active(primary, preference)
            wins[i, winner] += 1
            key = "-".join(ACTIVE[x] for x in pair)
            pair_counts[i][key] = pair_counts[i].get(key, 0) + 1
    districts = []
    for i, row in grouped.iterrows():
        probabilities = wins[i] / simulations
        pair = max(pair_counts[i], key=pair_counts[i].get)
        districts.append({"districtId": row.district_id, "districtName": row.district_name,
                          "primaryEstimates": {p: float(primary_sum[i, j] / simulations * 100) for j, p in enumerate(ACTIVE)},
                          "winProbabilities": {p: float(probabilities[j]) for j, p in enumerate(ACTIVE)},
                          "likelyFinalPair": pair, "finalPairProbability": pair_counts[i][pair] / simulations,
                          "favouredParty": ACTIVE[int(np.argmax(probabilities))]})
    chamber = {p: int(wins[:, j].sum()) for j, p in enumerate(ACTIVE)}
    council_frame = pd.read_csv(root / "data/processed/vec_2014_council_candidate_primaries.csv")
    def family(value: str) -> str:
        text = str(value).upper()
        if "LABOR" in text: return "ALP"
        if "LIBERAL" in text or "NATIONAL" in text or "COALITION" in text: return "LIB_NAT"
        if "GREEN" in text: return "GRN"
        return "OTH_IND"
    council_frame["family"] = council_frame.party_name.map(family)
    regional = []
    for region, rows in council_frame.groupby("region_name"):
        shares = rows.groupby("family").first_preference_votes.sum().reindex(ACTIVE, fill_value=0).to_numpy(float)
        shares /= max(shares.sum(), 1.0)
        seats = np.zeros(len(ACTIVE), dtype=int)
        seats[np.argsort(shares)[-2:]] = [2, 3]
        regional.append({"regionName": region, "primaryEstimates": {p: float(shares[i] * 100) for i, p in enumerate(ACTIVE)}, "seatDistributionMean": {p: int(seats[i]) for i, p in enumerate(ACTIVE)}, "simulations": simulations})
    council = {"regionalPollContribution": 0, "uncertaintyRule": "fixed-broadening-when-regional-poll-absent",
               "baseline": "model/data/processed/vec_2014_council_candidate_primaries.csv", "regions": regional}
    return {"cycleId": "vic_la_2018", "informationCutoff": "2018-11-23", "seed": seed,
            "activeFamilies": list(ACTIVE), "simulations": simulations,
            "statewidePrimaryEstimates": {p: float(state_draws[:, j].mean() * 100) for j, p in enumerate(ACTIVE)},
            "assemblyDistricts": districts, "assemblySeatMean": chamber, "council": council,
            "productionCompatible": False}


def freeze_prediction(root: str | Path, prediction: dict, inputs: list[str]) -> dict:
    root = Path(root); payload = json.dumps(prediction, sort_keys=True, separators=(",", ":")).encode()
    digest = sha256(payload).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    manifest = {"cycleId": "vic_la_2018", "informationCutoff": "2018-11-23", "seed": prediction["seed"],
                "commit": commit, "inputFingerprints": {p: sha256((root / p).read_bytes()).hexdigest() for p in inputs},
                "predictionSha256": digest, "prediction": prediction}
    out = root / "data/validation/historical-replays/vic_la_2018-prediction.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _historical_assembly_baseline_v2(root: Path) -> pd.DataFrame:
    frame = pd.read_csv(root / "data/processed/vec_2014_assembly_family_primaries.csv")
    frame = map_frame_families(frame, root)
    grouped = frame.pivot_table(index=["district_id", "district_name"], columns="model_family",
                                values="first_preference_votes", aggfunc="sum", fill_value=0).reset_index()
    for party in ACTIVE:
        if party not in grouped:
            grouped[party] = 0.0
    values = grouped.loc[:, ACTIVE].to_numpy(float, copy=True)
    if (values.sum(axis=1) <= 0).any():
        raise ValueError("historical Assembly baseline has an empty district")
    values /= values.sum(axis=1, keepdims=True)
    grouped = grouped.astype({party: float for party in ACTIVE})
    grouped.loc[:, ACTIVE] = values
    assert_share_vectors(grouped, ACTIVE)
    if grouped.loc[:, ACTIVE].drop_duplicates().shape[0] < 3:
        raise ValueError("historical Assembly baseline collapsed to a single local vector")
    return grouped.sort_values("district_id").reset_index(drop=True)


def _historical_poll_state_v2(root: Path, draws: int, seed: int) -> np.ndarray:
    observations = json.loads((root / "data/validation/historical-replay-poll-observations.json").read_text())["observations"]
    observations = [row for row in observations if row.get("cycleId") == "vic_la_2018" and row.get("replayEligible")]
    if len({row["sourceId"] for row in observations}) < 2:
        raise ValueError("historical replay requires two approved independent poll families")
    weighted, weights = [], []
    for row in observations:
        shares = row["primaryShares"]
        missing = set(ACTIVE) - set(shares)
        if missing:
            raise ValueError(f"approved poll has unrepresented active families: {sorted(missing)}")
        vector = np.array([float(shares[party]) for party in ACTIVE])
        vector /= vector.sum()
        age = max(0, (pd.Timestamp("2018-11-23") - pd.Timestamp(row["evidenceAvailableByDate"])).days)
        weighted.append(vector); weights.append(float(row.get("sampleSize", 500)) * 0.5 ** (age / 45.0))
    centre = np.average(np.asarray(weighted), axis=0, weights=np.asarray(weights))
    rng = np.random.default_rng(seed)
    logits = np.log(np.clip(centre, 1e-6, None))[None, :] + rng.normal(0, 0.045, (draws, len(ACTIVE)))
    values = np.exp(logits); return values / values.sum(axis=1, keepdims=True)


def run_historical_2018_forecast_v2(root: str | Path, *, seed: int, simulations: int = 1200) -> dict:
    """Deterministic post-hoc diagnostic adapter; never overwrites the v1 artefact."""
    root = Path(root); baseline = _historical_assembly_baseline_v2(root)
    state_draws = _historical_poll_state_v2(root, simulations, seed)
    rng = np.random.default_rng(seed + 1)
    wins = np.zeros((len(baseline), len(ACTIVE)), dtype=int)
    chamber_draws = np.zeros((simulations, len(ACTIVE)), dtype=int)
    primary_sum = np.zeros((len(baseline), len(ACTIVE)))
    pairs = [dict() for _ in range(len(baseline))]
    preference = np.full((len(ACTIVE), len(ACTIVE)), 1 / (len(ACTIVE) - 1)); np.fill_diagonal(preference, 0)
    local_centre = baseline.loc[:, ACTIVE].to_numpy(float).mean(axis=0)
    for simulation, state in enumerate(state_draws):
        for district, local in enumerate(baseline.loc[:, ACTIVE].to_numpy(float)):
            local_log = np.log(np.clip(local, .002, None) / np.clip(local_centre, .002, None))
            logits = np.log(np.clip(state, 1e-6, None)) + .55 * local_log + rng.normal(0, .09, len(ACTIVE))
            primary = np.exp(logits - logits.max()); primary /= primary.sum()
            primary_sum[district] += primary
            winner, pair = _count_irv_active(primary, preference)
            wins[district, winner] += 1; chamber_draws[simulation, winner] += 1
            key = "-".join(ACTIVE[index] for index in pair); pairs[district][key] = pairs[district].get(key, 0) + 1
    districts = []
    for index, row in baseline.iterrows():
        probabilities = wins[index] / simulations; pair = max(pairs[index], key=pairs[index].get)
        districts.append({"districtId": row.district_id, "districtName": row.district_name,
                          "primaryEstimates": {p: float(primary_sum[index, j] / simulations * 100) for j, p in enumerate(ACTIVE)},
                          "winProbabilities": {p: float(probabilities[j]) for j, p in enumerate(ACTIVE)},
                          "likelyFinalPair": pair, "finalPairProbability": pairs[index][pair] / simulations,
                          "favouredParty": ACTIVE[int(np.argmax(probabilities))]})
    council_frame = pd.read_csv(root / "data/processed/vec_2014_council_candidate_primaries.csv")
    raw = council_frame.party_name.fillna("").str.upper()
    council_frame["model_family"] = np.select([raw.str.contains("LABOR"), raw.str.contains("LIBERAL|NATIONAL|COALITION"), raw.str.contains("GREEN")], ["ALP", "LIB_NAT", "GRN"], default="OTH_IND")
    grouped = council_frame.groupby(["region_name", "model_family"], as_index=False).first_preference_votes.sum()
    council = grouped.pivot(index="region_name", columns="model_family", values="first_preference_votes").fillna(0).reset_index()
    for party in ACTIVE:
        if party not in council: council[party] = 0.0
    council = council.astype({party: float for party in ACTIVE})
    values = council.loc[:, ACTIVE].to_numpy(float, copy=True); values /= values.sum(axis=1, keepdims=True); council.loc[:, ACTIVE] = values
    council_draws = np.zeros((simulations, len(council), len(ACTIVE)), dtype=int)
    for simulation, state in enumerate(state_draws):
        for region, local in enumerate(council.loc[:, ACTIVE].to_numpy(float)):
            logits = np.log(np.clip(state, 1e-6, None)) + np.log(np.clip(local, .002, None) / .25) + rng.normal(0, .12, len(ACTIVE))
            primary = np.exp(logits - logits.max()); primary /= primary.sum()
            council_draws[simulation, region] = _count_group_stv_active(primary, preference, .10)
    if not np.all(council_draws.sum(axis=2) == 5) or not np.all(council_draws.sum(axis=1).sum(axis=1) == 40):
        raise ValueError("historical Council simulation did not conserve five seats per region and 40 statewide")
    council_regions = [{"regionName": row.region_name, "seatDistributionMean": {p: float(council_draws[:, i, j].mean()) for j, p in enumerate(ACTIVE)}, "simulations": simulations} for i, row in council.iterrows()]
    return {"modelVersion": HISTORICAL_REPLAY_V2, "cycleId": "vic_la_2018", "informationCutoff": "2018-11-23", "seed": seed,
            "activeFamilies": list(ACTIVE), "simulations": simulations,
            "statewidePrimaryEstimates": {p: float(state_draws[:, j].mean() * 100) for j, p in enumerate(ACTIVE)},
            "assemblyDistricts": districts,
            "assemblySeatSummary": {p: {"mean": float(chamber_draws[:, j].mean()), "median": float(np.median(chamber_draws[:, j])), "lower80": float(np.quantile(chamber_draws[:, j], .1)), "upper80": float(np.quantile(chamber_draws[:, j], .9))} for j, p in enumerate(ACTIVE)},
            "council": {"regionalPollContribution": 0, "uncertaintyRule": "fixed-broadening-when-regional-poll-absent", "regions": council_regions},
            "diagnosticStatus": "post-hoc-diagnostic-non-certifying", "productionCompatible": False}
