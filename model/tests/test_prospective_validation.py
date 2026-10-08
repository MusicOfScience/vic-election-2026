"""Synthetic arithmetic and non-empirical archives; no election targets loaded."""
import json
import hashlib
from datetime import timedelta
from pathlib import Path
import pytest
from model.validation.prospective import package as sealing
from model.validation.prospective.comparators import build_comparators, swing, unavailable
from model.validation.prospective.governance import read, instant, canonical, check_governance
from model.validation.prospective.scoring import evaluate_predictions, seat_metrics, score_snapshot, validate_scorer_readiness
from vicforecast.forecast_2026 import PARTIES

ROOT = Path(__file__).resolve().parents[2]


def test_owner_approval_and_frozen_rules():
    protocol, approval = check_governance(ROOT)
    assert approval['reviewerRole'] == 'project-owner' and approval['decision'] == 'approved'
    assert instant(approval['recordedAt']) < sealing.now()
    assert not protocol['scoringAuthorised'] and not approval['productionAuthorised']


def test_actual_clock_cutoff_and_no_backdating():
    p = read(ROOT, 'metadata/model-vnext-validation-protocol.json')
    cutoff = instant(p['snapshots'][1]['cutoff'])
    assert sealing.check_window(p, 'writ_roll_close', cutoff)[1] == cutoff
    with pytest.raises(ValueError, match='missed/backdated'):
        sealing.check_window(p, 'writ_roll_close', cutoff+timedelta(microseconds=1))
    with pytest.raises(ValueError, match='not yet due'):
        sealing.check_window(p, 'writ_roll_close', cutoff-timedelta(days=1))
    with pytest.raises(ValueError, match='precede approval'):
        sealing.check_window(p, 'post_freshwater_registration', instant(p['approval']['recordedAt'])-timedelta(seconds=1))


