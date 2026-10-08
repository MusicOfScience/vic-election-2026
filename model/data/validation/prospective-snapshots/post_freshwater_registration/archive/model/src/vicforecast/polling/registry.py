"""Canonical poll registry validation and audit helpers.

Poll metadata and party estimates are deliberately separated. This avoids
copying poll-level facts across rows and makes methodological regime changes
(prompting, undecided treatment, leadership, source quality) explicit inputs.
"""
from __future__ import annotations

from datetime import date
import pandas as pd


class PollDataError(RuntimeError):
    pass


POLL_EVENT_REQUIRED = {
    "poll_id", "pollster", "fieldwork_start", "fieldwork_end", "sample_size",
    "geography", "population", "vote_base", "source_tier", "verification_status",
    "model_eligible",
}
POLL_ESTIMATE_REQUIRED = {"poll_id", "party_id", "primary_pct", "estimate_status"}

VALID_VOTE_BASES = {"decided_reallocated", "all_respondents", "unknown"}
VALID_SOURCE_TIERS = {
    "primary_pollster",
    "primary_publisher",
    "reputable_secondary",
    "aggregator",
    "unverified",
}
VALID_VERIFICATION = {"verified", "partially_verified", "provisional", "exclude"}
VALID_QUESTIONNAIRE_REGIMES = {"explicit_multi_party", "legacy_other_bucket", "unknown"}
VALID_ESTIMATE_STATUS = {"reported", "derived_remainder", "imputed", "modelled"}


def validate_poll_events(events: pd.DataFrame) -> pd.DataFrame:
    missing = POLL_EVENT_REQUIRED - set(events.columns)
    if missing:
        raise PollDataError(f"poll events missing columns: {sorted(missing)}")
    out = events.copy()
    if out["poll_id"].duplicated().any():
        raise PollDataError("poll_id must be unique in poll events")

    out["fieldwork_start"] = pd.to_datetime(out["fieldwork_start"], errors="raise").dt.date
    out["fieldwork_end"] = pd.to_datetime(out["fieldwork_end"], errors="raise").dt.date
    if any(s > e for s, e in zip(out.fieldwork_start, out.fieldwork_end)):
        raise PollDataError("fieldwork_start after fieldwork_end")

    out["sample_size"] = pd.to_numeric(out["sample_size"], errors="raise").astype("int64")
    if (out["sample_size"] <= 0).any():
        raise PollDataError("sample_size must be positive")

    if "effective_sample_size" in out.columns:
        eff = pd.to_numeric(out["effective_sample_size"], errors="coerce")
        bad = eff.notna() & ((eff <= 0) | (eff > out["sample_size"]))
        if bad.any():
            raise PollDataError("effective_sample_size must be positive and <= sample_size")
        out["effective_sample_size"] = eff

    bad = sorted(set(out["vote_base"]) - VALID_VOTE_BASES)
    if bad:
        raise PollDataError(f"unknown vote_base values: {bad}")
    bad = sorted(set(out["source_tier"]) - VALID_SOURCE_TIERS)
    if bad:
        raise PollDataError(f"unknown source_tier values: {bad}")
    bad = sorted(set(out["verification_status"]) - VALID_VERIFICATION)
    if bad:
        raise PollDataError(f"unknown verification_status values: {bad}")

    if out["model_eligible"].isna().any():
        raise PollDataError("model_eligible may not be null")
    out["model_eligible"] = out["model_eligible"].astype(bool)

    forbidden = out["model_eligible"] & out["verification_status"].isin(["provisional", "exclude"])
    if forbidden.any():
        ids = out.loc[forbidden, "poll_id"].tolist()
        raise PollDataError(f"provisional/excluded polls cannot be model_eligible: {ids}")

    if "questionnaire_regime" in out.columns:
        vals = set(out["questionnaire_regime"].dropna())
        bad = sorted(vals - VALID_QUESTIONNAIRE_REGIMES)
        if bad:
            raise PollDataError(f"unknown questionnaire_regime values: {bad}")

    # Mid-date is a deterministic modelling convenience, not a new observation.
    out["fieldwork_mid"] = [s + (e - s) / 2 for s, e in zip(out.fieldwork_start, out.fieldwork_end)]
    return out


