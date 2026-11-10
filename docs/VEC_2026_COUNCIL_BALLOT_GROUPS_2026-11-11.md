# VEC 2026 Council ballot-group reconciliation — 11 November 2026

## Result: 303/303 candidates verified against eight official VEC pages

Following the complete official nominations source capture and publication of all 1,037 names in PR #161, the VEC's live **Legislative Council region nomination pages** have now been independently fetched and reconciled to the 303 candidate names in the immutable source-derived roster. This resolves the important field omitted by the VEC Excel candidate-contact-person report: **upper-house ballot group letter, group label, grouped candidate order and ungrouped classification**.

The successful source capture was run by GitHub Actions on **11 November 2026 AEDT**, using `scripts/audit_vec_council_groups.py`. It finished with **eight regions matched, 303 nominees matched in strict source sequence, zero errors**. The independently captured page SHA-256 digests and exact group-boundary counts are in `app/vec-council-groups-2026.review.json`, derived from the audited 7-day GitHub review artifact. Candidate-display roster SHA-256 and original VEC XLS SHA-256 are both recorded.

| Legislative Council region | Candidates | Lettered groups | Ungrouped candidates |
| --- | ---: | ---: | ---: |
| Eastern Victoria | 32 | 11 | 0 |
| North-Eastern Metropolitan | 38 | 12 | 0 |
| Northern Metropolitan | 43 | 13 | 1 |
| Northern Victoria | 37 | 13 | 1 |
| South-Eastern Metropolitan | 35 | 12 | 1 |
| Southern Metropolitan | 31 | 11 | 0 |
| Western Metropolitan | 43 | 12 | 1 |
| Western Victoria | 44 | 15 | 1 |
| **Total** | **303** | **99** | **5** |

The five ungrouped names confirmed in the independent page-level audit are **Peter Razos (Northern Metropolitan)**, **Nick McHugh (Northern Victoria)**, **Susantha Abeysinghe (South-Eastern Metropolitan)**, **Rakesh Raizada (Western Metropolitan)** and **Eve Fisher (Western Victoria)**. The remaining 298 candidates stand in lettered groups, some with an **Unnamed-1/Unnamed-2** group designation. Candidates without a registered party in the original XLS must not all be described as ungrouped: **unnamed groups are still ballot groups**.

VEC primary-source examples:
- <https://www.vec.vic.gov.au/electoral-boundaries/state-regions/north-eastern-metropolitan-region/nominations>
- <https://www.vec.vic.gov.au/electoral-boundaries/state-regions/northern-metropolitan-region/nominations>
- <https://www.vec.vic.gov.au/electoral-boundaries/state-regions/western-metropolitan-region/nominations>
- <https://www.vec.vic.gov.au/candidates-and-parties/become-a-state-election-candidate/upper-house-groups>

## Data-minimisation, validity and governance

The original VEC pages expose named candidate contact persons, phone numbers and email addresses. **The workflow never retains raw source HTML in the artifact**. The committed dataset consists solely of **eight source-page hashes and 104 group boundaries** (99 lettered + five Ungrouped), their official VEC labels and candidate counts. Each group boundary assigns candidates by their **strictly audited original VEC Council source order**, rather than fabricating a mapping from party names.

The public app's **Official candidates** tab can therefore show the actual 2026 Council ballot-group layout, including ungrouped candidates, independently of the five-family election prediction model.

Crucially, **Victoria abolished group voting tickets for 2026**. A ballot column indicates a group and its placement, **not a registered transfer ticket or estimated preference-flow matrix**. No candidate-weight, forecast-input, baseline, probability, calibration or production authorisation is changed.

The source snapshot is **11 November 2026**, not a live guarantee against subsequent VEC edits. Future workflow runs must compare fresh page SHA-256s and candidate lists against this captured version; changed source material needs an explicit evidence review. The registered prospective validation schedule and 6/9 release readiness status remain unchanged.

## Tests

- VEC live capture: exact **303 Council candidate name-and-order** matches, all eight regions, group letters A… without omissions, Ungrouped only after lettered columns.
- Source integrity: original VEC workbook and candidate-display JSON hashes.
- Derived per-region group boundary counts sum to VEC candidate totals; 99 lettered groups and five ungrouped names.
- No public contact details; no group voting tickets inferred; no auto-promotion of provisional candidates.
- Python unit tests cover out-of-order/missing candidates, missing group letter, source header failure, and ungrouped behaviour; Node tests cover public-data invariants and named spots.

**Status:** factual ballot structure independently sourced and ready for public display, subject to the owner's review/merge. **Not** statistical certification or a fresh forecast.
