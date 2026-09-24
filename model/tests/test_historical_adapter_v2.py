import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from vicforecast.historical_families import load_family_mapping, map_frame_families
from vicforecast.historical_forecast import run_historical_2018_forecast_v2


ROOT = Path(__file__).resolve().parents[1]


def test_historical_family_mapping_preserves_2014_local_structure():
    frame = pd.read_csv(ROOT / "data/processed/vec_2014_assembly_family_primaries.csv")
    mapped = map_frame_families(frame, ROOT)
    assert load_family_mapping(ROOT)["Coalition"] == "LIB_NAT"
    pivot = mapped.pivot_table(index="district_id", columns="model_family", values="first_preference_votes", aggfunc="sum", fill_value=0)
    for party in ("ALP", "LIB_NAT", "GRN", "OTH_IND"):
        assert pivot[party].sum() > 0
    shares = pivot.loc[:, ["ALP", "LIB_NAT", "GRN", "OTH_IND"]].div(pivot.sum(axis=1), axis=0)
    assert np.allclose(shares.sum(axis=1), 1)
    assert shares.loc["brunswick", "GRN"] > shares.loc["brighton", "GRN"]
    assert shares.drop_duplicates().shape[0] > 10


def test_v2_simulation_conserves_assembly_and_council_seats():
    result = run_historical_2018_forecast_v2(ROOT, seed=20181123, simulations=32)
    assert result["modelVersion"] == "historical_replay_v2"
    assert sum(item["mean"] for item in result["assemblySeatSummary"].values()) == 88
    assert all(0 <= item["mean"] <= 88 for item in result["assemblySeatSummary"].values())
    assert len(result["council"]["regions"]) == 8
    assert all(sum(region["seatDistributionMean"].values()) == 5 for region in result["council"]["regions"])
    assert sum(sum(region["seatDistributionMean"].values()) for region in result["council"]["regions"]) == 40
    assert len({tuple(round(item["primaryEstimates"][p], 5) for p in result["activeFamilies"]) for item in result["assemblyDistricts"]}) > 10


def test_v1_prediction_and_score_hashes_remain_immutable():
    prediction = json.loads((ROOT / "data/validation/historical-replays/vic_la_2018-prediction.json").read_text())
    assert prediction["predictionSha256"] == "424552f6ad8fe362044543bb966d2642e34267c32a89b44c47ff390037a4c115"
    score = json.loads((ROOT / "data/validation/historical-replays/vic_la_2018-score-manifest.json").read_text())
    assert score["predictionSha256"] == prediction["predictionSha256"]
