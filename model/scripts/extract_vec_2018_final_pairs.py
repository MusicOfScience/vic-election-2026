#!/usr/bin/env python3
"""Build the scoring-only 2018 Assembly final-pair artefact from governed VEC pages."""
from __future__ import annotations

import csv, hashlib, html, json, re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "metadata/vec-historical-assembly-primary-source-manifest.csv"
CROSSWALK = ROOT / "model/config/historical-party-family-crosswalk.json"
OUT = ROOT / "model/data/processed/vec_2018_assembly_final_pairs.csv"

def norm(value: str) -> str: return " ".join(value.split()).casefold()
def sha(payload: bytes) -> str: return hashlib.sha256(payload).hexdigest()
def family(label: str, aliases: dict[str, str]) -> str:
    key = norm(label)
    if key not in aliases: raise ValueError(f"unadjudicated VEC party label: {label!r}")
    return aliases[key]

def page(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "vic-election-2026-evidence/1.0"}), timeout=60) as response:
        return response.read()

def parse_distribution(source: str, url: str, party_by_candidate: dict[str, str], family_by_candidate: dict[str, str], aliases: dict[str, str]) -> tuple[list[tuple[str, str, int, float, str]], str, str]:
    for rows in table_rows(source):
        if not rows or not rows[0] or rows[0][0] != "": continue
        final = next((row for row in rows[1:] if row and norm(row[0]) == "final total"), None)
        if not final: continue
        names = rows[0][1:-1]; values = final[1:1 + len(names)]
        parsed = []
        for name, value in zip(names, values):
            if not value: continue
            candidate = name.strip(); raw = party_by_candidate.get(norm(candidate))
            resolved_family = family(raw, aliases) if raw else family_by_candidate.get(norm(candidate))
            if not resolved_family: raise ValueError(f"unadjudicated distribution party for candidate: {candidate}")
            parsed.append((candidate, raw, int(value.replace(",", "")), 0.0, resolved_family))
        if len(parsed) < 2: continue
        parsed = sorted(parsed, key=lambda row: row[2], reverse=True)[:2]
        total = sum(row[2] for row in parsed)
        parsed = [(a,b,c,float(c / total * 100),e) for a,b,c,_,e in parsed]
        return parsed, "distribution-page-final-total", url
    raise ValueError("distribution page has no FINAL TOTAL row")

def table_rows(source: str) -> list[list[str]]:
    tables = []
    for table in re.findall(r"(?is)<table[^>]*>(.*?)</table>", source):
        rows = []
        for row in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", table):
            cells = [" ".join(html.unescape(re.sub(r"(?s)<[^>]+>", " ", cell)).split()) for cell in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row)]
            if cells: rows.append(cells)
        tables.append(rows)
    return tables

