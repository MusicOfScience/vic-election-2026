#!/usr/bin/env python3
"""Prepare/verify an archive; live mode requires approval already merged on main."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'model/src')]
from model.validation.prospective.package import build_package, verify_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', action='store_true', help='non-empirical temporary package; never registers a live snapshot')
    parser.add_argument('--verify', type=Path, help='reconcile a package without scoring outcomes')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--snapshot-id', default='post_freshwater_registration')
    args = parser.parse_args()
    if args.verify:
        if args.fixture or args.output:
            parser.error('--verify cannot build a package')
        manifest = verify_package(args.verify)
    else:
        if not args.output:
            parser.error('--output required; existing archive destinations are never overwritten')
        manifest = build_package(ROOT, args.output, snapshot_id=args.snapshot_id, fixture=args.fixture)
    print(json.dumps({k: manifest[k] for k in ('kind','snapshotId','manifestSha256','witnessedAt','scoringAuthorised','productionAuthorised')}))


if __name__ == '__main__': main()
