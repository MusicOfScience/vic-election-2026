"""Registered deterministic 2022 prior-result and uniform-swing comparators.

No forecasts are regenerated; no target-year outcomes are read.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
import numpy as np
from vicforecast.forecast_2026 import PARTIES, PREFERENCE_PRIOR, _count_irv, _count_group_stv
from .governance import read


def rows(root, path):
    with (Path(root) / path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def unavailable(reason):
    return {'status': 'unavailable', 'reason': reason}


def vector(value):
    result = np.array([float(value[p]) for p in PARTIES])
    if not np.isfinite(result).all() or (result < 0).any() or not np.isclose(result.sum(), 100, atol=1e-7):
        raise ValueError('complete five-family percentage vector required')
    return result


def swing(prior, state, baseline):
    value = np.maximum(vector(prior) + vector(state) - vector(baseline), 0)
    if value.sum() <= 0:
        raise ValueError('uniform-swing composition empty after truncation')
    value *= 100 / value.sum()
    return dict(zip(PARTIES, map(float, value)))


def one_hot(winner):
    if winner not in PARTIES:
        raise ValueError('unknown winner family')
    return {p: float(p == winner) for p in PARTIES}


def deterministic_seats(counts):
    return {p: {'mean': float(counts[p]), 'median': float(counts[p]),
                'lower80': float(counts[p]), 'upper80': float(counts[p])} for p in PARTIES}


def build_comparators(root):
    contract = read(root, 'metadata/prospective-validation-input-contract.json')
    mapping = read(root, 'metadata/historical-party-family-mapping.json')['historicalToModel']
    forecast = read(root, 'model/data/processed/experimental_forecast_2026.json')
    current = rows(root, 'model/data/processed/experimental_forecast_2026_districts.csv')
    assembly = defaultdict(dict)
    formal = {}
    for row in rows(root, 'model/data/processed/vec_2022_assembly_family_primaries.csv'):
        # Narracan January 2023 is not a November 2022 general-election prior.
        if row['contest'] != 'general-election':
            continue
        did = row['district_id']; family = mapping[row['party_family']]
        if family in assembly[did]:
            raise ValueError('duplicate prior family')
        assembly[did][family] = float(row['first_preference_votes'])
        formal[did] = float(row['formal_votes'])
    prior = {}
    for did, votes in assembly.items():
        if set(votes) != set(PARTIES) or not np.isclose(sum(votes.values()), formal[did]):
            raise ValueError('official district prior not reconciled')
        prior[did] = {p: 100 * votes[p] / formal[did] for p in PARTIES}
    winners = {r['district_id']: mapping[r['elected_party_family']] for r in rows(root, 'model/data/processed/vec_2022_assembly_final_pairs.csv')}
    assembly_state = {p: sum(assembly[d][p] for d in assembly) / sum(formal.values()) * 100 for p in PARTIES}
    council = defaultdict(lambda: dict.fromkeys(PARTIES, 0.0))
    council_formal, candidate_family = {}, {}
    for row in rows(root, 'model/data/processed/vec_2022_council_candidate_primaries.csv'):
        region = row['region_name'].removesuffix(' Region')
        family = contract['councilPartyToFamily'][row['party_name']]
        council[region][family] += float(row['first_preference_votes'])
        council_formal[region] = float(row['formal_votes'])
        candidate_family[region, row['candidate_name']] = family
    council_prior, elected = {}, {}
    for region, votes in council.items():
        if not np.isclose(sum(votes.values()), council_formal[region]):
            raise ValueError('official regional prior not reconciled')
        council_prior[region] = {p: 100 * votes[p] / council_formal[region] for p in PARTIES}
    for row in read(root, 'model/data/seed/vec_2022_council_validation_targets.json')['regions']:
        counts = dict.fromkeys(PARTIES, 0)
        for name in row['elected_order']:
            counts[candidate_family[row['region_name'], name]] += 1
        if sum(counts.values()) != 5:
            raise ValueError('official prior elected families not reconciled')
        elected[row['region_name']] = counts
    council_state = {p: sum(council[d][p] for d in council) / sum(council_formal.values()) * 100 for p in PARTIES}
    result = {}
    for kind in ('prior_result', 'uniform_swing'):
        districts = {}
        counts = dict.fromkeys(PARTIES, 0)
        for row in current:
            did = row['district_id']
            if did not in prior or did not in winners:
                districts[did] = unavailable('No November 2022 general-election prior/winner mapping; no supplementary substitution.')
                continue
            value = prior[did] if kind == 'prior_result' else swing(prior[did], forecast['polling']['mean'], assembly_state)
            winner = winners[did] if kind == 'prior_result' else PARTIES[_count_irv(vector(value) / 100, PREFERENCE_PRIOR)[0]]
            counts[winner] += 1
            districts[did] = {'status': 'available', 'primary': value, 'probabilities': one_hot(winner), 'winner': winner}
        regions, totals = {}, dict.fromkeys(PARTIES, 0)
        for region in sorted(council_prior):
            value = council_prior[region] if kind == 'prior_result' else swing(council_prior[region], forecast['polling']['mean'], council_state)
            seats = elected[region] if kind == 'prior_result' else dict(zip(PARTIES, map(int, _count_group_stv(vector(value) / 100, PREFERENCE_PRIOR, contract['councilExhaustionProbability']))))
            regions[region] = {'status': 'available', 'primary': value, 'seats': deterministic_seats(seats)}
            for p in PARTIES: totals[p] += seats[p]
        complete = len(districts) == 88 and all(r['status'] == 'available' for r in districts.values())
        result[kind] = {'partyOrder': list(PARTIES), 'assemblyDistricts': districts,
                        'assemblySeats': deterministic_seats(counts) if complete else unavailable('Incomplete district prior: chamber comparator unavailable, not 87-seat chamber.'),
                        'hungProbability': float(max(counts.values()) < 45) if complete else None,
                        'councilRegions': regions, 'councilSeats': deterministic_seats(totals),
                        'baselineStatewide': {'assembly': assembly_state, 'council': council_state},
                        'logLossEpsilon': 1e-12, 'finalPairs': unavailable('Comparator exports no prospective final-pair probabilities.')}
    return result
