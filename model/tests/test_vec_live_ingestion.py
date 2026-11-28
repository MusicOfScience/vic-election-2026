"""Public synthetic checks and optional first-party fixture integration."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from vec_live.azure import AzureFeed, TransportError, credentials  # noqa: E402
from vec_live.schema import FeedError, extract_inputs, identify, register_from_repository, snapshot, xml  # noqa: E402
from vec_live.store import decoded, open_store  # noqa: E402


def zip_bytes(name, content):
    target = BytesIO()
    with ZipFile(target, "w") as archive:
        archive.writestr(name, content)
    return target.getvalue()


def test_archive_integrity_and_no_external_xml():
    stem = "TestState2026mediafilelitepplhv2_20260921_090801"
    raw = zip_bytes(stem + ".xml", b"<root/>")
    [(info, member, carrier)] = extract_inputs(stem + ".zip", raw)
    assert info.house == "L"
    assert info.sample
    assert member == b"<root/>"
    assert carrier == raw
    with pytest.raises(FeedError, match="matching XML"):
        list(extract_inputs(stem + ".zip", zip_bytes("other.xml", b"<root/>")))
    with pytest.raises(FeedError, match="integrity"):
        list(extract_inputs(stem + ".zip", raw[:-6]))
    with pytest.raises(FeedError, match="unsafe XML"):
        xml(b'<!DOCTYPE root [<!ENTITY x SYSTEM "file:///private/local">]><root>&x;</root>')
    assert identify("State2022mediafilelitepplh_20221126_220008.zip") is None


def test_azure_credential_alternatives_limits_and_preopening():
    now = datetime(2026, 11, 28, 8, tzinfo=timezone.utc)
    token = "sp=rl&sr=c&sig=synthetic"
    endpoint = "https://example.blob.core.windows.net"
    assert credentials({"VEC_SAS_URL": f"{endpoint}/results?{token}"}, now) == (endpoint, token)
    assert credentials({"VEC_STORAGE_ACCOUNT": "example", "VEC_SAS_TOKEN": f"?{token}"}, now) == (endpoint, token)
    cases = [
        (f"{endpoint}/results?sp=rwl&sig=synthetic", "read and list"),
        ("https://unrelated.example/results?" + token, "Invalid HTTPS"),
        (f"{endpoint}/results?{token}&se=2020-01-01T00:00:00Z", "expired"),
        (f"{endpoint}/results?{token}&st=2030-01-01T00:00:00Z", "not yet valid"),
    ]
    for url, expected in cases:
        with pytest.raises(TransportError, match=expected) as exc:
            credentials({"VEC_SAS_URL": url}, now)
        assert "synthetic" not in str(exc.value)
    with pytest.raises(TransportError, match="18:00 AEDT"):
        AzureFeed({}, now=datetime(2026, 11, 28, 6, tzinfo=timezone.utc))


def test_bad_input_does_not_replace_private_state_and_lock_is_exclusive(tmp_path):
    with open_store(tmp_path, "sample") as store:
        store.publish_private("waiting", [])
        previous = (store.path / "status.json").read_bytes()
        with pytest.raises(FeedError, match="lock"):
            with open_store(tmp_path, "sample"):
                pass
        with pytest.raises(FeedError, match="integrity"):
            store.ingest_file("bad.zip", b"not a zip", "sharepoint")
        assert (store.path / "status.json").read_bytes() == previous
        assert store.db.execute("SELECT COUNT(*) FROM quarantines").fetchone()[0] == 1
    with pytest.raises(FeedError, match="outside"):
        with open_store(ROOT, "production"):
            pass


def test_archived_forecast_matches_pre_election_release_tree():
    receipt = json.loads((ROOT / "metadata/election-night-forecast-preservation-2026.json").read_text())
    assert receipt["productionCompatible"] is False
    assert receipt["prospectiveFinalSnapshotStatus"] == "missed-witnessed-cutoff"
    for path, expected in receipt["artifacts"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected
    if os.environ.get("GITHUB_ACTIONS") != "true":
        commit = receipt["releaseCommit"]
        for path, expected in receipt["artifacts"].items():
            raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
            assert sha256(raw).hexdigest() == expected


@pytest.fixture
def sample_pack():
    override = os.environ.get("VEC_SE26_SAMPLE_ZIP")
    if not override:
        pytest.skip("Set VEC_SE26_SAMPLE_ZIP to the private VEC sample pack")
    path = Path(override)
    return path.name, path.read_bytes()


def test_official_sample_pack_semantics_and_production_isolation(tmp_path, sample_pack):
    name, content = sample_pack
    with open_store(tmp_path, "production") as store:
        with pytest.raises(FeedError, match="Sample or trial"):
            store.ingest_file(name, content, "sharepoint")
        assert store.db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 0
    with open_store(tmp_path, "sample") as store:
        assert store.ingest_file(name, content, "sharepoint") == (129, [])
        assert store.ingest_file(name, content, "sharepoint") == (0, [])
        assert Counter(store.db.execute("SELECT house,rank FROM snapshots")) == {
            ("L", 0): 23, ("L", 1): 23, ("L", 2): 23,
            ("U", 0): 20, ("U", 1): 20, ("U", 2): 20,
        }
        assert len(store.references["contests"]["L"]) == 6
        assert len(store.references["contests"]["U"]) == 1
        for house in ("L", "U"):
            frames = [decoded(raw) for raw, in store.db.execute(
                "SELECT data FROM snapshots WHERE house=? AND rank=2 ORDER BY published", (house,))]
            assert [frame["publishedAt"] for frame in frames] == sorted(frame["publishedAt"] for frame in frames)
            if house == "U":
                assert all(row["first"] is None or row["first"]["status"] == "unavailable"
                           for row in frames[0]["results"].values())
                assert sum(len(frame["quarantined"]) for frame in frames) == 5
                assert all(row["pair"] is None for frame in frames for row in frame["results"].values())
                row = next(iter(frames[1]["results"].values()))["first"]
                assert sum(g["votes"] for g in row["groups"].values()) + sum(
                    c["votes"] for c in row["candidates"].values()) == row["formal"]["votes"]
                assert all(g["aboveTheLine"] + g["belowTheLine"] == g["votes"] for g in row["groups"].values())
                continue
            evelyn = next(key for key, ref in store.references["contests"]["L"].items()
                          if ref["name"] == "Evelyn District")
            rows = [frame["results"][evelyn] for frame in frames if evelyn in frame["results"]]
            old = next(row["pair"] for row in rows if row["pair"]["status"] == "reported")
            withheld = next(row for row in rows if row["pair"]["status"] == "withheld")
            assert withheld["pair"]["candidates"] == {}
            assert withheld["first"]["formal"]["votes"] > 0
            assert all(place["pair"]["candidates"] == {} for place in withheld["places"].values())
            assert rows[-1]["pair"]["candidates"].keys() != old["candidates"].keys()
            assert any(a["first"]["formal"]["votes"] > b["first"]["formal"]["votes"]
                       for a, b in zip(rows, rows[1:]))
            assert any(row["aggregateOnly"] and not row["places"]
                       for frame in frames for row in frame["results"].values())
            assert all(row["declared"] for row in frames[-1]["results"].values())
        store.publish_private("updated", [])
        saved = json.loads((store.path / "private-view.json").read_bytes())
        assert saved["houses"]["L"]["publishedAt"] != saved["houses"]["U"]["publishedAt"]
        with pytest.raises(FeedError):
            store.ingest_file("bad.zip", b"bad", "sharepoint")
        store.publish_private("attention required", ["ZIP integrity or compression check failed"])
        after = json.loads((store.path / "private-view.json").read_bytes())
        assert after["houses"] == saved["houses"]
        assert after["status"]["lastSuccessfulIngestionAt"] == saved["status"]["lastSuccessfulIngestionAt"]


def test_snapshot_rejects_renamed_sample(sample_pack):
    _, raw = sample_pack
    info, content, _ = next(entry for entry in extract_inputs("sample.zip", raw) if entry[0].house == "L")
    real_name = identify(info.name[4:])
    with pytest.raises(FeedError, match="Sample or trial"):
        snapshot(real_name, content, {}, "production")


def test_exception_register_requires_official_ids_before_adjustment():
    [exception] = register_from_repository()["exceptions"]
    assert exception["districtLabel"] == "Mordialloc District"
    assert {row["referenceLabel"]: row["status"] for row in exception["locations"]} == {
        "Keysborough Gardens": "closed", "Chapel": "receiving"
    }
    assert all(not row["includeInMatchedBoothSwing"] for row in exception["locations"])
