"""Frozen descriptive scoring primitives and fail-closed future scoring entry.

Only synthetic unit tests invoke the pure arithmetic below in this batch.
The registered entry checks governance before opening any target file.
"""
from __future__ import annotations
import math
from datetime import datetime, timezone
import numpy as np
from vicforecast.forecast_2026 import PARTIES
from vicforecast.validation_metrics import reliability_bins
from .comparators import unavailable, vector
from .governance import read, instant, material_rules, canonical, digest, APPROVED_RULES_SHA256

EPSILON = 1e-12


def binary_scores(probability, observed):
    p = float(probability)
    if not math.isfinite(p) or not 0 <= p <= 1 or observed not in (0, 1):
        raise ValueError('invalid binary event')
    q = p if observed else 1-p
    return {'brier': (p-observed)**2, 'logLoss': -math.log(max(EPSILON, min(1-EPSILON, q))),
            'zeroProbabilityEvents': int(q == 0), 'clippedEvents': int(q < EPSILON or q > 1-EPSILON)}


def seat_metrics(prediction, outcome):
    if prediction.get('status') == 'unavailable':
        return prediction
    result = {}
    for p in PARTIES:
        if p not in prediction or p not in outcome:
            result[p] = unavailable('Missing sealed family summary or official seat outcome.')
            continue
        v, y = prediction[p], float(outcome[p])
        if not math.isfinite(y) or y < 0 or y != int(y):
            raise ValueError('invalid observed seats')
        item = {}
        for key in ('mean', 'median'):
            item[key+'AbsoluteError'] = abs(float(v[key])-y) if key in v else unavailable('Summary not exported.')
        if 'lower80' in v and 'upper80' in v:
            lo, hi = float(v['lower80']), float(v['upper80'])
            if not math.isfinite(lo+hi) or lo > hi:
                raise ValueError('invalid interval bounds')
            item.update(coverage80=int(lo <= y <= hi), width80=hi-lo)
        else:
            item['interval80'] = unavailable('Regional interval bounds not exported prospectively.')
        result[p] = item
    return result


