#!/usr/bin/env python3
"""Refresh a private analysis view without restarting an active ingestion runner."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
from time import sleep

from vec_live.store import Store, atomic, encoded
from vec_live.schema import FeedError


def export(path, last_checked):
    status = json.loads((path / "status.json").read_text())
    checked = status["checkedAt"]
    target = path / "private-analysis.json"
    if checked == last_checked and target.is_file():
        return checked
    journal = (path / "journal.sqlite3").resolve().as_uri()
    with closing(sqlite3.connect(journal + "?mode=ro", uri=True)) as source:
        store = Store(path, "production", source, readonly=True)
        store.ingest_references([], None)
        if not store.references:
            raise FeedError("Complete the private production reference import before exporting the analysis view.")
        source.execute("BEGIN")
        view = store.view(status)
    atomic(target, encoded(view) + b"\n")
    print(f"Updated private analysis view for runner check {checked}.", flush=True)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--interval", type=int, default=0)
    args = parser.parse_args()
    if args.interval and args.interval < 15:
        parser.error("Repeat interval must be at least 15 seconds.")
    path = (args.root.expanduser().resolve() / "production").resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        parser.error("Use the private production directory outside Git.")
    if path.stat().st_mode & 0o077:
        parser.error("The private production directory must be accessible only to its owner.")
    os.umask(0o077)
    last_checked = None
    while True:
        try:
            last_checked = export(path, last_checked)
        except (OSError, sqlite3.Error, ValueError) as error:
            message = f"Private analysis export failed ({type(error).__name__})."
            if not args.interval or last_checked is None:
                parser.exit(1, message + "\n")
            print(message, flush=True)
        if not args.interval:
            return
        sleep(args.interval)


if __name__ == "__main__":
    main()
