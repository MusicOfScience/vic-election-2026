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


# The certifying runner below is deliberately specification-driven.  The older
# 2018 function above remains as the immutable diagnostic compatibility entry
# point; new cycles must use this adapter so cutoff, paths, families and contest
# counts cannot be inherited accidentally from 2018.
def load_historical_cycle_spec(root: str | Path, cycle_id: str) -> dict:
    root = Path(root)
    path = root / "metadata/historical-replay-v2-cycle-specs.json"
    if not path.exists():
        path = root.parent / "metadata/historical-replay-v2-cycle-specs.json"
    specs = json.loads(path.read_text())["cycles"]
    if cycle_id not in specs:
        raise ValueError(f"unknown historical v2 cycle: {cycle_id}")
    spec = dict(specs[cycle_id]); spec["cycleId"] = cycle_id
    return spec


def _cycle_path(root: Path, relative: str) -> Path:
    candidate = root / relative
    return candidate if candidate.exists() else root.parent / relative


def _generic_poll_state(root: Path, spec: dict, draws: int, seed: int) -> np.ndarray:
    payload = json.loads(_cycle_path(root, spec["pollInput"]).read_text())
    rows = [row for row in payload["observations"] if row.get("cycleId") == spec["cycleId"] and row.get("replayEligible")]
    families = spec["activeFamilies"]
    if len(rows) < 3 and spec["cycleId"] == "vic_la_2022":
        raise ValueError("2022 polling requires three approved observations")
    if len({row["sourceId"] for row in rows}) < 2:
        raise ValueError(f"{spec['cycleId']} polling requires two independent source families")
    vectors, weights = [], []
    for row in rows:
        shares = row.get("primaryShares", {})
        if spec["cycleId"] == "vic_la_2022":
            required = ("ALP", "LIB_NAT", "GRN", "OTH_IND")
            if any(name not in shares for name in required):
                raise ValueError("approved 2022 poll is missing a reported grouped residual")
            vector = np.array([float(shares[name]) for name in required], dtype=float)
        else:
            if any(name not in shares for name in families):
                raise ValueError("approved historical poll is missing an active family")
            vector = np.array([float(shares[name]) for name in families], dtype=float)
        if vector.sum() <= 0:
            raise ValueError("historical poll has no positive reported share")
        vector /= vector.sum()
        age = max(0, (pd.Timestamp(spec["informationCutoff"]) - pd.Timestamp(row["evidenceAvailableByDate"])).days)
        vectors.append(vector); weights.append(float(row.get("sampleSize", 500)) * 0.5 ** (age / 45.0))
    centre = np.average(np.asarray(vectors), axis=0, weights=np.asarray(weights))
    rng = np.random.default_rng(seed)
    logits = np.log(np.clip(centre, 1e-6, None))[None, :] + rng.normal(0, 0.045, (draws, len(centre)))
    values = np.exp(logits); return values / values.sum(axis=1, keepdims=True)


def _generic_assembly_inputs(root: Path, spec: dict) -> tuple[pd.DataFrame, list[str]]:
    families = spec["activeFamilies"]
    if spec["cycleId"] == "vic_la_2022":
        frame = pd.read_csv(_cycle_path(root, spec["localInput"]))
        if len(frame) != spec["assemblyContestCount"] or frame.district_name.eq("Narracan").any():
            raise ValueError("2022 local input is not the 87-district November-election universe")
        values = frame[[f"aec_local_{family.lower()}" for family in families]].to_numpy(float)
        if not np.allclose(values.sum(axis=1), 1.0, atol=1e-8): raise ValueError("2022 local family shares do not reconcile")
        frame["_ballot"] = frame.ballot_active_families.fillna("").map(lambda value: set(str(value).split(";")))
        return frame, families
    return _historical_assembly_baseline_v2(root), families


