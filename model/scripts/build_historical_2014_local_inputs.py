"""Assemble the 2014 prediction-safe local input from prior-election evidence."""
from __future__ import annotations
import ast, csv, hashlib, json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "model/data/validation/historical-replay-2014-assembly-notional-baseline.csv"
PRIOR = ROOT / "model/data/processed/vec_2010_assembly_family_primaries.csv"
CROSSWALK = ROOT / "model/data/processed/historical_2014_crosswalk_core_features_long.csv"
MASK = ROOT / "model/data/validation/historical-replay-2014-ballot-mask.csv"
OUT = ROOT / "model/data/validation/historical-replay-2014-local-inputs.csv"
AUDIT = ROOT / "metadata/historical-replay-2014-input-audit.json"
FAMILIES = ["ALP", "LIB_NAT", "GRN", "OTH_IND"]
FEATURES = ["mortgage_share", "renter_share", "owned_outright_share", "separate_house_share", "apartment_share", "age_18_34_share", "age_65_plus_share"]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    baseline = pd.read_csv(BASELINE)
    prior = pd.read_csv(PRIOR)
    prior["model_family"] = prior.party_family.map({"ALP":"ALP", "Coalition":"LIB_NAT", "Greens":"GRN", "One Nation":"OTH_IND", "Other/Independent":"OTH_IND"})
    grouped = prior.groupby(["district_name", "model_family"], as_index=False).first_preference_votes.sum()
    pivot = grouped.pivot(index="district_name", columns="model_family", values="first_preference_votes").fillna(0)
    for f in FAMILIES:
        if f not in pivot: pivot[f] = 0.0
    pivot = pivot[FAMILIES].div(pivot[FAMILIES].sum(axis=1), axis=0)
    state = pivot.mean(axis=0)
    cross = pd.read_csv(CROSSWALK)
    cross["district_key"] = cross.district_name.str.strip().str.upper()
    features = cross.pivot(index="district_key", columns="feature_id", values="value").reset_index()
    mask = pd.read_csv(MASK)
    mask["district_key"] = mask.district_name.str.strip().str.upper()
    rows=[]
    for _, b in baseline.sort_values("district_id").iterrows():
        key = b.district_name.strip().upper()
        local = pivot.loc[b.district_name] if b.district_name in pivot.index else state
        status = "same-name-2010-prior" if b.district_name in pivot.index else "statewide-prior-fallback-for-redistributed-seat"
        m = mask.loc[mask.district_key == key]
        if len(m) != 1: raise ValueError(f"missing ballot mask {b.district_name}")
        ballot = ast.literal_eval(m.iloc[0].ballot_active_families)
        frow = features.loc[features.district_key == key]
        if len(frow) != 1: raise ValueError(f"missing crosswalk feature row {b.district_name}")
        row={"cycle_id":"vic_la_2014", "district_id":b.district_id, "district_name":b.district_name,
             "region_name":"", "ballot_active_families":";".join(sorted(ballot)), "incumbent_party_family":m.iloc[0].incumbent_party_family,
             "notional_holder_family":b.notional_holder_family, "notional_margin_pct":b.notional_margin_pct,
             "translation_status":status, "source_cutoff":"2014-11-28", "transformation_version":"historical_replay_v2_2014_prior_family_plus_governed_crosswalk_v1"}
        vals = [float(local[f]) for f in FAMILIES]; total=sum(vals); vals=[x/total for x in vals]
        row.update({f"local_{f}":f"{v:.12f}" for f,v in zip(FAMILIES, vals)})
        for feat in FEATURES: row[feat]=f"{float(frow.iloc[0][feat]):.12f}"
        rows.append(row)
    out=pd.DataFrame(rows)
    if len(out)!=88 or not ((out[[f"local_{f}" for f in FAMILIES]].astype(float).sum(axis=1)-1).abs()<1e-8).all(): raise ValueError("2014 local vectors do not reconcile")
    out.to_csv(OUT,index=False)
    AUDIT.write_text(json.dumps({"schemaVersion":2,"cycleId":"vic_la_2014","status":"pass-prediction-safe-local-input","rows":len(out),"crosswalk": {"path":str(CROSSWALK.relative_to(ROOT)),"sha256":sha(CROSSWALK),"features":FEATURES},"priorFamilyBaseline":{"path":str(PRIOR.relative_to(ROOT)),"sha256":sha(PRIOR),"role":"2010 prior election family composition"},"notionalBaseline":{"path":str(BASELINE.relative_to(ROOT)),"sha256":sha(BASELINE),"role":"pre-election major-party contest anchor"},"ballotMask":{"path":str(MASK.relative_to(ROOT)),"sha256":sha(MASK)},"output":{"path":str(OUT.relative_to(ROOT)),"sha256":sha(OUT)},"targetElectionOutcomesUsed":False,"forbiddenInputs":["model/data/processed/vec_2010_2014_redistribution_adjusted_tpp_swing.csv","2014 Victorian election outcomes"]},indent=2)+"\n")
    print(json.dumps({"rows":len(out),"sha256":sha(OUT)},indent=2))
if __name__ == "__main__": main()
