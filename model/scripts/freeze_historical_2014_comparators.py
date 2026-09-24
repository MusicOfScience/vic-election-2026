"""Build the corrected 2014 comparator bundle without opening outcomes."""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "metadata/historical-replay-v2-comparator-spec-2014.json"
PRED = ROOT / "model/data/validation/historical-replays/vic_la_2014-v2-prediction.json"
OLD = ROOT / "model/data/validation/historical-replays/vic_la_2014-v2-comparators.json"
OUT = ROOT / "model/data/validation/historical-replays/vic_la_2014-v2-comparators-v2.json"
AUDIT = ROOT / "metadata/historical-replay-2014-v2-comparator-defect-audit.json"
FAMILIES = ["ALP", "LIB_NAT", "GRN", "OTH_IND"]

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def softmax(values):
    import math
    m=max(values); e=[math.exp(v-m) for v in values]; s=sum(e); return [v/s for v in e]

def poll_state():
    payload=json.loads((ROOT/"model/data/validation/historical-replay-2014-poll-observations.json").read_text())
    rows=payload["observations"]
    rows=[r for r in rows if r.get("replayEligible") and r.get("cycleId")=="vic_la_2014"]
    vectors=[]; weights=[]
    cutoff=pd.Timestamp("2014-11-28")
    for r in rows:
        vectors.append([float(r["primaryShares"][p]) for p in FAMILIES])
        age=max(0,(cutoff-pd.Timestamp(r["evidenceAvailableByDate"])).days)
        weights.append(float(r.get("sampleSize",500))*0.5**(age/45.0))
    aggregate = pd.DataFrame(vectors, columns=FAMILIES).multiply(weights, axis=0).sum() / sum(weights) / 100
    return aggregate.to_dict()