def extract(entry: dict, aliases: dict[str, str], family_by_candidate: dict[str, str]) -> dict:
    payload = page(entry["source_url"])
    digest = sha(payload)
    if digest != entry["sha256"]: raise ValueError(f"source fingerprint changed for {entry['district_name']}: {digest}")
    source = payload.decode("utf-8", "replace")
    party_by_candidate = {}
    for rows in table_rows(source):
        if rows and rows[0] and rows[0][0].lower() == "candidate" and len(rows[0]) >= 3 and "1st pref" in norm(rows[0][2]):
            party_by_candidate.update({norm(row[0]): row[1] for row in rows[1:] if len(row) >= 2 and row[0]})
    elected = re.search(r'Elected member</h3>.*?bold-text">([^<]+).*?italic">([^<]*)', source, re.I | re.S)
    if not elected: raise ValueError(f"{entry['district_name']}: elected member missing")
    elected_candidate, elected_raw = (x.strip() for x in elected.groups())
    final = None; table_kind = "results-after-distribution"
    for rows in table_rows(source):
        if rows and rows[0] and norm(rows[0][0]) == "candidate" and len(rows[0]) >= 4 and "votes after distribution" in norm(rows[0][2]):
            final = [row for row in rows[1:] if len(row) >= 4 and re.fullmatch(r"[0-9,]+", row[2])]
            break
    outcome_source_url = entry["source_url"]
    outcome_source_sha = digest
    if final is not None and len(final) != 2:
        final = None
    if final is None:
        for rows in table_rows(source):
            if rows and rows[0] and rows[0][0].lower() == "candidate" and len(rows[0]) >= 3 and "preferred votes" in norm(rows[0][2]):
                final = [row for row in rows[1:] if len(row) >= 4 and re.fullmatch(r"[0-9,]+", row[2])]
                table_kind = "two-candidate-preferred-final-page"
                break
    if final is None or len(final) != 2:
        link = re.search(r'href=["\']([^"\']*distribution[^"\']*district\.html)["\']', source, re.I)
        if link:
            outcome_source_url = urljoin(entry["source_url"], link.group(1)); distribution_payload = page(outcome_source_url); outcome_source_sha = sha(distribution_payload)
            final, table_kind, _ = parse_distribution(distribution_payload.decode("utf-8", "replace"), outcome_source_url, party_by_candidate, family_by_candidate, aliases)
    if not final or len(final) != 2: raise ValueError(f"{entry['district_name']}: final distribution must contain exactly two candidates")
    parsed = []
    for row in final:
        if len(row) < 4: raise ValueError(f"{entry['district_name']}: malformed final distribution row")
        votes = int(str(row[2]).replace(",", "")); percent = float(str(row[3]).replace("%", ""))
        raw_party = row[1] or party_by_candidate.get(norm(row[0]))
        resolved_family = family(raw_party, aliases) if raw_party else family_by_candidate.get(norm(row[0]))
        if not resolved_family: raise ValueError(f"unadjudicated VEC party label for candidate: {row[0]}")
        parsed.append((row[0], raw_party, votes, percent, resolved_family))
    if not any(norm(row[0]) == norm(elected_candidate) for row in parsed): raise ValueError(f"{entry['district_name']}: elected member not in final pair")
    winner = max(parsed, key=lambda row: row[2])
    if norm(winner[0]) != norm(elected_candidate): raise ValueError(f"{entry['district_name']}: elected member does not have greater final votes")
    if abs(sum(row[3] for row in parsed) - 100.0) > 0.25: raise ValueError(f"{entry['district_name']}: final-pair percentages do not reconcile")
    return {"election_id":"vic_la_2018", "district_id": re.sub(r"[^a-z0-9]+", "-", entry["district_name"].casefold()).strip("-"), "district_name":entry["district_name"], "source_url":entry["source_url"], "source_sha256":digest,
      "elected_candidate":elected_candidate, "elected_party_raw":elected_raw, "elected_party_family":family(elected_raw, aliases) if elected_raw else family_by_candidate.get(norm(elected_candidate)),
      "finalist_1_candidate":parsed[0][0], "finalist_1_party_raw":parsed[0][1], "finalist_1_party_family":parsed[0][4], "finalist_1_votes":parsed[0][2], "finalist_1_percent":parsed[0][3],
      "finalist_2_candidate":parsed[1][0], "finalist_2_party_raw":parsed[1][1], "finalist_2_party_family":parsed[1][4], "finalist_2_votes":parsed[1][2], "finalist_2_percent":parsed[1][3],
      "winner_party_family":winner[4], "final_pair_family_label":f"{parsed[0][4]}-{parsed[1][4]}", "outcome_table_kind":table_kind, "outcome_source_url":outcome_source_url, "outcome_source_sha256":outcome_source_sha, "alp_won":int(winner[4] == "ALP")}

def main() -> None:
    crosswalk = json.loads(CROSSWALK.read_text())["aliases"]
    aliases = {norm(alias): fam for fam, values in crosswalk.items() for alias in values}
    with MANIFEST.open(newline="") as handle: entries = [row for row in csv.DictReader(handle) if row["election_year"] == "2018" and row["contest"] == "general-election" and row["district_name"] != "[summary]"]
    if len(entries) != 88: raise ValueError(f"expected 88 governed 2018 pages, found {len(entries)}")
    candidate_rows = list(csv.DictReader((ROOT / "model/data/processed/vec_2018_assembly_candidate_primaries.csv").open()))
    family_by_candidate = {norm(row["candidate_name"]): row["party_family"] for row in candidate_rows}
    rows = [extract(entry, aliases, family_by_candidate) for entry in entries]
    if len({row["district_id"] for row in rows}) != 88: raise ValueError("district ids are not unique")
    fields = list(rows[0]); OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(sorted(rows, key=lambda row: row["district_id"]))
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "rows": len(rows), "sha256": sha(OUT.read_bytes())}))

if __name__ == "__main__": main()
