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

REPOSITORY = Path(__file__).resolve().parents[2]
# Exercise frozen PR #126 pre-registration creation guards using its byte-exact
# archived source state. Active-registry checks are separate below; never rewrite
# the live protocol to manufacture a fixture or reopen the one-time live entry.
ROOT = REPOSITORY / 'model/data/validation/prospective-snapshots/post_freshwater_registration/archive'



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


def test_fixture_is_unmistakable_and_zero_replication(archive):
    manifest = sealing.verify_package(archive)
    assert manifest['kind'] == 'fixture-non-empirical' and manifest['independentElectionCount'] == 0
    assert not manifest['registered'] and manifest['snapshotId'].startswith('fixture/')


def test_archive_rejects_tampering_and_extra_files(archive):
    source = archive/'predictions.json'; original = source.read_bytes(); source.write_bytes(original+b' ')
    with pytest.raises(ValueError, match='hash mismatch'):
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
    # Isolate the feature-branch guard against the byte-exact archived source.
    # Its historical calendar receipt is intentionally immutable and will age;
    # calendar freshness is tested independently and must not mask this guard.
    original = sealing.git
    monkeypatch.setattr(sealing, 'check_calendar', lambda root, witnessed: None)
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


def test_scoring_arithmetic_is_deterministic_and_missingness_explicit():
    forecasts = {
        'a': {'assemblyDistricts': {'x': {'status':'available','probabilities': {'ALP':.6,'LIB_NAT':.4,'ONP':0.,'GRN':0.,'OTH_IND':0.}},
                                    'y': unavailable('no forecast')},
              'assemblySeats': {'status':'unavailable'}, 'councilSeats': {'status':'unavailable'}},
        'b': {'assemblyDistricts': {'x': {'status':'available','probabilities': {'ALP':.4,'LIB_NAT':.6,'ONP':0.,'GRN':0.,'OTH_IND':0.}}},
              'assemblySeats': {'status':'unavailable'}, 'councilSeats': {'status':'unavailable'}}}
    targets = {'assemblyDistricts': {'x':'ALP','y':'LIB_NAT'}, 'assemblySeats': {'ALP':40,'LIB_NAT':35,'ONP':8,'GRN':4,'OTH_IND':1}, 'councilSeats': {'ALP':12,'LIB_NAT':13,'ONP':8,'GRN':4,'OTH_IND':3}}
    result = evaluate_predictions(forecasts, targets)
    assert result['a']['assemblyWinner']['n'] == 1 and result['a']['assemblyWinner']['missing'] == ['y']
    assert result['b']['assemblyWinner']['brier'] > result['a']['assemblyWinner']['brier']
    assert result == evaluate_predictions(forecasts, targets)


def test_seat_metrics_are_proper_and_finite():
    metric = seat_metrics([{'ALP':.7,'LIB_NAT':.3,'ONP':0.,'GRN':0.,'OTH_IND':0.}], ['ALP'])
    assert metric['brier'] == pytest.approx(.18)
    assert metric['logLoss'] > 0 and metric['n'] == 1