def validate_poll_estimates(
    events: pd.DataFrame,
    estimates: pd.DataFrame,
    *,
    reallocated_sum_tolerance: float = 0.75,
) -> pd.DataFrame:
    events = validate_poll_events(events)
    missing = POLL_ESTIMATE_REQUIRED - set(estimates.columns)
    if missing:
        raise PollDataError(f"poll estimates missing columns: {sorted(missing)}")
    out = estimates.copy()
    if out.duplicated(subset=["poll_id", "party_id"]).any():
        raise PollDataError("duplicate party estimate within poll")
    unknown = sorted(set(out["poll_id"]) - set(events["poll_id"]))
    if unknown:
        raise PollDataError(f"estimates reference unknown poll_ids: {unknown}")
    out["primary_pct"] = pd.to_numeric(out["primary_pct"], errors="raise")
    if ((out["primary_pct"] < 0) | (out["primary_pct"] > 100)).any():
        raise PollDataError("primary_pct outside [0,100]")

    bad_status = sorted(set(out["estimate_status"]) - VALID_ESTIMATE_STATUS)
    if bad_status:
        raise PollDataError(f"unknown estimate_status values: {bad_status}")

    sums = out.groupby("poll_id", observed=True)["primary_pct"].sum()
    event_base = events.set_index("poll_id")["vote_base"]
    for poll_id, total in sums.items():
        base = event_base.loc[poll_id]
        if base == "decided_reallocated" and abs(float(total) - 100.0) > reallocated_sum_tolerance:
            raise PollDataError(f"{poll_id}: reallocated primary shares sum to {total}, not approximately 100")
        if base == "all_respondents" and total > 100.0 + 1e-9:
            raise PollDataError(f"{poll_id}: all-respondent primary shares exceed 100")
    return out


def poll_composition_report(events: pd.DataFrame, estimates: pd.DataFrame) -> pd.DataFrame:
    events = validate_poll_events(events)
    estimates = validate_poll_estimates(events, estimates)
    sums = estimates.groupby("poll_id", observed=True)["primary_pct"].sum().rename("primary_sum")
    counts = estimates.groupby("poll_id", observed=True)["party_id"].nunique().rename("party_count")
    cols = ["poll_id", "pollster", "vote_base", "source_tier", "verification_status", "model_eligible"]
    out = events[cols].merge(sums, on="poll_id").merge(counts, on="poll_id")
    out["unallocated_pct"] = (100 - out["primary_sum"]).clip(lower=0)
    return out


def poll_overlap_report(events: pd.DataFrame) -> pd.DataFrame:
    """Flag overlapping fieldwork from the same research family/series.

    Overlap is not automatically duplication. It is a review flag used to catch
    cases where the same underlying sample may have been reported twice (for
    example, a public poll and a related MRP/super-sample).
    """
    ev = validate_poll_events(events)
    rows = []
    for i, a in ev.iterrows():
        family_a = a.get("sample_family")
        if pd.isna(family_a) or family_a in (None, ""):
            continue
        for j, b in ev.iloc[i + 1 :].iterrows():
            family_b = b.get("sample_family")
            if family_a != family_b:
                continue
            start = max(a.fieldwork_start, b.fieldwork_start)
            end = min(a.fieldwork_end, b.fieldwork_end)
            if start <= end:
                rows.append({
                    "poll_id_a": a.poll_id,
                    "poll_id_b": b.poll_id,
                    "sample_family": family_a,
                    "overlap_start": start,
                    "overlap_end": end,
                    "review_required": True,
                })
    return pd.DataFrame(rows, columns=[
        "poll_id_a", "poll_id_b", "sample_family", "overlap_start", "overlap_end", "review_required"
    ])


def questionnaire_break_report(events: pd.DataFrame, *, party_flag: str = "one_nation_prompted") -> pd.DataFrame:
    """Identify within-pollster changes in whether a party was explicitly prompted."""
    ev = validate_poll_events(events)
    if party_flag not in ev.columns:
        return pd.DataFrame(columns=["pollster", "prior_poll_id", "poll_id", "prior_value", "value"])
    rows = []
    for pollster, group in ev.sort_values("fieldwork_mid").groupby("pollster", observed=True):
        group = group[group[party_flag].notna()]
        prev = None
        for _, row in group.iterrows():
            if prev is not None and bool(row[party_flag]) != bool(prev[party_flag]):
                rows.append({
                    "pollster": pollster,
                    "prior_poll_id": prev.poll_id,
                    "poll_id": row.poll_id,
                    "prior_value": bool(prev[party_flag]),
                    "value": bool(row[party_flag]),
                })
            prev = row
    return pd.DataFrame(rows)
