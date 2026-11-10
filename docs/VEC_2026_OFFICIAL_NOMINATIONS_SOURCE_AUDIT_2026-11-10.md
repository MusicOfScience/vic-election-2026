# Official VEC 2026 final candidate source — verified capture and privacy-minimised reconciliation

**Evidence reviewed:** Tuesday 10 November 2026. **Status:** source-count reconciliation **complete**; candidate-identity, Council ballot groups, governed registry admission and model integration **outstanding**. Tracks #151.

## First complete official source capture

The owner merged PR #158 and ran the corrected [manual candidate capture workflow](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42821242121) on main commit `51afe3a858c90f064d195240b6bc089cf9d24279`. Workflow **success**; artifact [13767960680](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42821242121) retained for **30 days, expiring 10 December 2026**.

- Landing: <https://www.vec.vic.gov.au/2026-state-election>
- Exact VEC workbook: <https://www.vec.vic.gov.au/-/media/f487c2abe7274ed4b5bb60daa2b001ad.xls>
- Format: **legacy Excel `.xls` OLE compound / BIFF8**, not a ZIP-based `.xlsx` file. Media type `application/vnd.ms-excel`.
- Source report title: **Candidate Contact Persons' Details Summary Report**, marked **9 November 2026 7:58 pm Melbourne time**. Downloaded **10 November 2026 13:05:01 UTC**.
- Raw file: **183,296 bytes**, SHA-256 **`f5c9505d01abb39bfd4e20cd389c6adea2e524a26423c7c82a51084e21d95c16`**, independently verified to match the capture receipt.
- `metadata/vec-nominations-2026-11-10-source-audit.json` contains the complete machine-readable provenance receipt and count checks without unnecessary contact data.

The earlier failed run #42819733898 was caused by the original extractor rejecting the legacy carrier; it was not a Node.js deprecation problem. PR #158 added a legacy XLS signature and failure artifact retention. This successful capture confirms that diagnosis.

## Result: authoritative counts reconcile at three levels

| Evidence unit | Expected | Extracted | Outcome |
| --- | ---: | ---: | --- |
| All nominations | 1,037 | 1,037 | **Match** |
| Legislative Assembly candidates | 734 | 734 | **Match** |
| Legislative Council candidates | 303 | 303 | **Match** |
| Assembly districts | 88 | 88 | **Match** |
| Council regions | 8 | 8 | **Match** |
| Contests with declared per-contest count matching extracted rows | 96 | 96 | **Match** |
| Duplicate exact candidate names inside one contest | 0 | 0 | **Match** |

The independent source cross-check is the VEC's **10 November 2026** announcement: <https://www.vec.vic.gov.au/about-us/media/media-releases/1037-candidates-will-contest-the-2026-state-election>.

### Council region counts

| Region | Named candidates |
| --- | ---: |
| Eastern Victoria | 32 |
| North-Eastern Metropolitan | 38 |
| Northern Metropolitan | 43 |
| Northern Victoria | 37 |
| South-Eastern Metropolitan | 35 |
| Southern Metropolitan | 31 |
| Western Metropolitan | 43 |
| Western Victoria | 44 |
| **Total** | **303** |

### Full-coverage party nominations

By the **exact VEC registered-party label** column, One Nation Victoria, the Australian Labor Party, Australian Greens Victoria and Victorian Socialists each nominate in **all 88 Assembly districts**. Liberal Party of Australia – Victorian Division has 77 Assembly entries and National Party of Australia – Victoria has 12; this is **not** a seat-universe mapping of Coalition identity and does not imply a 89-seat Coalition slate without resolving party/contest overlaps.

There are **91 Assembly** and **21 Council** rows with the `RPP Name` cell blank. **Do not infer all are independents**: Council non-party groups and ungrouped candidates need page-level reconciliation; absence of registered-party affiliation is not itself a ballot-group label.

Two VEC candidate names do not follow the usual `SURNAME, Given` format. Do not reject genuine official records simply because the name string lacks a comma.

## Forecast implications and disconfirmation

The 31 October experimental model produces some very high One Nation district win frequencies. One candidate-availability hypothesis can now be rejected: **One Nation does have a named official candidate in each of those seats** and indeed all 88 Assembly seats. The factual 2026 ballot remains absent from the five-family model engine, however, and its geographic propensity, preference transfers, seat-win probabilities and statistical calibration still need independent scrutiny. See #157. **This finding does not validate those high frequencies.**

The official Melbourne district One Nation candidate is **COURTIS, Phillip**, whereas the 305-entry provisional registry contains **Matthew Collins**. Treat as an explicit replacement/identity discrepancy, not proof of withdrawal or authorisation to silently overwrite the accepted registry. The old provisional `Ben Gilbert` and official Ovens Valley `GILBERT, Benjamin` likely represent one person but still require name-alias review.

## Critical limitation: Council group/ballot metadata

The spreadsheet contains candidate names, RPP labels and their **row sequence**. For Assembly districts, row sequence matched example official ballot-order district pages (Albert Park and Melbourne). The XLS does **not** explicitly encode Council **group letter, unnamed-group membership, ungrouped classification or above-the-line presentation**. VEC region pages do: for example <https://www.vec.vic.gov.au/electoral-boundaries/state-regions/northern-metropolitan-region/nominations> shows group letters A through M, including `Unnamed-1` and `Unnamed-2`, plus `Ungrouped`.

**Do not derive Council group letters from the RPP label or position alone.** Victoria abolished group voting tickets for the 2026 election; ballot groups still exist but are not group voting tickets. Existing VEC pages' legacy broken group-ticket links are not evidence of a ticket.

## Data minimisation

The XLS includes identifiable candidate-contact-person names, private-style email addresses and phone numbers. These **are unnecessary for this public forecasting tool** and must be omitted from any public derived roster, test fixtures or console logs. A local review-only extraction generated a clean candidate list retaining **chamber, contest, source name, registered-party label and row ordinal**; this PR intentionally commits **only a checksum-based evidence receipt and source audit**, not raw contact material or a falsely finalised public roster.

## Next authorised work

1. Preserve or renew the VEC carrier before artifact expiration; source hashes and URL are retained in Git even after the ephemeral raw artifact expires.
2. Make the clean 1,037-row candidate list reproducible within the repository, **with no contact fields**; tie it to the exact captured source hash and 96 per-contest counts. Publish only reviewed fields.
3. Complete Assembly and Council candidate/party aliases, VEC Council group letters, unnamed groups and ungrouped classification from authoritative VEC pages.
4. Generate full 1,037 versus 305 identity/contest/party review and owner-approved promotion through the existing fail-closed registry governance. Review all new candidates, not just accepted prior names.
5. Keep the experimental forecast and 6/9 PROD gates unchanged. A separate preregistered candidate-resolved challenger would be necessary for any forecast-model change.

**This PR contains no model input, numerical forecast, probability calibration, historical output, prospective seal, candidate registry or production status changes.** The release is **source-verified**, not model-certified.
