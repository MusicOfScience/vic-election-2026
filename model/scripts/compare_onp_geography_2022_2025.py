#!/usr/bin/env python3
"""Compare the current 2022 ONP spatial signal with the official-data 2025 challenger.

This is descriptive shadow validation. It does not read 2026 seat polling or
write forecast inputs. District names are joined case-insensitively because
Vicmap publishes its district field in uppercase while the model uses title case.
"""
from __future__ import annotations

import argparse
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


def _key(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def build() -> dict:
    old = pd.read_csv(OLD, compression="gzip")
    old = old[old.party_id.ne("INFORMAL")].copy()
    totals = old.groupby(["district_name"], as_index=False).allocated_ballots.sum().rename(columns={"allocated_ballots": "formal"})
    onp = old[old.party_id.eq("ON")].groupby("district_name", as_index=False).allocated_ballots.sum().rename(columns={"allocated_ballots": "onp"})
    old_seat = totals.merge(onp, on="district_name", how="left").fillna({"onp": 0.0})
    old_seat["share2022"] = old_seat.onp / old_seat.formal
    old_state = old_seat.share2022.mean()
    old_seat["signal2022"] = np.log(np.clip(old_seat.share2022, .004, None) / max(old_state, .004))
    old_seat["district_key"] = _key(old_seat.district_name)

    new = pd.read_csv(NEW)
    new["district_key"] = _key(new.district_name)
    new = new.rename(columns={"district_name": "district_name_2025"})
    merged = old_seat[["district_name", "district_key", "share2022", "signal2022"]].merge(
        new,
        on="district_key",
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    if len(merged) != 88 or not (merged._merge == "both").all():
        missing = merged.loc[
            merged._merge.ne("both"),
            ["district_name", "district_name_2025", "district_key", "_merge"],
        ].to_dict("records")
        raise ValueError(f"2022/2025 district-name mismatch after normalisation: {missing}")

    x_raw = merged.signal2022.to_numpy(float)
    y_raw = merged.onp_log_ratio_to_located_state.to_numpy(float)
    # Additive log-signal centres are arbitrary because the two source surfaces
    # use different statewide denominators. Compare relative geography after
    # de-meaning both signals. Correlation and slope are invariant to this step;
    # absolute change is not, so centred change is the scientifically relevant one.
    x = x_raw - x_raw.mean()
    y = y_raw - y_raw.mean()
    pearson = float(np.corrcoef(x, y)[0, 1])
    spearman = float(np.corrcoef(_rank(x), _rank(y))[0, 1])
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x
    residual = y - fitted
    merged["signal2022_centered"] = x
    merged["signal2025_centered"] = y
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
            "signal2022Centered": float(row.signal2022_centered),
            "signal2025Centered": float(row.signal2025_centered),
            column: float(row[column]),
        } for _, row in frame.iterrows()]

    return {
        "schemaVersion": 2,
        "status": "shadow-descriptive-comparison",
        "districts": 88,
        "joinRule": "case-insensitive trimmed district name; canonical report labels from the 2022 model surface",
        "signalCentreRule": "demean each log-relative surface across the 88 districts before absolute change comparison",
        "pearsonSignalCorrelation": pearson,
        "spearmanRankCorrelation": spearman,
        "linearFit2025On2022": {"intercept": float(intercept), "slope": float(slope), "rSquared": pearson ** 2},
        "meanAbsoluteCenteredSignalChange": float(np.mean(np.abs(y - x))),
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
