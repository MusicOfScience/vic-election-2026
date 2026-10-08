"""Self-contained archive builder. Fixture mode is never registered evidence."""
from __future__ import annotations
import csv
import json
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import yaml
from vicforecast.forecast_2026 import PARTIES
from vicforecast.polling.benchmark import eligible_poll_events
from .governance import (PROTOCOL, RULES, APPROVAL, IMPLEMENTATION, canonical, digest,
                         read, check_governance, instant, material_rules, APPROVED_RULES_SHA256)
from .comparators import build_comparators, rows, unavailable

MODEL_INPUTS = [
    'model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz',
    'model/data/processed/aec_2022_state_region_party_surface_vic.csv.gz',
    'model/data/processed/vec_2022_indicative_candidate_evidence.csv',
    'model/data/processed/vec_enrolment_district_2026-09-04.csv',
    'model/data/processed/vec_enrolment_region_2026-09-04.csv',
    'model/data/processed/district_region_membership_2026.csv',
    'model/data/processed/poll_events_seed.csv', 'model/data/processed/poll_estimates_seed.csv',
    'model/data/seed/recent_state_by_elections.json',
]
COMPARATOR_INPUTS = [
    'model/data/processed/vec_2022_assembly_family_primaries.csv',
    'model/data/processed/vec_2022_assembly_final_pairs.csv',
    'model/data/processed/vec_2022_council_candidate_primaries.csv',
    'model/data/seed/vec_2022_council_validation_targets.json',
    'metadata/historical-party-family-mapping.json',
]
EVIDENCE = [
    'metadata/sources.json', 'metadata/source-provenance.generated.json',
    'metadata/accepted-polls-2026.json', 'metadata/primary-source-evidence-2026.json',
    'metadata/manual-source-evidence-2026.json', 'metadata/poll-model-eligibility-decisions.json',
    'metadata/poll-review-approval-2026.json', 'metadata/poll-coverage-ledger-2026.json',
    'metadata/current-evidence-adjudication-2026-10-08.json',
    'metadata/candidates-2026.json', 'metadata/validation-evidence-contamination-audit.json',
    'metadata/release-readiness.generated.json', 'metadata/model-validation-status.json',
]
CALENDAR = 'metadata/prospective-validation-calendar-check.json'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def now():
    return datetime.now(timezone.utc)


def stamp(value):
    return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def check_window(protocol, snapshot_id, witnessed):
    snapshot = next((s for s in protocol['snapshots'] if s['id'] == snapshot_id), None)
    if snapshot is None:
        raise ValueError('unregistered snapshot ID')
    if witnessed < instant(protocol['approval']['recordedAt']):
        raise ValueError('witness cannot precede approval')
    if snapshot['cutoff']:
        cutoff = instant(snapshot['cutoff'])
        if witnessed > cutoff:
            raise ValueError('missed/backdated cutoff')
        if witnessed < cutoff-timedelta(seconds=60):
            raise ValueError('scheduled freeze trigger not yet due; stage inputs beforehand')
    else:
        cutoff = witnessed
        if witnessed >= instant(protocol['snapshots'][1]['cutoff']):
            raise ValueError('registration snapshot must precede later electoral milestones')
    return snapshot, cutoff


def check_calendar(root, witnessed):
    receipt = read(root, CALENDAR)
    checked = instant(receipt['checkedAt'])
    if checked > witnessed or witnessed-checked > timedelta(hours=24) or receipt['conflict']:
        raise ValueError('fresh conflict-free primary VEC calendar review required before seal')
    if receipt['dates'] != {'rollClose': '2026-11-03T20:00:00+11:00', 'nominationsClose': '2026-11-09T12:00:00+11:00', 'earlyVotingStarts': '2026-11-18', 'electionDay': '2026-11-28'}:
        raise ValueError('calendar amendment required')
    if set(receipt['sources']) != {'https://www.vec.vic.gov.au/voting/types-of-elections/state-elections', 'https://www.vec.vic.gov.au/voting/2026-state-election'}:
        raise ValueError('canonical primary calendar sources required')
    return receipt


