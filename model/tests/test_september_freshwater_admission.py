"""Checks of owner admission, factual extraction and preserved scenario vintage."""
from pathlib import Path
import importlib.util
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def test_admitted_freshwater_matches_retained_workbook_and_preserves_bases():
    spec = importlib.util.spec_from_file_location("extract_freshwater", ROOT / "scripts/extract-freshwater-workbooks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    captured = ROOT / "metadata/current-evidence/2026-10-08"
    extracted = module.extract_workbook((captured / "freshwater-september-tables.xlsx").read_bytes())
    assert extracted == json.loads((captured / "freshwater-extraction.json").read_text())
    events = pd.read_csv(ROOT / "model/data/processed/poll_events_seed.csv")
    estimates = pd.read_csv(ROOT / "model/data/processed/poll_estimates_seed.csv")
    new = events[events.poll_id == "freshwater_2026-09"]
    assert len(new) == 1
    assert new.iloc[0].sample_size == 1030
    assert pd.isna(new.iloc[0].effective_sample_size)
    assert new.iloc[0].sample_family == "freshwater"
    assert new.iloc[0].leader_regime == "Carroll-Wilson"
    for source, party in {"alp": "ALP", "coalition": "LIB_NAT", "oneNation": "ONP", "greens": "GRN", "otherParties": "OTH"}.items():
        row = estimates[(estimates.poll_id == "freshwater_2026-09") & (estimates.party_id == party)]
        assert len(row) == 1
        assert row.iloc[0].primary_pct == extracted["primaryVoteExact"][source]
    forbidden = {"redbridge_accent_2026-09", "demosau_2026-09", "resolve_strategic_2026-09"}
    assert not forbidden.intersection(events.poll_id)


def test_original_august_scenario_excludes_admitted_september_wave():
    import sys
    sys.path.insert(0, str(ROOT / "model/scripts"))
    from run_staged_poll_shadow import build_shadow_report
    report = build_shadow_report(ROOT, draws=100)
    assert report["asOf"] == "2026-08-26"
    assert report["scenarios"]["canonical"]["pollCount"] == 12
    assert report["scenarios"]["plus_both"]["pollCount"] == 14
