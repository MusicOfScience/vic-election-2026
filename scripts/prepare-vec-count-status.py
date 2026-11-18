#!/usr/bin/env python3
"""Convert saved Victorian Electoral Commission Lower House XML snapshots into a count-status ledger."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

VEC = "http://www.vec.vic.gov.au"
EML = "urn:oasis:names:tc:evs:schema:eml"
MELBOURNE = ZoneInfo("Australia/Melbourne")


def node(parent, name, namespace=VEC):
    return parent.find(f"{{{namespace}}}{name}")


def children(parent, name, namespace=VEC):
    return parent.findall(f"{{{namespace}}}{name}")


def required(parent, name, namespace=VEC):
    result = node(parent, name, namespace)
    if result is None:
        raise ValueError(f"Missing {name}")
    return result


def identifier(parent, name):
    result = required(parent, name, EML)
    if not result.get("Id"):
        raise ValueError(f"Missing {name} Id")
    return result.get("Id")


def value(parent, name, namespace=VEC):
    return (required(parent, name, namespace).text or "").strip()


def root_from(path):
    raw = path.read_bytes()
    if len(raw) > 20_000_000 or b"<!DOCTYPE" in raw.upper() or b"\x00" in raw:
        raise ValueError(f"Unsupported XML input: {path.name}")
    return ET.fromstring(raw), sha256(raw).hexdigest()


def timestamp(text):
    result = datetime.fromisoformat(text)
    return (result if result.tzinfo is not None else result.replace(tzinfo=MELBOURNE)).astimezone(timezone.utc)


def count_number(text):
    if not text.isascii() or not text.isdecimal():
        raise ValueError(f"Invalid count: {text!r}")
    return int(text)


def coverage(element):
    returned = element.get("PollingPlacesReturned")
    expected = element.get("PollingPlacesExpected")
    if returned in (None, "") or expected in (None, ""):
        return None
    got, total = count_number(returned), count_number(expected)
    if got > total:
        raise ValueError("Returned locations exceed the number expected")
    return {"returned": got, "expected": total}


def vote_modes(total):
    block = node(total, "VotesByType")
    modes = {}
    if block is not None:
        for row in children(block, "Votes"):
            vote_type = row.get("Type")
            if not vote_type or vote_type in modes:
                raise ValueError("Missing or repeated vote type")
            modes[vote_type] = count_number((row.text or "").strip())
    return modes


def setup(path, event_id, election_id, live):
    root, digest = root_from(path)
    listing = required(root, "CandidateList", EML)
    if identifier(listing, "EventIdentifier") != event_id:
        raise ValueError("Candidate setup belongs to a different event")
    event = required(listing, "EventIdentifier", EML)
    event_name = value(event, "EventName", EML)
    if live and any(word in event_name.casefold() for word in ("test", "trial", "sample", "rehearsal")):
        raise ValueError("Rehearsal setup cannot enter a live ledger")
    elections = [e for e in children(listing, "Election", EML) if identifier(e, "ElectionIdentifier") == election_id]
    if len(elections) != 1:
        raise ValueError("Candidate setup has no unique matching election")
    roster = {}
    for contest in children(elections[0], "Contest", EML):
        key = identifier(contest, "ContestIdentifier")
        name = value(required(contest, "ContestIdentifier", EML), "ContestName", EML)
        people = {}
        for person in children(contest, "Candidate", EML):
            person_id = identifier(person, "CandidateIdentifier")
            person_name = value(required(person, "CandidateIdentifier", EML), "CandidateName", EML)
            if not person_name or person_id in people:
                raise ValueError(f"Invalid candidate identity in {name}")
            people[person_id] = person_name
        if key in roster or not people or not name:
            raise ValueError(f"Invalid setup contest {key}")
        roster[key] = {"name": name, "candidates": people}
    if not roster or (live and len(roster) != 88):
        raise ValueError("Live setup requires all 88 Assembly districts")
    return roster, digest, event_name


def tallies(section, roster):
    counts = {}
    for person in children(section, "Candidate"):
        key = identifier(person, "CandidateIdentifier")
        if key not in roster or key in counts:
            raise ValueError(f"Unreconciled candidate ID {key}")
        counts[key] = count_number(value(person, "Votes"))
    return counts


def parse_snapshot(path, roster, event_id, election_id, live):
    root, digest = root_from(path)
    if root.tag != f"{{{VEC}}}MediaFeed" or identifier(root, "EventIdentifier") != event_id:
        raise ValueError("Expected a VEC MediaFeed for the selected event")
    event_name = value(required(root, "EventIdentifier", EML), "EventName", EML)
    if live and any(word in event_name.casefold() for word in ("test", "trial", "sample", "rehearsal")):
        raise ValueError("Rehearsal results cannot enter a live ledger")
    election = required(root, "Election")
    if identifier(election, "ElectionIdentifier") != election_id:
        raise ValueError("Snapshot belongs to a different election")
    created = timestamp(root.get("Created", ""))
    if live:
        opening = datetime(2026, 11, 28, 18, tzinfo=MELBOURNE)
        if created < opening or created > datetime.now(timezone.utc):
            raise ValueError("Live snapshot timestamp is outside the count period")
    records = {}
    for contest in children(required(required(election, "House"), "Contests"), "Contest"):
        contest_id = identifier(contest, "ContestIdentifier")
        if contest_id in records or contest_id not in roster:
            raise ValueError(f"Unexpected or repeated district {contest_id}")
        names = roster[contest_id]["candidates"]
        declared = value(contest, "Declared").lower()
        if declared not in ("true", "false"):
            raise ValueError(f"Invalid declaration flag in {contest_id}")
        first = required(contest, "FirstPreferences")
        candidates = tallies(first, names)
        formal_node = required(first, "Formal")
        formal = count_number(value(formal_node, "Votes"))
        if candidates.keys() != names.keys() or sum(candidates.values()) != formal:
            raise ValueError(f"First preferences do not reconcile in {contest_id}")
        first_update = first.get("Updated")
        first_preferences = {"formal": formal, "coverage": coverage(first),
                             "updatedAt": timestamp(first_update).isoformat() if first_update else None,
                             "votes": candidates, "voteModes": vote_modes(formal_node)}
        pair = node(contest, "TwoCandidatePreferred")
        count = {"status": "unavailable", "votes": {}, "coverage": None, "updatedAt": None}
        if pair is not None:
            flag = pair.get("Maverick")
            if flag not in (None, "true"):
                raise ValueError(f"Unexpected Maverick attribute in {contest_id}")
            pair_votes = tallies(pair, names)
            if (flag and pair_votes) or len(pair_votes) not in (0, 2):
                raise ValueError(f"Invalid two-candidate count in {contest_id}")
            update = pair.get("Updated")
            count = {"status": "withheld" if flag else ("published" if sum(pair_votes.values()) else "unavailable"),
                     "votes": pair_votes, "coverage": coverage(pair),
                     "updatedAt": timestamp(update).isoformat() if update else None}
        records[contest_id] = {"declared": declared == "true", "first": first_preferences, "pair": count}
    if records.keys() != roster.keys():
        raise ValueError("Snapshot district coverage differs from the registered roster")
    return created, digest, root.get("Phase"), records


def build(candidates, snapshots, mode, event_id, election_id):
    live = mode == "live"
    roster, setup_digest, event_name = setup(candidates, event_id, election_id, live)
    observations = {}
    for path in snapshots:
        created, digest, phase, records = parse_snapshot(path, roster, event_id, election_id, live)
        if created in observations and observations[created][0] != digest:
            raise ValueError(f"Conflicting files at {created.isoformat()}")
        observations[created] = (digest, phase, records)
    histories = {key: [] for key in roster}
    state = {}
    frames = []
    for created, (digest, phase, records) in sorted(observations.items()):
        frames.append({"createdAt": created.isoformat(), "sha256": digest, "phase": phase})
        for key, record in records.items():
            previous, last_pair, series, interrupted = state.get(key, (None, None, 0, False))
            if record == previous:
                continue
            pair = record["pair"]
            current = tuple(sorted(pair["votes"])) if pair["status"] == "published" else None
            transition = None
            if current:
                if not last_pair:
                    series += 1
                    transition = "pair-published"
                elif current != last_pair:
                    series += 1
                    transition = "pair-changed"
                elif interrupted:
                    series += 1
                    transition = "pair-restored"
                last_pair, interrupted = current, False
            elif pair["status"] == "withheld" and (not previous or previous["pair"]["status"] != "withheld"):
                transition, interrupted = "pair-withheld", True
            elif last_pair:
                interrupted = True
            state[key] = record, last_pair, series, interrupted
            histories[key].append({"createdAt": created.isoformat(), **record,
                                   "series": series if current else None, "transition": transition})
    return {"schemaVersion": 1, "mode": mode, "eventId": event_id, "electionId": election_id,
            "eventName": event_name, "setupSha256": setup_digest, "frames": frames,
            "districts": {key: {**entry, "history": histories[key]} for key, entry in roster.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--mode", choices=("sample", "trial", "live"), required=True)
    parser.add_argument("--event-id", required=True, help="Explicit ID from the authorised setup register")
    parser.add_argument("--election-id", default="L")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("snapshots", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        data = build(args.candidates, args.snapshots, args.mode, args.event_id, args.election_id)
        previous = json.loads(args.output.read_text()) if args.output.exists() else None
        if previous and previous["mode"] == "live":
            lineage = ("mode", "eventId", "electionId", "setupSha256")
            if any(previous[k] != data[k] for k in lineage) or previous["frames"] != data["frames"][:len(previous["frames"])]:
                raise ValueError("A published live ledger can only be extended with the same roster and source history")
    except (ET.ParseError, OSError, ValueError) as error:
        parser.exit(1, f"Count ledger rejected: {error}\n")
    with NamedTemporaryFile(dir=args.output.parent, encoding="utf-8", mode="w", delete=False) as temporary:
        temporary.write(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    Path(temporary.name).replace(args.output)
    print(f"Prepared {len(data['districts'])} districts across {len(data['frames'])} {args.mode} snapshots")


if __name__ == "__main__":
    main()