def repository_receipt(root, path):
    # Conservative witnessed repository availability, not an invented original capture.
    value = git(root, 'log', '-1', '--format=%H|%cI', '--', path)
    if not value:
        raise ValueError(f'input has no committed provenance: {path}')
    commit, date = value.split('|')
    return {'commit': commit, 'availableBy': date, 'basis': 'latest carrier commit; original capture/admission instant may be unknown'}


def normalised_prediction(root):
    forecast = read(root, 'model/data/processed/experimental_forecast_2026.json')
    def summaries(path):
        return {r['party']: {k: float(r[k]) for k in ('mean', 'median', 'lower80', 'upper80')} for r in rows(root, path)}
    districts = {}
    for row in rows(root, 'model/data/processed/experimental_forecast_2026_districts.csv'):
        p = {f: float(row['win_'+f.lower()]) for f in PARTIES}
        primary = {f: float(row['primary_'+f.lower()]) for f in PARTIES}
        if not all(np.isfinite(list(p.values()))) or any(v < 0 for v in p.values()) or not np.isclose(sum(p.values()), 1):
            raise ValueError('invalid exported district probabilities')
        districts[row['district_id']] = {'status': 'available', 'probabilities': p, 'primary': primary,
                                          'finalPair': {'label': row['likely_final_pair'], 'probability': float(row['final_pair_probability'])}}
    regions = {}
    for row in rows(root, 'model/data/processed/experimental_forecast_2026_council_regions.csv'):
        regions[row['region_name']] = {'status': 'available', 'primary': {f: float(row['primary_'+f.lower()]) for f in PARTIES},
                                       'seats': {f: {'mean': float(row['mean_'+f.lower()])} for f in PARTIES}}
    if len(districts) != 88 or len(regions) != 8:
        raise ValueError('complete current forecast universe required')
    return {'partyOrder': list(PARTIES), 'assemblyDistricts': districts,
            'assemblySeats': summaries('model/data/processed/experimental_forecast_2026_chamber.csv'),
            'hungProbability': forecast['assembly']['hung_probability'], 'councilRegions': regions,
            'councilSeats': summaries('model/data/processed/experimental_forecast_2026_council.csv'),
            'unavailable': read(root, 'metadata/prospective-validation-input-contract.json')['unexportedMetrics']}


def source_ledger(root, cutoff, receipts):
    events = pd.read_csv(Path(root) / 'model/data/processed/poll_events_seed.csv')
    estimates = pd.read_csv(Path(root) / 'model/data/processed/poll_estimates_seed.csv')
    selected, _ = eligible_poll_events(events, estimates)
    forecast = read(root, 'model/data/processed/experimental_forecast_2026.json')
    selected = selected[selected.fieldwork_mid.astype(str) <= forecast['as_of']]
    accepted = {p['evidenceId']: p for p in read(root, 'metadata/accepted-polls-2026.json')['polls']}
    decisions = read(root, 'metadata/poll-model-eligibility-decisions.json')
    by_poll = {d['pollId']: d for d in decisions['decisions']}
    admitted = []
    upper = receipts['model/data/processed/poll_events_seed.csv']
    for _, event in selected.iterrows():
        publication = str(event.get('publication_date', ''))
        if publication in ('', 'nan', 'NaT'):
            raise ValueError('publication date unknown for admitted poll')
        published_upper = instant(publication[:10]+'T23:59:59+11:00')
        if published_upper > cutoff or instant(upper['availableBy']) > cutoff:
            raise ValueError('post-cutoff poll evidence')
        decision = by_poll.get(event['poll_id'])
        accepted_record = accepted.get(decision['evidenceId']) if decision else None
        original_admission = None
        decision_record_at = decisions['decidedAt'] if decision else None
        if decision_record_at and instant(decision_record_at) > cutoff:
            raise ValueError('post-cutoff admission')
        admitted.append({'pollId': event['poll_id'], 'sourceFamily': str(event['sample_family']) if pd.notna(event.get('sample_family')) and event['sample_family'] else str(event['pollster']),
                         'sampleFamilyDisclosure': None if pd.isna(event.get('sample_family')) else str(event['sample_family']),
                         'sourceUrl': str(event['source_url']), 'publicationDate': publication,
                         'publicationAtUpperBound': stamp(published_upper),
                         'originalCaptureAt': None, 'capturedByRepositoryAt': upper['availableBy'],
                         'originalAdmissionAt': original_admission, 'eligibilityDecisionRecordAt': decision_record_at, 'modelAdmittedByRepositoryAt': upper['availableBy'],
                         'timingBasis': upper['basis'], 'evidenceId': decision['evidenceId'] if decision else None,
                         'acceptedEvidence': accepted_record})
    if len(admitted) != forecast['polling']['poll_count']:
        raise ValueError('poll ledger does not match forecast observation count')
    return {'admittedPolls': admitted, 'heldOrExcluded': [d for d in decisions['decisions'] if d['decision'] != 'eligible'],
            'canonicalExcluded': events.loc[~events.poll_id.isin(selected.poll_id)].fillna('').to_dict('records'),
            'legacyTimingLimit': 'No original capture instants fabricated. Committed immutable carriers prove availability by recorded repository time, not original web capture time. Raw missing legacy carriers are explicitly unavailable; extracted canonical registry is archived.',
            'currentCandidateUse': '2022 indicative candidate votes and recent by-election winner-family signals; current candidate registry archived as contextual evidence, not a new model signal.',
            'ballotUse': read(root, 'metadata/prospective-validation-input-contract.json')['familyAvailability']}


