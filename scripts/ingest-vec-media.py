#!/usr/bin/env python3
"""Ingest authorised VEC results into a private, replayable local store."""
import argparse
import os
from pathlib import Path
import sys
import time

from vec_live.azure import AzureFeed
from vec_live.schema import MAX_ARCHIVE, FeedError, identify
from vec_live.store import open_store


def incorporate(store, args):
    store.ingest_references([], None)
    added, issues = 0, []
    if args.command == "manual":
        paths = [item for path in args.input for item in (
            sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in (".zip", ".xml"))
            if path.is_dir() else [path]
        )]
        # Separate setup downloads precede the snapshots regardless of argument order.
        paths.sort(key=lambda p: not ((info := identify(p.name)) and info.reference))
        if not paths:
            raise FeedError("No ZIP or XML downloads found")
        for path in paths:
            try:
                with path.open("rb") as local:
                    count, errors = store.ingest_file(path.name, local.read(MAX_ARCHIVE + 1), "sharepoint")
                added += count
                issues.extend(errors)
            except FeedError as error:
                issues.append(str(error))
            except OSError:
                issues.append("A local source file could not be read")
    else:
        azure = AzureFeed(os.environ)
        items = list(azure.available())
        if not items:
            raise FeedError("Azure listing succeeded but has no eligible V2 files")
        items.sort(key=lambda item: (item[1].published_at or "", item[1].name))
        if args.command == "probe":
            blob, info = items[0]
            from vec_live.schema import extract_inputs, xml
            for _, raw, _ in extract_inputs(info.name, azure.fetch(blob)):
                xml(raw)
            return 0, [], "list and read verified"
        for blob, info in items:
            if store.downloaded(blob.name, blob.etag):
                continue
            try:
                count, errors = store.ingest_file(info.name, azure.fetch(blob), "azure")
                added += count
                issues.extend(errors)
                if not errors:
                    store.record_download(blob.name, blob.etag)
            except FeedError as error:
                issues.append(str(error))
    return added, issues, "updated" if added else "waiting for a new snapshot"


def run_once(args):
    try:
        with open_store(args.root, args.mode) as store:
            try:
                added, issues, state = incorporate(store, args)
            except FeedError as error:
                added, issues, state = 0, [str(error)], "attention required"
            if issues:
                state = "attention required"
            if args.command != "probe":
                store.publish_private(state, issues)
            print(f"{state}; {added} new snapshots; {len(issues)} issues", flush=True)
            for issue in issues[:20]:
                print(issue, file=sys.stderr, flush=True)
            return bool(issues)
    except (FeedError, OSError) as error:
        print(str(error) if isinstance(error, FeedError) else "Private source or state I/O failed",
              file=sys.stderr, flush=True)
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Private directory outside Git")
    parser.add_argument("--mode", choices=("sample", "production"), required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    manual = commands.add_parser("manual")
    manual.add_argument("input", nargs="+", type=Path)
    commands.add_parser("probe", help="Verify Azure list and one bounded read")
    sync = commands.add_parser("sync")
    sync.add_argument("--interval", type=int, help="Repeat at this many seconds; at least 60")
    args = parser.parse_args()
    if args.command != "manual" and args.mode != "production":
        parser.error("Azure is available only for production")
    if args.command == "sync" and args.interval is not None and args.interval < 60:
        parser.error("The ingestion interval must be at least 60 seconds")
    os.umask(0o077)
    if args.command == "sync" and args.interval:
        while True:
            run_once(args)
            time.sleep(args.interval)
    return int(run_once(args))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
