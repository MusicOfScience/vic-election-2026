# Campaign operations repairs — 31 October 2026

## Implemented repairs

Candidate discovery previously compared a discovery record carrying `kind: candidate` with accepted registry entries that do not carry `kind`. The latter fell through to poll identity construction. Known candidates therefore returned to quarantine. The comparison now uses candidate names and the existing governed contest aliases, while requiring the same party and status. Official VEC status still requires a matching VEC record; party endorsement cannot satisfy official nomination evidence.

A separate last-record-wins reduction keyed only by candidate name and contest could hide a new party endorsement behind a later, already-tracked municipal announcement. Discovery now retains distinct source-record IDs and removes exact duplicates only. This preserves conflicting or stronger evidence for review rather than declaring it already resolved.

The monitoring action report now includes the actual extraction error, such as HTTP 403, in its source-specific summary.

Electorate search previously filtered the table/cards while leaving all 88 seat tiles visible. Search and filters now precede the tile grid, and all result views use the same filtered list. This reduces scrolling on small screens and gives consistent search results. Electorate and voting-centre searches have explicit accessible names; the single-result count uses the singular.

## Acquisition and reconciliation

Direct first-party requests to both previously inaccessible party pages returned HTTP 200 in this work session. Candidate-heading/table excerpts, full-response hashes and retrieval times are preserved in `metadata/campaign-operations-2026-10-31/`. These are scoped excerpts, not complete carrier archives. The full HTML responses are not committed.

The captured One Nation roster yields 103 entries: 97 match accepted identities/statuses, five are untracked names, and one is an announcement-to-endorsement change. The Family First table has one configured Lowan entry whose spelling differs from the accepted name. The seven review items are:

| Candidate | Contest | Review requirement |
| --- | --- | --- |
| Michael Abelman | Caulfield | Untracked party endorsement |
| Steven Mitchell | Ashwood | Untracked party endorsement |
| Andrew Hirst | Cranbourne | Untracked party endorsement |
| David Laird | Kew | Untracked party endorsement |
| Clay Esler | Eastern Victoria | Untracked Council endorsement |
| Ashli Beards | Mornington | Party endorsement differs from the accepted municipal announcement |
| Lee Ann Elmes / Elms | Lowan | Reconcile table/profile spelling before any name change |

The machine reconciliation packet records every captured entry and its action. Existing candidate evidence remains excluded from the forecast; no accepted registry record, candidate decision or model input changes in this batch.

A full local discovery sweep after the identity repair reached all 12 enabled routes without extraction errors. The final distinct-carrier sweep is recorded separately when complete. Exact duplicate removal must not be confused with collapsing dependent source evidence into a new independent observation.

**GitHub runner access remains unresolved.** Run `41143280032`, attempt 2, was retried once. Its retained artifact `13019884016` still reports HTTP 403 from One Nation and Family First. The workflow correctly fails closed. Local HTTP 200 responses do not establish recovery in GitHub Actions. No source was disabled, no failure was suppressed, and no proxy or unverified alternate carrier was substituted.

## Official nomination boundary

The VEC candidate page still specifies nominations opening 4 November and closing at noon on 9 November. On this assessment date there is no final official candidate universe to reconcile. Party announcements and endorsements remain provisional evidence. Source: https://www.vec.vic.gov.au/candidates-and-parties/become-a-state-election-candidate . The separate registered 3 November snapshot window is unchanged and no new seal is created here.

## Validation and limits

- 211 JavaScript tests pass, including regressions for accepted records without `kind`, governed region aliases, party/status changes, VEC authority and distinct municipal/party carriers.
- Lint and the GitHub Pages static export pass. The ordinary non-Pages Next build still hits the existing unrelated Cloudflare server declaration type issue; the production static path uses its existing configuration.
- Generated readiness and prospective registration validators pass; readiness remains 6/9.
- Forecast, model inputs, accepted candidate registry, review decisions and validation archives are unchanged.
- Live browser checks verified electorate filtering, opening the Melbourne profile and closing it. The existing live tile-grid inconsistency was reproduced before the repair. The patch is build-checked; actual iOS/Android and mobile viewport visual QA remain outstanding. No real-device QA pass is claimed.
