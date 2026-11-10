# 11 November 2026 — October VEC enrolment capture and critical-source currency

**Purpose:** recover a newly available official primary source for the 2026 state election forecast, **without** changing the approved 31 October reference forecast or retroactively altering the model's 6/9/5/9 gate history.

## Confirmed evidence

- Latest VEC enrolment landing page: <https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics>. Search-indexed live content on 11 November publishes **October 2026 district and region spreadsheets**, both advertised as **.xls** downloads, alongside September .xlsx extracts. It gives a statewide roll of **4,725,477 electors as of 5 November 2026**.
- Existing project official VEC extract effective **4 September 2026**: **4,683,403** electors reconciled independently across 88 districts and eight regions, with workbook fingerprints and 88/8 records in `metadata/vec-enrolment-validation-2026-09-04.json`.
- Difference between those two *published statewide totals*: **42,074** electors (+0.898%). This is provisional source-to-source comparison; it is **not** evidence of a uniform 0.898% increase within every district or an estimated seat model effect. It is not a district-level admission.
- The 4 September source is **68 days old on 11 November**. `metadata/sources.json` gives the critical VEC source a **62-day** limit, so the **criticalSourceFreshness gate is correctly failed** and the real current overall readiness is **5/9**, down from 6/9 at the older assessment.
- Original October workbooks and their precise row structure have **not yet** been fully reconciled in this PR until the separate read-only GitHub workflow passes; a fresh listing alone cannot be treated as accepted 88/8 input evidence.

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
