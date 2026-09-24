"""Single governed translation between historical and model family labels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


def load_family_mapping(root: str | Path) -> dict[str, str]:
    root = Path(root)
    path = root / "metadata/historical-party-family-mapping.json"
    if not path.exists():
        path = root.parent / "metadata/historical-party-family-mapping.json"
    mapping = json.loads(path.read_text(encoding="utf-8"))["historicalToModel"]
    if set(mapping) != {"ALP", "Coalition", "Greens", "One Nation", "Other/Independent"}:
        raise ValueError("historical party-family mapping is incomplete")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("historical party-family mapping is not one-to-one")
    return mapping


def map_historical_family(value: str, mapping: Mapping[str, str]) -> str:
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unknown historical party family: {value!r}") from exc


def map_frame_families(frame, root: str | Path, column: str = "party_family"):
    mapping = load_family_mapping(root)
    unknown = sorted(set(frame[column].dropna()) - set(mapping))
    if unknown:
        raise ValueError(f"unknown historical party families: {unknown}")
    result = frame.copy()
    result["model_family"] = result[column].map(mapping)
    if result["model_family"].isna().any():
        raise ValueError("historical family mapping silently produced missing values")
    return result


def assert_share_vectors(frame, families: Iterable[str], tolerance: float = 1e-8) -> None:
    values = frame.loc[:, list(families)].to_numpy(float)
    if (values < -tolerance).any():
        raise ValueError("historical family shares contain a negative value")
    totals = values.sum(axis=1)
    if not (abs(totals - 1.0) <= tolerance).all():
        raise ValueError("historical family shares do not reconcile to one")
