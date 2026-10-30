"""Audit the owner-approved two-wave refresh against its immutable predecessor."""
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='9b32cdae813e1a06f3cda1512d136275604e63a3'
NEW_IDS={'demosau_2026-09','roy_morgan_2026-10-29'}
def before(path): return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
def current(path): return (ROOT/path).read_bytes()
def sha(data): return hashlib.sha256(data).hexdigest()
def rows(data): return list(csv.DictReader(io.StringIO(data.decode())))
def delta(a,b): return {'before':float(a),'after':float(b),'change':float(b)-float(a)}
def build():
    path='model/data/processed/experimental_forecast_2026.json';old=json.loads(before(path));new=json.loads(current(path));parties=new['party_order']
    events='model/data/processed/poll_events_seed.csv';estimates='model/data/processed/poll_estimates_seed.csv'
    assert [r for r in rows(current(events)) if r['poll_id'] not in NEW_IDS]==rows(before(events))
    assert [r for r in rows(current(estimates)) if r['poll_id'] not in NEW_IDS]==rows(before(estimates))
    assert set(r['poll_id'] for r in rows(current(events)))-set(r['poll_id'] for r in rows(before(events)))==NEW_IDS
    config='model/config/experimental_forecast.yml'
    assert re.sub(rb'^as_of:.*\n',b'',before(config),flags=re.M)==re.sub(rb'^as_of:.*\n',b'',current(config),flags=re.M)
    archived=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'model/data/validation'],cwd=ROOT,text=True).splitlines()
    for p in archived: assert sha(before(p))==sha(current(p)),p
    district='model/data/processed/experimental_forecast_2026_districts.csv';a={r['district_id']:r for r in rows(before(district))};changes=[]
    for r in rows(current(district)):
        p=a[r['district_id']];wins={party:delta(p[f'win_{party.lower()}'],r[f'win_{party.lower()}']) for party in parties}
        changes.append({'districtId':r['district_id'],'districtName':r['district_name'],'winProbabilities':wins,'maximumAbsoluteProbabilityChange':max(abs(x['change']) for x in wins.values()),'favouredParty':{'before':p['favoured_party'],'after':r['favoured_party']},'likelyFinalPair':{'before':p['likely_final_pair'],'after':r['likely_final_pair']}})
    def chamber(name):
        path=f'model/data/processed/experimental_forecast_2026_{name}.csv';a={r['party']:r for r in rows(before(path))}
        return {r['party']:{k:delta(a[r['party']][k],r[k]) for k in ['mean','median','lower80','upper80','majority_probability']} for r in rows(current(path))}
    region='model/data/processed/experimental_forecast_2026_council_regions.csv';a={r['region_id']:r for r in rows(before(region))}
    sensitivity=json.loads(current('metadata/poll-admission-sensitivity-2026-10-31.json'))['scenarios']['primary_admission_candidate']['summary']['assembly']
    for r in rows(current('model/data/processed/experimental_forecast_2026_chamber.csv')):
        assert abs(float(r['mean'])-sensitivity['parties'][r['party']]['meanSeats'])<1e-12
        assert abs(float(r['majority_probability'])-sensitivity['parties'][r['party']]['majorityProbability'])<1e-12
    return {'schemaVersion':1,'baseCommit':BASE,'assessedAsOf':new['as_of'],'approvalPath':'metadata/poll-admission-approval-2026-10-31.json','forecast':{'path':path,'sha256Before':sha(before(path)),'sha256After':sha(current(path)),'asOfBefore':old['as_of'],'asOfAfter':new['as_of'],'simulations':new['simulations'],'seed':new['seed']},'canonicalPolling':{'eventsBefore':len(rows(before(events))),'eventsAfter':len(rows(current(events))),'eligibleBefore':old['polling']['poll_count'],'eligibleAfter':new['polling']['poll_count'],'addedPollIds':sorted(NEW_IDS)},'statewidePrimary':{p:delta(old['polling']['mean'][p],new['polling']['mean'][p]) for p in parties},'assembly':{'families':chamber('chamber'),'hungProbability':delta(old['assembly']['hung_probability'],new['assembly']['hung_probability']),'materialDistrictThreshold':0.05,'allDistrictChanges':changes,'materialDistricts':sorted([r for r in changes if r['maximumAbsoluteProbabilityChange']>=.05],key=lambda r:-r['maximumAbsoluteProbabilityChange']),'favouredPartyChanges':[r for r in changes if r['favouredParty']['before']!=r['favouredParty']['after']],'orderedFinalPairChanges':[r for r in changes if r['likelyFinalPair']['before']!=r['likelyFinalPair']['after']],'likelyFinalPairChanges':[r for r in changes if sorted(r['likelyFinalPair']['before'].split('–'))!=sorted(r['likelyFinalPair']['after'].split('–'))]},'council':{'families':chamber('council'),'regionalInputChanged':False,'regionalInput':'upper_house_region_poll_2026-08.csv','interpretation':'Only the statewide polling state and assessment date changed; no newer Council regional evidence was injected.','regions':[{'regionId':r['region_id'],'regionName':r['region_name'],'families':{p:{k:delta(a[r['region_id']][f'{k}_{p.lower()}'],r[f'{k}_{p.lower()}']) for k in ['primary','mean','at_least_one']} for p in parties}} for r in rows(current(region))]},'integrity':{'existingPollRowsUnchanged':True,'modelParametersUnchanged':True,'validationArchiveFilesUnchanged':len(archived),'matchesApprovedSensitivity':True,'productionAuthorisation':False,'prospectiveSealCreated':False}}
if __name__=='__main__':
    payload=json.dumps(build(),indent=2)+'\n';target=ROOT/'metadata/forecast-refresh-2026-10-31.json'
    if '--check' in sys.argv: assert target.read_text()==payload
    else: target.write_text(payload)
    r=json.loads(payload);print('Approved refresh audit:',len(r['assembly']['materialDistricts']),'material districts;',len(r['assembly']['favouredPartyChanges']),'modal-winner changes;',len(r['assembly']['likelyFinalPairChanges']),'final-pair changes;',r['integrity']['validationArchiveFilesUnchanged'],'archive files preserved.')
