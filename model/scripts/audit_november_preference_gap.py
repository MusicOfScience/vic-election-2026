"""Compare November poll 2PP with fixed-primary modelled transfers."""
import json
from pathlib import Path

import numpy as np
import yaml

from diagnose_campaign_preferences import project
from vicforecast.forecast_2026 import PREFERENCE_PRIOR

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "metadata/november-poll-evidence-review-2026-11-11.json"


def main():
    evidence = json.loads(REVIEW.read_text())["evidence"]
    config = yaml.safe_load((ROOT / "model/config/experimental_forecast.yml").read_text())
    rng = np.random.default_rng(config["seed"])
    concentration = config["assembly"]["preference_prior_concentration"]
    preferences = [
        np.vstack([rng.dirichlet(np.maximum(row * concentration, .02)) for row in PREFERENCE_PRIOR])
        for _ in range(config["simulations"])
    ]
    report = []
    for poll in evidence:
        published = poll.get("reportedTwoPartyPreferred")
        if poll["scope"] != "state_assembly" or not published:
            continue
        primary = [poll["reportedPrimaries"][p] for p in ("alp", "coalition", "onp", "greens")]
        primary.append(100 - sum(primary))
        values = np.array([project(primary, matrix, (0, 1))[1] for matrix in preferences])
        transferable = sum(primary[2:])
        report.append({
            "poll": poll["id"],
            "coalitionPublished": published["coalition"],
            "coalitionModelMean": round(float(values.mean()), 2),
            "coalitionModelMiddle80": np.quantile(values, [.1, .9]).round(2).tolist(),
            "coalitionGapPp": round(published["coalition"] - float(values.mean()), 2),
            "extraCoalitionShareOfNonMajorVotesPp": round(100 * (published["coalition"] - values.mean()) / transferable, 2),
        })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
