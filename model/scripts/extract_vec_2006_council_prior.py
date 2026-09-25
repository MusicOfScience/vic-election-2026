#!/usr/bin/env python3
"""Extract a prediction-safe 2006 Council regional family prior for 2010."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


BASE = "https://itsitecoreblobvecprd01.blob.core.windows.net/public-files/historical-results/state2006/"
SUMMARY = BASE + "state2006resultsummary.html"
REGION_LINKS = {
    "eastern-metropolitan": "state2006resulteasternmetropolitanregion.html",
    "eastern-victoria": "state2006resulteasternvictoriaregion.html",
    "northern-metropolitan": "state2006resultnorthernmetropolitanregion.html",
    "northern-victoria": "state2006resultnorthernvictoriaregion.html",
    "south-eastern-metropolitan": "state2006resultsoutheasternmetropolitanregion.html",
    "southern-metropolitan": "state2006resultsouthernmetropolitanregion.html",
    "western-metropolitan": "state2006resultwesternmetropolitanregion.html",
    "western-victoria": "state2006resultwesternvictoriaregion.html",
}
FAMILIES = ("ALP", "LIB_NAT", "GRN", "OTH_IND")


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.table=None; self.row=None; self.cell=None; self.title=""
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=="table": self.table=[]; self.title=attrs.get("title") or ""
        elif self.table is not None and tag=="tr": self.row=[]
        elif self.row is not None and tag in {"td","th"}: self.cell=[]
    def handle_endtag(self, tag):
        if tag in {"td","th"} and self.row is not None and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split())); self.cell=None
        elif tag=="tr" and self.table is not None and self.row is not None:
            if self.row: self.table.append(self.row)
            self.row=None
        elif tag=="table" and self.table is not None:
            self.tables.append((self.title,self.table)); self.table=None
    def handle_data(self,data):
        if self.cell is not None: self.cell.append(data)


def fetch(url):
    with urlopen(Request(url,headers={"User-Agent":"vic-election-2026 historical evidence extractor"}),timeout=60) as r: return r.read()


def family(raw):
    value=raw.upper()
    if "LABOR" in value or value=="ALP": return "ALP"
    if "LIBERAL" in value or "NATIONAL" in value: return "LIB_NAT"
    if "GREEN" in value: return "GRN"
    return "OTH_IND"


def main():
    rows=[]; sources=[]
    for region_id, name in REGION_LINKS.items():
        url=BASE+name; payload=fetch(url); sources.append({"regionId":region_id,"url":url,"sha256":hashlib.sha256(payload).hexdigest(),"evidenceAvailableBy":"2006-11-25"})
        p=Tables(); p.feed(payload.decode("utf-8",errors="replace")); tables=[r for t,r in p.tables if t.lower()=="first preference votes"]
        if len(tables)!=1: raise ValueError(f"{region_id}: expected one first preference table")
        votes={f:0 for f in FAMILIES}; total=0
        for row in tables[0][1:]:
            if len(row)>=3 and row[2].replace(",","").isdigit():
                n=int(row[2].replace(",","")); votes[family(row[1])]+=n; total+=n
        for f in FAMILIES:
            rows.append({"cycle_id":"vic_lc_2010","prior_cycle":"vic_lc_2006","region_id":region_id,"party_family":f,"first_preference_votes":votes[f],"formal_votes":total,"source_url":url,"source_sha256":sources[-1]["sha256"],"evidence_available_by":"2006-11-25","target_outcome_dependency":"false"})
    out=Path("model/data/validation/historical-replay-2010-council-prior.csv"); out.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0])
    with out.open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)
    audit={"schemaVersion":1,"cycleId":"vic_la_2010","priorCycle":"vic_lc_2006","regionCount":8,"seatsPerRegion":5,"boundaryContinuity":"direct-eight-region-system-confirmed-by-official-2006-region-pages-and-2010-cycle-rule","targetOutcomeDependency":False,"sources":sources}
    Path("metadata/historical-replay-2010-council-prior-audit.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__": main()
