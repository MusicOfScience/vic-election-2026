"""Private content-addressed archive, SQLite journal, and atomic viewer export."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from tempfile import NamedTemporaryFile
import zlib

from .schema import (MAX_ARCHIVE, FeedError, extract_inputs, identify, load_references,
                     reference_root, register_from_repository, snapshot)

VARIANT_RANK = {"lite": 0, "verbose": 1, "litepp": 2}
HOUSES = ("L", "U")


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()


def decoded(data):
    return json.loads(zlib.decompress(data))


def atomic(path, contents):
    temporary_name = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temporary_name = temporary.name
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


@contextmanager
def open_store(directory, mode):
    path = directory.expanduser().resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise FeedError("Private feed storage must be outside every Git checkout")
    if not path.is_dir():
        raise FeedError("Create the private feed root before running ingestion")
    path = path / mode
    path.mkdir(mode=0o700, exist_ok=True)
    if path.is_symlink() or path.stat().st_mode & 0o077:
        raise FeedError("Private feed state must be an owner-only directory")
    with (path / ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise FeedError("Another ingestion process holds the private store lock") from None
        with closing(sqlite3.connect(path / "journal.sqlite3")) as database:
            yield Store(path, mode, database)


class Store:
    def __init__(self, path, mode, db):
        self.path, self.mode, self.db = path, mode, db
        self.archive = path / "archive"
        self.archive.mkdir(mode=0o700, exist_ok=True)
        db.executescript("""
            CREATE TABLE IF NOT EXISTS references_inbox (
                kind TEXT PRIMARY KEY, name TEXT, digest TEXT, source TEXT
            );
            CREATE TABLE IF NOT EXISTS snapshots (
                sequence INTEGER PRIMARY KEY, house TEXT, published TEXT, rank INTEGER,
                xml_digest TEXT, source_digest TEXT, source_name TEXT, source TEXT,
                accepted TEXT, data BLOB,
                UNIQUE(xml_digest, house, published, rank)
            );
            CREATE INDEX IF NOT EXISTS snapshot_chronology
                ON snapshots(house, published DESC, rank DESC, sequence DESC);
            CREATE TABLE IF NOT EXISTS downloads (
                name TEXT, etag TEXT, PRIMARY KEY(name, etag)
            );
            CREATE TABLE IF NOT EXISTS quarantines (
                id INTEGER PRIMARY KEY, recorded TEXT, name TEXT, digest TEXT, reason TEXT,
                UNIQUE(name, digest, reason)
            );
        """)
        self.references = None

    def retain(self, data, suffix):
        digest = sha256(data).hexdigest()
        path = self.archive / f"{digest}.{suffix}"
        if not path.exists():
            atomic(path, data)
        return digest

    def quarantined(self, name, digest, reason):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO quarantines(recorded,name,digest,reason) VALUES (?,?,?,?)",
                            (now(), name, digest, reason))

    def ingest_references(self, entries, source):
        existing = self.db.execute("SELECT kind,name,digest FROM references_inbox").fetchall()
        items = {kind: (identify(name), (self.archive / f"{digest}.xml").read_bytes())
                 for kind, name, digest in existing}
        for info, raw in entries:
            reference_root(info, raw, self.mode)
            previous = items.get(info.reference)
            if previous and previous[1] != raw:
                raise FeedError("Reference version changed; review and reconcile in a new private store")
            items[info.reference] = info, raw
        if len(items) == 3 and (entries or self.references is None):
            self.references = load_references(items, self.mode, register_from_repository())
        with self.db:
            for info, raw in entries:
                self.db.execute("INSERT OR IGNORE INTO references_inbox VALUES (?,?,?,?)",
                                (info.reference, info.name, self.retain(raw, "xml"), source))

    def ingest_snapshot(self, info, raw, carrier, source):
        if self.references is None:
            raise FeedError("Set up the three VEC V2 reference files before ingesting results")
        digest = self.retain(raw, "xml")
        carrier_digest = self.retain(carrier, "zip") if carrier is not None else digest
        rank = VARIANT_RANK[info.variant]
        if self.db.execute("SELECT 1 FROM snapshots WHERE xml_digest=? AND house=? AND published=? AND rank=?",
                           (digest, info.house, info.published_at, rank)).fetchone():
            return False
        parsed = snapshot(info, raw, self.references, self.mode)
        accepted = now()
        payload = zlib.compress(encoded(parsed))
        with self.db:
            self.db.execute("""
                INSERT INTO snapshots (house,published,rank,xml_digest,source_digest,source_name,source,accepted,data)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (info.house, info.published_at, rank, digest, carrier_digest, info.name, source, accepted, payload))
        return True

    def ingest_file(self, name, raw, source):
        if len(raw) > MAX_ARCHIVE:
            raise FeedError("Input exceeds the file size limit")
        try:
            if source == "sharepoint" and self.mode == "production" and name.lower().endswith(".zip"):
                # Keep a byte-exact copy of the SharePoint wrapper as well as VEC's nested ZIPs.
                self.retain(raw, "zip")
            items = list(extract_inputs(name, raw))
            if self.mode == "production" and any(info.sample for info, _, _ in items):
                raise FeedError("Sample or trial data cannot enter production")
            if any(info.reference for info, _, _ in items):
                self.ingest_references([(info, data) for info, data, _ in items if info.reference], source)
        except ValueError as error:
            reason = str(error) if isinstance(error, FeedError) else "Invalid file metadata"
            self.quarantined(name, sha256(raw).hexdigest(), reason)
            raise FeedError(reason) from None
        added = 0
        issues = []
        for info, xml, carrier in sorted(items, key=lambda item: item[0].published_at or ""):
            if info.reference:
                continue
            try:
                added += self.ingest_snapshot(info, xml, carrier, source)
            except ValueError as error:
                reason = str(error) if isinstance(error, FeedError) else "Invalid XML field or timestamp"
                self.quarantined(info.name, sha256(xml).hexdigest(), reason)
                issues.append(f"{info.name}: {reason}")
        return added, issues

    def downloaded(self, name, etag):
        return self.db.execute("SELECT 1 FROM downloads WHERE name=? AND etag=?", (name, etag)).fetchone()

    def record_download(self, name, etag):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO downloads VALUES (?,?)", (name, etag))

    def publish_private(self, state, failures):
        checked_at = now()
        latest = {}
        for house in HOUSES:
            row = self.db.execute("""
                SELECT accepted,data FROM snapshots WHERE house=?
                ORDER BY published DESC, rank DESC, sequence DESC LIMIT 1
            """, (house,)).fetchone()
            if row:
                latest[house] = {**decoded(row[1]), "ingestedAt": row[0]}
        accepted_at = self.db.execute("SELECT max(accepted) FROM snapshots").fetchone()[0]
        status = {"state": state, "checkedAt": checked_at, "lastSuccessfulIngestionAt": accepted_at,
                  "failures": failures, "mode": self.mode}
        if self.references:
            output = {"schemaVersion": 2, "mode": self.mode,
                      "source": "Victorian Electoral Commission results data feed",
                      "eventId": self.references["eventId"], "eventName": self.references["eventName"],
                      "status": status, "houses": self.viewer_houses(latest)}
            atomic(self.path / "private-view.json", encoded(output) + b"\n")
        atomic(self.path / "status.json", encoded(status) + b"\n")

    def viewer_houses(self, latest):
        result = {}
        for house in HOUSES:
            contests = self.references["contests"][house]
            current = latest.get(house)
            rows = current["results"] if current else {}
            histories = self.progression(house)
            annotations = self.references["operationalExceptions"]
            result[house] = {
                "publishedAt": current["publishedAt"] if current else None,
                "ingestedAt": current["ingestedAt"] if current else None,
                "variant": current["variant"] if current else None,
                "phase": current["phase"] if current else None,
                "warnings": [*self.references["warnings"], *(current["warnings"] if current else [])],
                "quarantined": current["quarantined"] if current else [],
                "statewide": statewide(house, contests, rows),
                "contests": [
                    {"id": key, "name": ref["name"], "candidates": ref["candidates"],
                     "groups": ref.get("groups", {}), "count": compact_result(rows.get(key)),
                     "history": histories.get(key, []),
                     "operationalExceptions": [item for item in annotations if item["contestId"] == key],
                     "analyticalCoverage": analytical_coverage(
                         rows.get(key), [item for item in annotations if item["contestId"] == key]
                     )}
                    for key, ref in sorted(contests.items(), key=lambda x: x[1]["name"])
                ],
            }
        return result

    def progression(self, house):
        history = {}
        recent = self.db.execute("""
            WITH ranked AS (
                SELECT data, published, row_number() OVER (
                    PARTITION BY published ORDER BY rank DESC, sequence DESC
                ) AS preference FROM snapshots WHERE house=?
            )
            SELECT data FROM ranked WHERE preference=1 ORDER BY published DESC LIMIT 15
        """, (house,)).fetchall()
        for data, in reversed(recent):
            frame = decoded(data)
            for key in self.references["contests"][house]:
                row = frame["results"].get(key) or {}
                first, pair = row.get("first") or {}, row.get("pair") or {}
                formal = first["formal"]["votes"] if first.get("status") == "reported" else None
                point = {"publishedAt": frame["publishedAt"], "formal": formal, "declared": row.get("declared"),
                         "pairStatus": pair.get("status"),
                         "pairVotes": {k: v["votes"] for k, v in pair.get("candidates", {}).items()}}
                previous = history.setdefault(key, [])
                if not previous or any(point[k] != previous[-1][k] for k in point if k != "publishedAt"):
                    previous.append(point)
        return history