def _generic_council_surface(root: Path, spec: dict, families: list[str]) -> pd.DataFrame:
    if spec["cycleId"] != "vic_la_2022":
        frame = pd.read_csv(_cycle_path(root, spec["councilInput"]))
        raw = frame.party_name.fillna("").str.upper()
        frame["model_family"] = np.select([raw.str.contains("LABOR"), raw.str.contains("LIBERAL|NATIONAL|COALITION"), raw.str.contains("GREEN")], ["ALP", "LIB_NAT", "GRN"], default="OTH_IND")
        grouped = frame.groupby(["region_name", "model_family"], as_index=False).first_preference_votes.sum()
        return grouped.pivot(index="region_name", columns="model_family", values="first_preference_votes").fillna(0).reset_index()
    frame = pd.read_csv(_cycle_path(root, spec["councilInput"]), compression="gzip")
    mapping = {"ALP": "ALP", "GRN": "GRN", "ON": "ONP", "LP": "LIB_NAT", "NP": "LIB_NAT"}
    frame["model_family"] = frame.party_id.map(lambda value: mapping.get(str(value), "OTH_IND"))
    grouped = frame.groupby(["region_name", "model_family"], as_index=False).allocated_ballots.sum()
    result = grouped.pivot(index="region_name", columns="model_family", values="allocated_ballots").fillna(0).reset_index()
    if len(result) != spec["councilRegions"]: raise ValueError("2022 Council surface does not cover eight regions")
    for family in families:
        if family not in result: result[family] = 0.0
    return result


def run_historical_forecast_v2(root: str | Path, cycle_id: str, *, seed: int | None = None, simulations: int | None = None) -> dict:
    """Run the same v2 simulation architecture from a frozen cycle contract."""
    root = Path(root); spec = load_historical_cycle_spec(root, cycle_id)
    seed = spec["seed"] if seed is None else seed; simulations = spec["simulations"] if simulations is None else simulations
    families = list(spec["activeFamilies"]); state_draws = _generic_poll_state(root, spec, simulations, seed)
    local, _ = _generic_assembly_inputs(root, spec)
    if cycle_id == "vic_la_2022":
        local_values = local[[f"aec_local_{family.lower()}" for family in families]].to_numpy(float)
    else:
        local_values = local.loc[:, families].to_numpy(float)
    local_centre = local_values.mean(axis=0); rng = np.random.default_rng(seed + 1)
    n_districts = len(local_values); n_families = len(families)
    wins = np.zeros((n_districts, n_families), dtype=int); chamber = np.zeros((simulations, n_families), dtype=int)
    primary_sum = np.zeros((n_districts, n_families)); pairs = [dict() for _ in range(n_districts)]
    preference = np.full((n_families, n_families), 1 / max(n_families - 1, 1)); np.fill_diagonal(preference, 0)
    for sim, state in enumerate(state_draws):
        if cycle_id == "vic_la_2022":
            poll = np.zeros(n_families); poll[:3] = state[:3]
        for district, local_vector in enumerate(local_values):
            if cycle_id == "vic_la_2022":
                ballot = local.iloc[district]["_ballot"]
                residual = state[3]
                onp_ratio = local_vector[3] / max(local_vector[3] + local_vector[4], 1e-12)
                poll[3] = residual * onp_ratio if "ONP" in ballot else 0.0
                poll[4] = residual - poll[3]
                poll = poll * np.array([1.0 if family in ballot else 0.0 for family in families])
                if poll.sum() <= 0: raise ValueError("ballot availability removed all 2022 poll mass")
                poll /= poll.sum()
            else:
                poll = state
            local_log = np.log(np.clip(local_vector, .002, None) / np.clip(local_centre, .002, None))
            logits = np.log(np.clip(poll, 1e-6, None)) + .55 * local_log + rng.normal(0, .09, n_families)
            primary = np.exp(logits - logits.max()); primary /= primary.sum()
            if cycle_id == "vic_la_2022":
                primary *= np.array([1.0 if family in ballot else 0.0 for family in families])
                primary /= primary.sum()
            primary_sum[district] += primary
            winner, pair = _count_irv_generic(primary, preference); wins[district, winner] += 1; chamber[sim, winner] += 1
            key = "-".join(families[index] for index in pair); pairs[district][key] = pairs[district].get(key, 0) + 1
    districts = []
    for index, row in local.reset_index(drop=True).iterrows():
        probabilities = wins[index] / simulations; pair = max(pairs[index], key=pairs[index].get)
        districts.append({"districtId": row.district_id, "districtName": row.district_name, "primaryEstimates": {p: float(primary_sum[index, j] / simulations * 100) for j, p in enumerate(families)}, "winProbabilities": {p: float(probabilities[j]) for j, p in enumerate(families)}, "likelyFinalPair": pair, "finalPairProbability": pairs[index][pair] / simulations, "favouredParty": families[int(np.argmax(probabilities))]})
    council_frame = _generic_council_surface(root, spec, families); council_draws = np.zeros((simulations, len(council_frame), n_families), dtype=int)
    for sim, state in enumerate(state_draws):
        state5 = np.pad(state, (0, n_families - len(state)), constant_values=0) if len(state) < n_families else state
        if cycle_id == "vic_la_2022":
            residual = state[3]; state5[4] = residual * .75; state5[3] = residual * .25
        state5 = state5 / state5.sum()
        for region, row in enumerate(council_frame.iterrows()):
            local_vector = row[1][families].to_numpy(float); local_vector /= max(local_vector.sum(), 1.0)
            logits = np.log(np.clip(state5, 1e-6, None)) + np.log(np.clip(local_vector, .002, None) / max(local_vector.mean(), .002)) + rng.normal(0, .12, n_families)
            primary = np.exp(logits - logits.max()); primary /= primary.sum(); council_draws[sim, region] = _count_group_stv_generic(primary, preference, .15)
    if not np.all(council_draws.sum(axis=2) == 5) or not np.all(council_draws.sum(axis=1).sum(axis=1) == 40): raise ValueError("Council simulation did not conserve 5 seats per region and 40 statewide")
    council_regions = [{"regionName": row.region_name, "seatDistributionMean": {p: float(council_draws[:, i, j].mean()) for j, p in enumerate(families)}, "simulations": simulations} for i, row in council_frame.iterrows()]
    return {"modelVersion": HISTORICAL_REPLAY_V2, "cycleId": cycle_id, "informationCutoff": spec["informationCutoff"], "seed": seed, "activeFamilies": families, "simulations": simulations, "pollObservationState": {"buckets": ["ALP", "LIB_NAT", "GRN", "OTH_RESIDUAL"] if cycle_id == "vic_la_2022" else families, "unreportedFamilies": ["ONP"] if cycle_id == "vic_la_2022" else [], "residualDecomposition": spec.get("groupedResidualRule", "none")}, "statewidePrimaryEstimates": {p: float(state_draws[:, j].mean() * 100) for j, p in enumerate((['ALP', 'LIB_NAT', 'GRN', 'OTH_IND'] if cycle_id == 'vic_la_2022' else families))}, "assemblyDistricts": districts, "assemblySeatSummary": {p: {"mean": float(chamber[:, j].mean()), "median": float(np.median(chamber[:, j])), "lower80": float(np.quantile(chamber[:, j], .1)), "upper80": float(np.quantile(chamber[:, j], .9))} for j, p in enumerate(families)}, "council": {"regionalPollContribution": 0, "uncertaintyRule": "fixed-broadening-when-regional-poll-absent", "regions": council_regions}, "certificationStatus": "held-out-certifying-prediction-frozen" if cycle_id == "vic_la_2022" else "diagnostic", "productionCompatible": False}


