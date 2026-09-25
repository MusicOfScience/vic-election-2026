"""Build descriptive aggregate evidence from immutable certifying cycle scores.

This report never changes a prediction, score, threshold, or model parameter and
excludes the non-certifying 2018 implementation-defect replay.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "data/validation/historical-replays/historical-certifying-v2-aggregate.json"
STATUS = ROOT / "data/validation/historical-replays/historical-four-cycle-validation-status.json"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    cycles = {}
    for cycle in ("vic_la_2010", "vic_la_2014", "vic_la_2022"):
        path = ROOT / f"data/validation/historical-replays/{cycle}-v2-score.json"
        data = json.loads(path.read_text())
        cycles[cycle] = {
            "scorePath": str(path.relative_to(REPO)),
            "scoreSha256": data["scoreSha256"],
            "districtCount": data["assembly"]["districtCount"],
            "winnerAccuracy": data["assembly"]["winner"]["accuracy"],
            "multiclassBrier": data["assembly"]["winner"]["multiclassBrier"],
            "multiclassLogLoss": data["assembly"]["winner"]["multiclassLogLoss"],
            "districtPrimaryMAE": data["assembly"]["districtPrimaryMAE"],
            "statewideVoteErrors": data["assembly"]["statewideVoteErrors"],
            "seatCount": data["assembly"]["assemblySeats"],
            "finalPair": data["assembly"]["finalPair"],
            "thresholdAssessment": data["thresholds"]["cycleLevelAssessment"],
        }
    comparable = {k: [cycles[c][k] for c in cycles] for k in ("winnerAccuracy", "multiclassBrier", "multiclassLogLoss", "districtPrimaryMAE")}
    pooled = {k: sum(v) / len(v) for k, v in comparable.items()}
    report = {
        "schemaVersion": 1,
        "status": "descriptive-three-cycle-certifying-evidence; four-cycle-gate-closed",
        "certifyingCycles": ["vic_la_2022", "vic_la_2014", "vic_la_2010"],
        "nonCertifyingCyclesExcluded": [{"cycleId": "vic_la_2018", "reason": "v1 implementation defect; v2 post-hoc diagnostic"}],
        "cycles": cycles,
        "descriptivePooledMetrics": pooled,
        "metricAggregation": "unweighted mean of cycle-level metrics; not a certification decision",
        "comparatorAggregate": "Only comparator metrics explicitly frozen and present in each cycle score may be compared; no cross-cycle baseline is asserted where metric availability differs.",
        "probabilityCalibration": {"status": "closed-incomplete", "reason": "preregistered cycle-clustered slope/intercept and reliability protocol is not complete for the required four certifying cycles"},
        "completeForecastBacktest": {"status": "closed-incomplete", "reason": "2010, 2014 and 2022 are scored; the fourth certifying cycle is not available because 2018 is non-certifying"},
        "productionAuthorisation": "closed",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    status = {
        "schemaVersion": 1,
        "runnableCycles": 4,
        "predictedCycles": 4,
        "scoredCycles": 4,
        "certifyingPredictedCycles": 3,
        "certifyingScoredCycles": 3,
        "certifyingCycleScores": {c: cycles[c]["scoreSha256"] for c in cycles},
        "nonCertifying2018": "scored-implementation-defect-discovered; post-hoc-v2-diagnostic",
        "completeForecastBacktest": "closed-incomplete-certifying-four-cycle-protocol",
        "probabilityCalibration": "closed-incomplete-cycle-clustered-protocol",
        "productionAuthorisation": "closed",
        "aggregateReport": str(OUT.relative_to(REPO)),
        "aggregateReportSha256": sha(OUT),
    }
    STATUS.write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps({"aggregate": str(OUT.relative_to(REPO)), "status": str(STATUS.relative_to(REPO))}, indent=2))

if __name__ == "__main__":
    main()