def compact_result(row):
    if row is None:
        return None
    # Polling-location parcels and full validation detail remain in the private journal.
    return {key: value for key, value in row.items() if key != "places"}


def analytical_coverage(row, annotations):
    if not row or len(annotations) != 2 or not row["places"]:
        return None
    excluded = {item["pollingLocationId"] for item in annotations}
    places = {key: value for key, value in row["places"].items() if key not in excluded}
    reported = sum(1 for value in places.values() if (value["first"] or {}).get("status") == "reported")
    return {"reportedEligibleDetailRows": reported, "eligibleDetailRows": len(places)}


def statewide(house, contests, rows):
    reporting, formal, parties = 0, 0, {}
    for key, tally in rows.items():
        first = tally["first"]
        if first is None or first["status"] != "reported":
            continue
        reporting += 1
        formal += first["formal"]["votes"]
        if house != "L":
            continue
        candidates = contests[key]["candidates"]
        for candidate_id, number in first["candidates"].items():
            candidate = candidates[candidate_id]
            affiliation = candidate["affiliation"] or {}
            registered = affiliation.get("register") or {}
            official_id = affiliation.get("id")
            if official_id:
                identity = official_id
                label = registered.get("ballotName") or affiliation.get("feedName") or f"Affiliation {official_id}"
            elif candidate["independent"]:
                identity, label = "independent", "Independent candidates"
            else:
                identity, label = "unclassified", "Unregistered or unclassified affiliation"
            bucket = parties.setdefault(identity, {"name": label, "votes": 0})
            bucket["votes"] += number["votes"]
    return {"reporting": reporting, "expected": len(contests), "formal": formal if reporting else None,
            "primaries": sorted(parties.values(), key=lambda item: (-item["votes"], item["name"]))}
