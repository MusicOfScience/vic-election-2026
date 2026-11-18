# Victorian Assembly count status

18 November 2026

## Access and publication

The [Victorian Electoral Commission (VEC) results feed page](https://www.vec.vic.gov.au/about-us/media/2026-results-data-feed) provides the request form, terms, user guide and public samples. The [terms](https://www.vec.vic.gov.au/-/media/b7e4b56d7c3c4829b8c121e41ae0ae9f.pdf) restrict release of the feed in original or modified form. Keep feed-derived ledgers private unless the VEC expressly approves the intended publication. Feed access and public display are separate decisions. The Wednesday 25 November trial uses test data and omits the indicative two-candidate preferred (2CP) prediction. Rehearse withheld and changed pairs separately using the downloadable September–October samples.

The app opens in an awaiting-results state and links to the VEC. Its private file viewer processes a local ledger in the browser without uploading it. Its rehearsal uses fictional candidate labels and totals. The forecast and count views are independent. The count view displays official reported first preferences, available vote-type breakdowns, the paired vote and its reported coverage, and the declaration flag.

## Prepare, verify and publish

1. Obtain the candidates setup and a consistent series of Lower House Lite or LitePP result files through authorised access. Keep raw XML and access details outside the public repository. Retain the original filenames and file bytes. Use the identifiers in the approved setup. The public sample uses event `18738` and election `L`; event `18738` is a test event.
2. Extract each saved results ZIP into a private input directory. Run the converter against saved XML. Use `sample` for public fixtures, `trial` for rehearsal files or `live` for results after the count opens. Use a staging output outside the repository.
3. Check that the source event, roster, timestamp and latest figures agree with the VEC. Check first preferences and 2CP coverage independently. A removed disclosure, incomplete candidate reconciliation or stale capture warrants review. Reconcile the actual statutory distribution or declared candidate separately when the VEC publishes the material, since the XML does not provide the formal distribution or declaration date.
4. Open **Count status → Review a count file privately** and select the staged JSON. Keep that ledger and its source captures out of the public repository. A failed parse preserves the previous local ledger. The converter rejects a changed or truncated live history. A genuine roster correction needs separate reconciliation.
5. For any public count display, use results already released publicly by the VEC through a permitted reuse path, or obtain the VEC’s express written approval for the proposed feed-derived display. This branch contains no publication path for restricted ledgers.

```bash
python scripts/prepare-vec-count-status.py \
  --mode live --event-id VERIFIED_EVENT_ID --election-id L \
  --candidates /path/to/private/candidates.xml \
  --output /path/to/staging/count-ledger.json /path/to/private/results/*.xml
```

The file-based approach supports operator review and a public static build. It has no background downloader or publication schedule. Avoid promising live cadence until the authorised transport and hosting path have been tested.

## Count semantics

- Missing 2CP means the count is awaiting available results. If `Maverick="true"` appears on the district-level 2CP element, the pair is explicitly withheld. Several reasons are possible, including a three-candidate count. The flag does not identify the reason or carry three-candidate tallies.
- Candidate IDs are canonical within the contest. Reordering the same two candidates leaves the series intact. A changed pair, or the return of a pair after an interruption, begins a new series. Withholding hides the previous margin in the current snapshot.
- The declaration flag is reported separately from the indicative tally. A snapshot's capture time records when the flag was observed, without implying that it is the official declaration time. First-preference and indicative-2CP reporting coverage are different denominators.
- The feed may report rechecks or recounts with revised totals and fewer location breakdowns. Retain the source phase and timestamp. Never assume counts increase monotonically across snapshots.

The [2026 VEC media feed guide](https://www.vec.vic.gov.au/-/media/caa76d02dbe94dc481d8584db66af4c3.pdf) documents the Lower House schema, withheld status and exclusions. The converter was exercised against the published SE26 candidates setup and 23 public Lite Lower House snapshots, covering six sample districts. The Evelyn fixture includes a published pair, withholding, a changed pair and a declaration flag.
