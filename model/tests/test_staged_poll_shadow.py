from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "model/scripts/run_staged_poll_shadow.py"
spec = importlib.util.spec_from_file_location("run_staged_poll_shadow", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_shadow_report_keeps_canonical_inputs_untouched():
    report = module.build_shadow_report(REPO_ROOT, draws=400)
    assert report["mode"] == "shadow-polling-sensitivity-only"
    assert report["canonicalModelInputsChanged"] is False
    assert report["seatForecastRecomputed"] is False
    assert report["scenarios"]["canonical"]["pollCount"] == 9
    assert report["scenarios"]["plus_demosau"]["pollCount"] == 10
    assert report["scenarios"]["plus_resolve"]["pollCount"] == 10
    assert report["scenarios"]["plus_both"]["pollCount"] == 11


def test_shadow_compositions_remain_coherent_and_deltas_net_to_zero():
    report = module.build_shadow_report(REPO_ROOT, draws=400)
    for scenario in report["scenarios"].values():
        assert sum(scenario["mean"].values()) == pytest.approx(100.0, abs=1e-8)
        assert sum(scenario["deltaMeanVsCanonical"].values()) == pytest.approx(0.0, abs=1e-8)
    assert report["scenarios"]["canonical"]["maxAbsoluteMeanShift"] == pytest.approx(0.0)


def test_resolve_shadow_retains_secondary_evidence_warning():
    report = module.build_shadow_report(REPO_ROOT, draws=200)
    assert "secondary evidence" in report["evidenceCaveats"]["Resolve Strategic"].lower()
    assert "human evidence acceptance" in report["evidenceCaveats"]["DemosAU"].lower()