def test_unapproved_seal_refused(tmp_path):
    import shutil
    for path in ['metadata/model-vnext-validation-protocol.json','metadata/prospective-validation-approval.json','metadata/prospective-validation-approved-rules.json']:
        target = tmp_path/path; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/path,target)
    protocol = read(tmp_path,'metadata/model-vnext-validation-protocol.json')
    protocol['status'] = 'proposed-awaiting-owner-review'
    (tmp_path/'metadata/model-vnext-validation-protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError,match='approved protocol required'):
        sealing.build_package(tmp_path,tmp_path/'no',fixture=True)
    assert not (tmp_path/'no').exists()


@pytest.fixture
def archive(tmp_path):
    before = sealing.now()
    manifest = sealing.build_package(ROOT, tmp_path/'fixture', fixture=True)
    assert before <= instant(manifest['witnessedAt']) <= sealing.now()
    return tmp_path/'fixture'


def test_fixture_construction_hashes_and_comparators(archive):
    m = sealing.verify_package(archive)
    assert m['kind'] == 'fixture-non-empirical' and not m['registered']
    assert m['snapshotId'].startswith('fixture/')
    assert m['independentElectionCount'] == 0
    assert read(ROOT,'metadata/model-vnext-validation-protocol.json')['sealing']['currentlySealedSnapshots'] == []
    assert len(m['files']) > 35
    for path, receipt in m['files'].items():
        assert hashlib.sha256((archive/path).read_bytes()).hexdigest() == receipt['sha256']
    copied = read(archive,'predictions.json')
    assert copied['prior_result'] == build_comparators(ROOT)['prior_result']
    assert copied['current_model']['assemblyDistricts']['albert-park']['probabilities']['ALP'] == .693
    assert read(archive,'source-ledger.json')['admittedPolls'].__len__() == 13
    assert not m['productionAuthorised'] and not m['scoringAuthorised']


def test_tampering_extra_files_and_fixture_promotion_fail(archive):
    source = archive/'manifest.json'; original = source.read_bytes(); manifest = json.loads(original)
    manifest['kind'] = 'prospective-live'; manifest['registered'] = True; manifest['independentElectionCount'] = 1
    manifest['snapshotId'] = manifest['snapshotId'].removeprefix('fixture/')
    manifest.pop('manifestSha256'); manifest['manifestSha256'] = hashlib.sha256(canonical(manifest)).hexdigest()
    source.write_bytes(canonical(manifest))
    with pytest.raises(ValueError, match='fixture availability'):
        sealing.verify_package(archive)
    source.write_bytes(original)
    changed = json.loads(original); changed['forecastSha256'] = '0'*64
    changed.pop('manifestSha256'); changed['manifestSha256'] = hashlib.sha256(canonical(changed)).hexdigest()
    source.write_bytes(canonical(changed))
    with pytest.raises(ValueError, match='forecast identity mismatch'):
        sealing.verify_package(archive)
    source.write_bytes(original)
    (archive/'unexpected').write_text('not governed')
    with pytest.raises(ValueError, match='inventory mismatch'):
        sealing.verify_package(archive)
    (archive/'unexpected').unlink()
    (archive/'predictions.json').write_text('{}')
    with pytest.raises(ValueError, match='hash mismatch'):
        sealing.verify_package(archive)


def test_unsealed_and_unauthorised_scoring_never_opens_outcomes(archive, tmp_path, monkeypatch):
    with pytest.raises((ValueError,FileNotFoundError)):
        score_snapshot(tmp_path/'unsealed', {}, tmp_path/'never-open-outcomes.json')
    with pytest.raises(ValueError, match='fixture/unsealed'):
        score_snapshot(archive, {}, tmp_path/'never-open-outcomes.json')
    # Isolate permission guard, without creating or registering a fake live archive.
    manifest = sealing.verify_package(archive); manifest.update(kind='prospective-live',registered=True)
    monkeypatch.setattr(sealing, 'verify_package', lambda _: manifest)
    with pytest.raises(ValueError, match='scoringAuthorised=false'):
        validate_scorer_readiness(archive, {'decision':'authorise-scoring','reviewerRole':'project-owner'})


def test_live_seal_refuses_feature_branch_without_producing_snapshot(tmp_path, monkeypatch):
    # Always force the feature-branch guard; never attempt a real seal even on main CI.
    original = sealing.git
    monkeypatch.setattr(sealing,'git',lambda root,*args: 'codex/test-fixture' if args == ('branch','--show-current') else original(root,*args))
    with pytest.raises(ValueError, match='clean merged main'):
        sealing.build_package(ROOT,tmp_path/'live')
    assert not (tmp_path/'live').exists()


def test_deterministic_registered_comparators_and_missingness():
    a, b = build_comparators(ROOT), build_comparators(ROOT)
    assert canonical(a) == canonical(b)
    for kind, comp in a.items():
        assert comp['assemblyDistricts']['narracan']['status'] == 'unavailable'
        assert comp['assemblySeats']['status'] == 'unavailable'
        assert len(comp['councilRegions']) == 8
        assert all(sum(v[p]['mean'] for p in PARTIES) == 5 for v in [r['seats'] for r in comp['councilRegions'].values()])
        assert all(set(r['probabilities'].values()) <= {0.,1.} for r in comp['assemblyDistricts'].values() if r['status'] == 'available')
    assert a['prior_result']['assemblyDistricts']['albert-park']['winner'] == 'ALP'
    assert sum(v['mean'] for v in a['prior_result']['councilSeats'].values()) == 40
    contract = read(ROOT,'metadata/prospective-validation-input-contract.json')
    assert contract['councilPartyToFamily']['Liberal Democrats'] == 'OTH_IND'
    assert contract['councilPartyToFamily']["Pauline Hanson's One Nation"] == 'ONP'
    fixture = lambda v: dict(zip(PARTIES,v))
    moved = swing(fixture([50,30,0,10,10]),fixture([25,25,30,10,10]),fixture([40,35,0,10,15]))
    assert list(moved.values()) == [35.,20.,30.,10.,5.]
    moved = swing(fixture([10,60,0,10,20]),fixture([5,15,60,10,10]),fixture([40,35,0,10,15]))
    assert moved['ALP'] == 0 and sum(moved.values()) == pytest.approx(100)


def synthetic():
    # Toy named units are not Victorian target rows or scoring receipts.
    primary = dict(zip(PARTIES,[50,50,0,0,0]))
    seats = dict(zip(PARTIES,[2,0,0,0,0]))
    summaries = {p:{'mean':float(seats[p]),'median':float(seats[p]),'lower80':float(seats[p]),'upper80':float(seats[p])} for p in PARTIES}
    pred = {'assemblyDistricts': {
        'toy_a':{'primary':primary,'probabilities':dict(zip(PARTIES,[.5,.5,0,0,0])), 'finalPair':{'label':'ALP–LIB_NAT','probability':.75}},
        'toy_b':{'primary':primary,'probabilities':dict(zip(PARTIES,[0,1,0,0,0]))}},
        'assemblySeats':summaries, 'hungProbability':.8,
        'councilRegions':{'toy_region':{'primary':primary,'seats':summaries}},'councilSeats':summaries}
    target = {'assemblyDistricts': {
        'toy_a':{'primary':primary,'winner':'ALP','formalVotes':10,'finalPair':'ALP–LIB_NAT'},
        'toy_b':{'primary':dict(zip(PARTIES,[0,0,0,100,0])),'winner':'GRN','formalVotes':30}},
        'assemblySeats':seats,'councilRegions':{'toy_region':{'primary':primary,'seats':seats}},'councilSeats':seats}
    return pred,target


def test_synthetic_metrics_known_arithmetic_and_tie_order():
    p,y = synthetic(); result = evaluate_predictions(p,y)
    assert result['assembly']['multiclassBrier'] == 1.25
    assert result['assembly']['winnerAccuracy'] == .5  # ALP wins .5/.5 tie.
    assert result['assembly']['zeroProbabilityEvents'] == 1
    assert result['assembly']['clippedEvents'] == 1
    assert result['assembly']['logLoss'] == pytest.approx((-.5*__import__('math').log(.5)) + (-.5*__import__('math').log(1e-12)))
    assert result['assembly']['statewide']['observed']['GRN'] == 75
    assert result['assembly']['primaryCellDenominator'] == 10
    assert sum(b['count'] for b in result['assembly']['reliability']) == 10
    assert result['finalPairs']['brier'] == .0625
    assert result['hung']['brier'] == pytest.approx(.04)
    assert result['councilRegionalFamilyPrimaryMae'] == 0
    assert result['descriptiveOnly'] and not result['productionAuthorised']
    interval = seat_metrics({'ALP':{'mean':1.5,'median':2,'lower80':1,'upper80':2}}, {'ALP':2})
    assert interval['ALP']['coverage80'] == 1 and interval['ALP']['width80'] == 1


def test_missing_metrics_never_zero_or_partial_state():
    p,y = synthetic(); p['assemblyDistricts']['toy_b'] = unavailable('No mapping.')
    result = evaluate_predictions(p,y)
    assert result['assembly']['denominator'] == 1
    assert result['assembly']['missing'][0]['districtId'] == 'toy_b'
    assert result['assembly']['statewide']['status'] == 'unavailable'
    p,y = synthetic(); del p['assemblyDistricts']['toy_a']['finalPair']
    assert evaluate_predictions(p,y)['finalPairs']['status'] == 'unavailable'
    p,y = synthetic(); y['assemblyDistricts'].pop('toy_b')
    with pytest.raises(ValueError,match='wrong district'):
        evaluate_predictions(p,y)