def evaluate_predictions(prediction, outcome):
    """Pure arithmetic; not a governed scoring action or release decision."""
    district_scores, missing = [], []
    primaries, state_weights, observed_state, predicted_state = [], [], [], []
    probs, labels, pair_scores = [], [], []
    districts = prediction['assemblyDistricts']
    if set(districts) != set(outcome['assemblyDistricts']):
        raise ValueError('wrong district target universe')
    for did, pred in districts.items():
        actual = outcome['assemblyDistricts'][did]
        if pred.get('status') == 'unavailable' or actual.get('status') == 'unavailable':
            missing.append({'districtId': did, 'reason': pred.get('reason') or actual.get('reason')})
            continue
        p = np.array([pred['probabilities'][family] for family in PARTIES], float)
        if not np.isfinite(p).all() or (p < 0).any() or not np.isclose(p.sum(), 1):
            raise ValueError('invalid district probability vector')
        winner = actual['winner']; i = PARTIES.index(winner)
        y = np.eye(len(PARTIES))[i]; q = p[i]
        district_scores.append({'brier': float(((p-y)**2).sum()), 'logLoss': -math.log(max(EPSILON, min(1-EPSILON, q))),
                                'correct': int(PARTIES[int(p.argmax())] == winner),
                                'zero': int(q == 0), 'clipped': int(q < EPSILON or q > 1-EPSILON)})
        predicted = vector(pred['primary']); observed = vector(actual['primary'])
        primaries.extend(abs(predicted-observed).tolist())
        formal = float(actual['formalVotes'])
        if not math.isfinite(formal) or formal <= 0:
            raise ValueError('official formal-vote weight required')
        state_weights.append(formal); observed_state.append(observed); predicted_state.append(predicted)
        probs.extend(p); labels.extend(y)
        if pred.get('finalPair') and actual.get('finalPair'):
            # Ordered winner-runner label, matching the exact engine's exported event.
            pair_scores.append(binary_scores(pred['finalPair']['probability'], int(pred['finalPair']['label'] == actual['finalPair'])))
    n = len(district_scores)
    assembly = unavailable('No valid district targets.') if not n else {
        'denominator': n, 'missing': missing,
        'multiclassBrier': float(np.mean([v['brier'] for v in district_scores])),
        'logLoss': float(np.mean([v['logLoss'] for v in district_scores])),
        'winnerAccuracy': float(np.mean([v['correct'] for v in district_scores])),
        'zeroProbabilityEvents': sum(v['zero'] for v in district_scores),
        'clippedEvents': sum(v['clipped'] for v in district_scores),
        'districtFamilyPrimaryMae': float(np.mean(primaries)), 'primaryCellDenominator': len(primaries),
        'reliability': reliability_bins(probs, labels, bins=10), 'reliabilityElectionCount': 1,
    }
    if n and not missing:
        obs = np.average(observed_state, axis=0, weights=state_weights)
        estimated = np.average(predicted_state, axis=0, weights=state_weights)
        assembly['statewide'] = {'observed': dict(zip(PARTIES, map(float, obs))),
                                 'predicted': dict(zip(PARTIES, map(float, estimated))),
                                 'errors': dict(zip(PARTIES, map(float, estimated-obs))),
                                 'mae': float(abs(estimated-obs).mean()), 'formalVotes': sum(state_weights)}
    elif n:
        assembly['statewide'] = unavailable('Incomplete district universe; no partial state presented as statewide.')
    if set(prediction['councilRegions']) != set(outcome['councilRegions']):
        raise ValueError('wrong Council target universe')
    council, regional_primary = {}, []
    for region, pred in prediction['councilRegions'].items():
        actual = outcome['councilRegions'][region]
        if pred.get('status') == 'unavailable' or actual.get('status') == 'unavailable':
            council[region] = unavailable(pred.get('reason') or actual.get('reason')); continue
        errs = abs(vector(pred['primary'])-vector(actual['primary']))
        regional_primary.extend(errs)
        council[region] = {'primaryMae': float(errs.mean()), 'seats': seat_metrics(pred['seats'], actual['seats'])}
    complete_targets = all(v.get('status') != 'unavailable' for v in outcome['assemblyDistricts'].values())
    return {'descriptiveOnly': True, 'independentElectionCount': 1, 'productionAuthorised': False,
            'assembly': assembly,
            'assemblySeats': seat_metrics(prediction['assemblySeats'], outcome['assemblySeats']) if complete_targets else unavailable('Incomplete official Assembly universe.'),
            'hung': binary_scores(prediction['hungProbability'], int(max(outcome['assemblySeats'].values()) < 45)) if complete_targets and prediction.get('hungProbability') is not None else unavailable('Hung event not exported or incomplete targets.'),
            'councilRegions': council, 'councilRegionalFamilyPrimaryMae': float(np.mean(regional_primary)) if regional_primary else unavailable('No regional metrics.'),
            'councilPrimaryCellDenominator': len(regional_primary), 'councilSeats': seat_metrics(prediction['councilSeats'], outcome['councilSeats']) if all(v.get('status') != 'unavailable' for v in outcome['councilRegions'].values()) else unavailable('Incomplete official Council universe.'),
            'finalPairs': {'denominator': len(pair_scores), 'brier': float(np.mean([s['brier'] for s in pair_scores])), 'logLoss': float(np.mean([s['logLoss'] for s in pair_scores]))} if pair_scores else unavailable('No sealed pair probability and corresponding official pair; conditional preference metrics not exported.')}