def verify_package(package):
    package = Path(package)
    manifest = read(package, 'manifest.json')
    expected = manifest['manifestSha256']; body = dict(manifest); body.pop('manifestSha256')
    if digest(canonical(body)) != expected:
        raise ValueError('manifest hash mismatch')
    if manifest['electionUnit'] != 'vic_2026_general_election' or manifest['independentElectionCount'] != (1 if manifest['registered'] else 0):
        raise ValueError('invalid election replication count')
    if manifest['kind'] not in ('fixture-non-empirical','prospective-live'):
        raise ValueError('simulation/unknown archive kind cannot be empirical')
    if manifest['kind'] == 'fixture-non-empirical' and manifest['registered']:
        raise ValueError('fixture cannot be registered')
    actual = {str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'manifest.json'}:
        raise ValueError('archive inventory mismatch (extra or missing files)')
    for path, receipt in manifest['files'].items():
        member = package / path
        if member.is_symlink() or '..' in Path(path).parts or Path(path).is_absolute():
            raise ValueError('unsafe archive member')
        if digest(member.read_bytes()) != receipt['sha256'] or member.stat().st_size != receipt['bytes']:
            raise ValueError(f'archive hash mismatch: {path}')
    protocol = read(package, 'archive/'+PROTOCOL); approval = read(package, 'archive/'+APPROVAL)
    if approval['decision'] != 'approved' or approval['reviewerRole'] != 'project-owner' or protocol['approval'] != approval:
        raise ValueError('unapproved archive')
    if manifest['protocolSha256'] != APPROVED_RULES_SHA256:
        raise ValueError('unregistered approved protocol hash')
    if digest(canonical(material_rules(protocol))) != manifest['protocolSha256'] or approval['approvedProtocolSha256'] != manifest['protocolSha256']:
        raise ValueError('archive protocol changed')
    if manifest['kind'] == 'fixture-non-empirical':
        if not manifest['snapshotId'].startswith('fixture/'):
            raise ValueError('fixture ID must be unmistakably non-registered')
        snapshot = next(s for s in protocol['snapshots'] if s['id'] == manifest['snapshotId'].removeprefix('fixture/'))
        cutoff = instant(manifest['witnessedAt'])
    else:
        snapshot, cutoff = check_window(protocol, manifest['snapshotId'], instant(manifest['witnessedAt']))
    if snapshot['role'] != manifest['role'] or instant(manifest['cutoff']) != cutoff:
        raise ValueError('snapshot cutoff/role mismatch')
    implementation = read(package, 'archive/'+IMPLEMENTATION)
    for path, sha in implementation['files'].items():
        if digest((package/'archive'/path).read_bytes()) != sha:
            raise ValueError('archived comparator/scorer implementation mismatch')
    ledger = read(package, 'source-ledger.json')
    if ledger != source_ledger(package/'archive', instant(manifest['cutoff']), manifest['repositoryAvailability']):
        raise ValueError('source ledger does not reconcile to archived evidence')
    if manifest['kind'] == 'prospective-live' and any('fixture' in v['basis'] for v in manifest['repositoryAvailability'].values()):
        raise ValueError('fixture availability receipt cannot enter live package')
    for receipt in manifest['repositoryAvailability'].values():
        if instant(receipt['availableBy']) > instant(manifest['cutoff']):
            raise ValueError('post-cutoff input carrier receipt')
    predictions = read(package, 'predictions.json')
    expected_predictions = {'current_model': normalised_prediction(package/'archive'), **build_comparators(package/'archive')}
    if predictions != expected_predictions:
        raise ValueError('predictions/comparators do not reconcile to archived canonical carriers')
    required = set(manifest['requiredRepositoryPaths'])
    contract = read(package, 'archive/metadata/prospective-validation-input-contract.json')
    mandatory = set(MODEL_INPUTS+COMPARATOR_INPUTS+EVIDENCE+[PROTOCOL,RULES,APPROVAL,IMPLEMENTATION,CALENDAR,'model/config/experimental_forecast.yml','model/pyproject.toml','package-lock.json','metadata/prospective-validation-input-contract.json'])
    mandatory |= set(protocol['model']['engineSha256']) | set(implementation['files'])
    config = yaml.safe_load((package/'archive/model/config/experimental_forecast.yml').read_text())
    mandatory.add('model/'+config['council']['regional_poll_path'])
    f = read(package, 'archive/model/data/processed/experimental_forecast_2026.json')
    mandatory |= {'model/data/processed/experimental_forecast_2026.json'} | {'model/'+v['path'] for v in f['outputs'].values()}
    if not mandatory <= required or any('archive/'+p not in manifest['files'] for p in required):
        raise ValueError('mandatory package artefact missing')
    for name in ('predictions.json','source-ledger.json','runtime.json'):
        if name not in manifest['files']:
            raise ValueError('generated package record missing')
    for path, expected_sha in protocol['model']['engineSha256'].items():
        if digest((package/'archive'/path).read_bytes()) != expected_sha:
            raise ValueError('archived model changed')
    if contract['partyOrder'] != list(PARTIES) or manifest['seed'] != protocol['model']['seed'] or manifest['simulations'] != protocol['model']['simulations']:
        raise ValueError('model identity mismatch')
    archive = package/'archive'
    config_path = protocol['model']['configurationPath']
    config_bytes = (archive/config_path).read_bytes()
    structural = ''.join(line for line in config_bytes.decode().splitlines(True) if not line.startswith('as_of:'))
    if digest(structural.encode()) != protocol['model']['structuralConfigurationSha256'] or manifest['structuralConfigSha256'] != protocol['model']['structuralConfigurationSha256']:
        raise ValueError('archived structural configuration changed')
    if manifest['configurationSha256'] != digest(config_bytes) or f['assumptions']['config_sha256'] != digest(config_bytes):
        raise ValueError('archived forecast/config identity mismatch')
    forecast_sha = digest((archive/'model/data/processed/experimental_forecast_2026.json').read_bytes())
    if manifest['forecastSha256'] != forecast_sha or manifest['forecastId'] != f['forecast_id'] or f['forecast_id'] != protocol['model']['forecastId']:
        raise ValueError('archived forecast identity mismatch')
    if snapshot['id'] == 'post_freshwater_registration' and forecast_sha != protocol['model']['baselineForecastSha256']:
        raise ValueError('registration forecast must remain the exact approved baseline')
    if (f['seed'], f['simulations']) != (manifest['seed'], manifest['simulations']):
        raise ValueError('archived forecast seed/simulations mismatch')
    if manifest['structuralModelSha256'] != digest(canonical(protocol['model']['engineSha256'])) or manifest['implementationSha256'] != digest((archive/IMPLEMENTATION).read_bytes()):
        raise ValueError('archived implementation identity mismatch')
    for output in f['outputs'].values():
        if digest((archive/'model'/output['path']).read_bytes()) != output['sha256']:
            raise ValueError('archived output differs from forecast manifest')
    if manifest['kind'] == 'prospective-live' and not manifest['mergeProof']:
        raise ValueError('missing merged-main proof')
    return manifest


