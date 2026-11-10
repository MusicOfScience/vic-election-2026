# 9 November 2026 nominations close — evening intake and reconciliation review

> **10 November authoritative correction:** The VEC has now announced **1,037 nominated candidates: 734 Legislative Assembly and 303 Legislative Council**. See the VEC's 10 November media release: <https://vec.vic.gov.au/about-us/media/media-releases/1037-candidates-will-contest-the-2026-state-election>. The **733** Assembly figure below is retained solely as the contemporaneous *9 November preliminary* Antony Green report; it is **superseded**, not the official final total. The VEC states that ballot draws for all 88 districts and eight regions were held, and its site provides a candidate spreadsheet and ballot-order pages. Official roster *acquisition and row-level reconciliation remain separate work*; the VEC announcement alone does not validate individual rows or the app.

**Status:** REVIEW ONLY; incomplete VEC carrier capture; no admission to accepted candidate registry, no forecast refresh, and no nomination-close seal.

**Observation period:** evening of Monday 9 November 2026, Melbourne time, after the scheduled 4 pm ballot draw. This review records externally visible evidence and a targeted read of committed `metadata/candidates-2026.json`. It does **not** assert the final post-draw VEC spreadsheet was downloaded, that raw responses were durably archived, or that all 96 contests were checked.

**Tracking:** #151.

## Source hierarchy and publication state

1. **Primary authority:** VEC 2026 election hub <https://www.vec.vic.gov.au/SE2026> and candidate pages for specific districts and Council regions. The candidate nomination deadline was **12:00 AEDT, 9 November**; the scheduled ballot draw was **4:00 pm on 9 November**. Several current VEC district pages still show “The final list of candidates will be available shortly” and list candidates **in nomination-receipt order**, not ballot order. Other VEC pages already say “The final list of candidates is below,” but still show inherited pre-draw text. Treat page-finality and ballot order as separate fields.
2. **Secondary contemporary count:** Antony Green, “VIC2026 – Candidate Numbers at Close of Nominations”, posted 9 November 2026 at <https://antonygreen.com.au/2026/11/>. He reports **733 Legislative Assembly candidates**, versus **740 in 2022**, averaging **8.3** in 88 districts. He states that the file ordered by ballot position would **not** be available until Tuesday morning, 10 November. Council candidate numbers were not yet in that initial article. This is a named secondary analyst report, **not** independently audited VEC row-level evidence.
3. **Legal change affecting the Council:** VEC 2026 candidate information <https://www.vec.vic.gov.au/candidates-and-parties/become-a-state-election-candidate> confirms **group voting tickets have been removed**. Council ballot groups/columns remain relevant; legacy group voting ticket preference transfers must not be inferred.

## Reported Assembly field-size variation (secondary evidence)

| District | Candidate count | Source |
| --- | ---: | --- |
| Footscray | 15 | Antony Green, 9 November |
| Prahran | 13 | Antony Green, 9 November |
| Ripon | 12 | Antony Green, 9 November |
| Sydenham | 12 | Antony Green, 9 November |
| Tarneit | 12 | Antony Green, 9 November |
| Sandringham | 5 | Antony Green, 9 November |

These counts are suitable for an **independent aggregate reconciliation target**, not proof of individual candidate identities or ballot position.

## Targeted VEC-page comparison against 305 accepted provisional entries

The 305 records in `metadata/candidates-2026.json` remain an *endorsed/announced* roster with `officialNomination:false`. For four inspected electorates:

| District | Names on VEC page during review | Existing provisional records for this district | Observation |
| --- | ---: | ---: | --- |
| Melbourne | 9 | 3 | VEC lists **Phillip Courtis** as One Nation; registry still has **Matthew Collins** in Melbourne. Do not assume the reason or mutate either name without official final VEC resolution. VEC page says final list available shortly. |
| Glen Waverley | 7 | 3 | VEC lists additional named contestants outside accepted provisional roster (e.g. Nicholas Siow, John Mullahy, Anna Dobie, Segar Nadarajah). VEC page says final list available shortly. |
| Murray Plains | 7 | 4 | VEC lists three names absent from accepted provisional roster: Asyiqin Sanif, Ewan McDonald, Peita Collard. VEC page labels list final, but displayed order is nomination-receipt order. |
| Ovens Valley | 9 | 2 | VEC uses **Benjamin Gilbert**, while provisional Greens record is **Ben Gilbert**: likely alias, not proven separate individual. Other candidates not in provisional roster; page labels list final but order is nomination-receipt order. |

VEC sources checked:
- Melbourne: <https://vec.vic.gov.au/electoral-boundaries/state-districts/melbourne-district/nominations>
- Glen Waverley: <https://www.vec.vic.gov.au/electoral-boundaries/state-districts/glen-waverley-district/nominations>
- Murray Plains: <https://www.vec.vic.gov.au/electoral-boundaries/state-districts/murray-plains-district/nominations>
- Ovens Valley: <https://www.vec.vic.gov.au/electoral-boundaries/state-districts/ovens-valley-district/nominations>
- Western Metropolitan (Council sample showing final-list notice): <https://www.vec.vic.gov.au/electoral-boundaries/state-regions/western-metropolitan-region/nominations>

**Methodological caveat:** This is a four-seat spot check, with publication states evolving during election-night operations. The 305-entry provisional roster was deliberately limited to previously adjudicated announcements/endorsements; a missing provisional entry is **not** proof of a missing candidate, mistake by the candidate, or a missed final nomination. Names and counts are subject to fresh official-carrier validation. Links and reviewed passages are recorded here but the raw VEC pages/spreadsheet have **not** been archived with SHA256 in this review. Do not represent this file as an immutable source receipt.

## Admission and forecasting boundaries

- Await the VEC's **post-draw official ballot-order candidate file**. Fetch and archive the raw source before parsing; preserve exact URL, retrieval instant, SHA256, file format, VEC publication/finality status, all 88 districts and eight Council regions. Do not derive ballot order from the current displayed nomination order.
- Produce a complete machine-reconciled candidate/party/contest ledger, including Council group/column order, ungrouped candidates, and official VEC party spelling. Resolve conflict/alias flags with primary evidence; supply reviewer packet for owner/governed admission **before** modifying `metadata/candidates-2026.json`.
- The existing engine's uniform five-family assumptions have no official 2026 ballot mask (see `docs/PROSPECTIVE_SNAPSHOT_SEALING.md`). Factual candidate coverage is a separate deliverable from a future, separately governed structural model revision.
- **Do not** modify engine parameters, seed, poll eligibility, forecast outputs, validation histories or 6/9 production-readiness status because nominations closed.
- The registered `nominations_close` prospective cutoff at **12 noon 9 November** has passed. A missed live seal cannot be manufactured after 4 pm or retroactively timestamped. Audit and report the actual seal status separately rather than infer a seal from schedule alone.

## Review acceptance criteria

A future reviewed change should supply all 96 VEC contests with complete list and official ballot/group order, VEC raw carrier(s) + hashes, a candidate conflict/alias report, party/contest counts reconciled against a single official data version, test evidence, and an explicit unchanged/changed forecast-input declaration.

**This PR's scope:** a preliminary evidence review only; no candidate statuses are promoted, no source-acquisition failures are declared repaired, no stale links are substituted for final ballot evidence, no statistical results are amended.
