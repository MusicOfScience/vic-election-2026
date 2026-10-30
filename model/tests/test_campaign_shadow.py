import sys
from pathlib import Path
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'model/scripts'))
from run_current_evidence_shadow import _scenario_registry, _load_evidence
from diagnose_campaign_preferences import project

def test_campaign_shadow_keeps_effective_n_and_separate_other_categories():
    evidence=_load_evidence(ROOT,'metadata/current-evidence-shadow-2026-10-31.json')
    import io, subprocess
    frozen=lambda path: io.StringIO(subprocess.check_output(['git','show',f'9b32cdae813e1a06f3cda1512d136275604e63a3:{path}'],cwd=ROOT,text=True))
    events=pd.read_csv(frozen('model/data/processed/poll_events_seed.csv')); estimates=pd.read_csv(frozen('model/data/processed/poll_estimates_seed.csv'))
    redbridge=next(r for r in evidence['assemblyPolls'] if r['pollster'].startswith('RedBridge'))
    morgan=evidence['assemblyPolls'][-1]
    original_events=events.copy(deep=True); original_estimates=estimates.copy(deep=True)
    e,v=_scenario_registry(events,estimates,[redbridge,morgan])
    assert e.loc[e.poll_id==redbridge['proposedModelPollId'],'effective_sample_size'].iloc[0]==775
    rows=v.loc[v.poll_id==morgan['proposedModelPollId']].set_index('party_id')
    assert rows.loc['IND','primary_pct']==7.5
    assert rows.loc['OTH','primary_pct']==6
    pd.testing.assert_frame_equal(events,original_events)
    pd.testing.assert_frame_equal(estimates,original_estimates)
    with pytest.raises(ValueError,match='already exists'):
        _scenario_registry(e,v,[morgan])

def test_forced_preference_comparison_conserves_votes():
    import numpy as np
    from vicforecast.forecast_2026 import PREFERENCE_PRIOR
    result=project([22.5,29.5,22,12.5,13.5],PREFERENCE_PRIOR,[0,2])
    assert result.sum()==pytest.approx(100)
    assert np.count_nonzero(result)==2
