import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('campaign_compare',Path(__file__).resolve().parents[2]/'scripts/compare-campaign-json.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_campaign_comparison_accepts_only_machine_precision_noise():
    assert module.compare({'mean':25.3,'simulations':5000},{'mean':25.3+1e-14,'simulations':5000})<1e-12
    with pytest.raises(AssertionError): module.compare({'win':0.5},{'win':0.5002})
    with pytest.raises(AssertionError): module.compare({'simulations':5000},{'simulations':4999})
    with pytest.raises(AssertionError): module.compare({'mode':'shadow'},{'mode':'canonical'})
    with pytest.raises(AssertionError): module.compare({'win':0.5},{'win':0.5,'extra':True})
