# 11 November 2026 — October VEC enrolment capture and critical-source currency

**Purpose:** recover a newly available official primary source for the 2026 state election forecast, **without** changing the approved 31 October reference forecast or retroactively altering the model's 6/9/5/9 gate history.

## Confirmed evidence

- Latest VEC enrolment landing page: <https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics>. Search-indexed live content on 11 November publishes **October 2026 district and region spreadsheets**, both advertised as **.xls** downloads, alongside September .xlsx extracts. It gives a statewide roll of **4,725,477 electors as of 5 November 2026**.
- Existing project official VEC extract effective **4 September 2026**: **4,683,403** electors reconciled independently across 88 districts and eight regions, with workbook fingerprints and 88/8 records in `metadata/vec-enrolment-validation-2026-09-04.json`.
- Difference between those two *published statewide totals*: **42,074** electors (+0.898%). This is provisional source-to-source comparison; it is **not** evidence of a uniform 0.898% increase within every district or an estimated seat model effect. It is not a district-level admission.
- The 4 September source is **68 days old on 11 November**. `metadata/sources.json` gives the critical VEC source a **62-day** limit, so the **criticalSourceFreshness gate is correctly failed** and the real current overall readiness is **5/9**, down from 6/9 at the older assessment.
- **Completed 11 November audit:** GitHub Actions [run #42866354349](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42866354349) passed the source trust tests and then downloaded and reconciled the **original BIFF .xls** district and region files: 88/88 and 8/8, 5 November extraction date, exact statewide total **4,725,477** in both, all names matched to the accepted September crosswalk. The capture artifact is [#13788245341](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42866354349/artifacts/13788245341), preserved for 30 days. **It remains review-only and is not a model admission.**

## Verified source bytes and geographical change

| Material | Official VEC source | SHA-256 |
| --- | --- | --- |
| Source listing page | [VEC roll statistics](https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics) | `5c88ecedc48b2c6ab8e8d08dfcb88312aa25ae249e6450011567a28fe8221f69` |
| October district workbook (93,184 bytes, genuine XLS BIFF) | [VEC district XLS](https://www.vec.vic.gov.au/-/media/4739cbf7670546dcb4b7b3427b278383.xls) | `bd0cb3ceee05b9abbb2f507b0a0cb522e6c589a55e5a453cda600ef710420fb1` |
| October region workbook (85,504 bytes, genuine XLS BIFF) | [VEC region XLS](https://www.vec.vic.gov.au/-/media/ff6250a17186410aa98e545b11f9e8e4.xls) | `50f9d64690fe98b47cd0f6425aa40c8fe92f04f4b6453d7c884aea5bb40f7c8d` |

Both workbooks state **Date Extracted: 5 November 2026**, match every original electorate/region name, and total **4,725,477 electors**, matching VEC publication. District and region preview CSVs are independently hashed (district `aea0784a3a18a85d57e2e42b265289aa7feaa9187e0a6ad3d7af56e10aac1e7d`; region `c778a069dd0a171073a33c179e4c6cba98a7fab5e90e9ca5d16db998ac452f21`).

Largest absolute changes since the accepted 4 September source are **Kalkallo +1,667 (+2.43%)**, **Berwick +1,348 (+2.05%)**, **Tarneit +1,248 (+2.10%)**, **Werribee +1,191 (+1.93%)**, **Pakenham +1,010 (+1.84%)**, **Melbourne +1,000 (+1.78%)**. Every one of the 88 districts increased; these nonuniform changes warrant real seat-by-seat weighting review rather than applying the statewide +0.90% to each district.

For Council, the largest region increases are **Western Metropolitan +7,938 (+1.30%)**, **Northern Metropolitan +6,817 (+1.13%)** and **South-Eastern Metropolitan +5,320 (+0.90%)**. All eight region changes are positive and the sum equals the district increase **42,074**.

This confirms **source eligibility and completeness**, not permission to silently retune a poll or make a new registered prediction. The 3 November electoral roll closure and the workbooks' 5 November extracted snapshot are separate legally relevant dates.

## Source capture

The standalone `scripts/capture-vec-enrolment-oct-2026.py` follows the official VEC listing, requires **both October 2026** links and HTTPS VEC hosts, fingerprints original page/workbook bytes, and verifies real file format by ZIP/XLS binary magic rather than extension. It supports the old XML .xlsx reader and BIFF .xls with pinned `xlrd` **only in the review-only runner**; it does **not** modify frozen modelling Python dependencies.

Checks required before any admission recommendation:

1. Exactly **88 distinct, ordered Assembly districts** and **eight distinct, ordered Council regions**.
2. Authentic VEC “Date Extracted” values for both, identical and plausible for the October publication.
3. District and region elector totals reconcile **exactly**, with a cross-check to the VEC's public statewide total when machine-readable on the official listing.
4. Every district and region name matches the September accepted crosswalk without silent remapping.
5. Original workbook source URLs, byte hashes, ETag/Last-Modified if available, retrieval timestamp, complete per-district/region deltas, change ranks, and preview CSVs are all preserved in a **30-day Actions review artifact**.
6. Source-layout changes, website caching, 403s, inconsistent dates or mismatched totals **stop** the review. They must not be presented as completed adoption.

The [source acquisition issue #167](https://github.com/MusicOfScience/vic-election-2026/issues/167) tracks the **second, owner-governed stage**: independent source review, potential exact input replacement, deterministic 88-seat and eight-region forecast impact calculations, a new prospective forecast vintage if approved, and re-evaluation of freshness. Do not attempt to restore the gate simply by advancing a timestamp.

## Operational interpretations

- The new website build deployed after merge #166 is **not itself a new electoral forecast**. A 31 October model as-of, 11 November site-build date, and 5/9 source-freshness warning can all be true simultaneously.
- No page code/forecast code or critical source metadata is changed in this PR.
- The approved model's inability to pass all historical seat-probability gates is unaffected by 2026 source currency. **Statistical 9/9 remains blocked** by complete-model backtesting, probability calibration and production authorisation.