def build_package(root, destination, *, snapshot_id='post_freshwater_registration', fixture=False):
    """Live witness comes from the clock, never a user --captured-at argument."""
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if (np.__version__, pd.__version__, yaml.__version__) != ('2.3.5','2.2.3','6.0.3'):
        raise ValueError('use model/constraints.txt runtime before deterministic sealing')
    protocol, approval = check_governance(root)
    started = now()
    if not fixture and any(s['snapshotId'] == snapshot_id for s in protocol['sealing']['currentlySealedSnapshots']):
        raise ValueError('snapshot already sealed; immutable archive cannot be replaced')
    if fixture:
        snapshot = next((s for s in protocol['snapshots'] if s['id'] == snapshot_id), None)
        if snapshot is None: raise ValueError('unknown fixture template')
        cutoff = started
        check_calendar(root, instant(read(root, CALENDAR)['checkedAt']))
    else:
        snapshot, cutoff = check_window(protocol, snapshot_id, started)
        check_calendar(root, started)
    head = git(root, 'rev-parse', 'HEAD')
    proof = None
    if not fixture:
        if git(root, 'branch', '--show-current') != 'main' or git(root, 'status', '--porcelain', '--untracked-files=no'):
            raise ValueError('live seal requires clean merged main, never approval PR branch')
        remote = git(root, 'ls-remote', 'origin', 'refs/heads/main').split()[0]
        if head != remote:
            raise ValueError('live seal requires exact current remote main')
        proof = {'remoteMain': remote, 'verifiedAt': stamp(started), 'approvalAlreadyInCommittedMain': True}
    forecast_path = 'model/data/processed/experimental_forecast_2026.json'
    forecast = read(root, forecast_path)
    config = yaml.safe_load((root/protocol['model']['configurationPath']).read_text())
    if snapshot_id == 'post_freshwater_registration' and digest((root/forecast_path).read_bytes()) != protocol['model']['baselineForecastSha256']:
        raise ValueError('registration requires unchanged 8 October forecast')
    if (forecast['seed'], forecast['simulations'], forecast['forecast_id']) != (protocol['model']['seed'], protocol['model']['simulations'], protocol['model']['forecastId']):
        raise ValueError('forecast identity drift')
    if digest((root/protocol['model']['configurationPath']).read_bytes()) != forecast['assumptions']['config_sha256']:
        raise ValueError('forecast/config mismatch')
    for v in forecast['outputs'].values():
        if digest((root/'model'/v['path']).read_bytes()) != v['sha256']:
            raise ValueError('canonical forecast output mismatch')
    paths = set(MODEL_INPUTS+COMPARATOR_INPUTS+EVIDENCE+[PROTOCOL,RULES,APPROVAL,IMPLEMENTATION,CALENDAR,'metadata/prospective-validation-input-contract.json',protocol['model']['configurationPath'],'model/pyproject.toml','package-lock.json',forecast_path])
    paths |= set(protocol['model']['engineSha256']) | set(read(root, IMPLEMENTATION)['files'])
    paths.add('model/'+config['council']['regional_poll_path'])
    paths |= {'model/'+v['path'] for v in forecast['outputs'].values()}
    paths |= set(git(root, 'ls-files', 'metadata/current-evidence').splitlines())
    receipts = {}
    if not fixture:
        for p in sorted(paths):
            receipts[p] = repository_receipt(root, p)
            if instant(receipts[p]['availableBy']) > cutoff:
                raise ValueError(f'post-cutoff repository carrier: {p}')
    else:
        # Synthetic clock/provenance is labelled fixture and has zero empirical units.
        receipts = {p: {'availableBy': protocol['approval']['recordedAt'], 'basis': 'fixture repository-availability placeholder, non-empirical', 'commit': head} for p in paths}
    if destination.exists():
        raise ValueError('snapshot destination already exists; never overwrite')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.prospective-', dir=destination.parent))
    try:
        for p in sorted(paths):
            member = root/p
            if member.is_symlink(): raise ValueError('source symlink forbidden')
            out = temporary/'archive'/p; out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(member.read_bytes())
        predictions = {'current_model': normalised_prediction(root), **build_comparators(root)}
        generated = {'predictions.json': predictions, 'source-ledger.json': source_ledger(root, cutoff, receipts),
                     'runtime.json': {'python': platform.python_version(), 'platform': platform.platform(), 'numpy': np.__version__, 'pandas': pd.__version__, 'pyyaml': yaml.__version__, 'locks': ['model/constraints.txt','model/pyproject.toml','package-lock.json']}}
        for p, value in generated.items(): (temporary/p).write_bytes(canonical(value)+b'\n')
        witnessed = now()
        if fixture:
            cutoff = witnessed
        else:
            snapshot, cutoff = check_window(protocol, snapshot_id, witnessed)
        if not fixture and git(root, 'rev-parse', 'HEAD') != head:
            raise ValueError('repository changed during seal')
        if witnessed.date() != started.date() and snapshot_id == 'post_freshwater_registration':
            raise ValueError('registration build crossed UTC date; retry with actual clock')
        # Detect working-tree/source mutation while copying, including outputs.
        for p in paths:
            if digest((root/p).read_bytes()) != digest((temporary/'archive'/p).read_bytes()):
                raise ValueError('source changed during seal')
        inventory = {str(p.relative_to(temporary)): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(temporary.rglob('*')) if p.is_file()}
        manifest = {'schemaVersion': 1, 'kind': 'fixture-non-empirical' if fixture else 'prospective-live', 'registered': not fixture,
                    'protocolId': protocol['protocolId'], 'protocolSha256': approval['approvedProtocolSha256'],
                    'snapshotId': 'fixture/'+snapshot_id if fixture else snapshot_id, 'electionUnit': snapshot['electionUnit'], 'role': snapshot['role'],
                    'independentElectionCount': 0 if fixture else 1, 'cutoff': cutoff.astimezone(ZoneInfo('Australia/Melbourne')).isoformat(),
                    'witnessedAt': stamp(witnessed), 'witnessBasis': 'actual system UTC clock; fixture not witnessed empirical evidence' if fixture else 'actual system UTC clock, remote-main receipt; no historical-time override',
                    'gitCommit': head, 'mergeProof': proof, 'forecastId': forecast['forecast_id'], 'forecastSha256': digest((root/forecast_path).read_bytes()),
                    'structuralModelSha256': digest(canonical(protocol['model']['engineSha256'])), 'structuralConfigSha256': protocol['model']['structuralConfigurationSha256'],
                    'configurationSha256': digest((root/protocol['model']['configurationPath']).read_bytes()), 'seed': forecast['seed'], 'simulations': forecast['simulations'],
                    'implementationSha256': digest((root/IMPLEMENTATION).read_bytes()), 'scoringAuthorised': False, 'productionAuthorised': False,
                    'uncertaintyIntervals': {'central80': [0.1,0.9], 'quantileMethod': 'NumPy linear', 'unexported': read(root, 'metadata/prospective-validation-input-contract.json')['unexportedMetrics']},
                    'requiredRepositoryPaths': sorted(paths), 'repositoryAvailability': receipts, 'files': inventory}
        manifest['manifestSha256'] = digest(canonical(manifest))
        (temporary/'manifest.json').write_bytes(canonical(manifest)+b'\n')
        verify_package(temporary)
        temporary.rename(destination)
        return manifest
    except BaseException:
        shutil.rmtree(temporary); raise
