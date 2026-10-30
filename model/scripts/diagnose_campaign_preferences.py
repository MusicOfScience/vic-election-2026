"""Compare forced statewide matchups with Morgan; never fit or alter priors.

Forced eliminations mimic the named hypothetical comparison, not seat geography.
They cannot identify original-parcel transfer rates or forecast final-pair survival.
"""
import json
from pathlib import Path
import numpy as np
import yaml
from vicforecast.forecast_2026 import PARTIES, PREFERENCE_PRIOR

ROOT = Path(__file__).resolve().parents[2]

def project(primary, preference, survivors):
    votes = np.array(primary, dtype=float)
    continuing = set(range(len(PARTIES)))
    while continuing != set(survivors):
        source = min(continuing - set(survivors), key=lambda i: (votes[i], i))
        continuing.remove(source)
        dest = sorted(continuing)
        weights = preference[source, dest]
        votes[dest] += votes[source] * weights / weights.sum()
        votes[source] = 0
    return votes

def build_report(draws=5000):
    evidence = json.loads((ROOT / 'metadata/current-evidence-shadow-2026-10-31.json').read_text())
    morgan = evidence['assemblyPolls'][-1]
    primary = morgan['primaryVote']
    shares = [primary['alp'], primary['coalition'], primary['oneNation'], primary['greens'], primary['otherParties'] + primary['independents']]
    config = yaml.safe_load((ROOT / 'model/config/experimental_forecast.yml').read_text())
    rng = np.random.default_rng(config['seed'])
    comparisons = [('ALP_vs_Coalition', [0,1], [44,56]), ('ALP_vs_ONP', [0,2], [54.5,45.5]), ('three_party', [0,1,2], [43,33,24])]
    outputs = {name: [] for name, _, _ in comparisons}
    for _ in range(draws):
        preference = np.vstack([rng.dirichlet(np.maximum(row * config['assembly']['preference_prior_concentration'], .02)) for row in PREFERENCE_PRIOR])
        for name, survivors, _ in comparisons:
            outputs[name].append(project(shares, preference, survivors)[survivors])
    result = {}
    for name, survivors, published in comparisons:
        values = np.array(outputs[name]); mean = values.mean(axis=0)
        result[name] = dict(parties=[PARTIES[i] for i in survivors], published=published, modelMean=mean.tolist(), modelLower80=np.quantile(values,.1,axis=0).tolist(), modelUpper80=np.quantile(values,.9,axis=0).tolist(), deltaModelMinusPublished=(mean-published).tolist())
    return dict(schemaVersion=1, mode='diagnostic-only-no-fitting', seed=int(config['seed']), draws=draws, primaryVector=shares, comparisons=result, excludedMatchup=dict(parties=['LIB_NAT','ONP'],reported=[74,29],reason='Source sums to 103; no correction inferred.'), limitations=['Fixed published primaries; intervals reflect preference-prior dispersion only, not total election or survey uncertainty.','Forced statewide comparisons do not estimate district final-pair survival or government formation.','Published outcomes from one survey are dependent; no fitting, independent observations or model promotion.'])

if __name__ == '__main__':
    (ROOT / 'metadata/campaign-preference-diagnostic-2026-10-31.json').write_text(json.dumps(build_report(), indent=2)+'\n')
