# Election night operations

28 November 2026, Australia/Melbourne

## Status and source boundary

GitHub main at the start of this work was `0ddd428010c17fc1d89874f719c6b7392dee453a`. PR #192 had merged the 27 November experimental release, PR #190 added the Greater Melbourne map, and PR #184 established the Assembly rehearsal and private count viewer. The older local checkout has user modifications and is untouched.

The [forecast preservation receipt](../metadata/election-night-forecast-preservation-2026.json) verifies seven release and input carrier hashes against the 27 November main commit. It records the 20-wave experimental release and the exact input tree and approval. The Git publication record predates polls closing. The precise model generation time is unavailable. The registered `final_pre_election` cutoff passed at 23:59:59 AEDT on 27 November without a witnessed seal. The release cannot be substituted for a protocol-eligible final snapshot. Production model authorisation and prospective scoring gates remain closed.

The VEC approved access to the SharePoint folder. Azure read/list authentication and production-reference reconciliation are pending. Public display of feed-derived figures is disabled. Clause 1.2 in the October public template restricts disclosure of the feed in original or modified form. Obtain written VEC permission covering the proposed dashboard and any public JSON distribution. The signed copy and original closure PDF were unavailable at handoff. The VEC closure email independently verifies the Mordialloc exception. [VEC feed, official resources and terms](https://vec.vic.gov.au/about-us/media/2026-results-data-feed).

The private source manifest is `~/Documents/VEC-2026-Private/source-manifest-2026-11-28.json`. Public sample tests passed 129 snapshots across all six variants, 23 publications per Lower House variant and 20 per Upper House variant. The sample has six Assembly contests and one Council region. Evelyn changes 2CP pairing after withholding while primaries continue. Later snapshots exercise smaller rechecked totals, district-wide recounts and declaration flags. Five Council polling-location first-preference rows from the 22 September simulated mobile-vote snapshot do not add to formal votes. They are quarantined in each affected detailed variant. Council region totals reconcile.

The 2022 sample ZIP contains 74 nested ZIPs, one XML and a scenario guide, and contains V1 carriers bearing real election dates. Authenticity of the counts for replay awaits reconciliation against published VEC results. The geography ZIP contains 88 valid Assembly polygons and eight valid Council polygons. Its longitude/latitude coordinates fall in Victoria, with no explicit CRS member. The VEC identifies the 2021 redivision as the latest. Exact production-ID correspondence has yet to be checked. [VEC boundary reviews](https://vec.vic.gov.au/electoral-boundaries/state-boundary-reviews).

## Mac runner

Use a local private folder outside Git on a Mac with Python 3.11 or newer. Keep the Mac connected to power and a stable network. macOS `caffeinate` below keeps idle sleep off while ingestion runs. After interruption, repeat the same command from the same checkout and private directory. The archive and journal make a repeat safe.

```zsh
umask 077
VEC_PRIVATE="$HOME/Documents/VEC-2026-Private"
mkdir -p "$VEC_PRIVATE/incoming"
python3 -m venv "$VEC_PRIVATE/.venv"
"$VEC_PRIVATE/.venv/bin/python" -m pip install -r scripts/vec-live-requirements.txt
```

### Manual SharePoint fallback

Download these three setup files into `incoming`. The VEC lists the production names as `State2026MediaFilePollingLocationsV2.xml`, `State2026MediaFileCandidatesV2.xml` and `State2026MediaFileGroupsAndTicketsV2.xml`. Download the current Lower House and Upper House LitePP results ZIPs once live. A SharePoint bulk ZIP containing those files also works. Keep the names and ZIPs as downloaded.

```zsh
"$VEC_PRIVATE/.venv/bin/python" scripts/ingest-vec-media.py \
  --root "$VEC_PRIVATE" --mode production manual "$VEC_PRIVATE/incoming"
```

Use `--mode trial` for manually saved 25 November rehearsal files and `--mode sample` for the public September sample pack. Those modes write to separate private directories.

Check `production/status.json`, then open **Count status → Review a count file privately** and choose `production/private-view.json` when the website includes V2 viewer support. Reload the file after an update. Keep the entire production folder out of Git and cloud sync. The closed Keysborough Gardens and receiving Chapel centres are resolved within Mordialloc against production polling-location IDs. An unresolved match is shown as a warning and disables the adjusted location denominator until reviewed. Official contest totals and official locations returned are preserved.

### Azure

In a trusted macOS Terminal, disable shell tracing if it was enabled. After the VEC supplies the SAS, enter the complete URL using the hidden prompt. The secret is scoped to the terminal and inherited by its ingestion subprocess. A VEC-issued storage account and token also work. For that form export `VEC_STORAGE_ACCOUNT` and read and export `VEC_SAS_TOKEN` through the same hidden prompt. Azure access starts at 18:00 AEDT.

```zsh
read -rs 'VEC_SAS_URL?VEC SAS URL (hidden): '
printf '\n'
export VEC_SAS_URL
"$VEC_PRIVATE/.venv/bin/python" scripts/ingest-vec-media.py \
  --root "$VEC_PRIVATE" --mode production probe
```

A successful probe verifies a container list and one read. After it passes, start polling.

```zsh
caffeinate -i "$VEC_PRIVATE/.venv/bin/python" scripts/ingest-vec-media.py \
  --root "$VEC_PRIVATE" --mode production sync --interval 300
# After stopping the runner with Ctrl-C
unset VEC_SAS_URL VEC_SAS_TOKEN VEC_STORAGE_ACCOUNT
```

Use the Mac first. GitHub Actions scheduling has variable latency and requires a separate permission and secret review. No live workflow or publishing service is enabled. The current Pages workflow continues deploying approved code changes. The polling loop stores Azure ETags, original archives and the full validated history privately. It selects the newest snapshot independently per house, with LitePP preferred at equal publication time. Older captures remain available for replay. A failed aggregate validation leaves the preceding accepted state in place. The status file records errors and the last successful ingestion.

## Next verified gates

1. Inspect the production setup. Verify official event and both Mordialloc polling-location IDs against it, then compare the first accepted snapshots for both houses against the VEC site.
2. Run the Azure probe after 18:00 AEDT and record its outcome. Use the SharePoint fallback in the meantime.
3. Arrange written approval for any feed-derived public display and distribution. The public VEC results pages are the visitor fallback.
4. Complete live model validation before making conditional projections or analytical calls. The current feed supplies observed counts. The VEC removed group voting tickets for the 2026 Council election. [VEC count rules](https://www.vec.vic.gov.au/voting/2026-state-election/how-votes-are-counted).