def validate_scorer_readiness(package, action, *, governance_root=None):
    from .package import verify_package
    manifest = verify_package(package)
    protocol = read(package, 'archive/metadata/model-vnext-validation-protocol.json')
    approval = read(package, 'archive/metadata/prospective-validation-approval.json')
    # An immutable pre-election archive records scoringAuthorised=false forever.
    # A future explicit action may use a separately governed operational copy;
    # it must preserve the approved methodological projection and owner receipt.
    if governance_root is not None:
        current = read(governance_root, 'metadata/model-vnext-validation-protocol.json')
        current_approval = read(governance_root, 'metadata/prospective-validation-approval.json')
        if digest(canonical(material_rules(current))) != APPROVED_RULES_SHA256 or current_approval != approval or current.get('approval') != approval:
            raise ValueError('future scoring governance changed approved methodological rules')
        protocol = current
    if protocol['status'] != 'approved-awaiting-registration-seal' or approval['decision'] != 'approved':
        raise ValueError('approved protocol required')
    if manifest['kind'] != 'prospective-live' or not manifest['registered']:
        raise ValueError('fixture/unsealed forecast is not empirical evidence')
    if not protocol['scoringAuthorised']:
        raise ValueError('scoringAuthorised=false; outcome loader remains closed')
    if action.get('decision') != 'authorise-scoring' or action.get('reviewerRole') != 'project-owner':
        raise ValueError('explicit scoring action required')
    if action.get('manifestSha256') != manifest['manifestSha256'] or action.get('electionUnit') != manifest['electionUnit'] or action.get('protocolSha256') != manifest['protocolSha256']:
        raise ValueError('wrong scoring action identity')
    if instant(action['recordedAt']) > datetime.now(timezone.utc):
        raise ValueError('scoring action cannot be future dated')
    if instant(action['recordedAt']) < instant('2026-11-28T18:00:00+11:00'):
        raise ValueError('target scoring cannot precede election')
    return manifest


def score_snapshot(package, action, outcome_path, *, governance_root=None):
    """Only entry that opens an official target file; guards run first."""
    manifest = validate_scorer_readiness(package, action, governance_root=governance_root)
    target = read('.', outcome_path)
    expected = read(package, 'predictions.json')
    if target.get('electionUnit') != manifest['electionUnit'] or target.get('certified') is not True or target.get('authority') != 'Victorian Electoral Commission':
        raise ValueError('correct certified official target universe required')
    if not str(target.get('sourceUrl', '')).startswith('https://www.vec.vic.gov.au/'):
        raise ValueError('official VEC receipt required')
    if len(target['assemblyDistricts']) != 88 or len(target['councilRegions']) != 8:
        raise ValueError('declared official 88-district/eight-region universe required')
    from .governance import digest
    from pathlib import Path
    if digest(Path(outcome_path).read_bytes()) != action.get('targetFileSha256'):
        raise ValueError('official target carrier bytes do not match scoring action')
    if target.get('sourceSha256') != action.get('targetSha256'):
        raise ValueError('scoring-only target receipt mismatch')
    if set(target['assemblyDistricts']) != set(expected['current_model']['assemblyDistricts']) or set(target['councilRegions']) != set(expected['current_model']['councilRegions']):
        raise ValueError('official geographic IDs do not match sealed universe')
    available_a = [v for v in target['assemblyDistricts'].values() if v.get('status') != 'unavailable']
    available_c = [v for v in target['councilRegions'].values() if v.get('status') != 'unavailable']
    if len(available_a) == 88:
        counts = {p: sum(v['winner'] == p for v in available_a) for p in PARTIES}
        if counts != target['assemblySeats']:
            raise ValueError('official Assembly seats do not reconcile to district winners')
    if len(available_c) == 8:
        if any(sum(v['seats'].values()) != 5 for v in available_c) or {p: sum(v['seats'][p] for v in available_c) for p in PARTIES} != target['councilSeats']:
            raise ValueError('official Council seat universe not reconciled')
    return {key: evaluate_predictions(pred, target) for key, pred in expected.items()}
