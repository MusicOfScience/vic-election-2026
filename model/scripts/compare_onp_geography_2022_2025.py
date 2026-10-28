#!/usr/bin/env python3
"""Compare the current 2022 ONP spatial signal with the official-data 2025 challenger.

This is descriptive shadow validation. It does not read 2026 seat polling or
write forecast inputs.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "model/data/processed/aec_2022_state_district_party_surface_vic.csv.gz"
NEW = ROOT / "model/data/validation/aec_2025_onp_state_district_surface.csv"
OUTPUT = ROOT / "metadata/onp-geography-2022-2025-comparison.json"


def _rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(method="average").to_numpy(float)


def build() -> dict:
    old = pd.read_csv(OLD, compression="gzip")
    old = old[old.party_id.ne("INFORMAL")].copy()
    totals = old.groupby(["district_name"], as_index=False).allocated_ballots.sum().rename(columns={"allocated_ballots": "formal"})
    onp = old[old.party_id.eq("ON")].groupby("district_name", as_index=False).allocated_ballots.sum().rename(columns={"allocated_ballots": "onp"})
    old_seat = totals.merge(onp, on="district_name", how="left").fillna({"onp": 0.0})
    old_seat["share2022"] = old_seat.onp / old_seat.formal
    old_state = old_seat.share2022.mean()
    old_seat["signal2022"] = np.log(np.clip(old_seat.share2022, .004, None) / max(old_state, .004))

    new = pd.read_csv(NEW)
    merged = old_seat[["district_name", "share2022", "signal2022"]].merge(new, on="district_name", how="outer", indicator=True)
    if len(merged) != 88 or not (merged._merge == "both").all():
        missing = merged.loc[merged._merge.ne("both"), ["district_name", "_merge"]].to_dict("records")
        raise ValueError(f"2022/2025 district-name mismatch: {missing}")
    x = merged.signal2022.to_numpy(float)
    y = merged.onp_log_ratio_to_located_state.to_numpy(float)
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(np.corrcoef(_rank(x), _rank(y))[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    residual = y - fitted
    merged["signal_change_2025_minus_2022"] = y - x
    merged["residual_from_2022_linear_fit"] = residual
    merged["rank2022"] = pd.Series(x).rank(ascending=False, method="average")
    merged["rank2025"] = pd.Series(y).rank(ascending=False, method="average")
    merged["rank_change_2025_minus_2022"] = merged.rank2022 - merged.rank2025

    def records(column: str, n: int = 15) -> list[dict]:
        frame = merged.reindex(merged[column].abs().sort_values(ascending=False).index).head(n)
        return [{
            "district": row.district_name,
            "share2022": float(row.share2022),
            "share2025Located": float(row.onp_share),
            "signal2022": float(row.signal2022),
            "signal2025": float(row.onp_log_ratio_to_located_state),
            column: float(row[column]),
        } for _, row in frame.iterrows()]

    return {
        "schemaVersion": 1,
        "status": "shadow-descriptive-comparison",
        "districts": 88,
        "pearsonSignalCorrelation": pearson,
        "spearmanRankCorrelation": spearman,
        "linearFit2025On2022": {"intercept": float(intercept), "slope": float(slope), "rSquared": pearson ** 2},
        "meanAbsoluteSignalChange": float(np.mean(np.abs(y - x))),
        "largestSignalChanges": records("signal_change_2025_minus_2022"),
        "largestLinearFitResiduals": records("residual_from_2022_linear_fit"),
        "interpretationRule": "High correlation alone does not justify retention; inspect slope, rank stability and structured residuals. Low correlation alone does not justify replacement; candidate-field and ecological artefacts require review.",
        "governance": {"productionInput": False, "validationOnly": True, "royMorganRead": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("districts", "pearsonSignalCorrelation", "spearmanRankCorrelation", "linearFit2025On2022")}, indent=2))


if __name__ == "__main__":
    main()
