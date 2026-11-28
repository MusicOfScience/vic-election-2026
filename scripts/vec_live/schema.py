"""Normalise VEC State 2026 V2 references and full results snapshots."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import BadZipFile, ZipFile
from zoneinfo import ZoneInfo

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

EML = "{urn:oasis:names:tc:evs:schema:eml}"
AEC = "{http://www.aec.gov.au/xml/schema/mediafeed}"
VEC = "{http://www.vec.vic.gov.au}"
MELBOURNE = ZoneInfo("Australia/Melbourne")
OPENING = datetime(2026, 11, 28, 18, tzinfo=MELBOURNE)
TRIAL_DAY = datetime(2026, 11, 25, tzinfo=MELBOURNE).date()
MAX_ARCHIVE = 48_000_000
MAX_XML = 24_000_000
FILENAME = re.compile(
    r"(?P<event>(?:test)?state2026)mediafile"
    r"(?:(?P<reference>candidates|groupsandtickets|pollinglocations)v2\.(?:xml|zip)|"
    r"(?P<variant>litepp|lite|verbose)(?P<house>lh|uh)v2_"
    r"(?P<stamp>\d{8}_\d{6})\.(?:xml|zip))", re.IGNORECASE,
)
TEST_MARKER = re.compile(r"\b(?:test|sample|trial|rehearsal|training)\b", re.IGNORECASE)
VOTE_TYPES = frozenset(("Ordinary", "EVCEarly", "MobileVotingEarly", "Postal", "Early",
                        "MarkedAsVoted", "Provisional", "Absent"))
REFERENCE_KINDS = frozenset(("candidates", "groupsandtickets", "pollinglocations"))


class FeedError(ValueError):
    """A feed item did not meet the verified contract."""


@dataclass(frozen=True)
class FileType:
    name: str
    sample: bool
    reference: str | None
    variant: str | None
    house: str | None
    published_at: str | None


def identify(name):
    leaf = PurePosixPath(name).name
    match = FILENAME.fullmatch(leaf)
    if not match:
        return None
    stamp = match["stamp"]
    published = (datetime.strptime(stamp, "%Y%m%d_%H%M%S").replace(tzinfo=MELBOURNE)
                 .astimezone(timezone.utc).isoformat()) if stamp else None
    return FileType(leaf, match["event"].lower().startswith("test"),
                    match["reference"].lower() if match["reference"] else None,
                    match["variant"].lower() if match["variant"] else None,
                    {"lh": "L", "uh": "U"}.get(match["house"].lower()) if stamp else None,
                    published)


def xml(raw):
    if len(raw) > MAX_XML:
        raise FeedError("XML exceeds the size limit")
    try:
        return ElementTree.fromstring(raw, forbid_dtd=True)
    except (ElementTree.ParseError, DefusedXmlException):
        raise FeedError("Malformed or unsafe XML") from None


def files_in_zip(raw):
    """Read bounded members in memory and let ZipFile verify their CRCs."""
    if len(raw) > MAX_ARCHIVE:
        raise FeedError("ZIP exceeds the download size limit")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            names = [entry for entry in archive.infolist() if not entry.is_dir()]
            if (len(names) > 512 or sum(entry.file_size for entry in names) > MAX_ARCHIVE
                    or len({entry.filename for entry in names}) != len(names)):
                raise FeedError("ZIP exceeds member limits or repeats a member")
            for entry in names:
                yield entry.filename, archive.read(entry)
    except (BadZipFile, RuntimeError, NotImplementedError, OSError):
        raise FeedError("ZIP integrity or compression check failed") from None


def extract_inputs(name, raw):
    """Accept an untouched VEC ZIP, a SharePoint bulk ZIP, or a reference XML."""
    info = identify(name)
    if name.lower().endswith(".xml"):
        if info is None:
            raise FeedError("Unrecognised VEC XML filename")
        yield info, raw, None
        return
    if not name.lower().endswith(".zip"):
        raise FeedError("Expected VEC ZIP or XML")
    members = list(files_in_zip(raw))
    if info:
        label = "Reference" if info.reference else "Results"
        if len(members) != 1 or PurePosixPath(members[0][0]).stem.lower() != Path(info.name).stem.lower():
            raise FeedError(f"{label} ZIP must contain its matching XML")
        if not members[0][0].lower().endswith(".xml"):
            raise FeedError(f"{label} ZIP member is not XML")
        # Archive the verified carrier but record reference provenance under its XML name.
        yield identify(members[0][0]) if info.reference else info, members[0][1], raw
        return
    recognised = [(member, content) for member, content in members if identify(member)]
    if not recognised:
        raise FeedError("ZIP contains no recognised VEC V2 files")
    for member, content in recognised:
        yield from extract_inputs(member, content)


def required(parent, tag):
    child = parent.find(tag)
    if child is None:
        raise FeedError(f"Missing {tag.rsplit('}', 1)[-1]}")
    return child


def attr_id(element):
    key = element.get("Id", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", key):
        raise FeedError("Missing or invalid official identifier")
    return key


def key(parent, tag):
    return attr_id(required(parent, tag))


def stripped(element):
    return (element.text or "").strip()


def text(parent, tag):
    return stripped(required(parent, tag))


def count(value):
    if not re.fullmatch(r"[0-9]{1,10}", value):
        raise FeedError("Invalid vote or position count")
    return int(value)


def optional_count(parent, tag):
    element = parent.find(tag)
    if element is None or not stripped(element):
        return None
    return count(stripped(element))


def optional_text(parent, tag):
    element = parent.find(tag)
    return stripped(element) or None if element is not None else None


def stamp(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=MELBOURNE)).astimezone(timezone.utc).isoformat()


def check_event(element, mode, info):
    identifier = required(element, EML + "EventIdentifier")
    event_id, name = attr_id(identifier), text(identifier, EML + "EventName")
    if not name:
        raise FeedError("Missing event name")
    if mode == "production" and (info.sample or event_id == "18738" or TEST_MARKER.search(name)):
        raise FeedError("Sample or trial data cannot enter production")
    if mode == "sample" and (not info.sample or event_id != "18738" or not TEST_MARKER.search(name)):
        raise FeedError("Input does not match the verified 2026 sample event")
    if mode == "trial" and (info.sample or event_id == "18738"):
        raise FeedError("The September sample event must stay in sample mode")
    return event_id, name


def affiliation(identifier):
    if identifier is None:
        return None
    return {"id": attr_id(identifier) if identifier.get("Id") else None,
            "feedName": optional_text(identifier, EML + "RegisteredName")}


def unique(mapping, identifier, record):
    if identifier in mapping:
        raise FeedError(f"Repeated official identifier {identifier}")
    mapping[identifier] = record


def candidate_references(listing):
    contests = {"L": {}, "U": {}}
    seen_houses = set()
    for election in listing.findall(EML + "Election"):
        house = key(election, EML + "ElectionIdentifier")
        if house not in contests or house in seen_houses:
            raise FeedError("Unexpected or duplicate reference house")
        seen_houses.add(house)
        for contest in election.findall(EML + "Contest"):
            candidates = {}
            for person in contest.findall(EML + "Candidate"):
                ident = required(person, EML + "CandidateIdentifier")
                name = text(ident, EML + "CandidateName")
                if not name:
                    raise FeedError("Missing candidate display name")
                unique(candidates, attr_id(ident), {
                    "name": name, "ballotPosition": optional_count(person, EML + "BallotPosition"),
                    "independent": {"yes": True, "no": False}.get(person.get("Independent")),
                    "affiliation": affiliation(person.find(f"{EML}Affiliation/{EML}AffiliationIdentifier")),
                })
            ident = required(contest, EML + "ContestIdentifier")
            name = text(ident, EML + "ContestName")
            if not name or not candidates:
                raise FeedError("Empty candidate reference contest")
            unique(contests[house], attr_id(ident), {
                "name": name, "districtId": key(contest, EML + "PollingDistrictIdentifier"),
                "enrolment": optional_count(contest, EML + "Enrolment"), "candidates": candidates,
            })
    return contests


def group_references(root, contests):
    election = required(root, AEC + "Election")
    if key(election, EML + "ElectionIdentifier") != "U":
        raise FeedError("Group reference does not describe the Council")
    seen = set()
    warnings = []
    for contest in required(election, AEC + "Contests").findall(AEC + "Contest"):
        contest_id = key(contest, EML + "ContestIdentifier")
        ref = contests.get(contest_id)
        if (ref is None or contest_id in seen
                or key(contest, AEC + "PollingDistrictIdentifier") != ref["districtId"]):
            raise FeedError("Group reference contest does not reconcile with candidates")
        seen.add(contest_id)
        groups = {}
        members = set()
        for group in contest.findall(AEC + "Group"):
            ident = required(group, AEC + "GroupIdentifier")
            candidate_ids = []
            for person in group.findall(AEC + "Candidate"):
                candidate_id = key(person, EML + "CandidateIdentifier")
                candidate = ref["candidates"].get(candidate_id)
                if candidate is None or candidate_id in members:
                    raise FeedError("Council group candidate ID is unknown or repeated")
                group_party = affiliation(person.find(EML + "AffiliationIdentifier"))
                candidate_party = candidate["affiliation"]
                if group_party and candidate_party and group_party["id"] != candidate_party["id"]:
                    warnings.append(f"Council reference affiliation disagreement for candidate {candidate_id}")
                candidate["groupAffiliation"] = group_party
                members.add(candidate_id)
                candidate_ids.append(candidate_id)
            unique(groups, attr_id(ident), {
                "name": text(ident, AEC + "GroupName"), "ticket": optional_text(ident, AEC + "Ticket"),
                "candidates": candidate_ids,
            })
        ref["groups"] = groups
        ref["ungrouped"] = sorted(ref["candidates"].keys() - members)
    if seen != contests.keys():
        raise FeedError("Group reference is missing Council contests")
    return warnings


def location_references(root):
    districts = {}
    for district in root.findall(AEC + "PollingDistrict"):
        ident = required(district, AEC + "PollingDistrictIdentifier")
        places = {}
        block = district.find(AEC + "PollingPlaces")
        if block is not None:
            for place in block.findall(AEC + "PollingPlace"):
                place_id = required(place, AEC + "PollingPlaceIdentifier")
                address = place.find(AEC + "Address")
                unique(places, attr_id(place_id), {
                    "name": place_id.get("Name"), "classification": place_id.get("Classification"),
                    "address": {tag: optional_text(address, AEC + tag) for tag in (
                        "AddressLongitude", "AddressLatitude", "AddressLine1", "AddressLine2", "Suburb", "Postcode"
                    )} if address is not None else None,
                })
        unique(districts, attr_id(ident), {"name": optional_text(ident, AEC + "Name"), "locations": places})
    return districts


def apply_exceptions(register, references, mode):
    if mode != "production":
        return []
    annotations = []
    for row in register["exceptions"]:
        assembly = references["contests"]["L"]
        contest_ids = [k for k, c in assembly.items() if c["name"] == row["districtLabel"]]
        if len(contest_ids) != 1:
            references["warnings"].append("Mordialloc exception could not be joined to one reference contest")
            continue
        contest_id = contest_ids[0]
        district_id = assembly[contest_id]["districtId"]
        locations = references["districts"].get(district_id, {}).get("locations", {})
        for place in row["locations"]:
            matches = [k for k, v in locations.items() if (v["name"] or "").strip().casefold()
                       == place["referenceLabel"].casefold()]
            if len(matches) != 1:
                references["warnings"].append(f"Operational exception location unresolved: {place['referenceLabel']}")
                continue
            place_id = matches[0]
            annotations.append({**place, "contestId": contest_id, "districtId": district_id,
                                "pollingLocationId": place_id, "sourceDate": row["sourceDate"]})
    return annotations


def reference_root(info, raw, mode):
    root = xml(raw)
    tags = {"candidates": EML + "EML", "groupsandtickets": AEC + "SenateGroups",
            "pollinglocations": AEC + "PollingDistrictList"}
    if root.tag != tags[info.reference]:
        raise FeedError("Unexpected reference XML namespace or root")
    if info.reference == "candidates":
        root = required(root, EML + "CandidateList")
    return root, check_event(root, mode, info)


def load_references(entries, mode, register):
    if set(entries) != REFERENCE_KINDS:
        raise FeedError("All three official V2 references are required")
    events, roots, digests = {}, {}, {}
    for kind, (info, raw) in entries.items():
        roots[kind], events[kind] = reference_root(info, raw, mode)
        digests[kind] = sha256(raw).hexdigest()
    event_id, event_name = events["candidates"]
    if len(set(events.values())) != 1:
        raise FeedError("Reference files disagree on event identity")
    contests = candidate_references(roots["candidates"])
    districts = location_references(roots["pollinglocations"])
    warnings = group_references(roots["groupsandtickets"], contests["U"])
    if not contests["L"] or not contests["U"] or not districts:
        raise FeedError("References omit required contest or location coverage")
    if mode == "production" and (len(contests["L"]), len(contests["U"])) != (88, 8):
        raise FeedError("Production candidate setup must cover 88 districts and eight regions")
    references = {"eventId": event_id, "eventName": event_name, "schemaVersion": 2,
                  "contests": contests, "districts": districts, "referenceSha256": digests,
                  "warnings": warnings}
    affiliations = json.loads((METADATA / "vec-affiliations-2026.json").read_text())["affiliations"]
    unmatched = set()
    for house in contests.values():
        for contest in house.values():
            for person in contest["candidates"].values():
                for field in ("affiliation", "groupAffiliation"):
                    party = person.get(field)
                    if party and party["id"]:
                        party["register"] = affiliations.get(party["id"])
                        if party["register"] is None:
                            unmatched.add(party["id"])
    if unmatched:
        warnings.append("Unmapped official affiliation IDs: " + ", ".join(sorted(unmatched)))
    references["operationalExceptions"] = apply_exceptions(register, references, mode)
    return references


def coverage(element):
    returned = element.get("PollingPlacesReturned")
    expected = element.get("PollingPlacesExpected")
    if returned in (None, "") or expected in (None, ""):
        return None
    got, total = count(returned), count(expected)
    if got > total:
        raise FeedError("Returned locations exceed expected locations")
    return {"returned": got, "expected": total}


def votes(element):
    total = count(text(element, VEC + "Votes"))
    modes = {}
    block = element.find(VEC + "VotesByType")
    if block is not None:
        for item in block.findall(VEC + "Votes"):
            vote_type = item.get("Type")
            if vote_type not in VOTE_TYPES:
                raise FeedError("Unsupported V2 vote type")
            unique(modes, vote_type, count(stripped(item)))
        if sum(modes.values()) != total:
            raise FeedError("Vote-type breakdown does not reconcile")
    return {"votes": total, "voteTypes": modes if block is not None else None}


def result_candidates(section, tag, roster):
    result = {}
    for row in section.findall(VEC + tag):
        candidate_id = key(row, EML + "CandidateIdentifier")
        if candidate_id not in roster:
            raise FeedError(f"Unreconciled result candidate {candidate_id}")
        elected = optional_text(row, VEC + "Elected")
        if elected not in (None, "true", "false"):
            raise FeedError("Invalid candidate elected flag")
        unique(result, candidate_id, {**votes(row), "elected": elected == "true" if elected else None})
    return result


def primary(section, house, roster, *, parcel=False):
    if section is None:
        return None
    updated = stamp(section.get("Updated"))
    totals = {}
    for name in ("Formal", "Informal", "Total"):
        element = section.find(VEC + name)
        if element is not None:
            totals[name.lower()] = votes(element)
    if not totals and len(section) == 0:
        return None
    if totals.keys() != {"formal", "informal", "total"}:
        raise FeedError("Incomplete first-preference totals")
    if (totals["formal"]["votes"] + totals["informal"]["votes"] != totals["total"]["votes"]):
        raise FeedError("Formal and informal votes do not reconcile to total")
    groups = {}
    if house == "L":
        candidates = result_candidates(section, "Candidate", roster["candidates"])
        expected = roster["candidates"].keys()
    else:
        candidates = result_candidates(section, "UngroupedCandidate", roster["ungrouped"])
        expected = set(roster["ungrouped"])
        for row in section.findall(VEC + "Group"):
            group_id = key(row, VEC + "GroupIdentifier")
            if group_id not in roster["groups"]:
                raise FeedError(f"Unreconciled Council group {group_id}")
            group = votes(required(row, VEC + "GroupVotes"))
            atl = votes(required(row, VEC + "TicketVotes"))["votes"]
            if atl > group["votes"]:
                raise FeedError("Above-the-line votes exceed total group first preferences")
            unique(groups, group_id, {**group, "aboveTheLine": atl, "belowTheLine": group["votes"] - atl})
    if (sum(row["votes"] for row in (*candidates.values(), *groups.values())) != totals["formal"]["votes"]
            or (not parcel and (candidates.keys() != expected
                                or groups.keys() != roster.get("groups", {}).keys()))):
        raise FeedError("First-preference results do not reconcile with formal votes or reference roster")
    modes = totals["total"]["voteTypes"]
    if modes is not None:
        formal_modes, informal_modes = totals["formal"]["voteTypes"], totals["informal"]["voteTypes"]
        if formal_modes is None or informal_modes is None or any(
            formal_modes.get(k, 0) + informal_modes.get(k, 0) != modes.get(k, 0)
            for k in modes.keys() | formal_modes.keys() | informal_modes.keys()
        ):
            raise FeedError("Formal and informal vote-type totals do not reconcile")
    state = "reported" if updated or totals["total"]["votes"] else "unavailable"
    return {"status": state, "updatedAt": updated, "coverage": coverage(section), **totals,
            "candidates": candidates, "groups": groups}


def preferred(section, roster, *, blocked=False):
    if section is None:
        return {"status": "withheld" if blocked else "unavailable", "candidates": {},
                "updatedAt": None, "coverage": None}
    flag = section.get("Maverick")
    if flag not in (None, "true"):
        raise FeedError("Invalid Maverick attribute")
    updated = stamp(section.get("Updated"))
    reported = result_candidates(section, "Candidate", roster)
    if flag and reported:
        raise FeedError("Maverick result contains candidate counts")
    if len(reported) not in (0, 2):
        raise FeedError("2CP result does not have two candidates")
    return {"status": "withheld" if blocked or flag else "reported" if reported else "unavailable",
            "updatedAt": updated, "coverage": coverage(section),
            "candidates": {} if blocked else reported}


def known_locations(reference, contest):
    district_id = contest["districtId"]
    districts = reference["districts"]
    if "groups" not in contest:
        return districts.get(district_id, {}).get("locations", {})
    # Council results report district polling locations. IDs are stable in the
    # polling reference even where a separate region membership file is absent.
    locations = {}
    for district in districts.values():
        for location_id, row in district["locations"].items():
            if location_id in locations and locations[location_id] != row:
                raise FeedError(f"Ambiguous Council polling-location ID {location_id}")
            locations[location_id] = row
    return locations


def snapshot(info, raw, reference, mode):
    root = xml(raw)
    if root.tag != VEC + "MediaFeed" or info.reference:
        raise FeedError("Unexpected result XML namespace or root")
    if check_event(root, mode, info) != (reference["eventId"], reference["eventName"]):
        raise FeedError("Results do not belong to the registered reference event")
    published = datetime.fromisoformat(info.published_at)
    created = stamp(root.get("Created"))
    if not created or abs((published - datetime.fromisoformat(created)).total_seconds()) > 90:
        raise FeedError("Filename and XML publication timestamps disagree")
    if mode == "production" and (published < OPENING or published > datetime.now(timezone.utc)):
        raise FeedError("Production snapshot is outside the live count window")
    if mode == "trial" and published.astimezone(MELBOURNE).date() != TRIAL_DAY:
        raise FeedError("Trial snapshot is outside the 25 November rehearsal date")
    if root.get("Verbose") != ("true" if info.variant == "verbose" else "false"):
        raise FeedError("Result variant does not agree with XML")
    election = required(root, VEC + "Election")
    house = info.house
    if key(election, EML + "ElectionIdentifier") != house:
        raise FeedError("Result filename and XML houses disagree")
    contests = reference["contests"][house]
    results = {}
    warnings = []
    quarantined = []
    closed_locations = {item["pollingLocationId"] for item in reference["operationalExceptions"]
                        if item.get("expectedZero")}
    body = required(election, VEC + ("House" if house == "L" else "Senate"))
    for contest in required(body, VEC + "Contests").findall(VEC + "Contest"):
        contest_id = key(contest, EML + "ContestIdentifier")
        roster = contests.get(contest_id)
        if roster is None or key(contest, VEC + "PollingDistrictIdentifier") != roster["districtId"]:
            raise FeedError(f"Unreconciled result contest or district {contest_id}")
        declared = text(contest, VEC + "Declared")
        if declared not in ("true", "false"):
            raise FeedError("Invalid declaration flag")
        first = primary(contest.find(VEC + "FirstPreferences"), house, roster)
        pair = preferred(contest.find(VEC + "TwoCandidatePreferred"), roster["candidates"]) if house == "L" else None
        places = {}
        locations = known_locations(reference, roster)
        block = contest.find(VEC + "PollingPlaces")
        if block is not None:
            for place in block.findall(VEC + "PollingPlace"):
                location_id = key(place, VEC + "PollingPlaceIdentifier")
                if location_id not in locations:
                    raise FeedError(f"Unreconciled polling-location ID {location_id}")
                try:
                    place_first = primary(place.find(VEC + "FirstPreferences"), house, roster, parcel=True)
                except FeedError as error:
                    quarantined.append({"contestId": contest_id, "pollingLocationId": location_id,
                                        "section": "first", "reason": str(error)})
                    place_first = None
                if location_id in closed_locations and place_first and place_first["total"]["votes"]:
                    warnings.append(f"Closed location {location_id} has a nonzero count; reconcile with the VEC")
                place_pair = preferred(place.find(VEC + "TwoCandidatePreferred"), roster["candidates"],
                                       blocked=pair["status"] == "withheld") if pair is not None else None
                if place_pair and place_pair["status"] == "reported" and place_pair["candidates"].keys() != pair["candidates"].keys():
                    warnings.append(f"Incompatible 2CP pairing at location {location_id}")
                    place_pair = {**place_pair, "status": "incompatible", "candidates": {}}
                unique(places, location_id, {"updatedAt": stamp(place.get("Updated")),
                                           "first": place_first, "pair": place_pair})
        aggregate_only = bool(first and first["status"] == "reported" and block is None
                              and first["total"]["voteTypes"] is None and info.variant != "lite")
        quota = contest.find(VEC + "Quota")
        unique(results, contest_id, {"declared": declared == "true", "updatedAt": stamp(contest.get("Updated")),
                                     "first": first, "pair": pair, "places": places,
                                     "aggregateOnly": aggregate_only,
                                     "quota": count(stripped(quota)) if quota is not None and stripped(quota) else None,
                                     "quotaProvisional": quota is not None and quota.get("Provisional") == "true"})
    if results and results.keys() != contests.keys():
        warnings.append(f"Snapshot includes {len(results)} of {len(contests)} reference contests")
    return {"house": house, "schemaVersion": 2, "variant": info.variant, "phase": root.get("Phase"),
            "publishedAt": info.published_at, "createdAt": created, "results": results,
            "warnings": warnings, "quarantined": quarantined}


METADATA = Path(__file__).resolve().parents[2] / "metadata"


def register_from_repository():
    return json.loads((METADATA / "vec-election-operations-2026.json").read_text())