def main():
    old_sha=sha(OLD); expected_old="d0178652ddcd922ae8b61cadac40ff6bab296c27f9bcc4be97cd5e34f43e3efd"
    if old_sha != expected_old: raise RuntimeError("old comparator bundle changed")
    pred=json.loads(PRED.read_text())
    if pred.get("predictionSha256") != "7621cd120c9efdd7f891d0d69fbd711b8d5316af632547df6035e3ea096b38b0" or pred.get("targetOutcomeLoaded"):
        raise RuntimeError("sealed 2014 prediction failed integrity check")
    spec=json.loads(SPEC.read_text()); poll=poll_state()
    baseline=pd.read_csv(ROOT/"model/data/validation/historical-replay-2014-assembly-notional-baseline.csv")
    local=pd.read_csv(ROOT/"model/data/validation/historical-replay-2014-local-inputs.csv")
    local=local.set_index("district_id"); baseline=baseline.set_index("district_id")
    districts=[]; uniform=[]; polling=[]; fundamentals=[]; seat=[]
    rng=random.Random(20141128)
    for district_id,row in baseline.iterrows():
        key=str(district_id); base=local.loc[key] if key in local.index else local.iloc[0]
        ballot=set(str(base.ballot_active_families).split(";"))
        margin=float(row.notional_margin_pct)/100
        holder=row.notional_holder_family
        # Uniform-swing: preserve each notional major-party margin while
        # applying one statewide ALP-v-Coalition movement from the poll state.
        tpp=poll["ALP"]/(poll["ALP"]+poll["LIB_NAT"]); movement=tpp-.5
        alp=0.5 + (margin if holder=="ALP" else -margin if holder=="LIB_NAT" else 0.0) + movement
        uniform_probs=softmax([alp*5,(1-alp)*5,0.02,0.01])
        uniform.append({"districtId":key,"districtName":row.district_name,"winProbabilities":dict(zip(FAMILIES,uniform_probs)),"notionalMarginPct":float(row.notional_margin_pct)})
        # Polling-only: one common statewide vector except for ballot masks.
        pv=[poll[p] if p in ballot else 0.0 for p in FAMILIES]; s=sum(pv); pv=[v/s for v in pv]
        polling.append({"districtId":key,"districtName":row.district_name,"primaryEstimates":{p:pv[i]*100 for i,p in enumerate(FAMILIES)},"winProbabilities":dict(zip(FAMILIES,softmax([v*5 for v in pv])))})
        # Deterministic fundamentals: blend frozen polling and local prior.
        lv=[float(base[f"local_{p}"]) if p in ballot else 0.0 for p in FAMILIES]; ls=sum(lv); lv=[v/ls for v in lv]
        fv=[.65*pv[i]+.35*lv[i] for i in range(4)]; fs=sum(fv); fv=[v/fs for v in fv]
        fundamentals.append({"districtId":key,"districtName":row.district_name,"primaryEstimates":{p:fv[i]*100 for i,p in enumerate(FAMILIES)},"winProbabilities":dict(zip(FAMILIES,softmax([v*5 for v in fv])))})
        # Independent-seat model: same frozen fundamentals, but fixed district
        # perturbation and independent IRV marginal approximation.
        jitter=[rng.gauss(0,.025) for _ in FAMILIES]; sv=[max(1e-6,fv[i]+jitter[i]) if p in ballot else 0.0 for i,p in enumerate(FAMILIES)]; ss=sum(sv); sv=[v/ss for v in sv]
        seat.append({"districtId":key,"districtName":row.district_name,"primaryEstimates":{p:sv[i]*100 for i,p in enumerate(FAMILIES)},"winProbabilities":dict(zip(FAMILIES,softmax([v*6 for v in sv]))),"uncertaintyRule":"fixed-pre-score-independent-seat-sd-0.025"})
    seat_comparator=dict(spec["comparators"]["seat-level-model"])
    seat_comparator.update(districts=seat, chamberAggregation="independent-seat-marginals")
    complete_comparator=dict(spec["comparators"]["complete-ensemble"])
    complete_comparator.update(predictionPath=str(PRED.relative_to(ROOT)), predictionSha256=pred["predictionSha256"])
    comparators={"uniform-swing-baseline":dict(spec["comparators"]["uniform-swing-baseline"],districts=uniform),"polling-only":dict(spec["comparators"]["polling-only"],districts=polling),"polling-plus-fundamentals":dict(spec["comparators"]["polling-plus-fundamentals"],districts=fundamentals),"seat-level-model":seat_comparator,"complete-ensemble":complete_comparator}
    # Structural checks are pre-outcome and fail closed.
    if json.dumps(uniform,sort_keys=True)==json.dumps(seat,sort_keys=True): raise RuntimeError("uniform and seat-level comparators alias")
    if json.dumps(polling,sort_keys=True)==json.dumps(fundamentals,sort_keys=True): raise RuntimeError("polling-only and fundamentals comparators alias")
    bundle={"schemaVersion":2,"modelVersion":"historical_replay_v2","cycleId":"vic_la_2014","informationCutoff":"2014-11-28","outcomesLoaded":False,"comparatorSpecPath":str(SPEC.relative_to(ROOT)),"comparatorSpecSha256":sha(SPEC),"certifyingPredictionPath":str(PRED.relative_to(ROOT)),"certifyingPredictionSha256":pred["predictionSha256"],"forbiddenDependencies":spec["forbiddenInputs"],"comparators":comparators}
    OUT.write_text(json.dumps(bundle,indent=2)+"\n")
    AUDIT.write_text(json.dumps({"schemaVersion":1,"cycleId":"vic_la_2014","status":"pre-score-implementation-defect-discovered-and-repaired","outcomesLoaded":False,"predictionUntouched":True,"oldBundlePath":str(OLD.relative_to(ROOT)),"oldBundleSha256":old_sha,"defect":"uniform-swing-baseline and seat-level-model used identical 88-district outputs","repair":"separate cycle-specific comparator contract and fixed pre-score independent-seat uncertainty","replacementBundlePath":str(OUT.relative_to(ROOT)),"replacementBundleSha256":sha(OUT),"targetOutcomesConsulted":False},indent=2)+"\n")
    print(json.dumps({"replacementBundleSha256":sha(OUT),"oldBundleSha256":old_sha,"predictionSha256":pred["predictionSha256"]},indent=2))

if __name__=="__main__": main()