def _count_irv_generic(primary: np.ndarray, preference: np.ndarray) -> tuple[int, tuple[int, int]]:
    votes = primary.copy(); continuing = set(range(len(primary)))
    while len(continuing) > 2:
        source = min(continuing, key=lambda index: (votes[index], index)); continuing.remove(source); destinations = sorted(continuing)
        probs = preference[source, destinations]; probs = probs / probs.sum(); votes[destinations] += votes[source] * probs; votes[source] = 0
    final = tuple(sorted(continuing, key=lambda index: votes[index], reverse=True)); return final[0], final


def _count_group_stv_generic(primary: np.ndarray, preference: np.ndarray, exhaustion_probability: float) -> np.ndarray:
    votes = primary.copy() * 100000.0; quota = 100000.0 / 6.0; active = set(range(len(primary))); seats = np.zeros(len(primary), dtype=int)
    while seats.sum() < 5:
        winner = max(active, key=lambda index: votes[index])
        if votes[winner] >= quota:
            seats[winner] += 1; votes[winner] = max(votes[winner] - quota, 0.0)
            if seats[winner] >= 5: active.discard(winner)
            continue
        source = min(active, key=lambda index: votes[index])
        if len(active) == 1: seats[source] += 5 - seats.sum(); break
        active.remove(source); destinations = sorted(active); probs = preference[source, destinations]; probs = probs / probs.sum(); votes[destinations] += votes[source] * (1 - exhaustion_probability) * probs; votes[source] = 0
    return seats
