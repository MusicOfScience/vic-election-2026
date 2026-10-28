#!/usr/bin/env python3
"""Generate the amended joint ONP persistence mixture before any 2026 seat run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "model/data/validation/onp-spatial-persistence-bootstrap.csv"
SURFACES = ROOT / "model/data/validation/onp-senate-spatial-surfaces-2016-2025.csv"
CALIBRATION = ROOT / "metadata/onp-spatial-persistence-calibration-2026-10-28.json"
MIXTURE = ROOT / "model/data/validation/onp-spatial-persistence-mixture.csv"
FREEZE = ROOT / "metadata/onp-spatial-persistence-freeze-v2-generated.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(series: pd.Series) -> dict:
    values = series.to_numpy(float)
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "q05": float(np.quantile(values, 0.05)),
        "q10": float(np.quantile(values, 0.10)),
        "q25": float(np.quantile(values, 0.25)),
        "q75": float(np.quantile(values, 0.75)),
        "q90": float(np.quantile(values, 0.90)),
        "q95": float(np.quantile(values, 0.95)),
    }


def build() -> tuple[pd.DataFrame, dict]:
    calibration = json.loads(CALIBRATION.read_text())
    if calibration["status"] != "frozen-pre-2026-seat-run":
        raise ValueError("unexpected base calibration status")
    governance = calibration["governance"]
    if governance["assembly2026SimulatorExecuted"] or governance["assembly2026OutputsRead"]:
        raise ValueError("cannot amend persistence distribution after 2026 outputs")

    boot = pd.read_csv(BOOTSTRAP)
    required = {
        "aTargetTriplet1", "kappaTargetTriplet1",
        "aTargetTriplet2", "kappaTargetTriplet2",
    }
    if not required.issubset(boot.columns):
        raise ValueError(f"bootstrap missing columns: {sorted(required - set(boot.columns))}")

    first = boot[["aTargetTriplet1", "kappaTargetTriplet1"]].rename(
        columns={"aTargetTriplet1": "aTarget", "kappaTargetTriplet1": "kappaTarget"}
    )
    first["sourceTriplet"] = "2016-2019-2022"
    first["sourceDraw"] = np.arange(len(first))
    second = boot[["aTargetTriplet2", "kappaTargetTriplet2"]].rename(
        columns={"aTargetTriplet2": "aTarget", "kappaTargetTriplet2": "kappaTarget"}
    )
    second["sourceTriplet"] = "2019-2022-2025"
    second["sourceDraw"] = np.arange(len(second))
    mixture = pd.concat([first, second], ignore_index=True)
    mixture.insert(0, "mixtureDraw", np.arange(len(mixture)))
    if len(mixture) != 10000:
        raise ValueError(f"expected 10000 mixture draws, got {len(mixture)}")
    if not mixture[["aTarget", "kappaTarget"]].apply(lambda s: s.between(0, 1).all()).all():
        raise ValueError("mixture retention outside [0,1]")

    MIXTURE.parent.mkdir(parents=True, exist_ok=True)
    mixture.to_csv(MIXTURE, index=False)
    corr = float(np.corrcoef(mixture.aTarget, mixture.kappaTarget)[0, 1])
    freeze = {
        "schemaVersion": 2,
        "date": "2026-10-28",
        "status": "frozen-pre-2026-seat-run-amended",
        "protocol": "docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_PROTOCOL.md",
        "amendment": "docs/ONP_SPATIAL_PERSISTENCE_CALIBRATION_AMENDMENT_1.md",
        "baseCalibrationSha256": _sha(CALIBRATION),
        "cycleSurfacesSha256": _sha(SURFACES),
        "baseBootstrapSha256": _sha(BOOTSTRAP),
        "mixture": {
            "rule": "equal-weight empirical mixture of the two triplet-specific region-block bootstrap distributions; joint (a,kappa) pairs preserved",
            "draws": int(len(mixture)),
            "triplet1Draws": int(first.shape[0]),
            "triplet2Draws": int(second.shape[0]),
            "sha256": _sha(MIXTURE),
            "generatedPath": str(MIXTURE.relative_to(ROOT)),
            "aTarget": _summary(mixture.aTarget),
            "kappaTarget": _summary(mixture.kappaTarget),
            "aKappaCorrelation": corr,
        },
        "pooledPointEstimateDiagnosticOnly": calibration["pooledPointEstimate"],
        "tripletPointFits": calibration["tripletPointFits"],
        "targetHorizon": calibration["targetHorizon"],
        "sourceHashes": [
            {
                "year": event["year"],
                "senateDivisionPayloadSetSha256": event["senateAcquisition"]["divisionPayloadSetSha256"],
                "placesSha256": event["placesSha256"],
            }
            for event in calibration["events"]
        ],
        "governance": {
            "productionInput": False,
            "assembly2026SimulatorExecuted": False,
            "assembly2026OutputsRead": False,
            "royMorganRead": False,
            "campaignSeatClaimsRead": False,
            "analystSeatCallsRead": False,
        },
        "githubRunId": os.environ.get("GITHUB_RUN_ID"),
        "allowedNextUse": "Only this amended joint mixture may be consumed by the subsequent 2026 shadow simulation. The pooled-average bootstrap is diagnostic only.",
    }
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps(freeze, indent=2) + "\n")
    return mixture, freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    _, freeze = build()
    print(json.dumps({
        "status": freeze["status"],
        "draws": freeze["mixture"]["draws"],
        "aTarget": freeze["mixture"]["aTarget"],
        "kappaTarget": freeze["mixture"]["kappaTarget"],
        "aKappaCorrelation": freeze["mixture"]["aKappaCorrelation"],
        "sha256": freeze["mixture"]["sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
