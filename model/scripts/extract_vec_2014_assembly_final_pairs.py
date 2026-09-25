"""Extract scoring-only final pairs and winners for all 88 2014 VEC districts."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_vec_2022_assembly_final_pairs import build  # noqa: E402

REPO = SCRIPT_DIR.parents[1]
MANIFEST = REPO / "metadata/vec-historical-assembly-primary-source-manifest.csv"
PRIMARY = REPO / "model/data/processed/vec_2014_assembly_candidate_primaries.csv"
DEFAULT_OUT = REPO / "model/data/processed/vec_2014_assembly_final_pairs.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = build(args.cache_dir, election_year="2014", expected_count=88, exclude_district=None, primary_input=PRIMARY, election_id="vic_la_2014")
    fields = list(rows[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import csv
    import hashlib
    import json
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"path": str(args.output.resolve().relative_to(REPO)), "rows": len(rows), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "finalPairUnavailable": sum(1 for row in rows if not row["final_pair_available"])}))


if __name__ == "__main__":
    main()
