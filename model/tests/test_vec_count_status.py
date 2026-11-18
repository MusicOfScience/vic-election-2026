import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/prepare-vec-count-status.py"
spec = importlib.util.spec_from_file_location("prepare_vec_count_status", SCRIPT)
count = importlib.util.module_from_spec(spec)
spec.loader.exec_module(count)

CANDIDATES = """<EML xmlns="urn:oasis:names:tc:evs:schema:eml"><CandidateList>
<EventIdentifier Id="sample"><EventName>Test State Election 2026</EventName></EventIdentifier>
<Election><ElectionIdentifier Id="L"/><Contest><ContestIdentifier Id="d"><ContestName>Example District</ContestName></ContestIdentifier>
<Candidate><CandidateIdentifier Id="a"><CandidateName>A</CandidateName></CandidateIdentifier></Candidate>
<Candidate><CandidateIdentifier Id="b"><CandidateName>B</CandidateName></CandidateIdentifier></Candidate>
<Candidate><CandidateIdentifier Id="c"><CandidateName>C</CandidateName></CandidateIdentifier></Candidate>
</Contest></Election></CandidateList></EML>"""


@pytest.fixture
def candidates(tmp_path):
    path = tmp_path / "candidates.xml"
    path.write_text(CANDIDATES)
    return path


def write_snapshot(folder, minute, pair=None, *, withheld=False, declared=False, formal=90, event="sample"):
    def tally(candidate_id, votes):
        return f'<Candidate><eml:CandidateIdentifier Id="{candidate_id}"/><Votes>{votes}</Votes></Candidate>'

    pair_xml = ""
    if withheld:
        pair_xml = '<TwoCandidatePreferred Maverick="true"/>'
    elif pair is not None:
        votes = "".join(tally(candidate, n) for candidate, n in pair)
        pair_xml = f'<TwoCandidatePreferred PollingPlacesReturned="1" PollingPlacesExpected="4">{votes}</TwoCandidatePreferred>'
    xml = f"""<MediaFeed xmlns="{count.VEC}" xmlns:eml="{count.EML}" Created="2026-11-28T18:{minute}:00+11:00" Phase="ElectionNight">
    <eml:EventIdentifier Id="{event}"><eml:EventName>Test State Election 2026</eml:EventName></eml:EventIdentifier>
    <Election><eml:ElectionIdentifier Id="L"/><House><Contests><Contest>
    <eml:ContestIdentifier Id="d"/><Declared>{str(declared).lower()}</Declared>
    <FirstPreferences PollingPlacesReturned="2" PollingPlacesExpected="4">
    {tally("a", 40)}{tally("b", 20)}{tally("c", 30)}
    <Formal><Votes>{formal}</Votes><VotesByType><Votes Type="Postal">11</Votes></VotesByType></Formal>
    </FirstPreferences>{pair_xml}</Contest></Contests></House></Election></MediaFeed>"""
    path = folder / f"{minute}.xml"
    path.write_text(xml)
    return path


def test_withheld_and_changed_pair_starts_new_series(tmp_path, candidates):
    snapshots = [
        write_snapshot(tmp_path, "00"),
        write_snapshot(tmp_path, "01", [("a", 11), ("b", 8)]),
        write_snapshot(tmp_path, "02", [("b", 8), ("a", 11)]),
        write_snapshot(tmp_path, "03", withheld=True),
        write_snapshot(tmp_path, "04", [("a", 19), ("c", 21)], declared=True),
    ]
    ledger = count.build(candidates, reversed(snapshots), "sample", "sample", "L")
    history = ledger["districts"]["d"]["history"]
    assert len(ledger["frames"]) == 5
    assert [s["transition"] for s in history] == [None, "pair-published", "pair-withheld", "pair-changed"]
    assert [s["series"] for s in history] == [None, 1, None, 2]
    assert history[2]["pair"]["votes"] == {}
    assert history[2]["first"]["votes"]["a"] == 40
    assert history[3]["pair"]["coverage"] == {"returned": 1, "expected": 4}
    assert history[3]["first"]["voteModes"] == {"Postal": 11}
    assert history[3]["declared"] is True


def test_returning_pair_gets_a_fresh_series(tmp_path, candidates):
    pair = [("a", 11), ("b", 8)]
    snapshots = [
        write_snapshot(tmp_path, "01", pair),
        write_snapshot(tmp_path, "02", withheld=True),
        write_snapshot(tmp_path, "03", pair),
    ]
    history = count.build(candidates, snapshots, "trial", "sample", "L")["districts"]["d"]["history"]
    assert history[-1]["transition"] == "pair-restored"
    assert history[-1]["series"] == 2


def test_invalid_xml_preserves_previous_output(tmp_path, candidates):
    output = tmp_path / "ledger.json"
    output.write_text(json.dumps({"previous": True}))
    invalid = write_snapshot(tmp_path, "04", formal=89)
    result = subprocess.run([sys.executable, str(SCRIPT), "--mode", "sample", "--event-id", "sample",
                             "--candidates", str(candidates), "--output", str(output), str(invalid)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "do not reconcile" in result.stderr
    assert json.loads(output.read_text()) == {"previous": True}


def test_rehearsal_roster_cannot_enter_live_mode(tmp_path, candidates):
    with pytest.raises(ValueError, match="Rehearsal setup"):
        count.build(candidates, [write_snapshot(tmp_path, "02")], "live", "sample", "L")
