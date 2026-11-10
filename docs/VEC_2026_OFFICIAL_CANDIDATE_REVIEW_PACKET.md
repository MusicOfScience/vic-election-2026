# 2026 official candidates: privacy-minimised VEC reconciliation packet

## Scope and authority

The VEC published 1,037 nominated candidates on 10 November 2026: 734 Assembly candidates in 88 districts and 303 Council candidates in eight regions. The exact raw Excel 97–2003 carrier and checksums are already captured in `metadata/vec-nominations-2026-11-10-source-audit.json`, merged through PR #159. **That audit is the source authority**, not the legacy 305-record provisional candidate list.

The source workbook is also a *Candidate Contact Persons' Details Summary Report*. It includes contact-person names, telephone numbers and email addresses. This workflow selects and exports **only** `chamber`, `contest`, `rowOrdinal`, `candidate`, `registeredParty`. Do not commit the original XLS or any contact columns to the public repository.

## Reproduce the official review packet

From GitHub Actions on a clean `main`, manually dispatch **Capture VEC 2026 final candidate carrier (review only)**. The workflow:

1. Fetches the VEC original and produces the archived raw SHA-256 receipt using the already released acquisition script.
2. Installs pinned `xlrd==2.0.1` for this legacy BIFF8/Excel source. This dependency is confined to the review-only workflow, not the public Next.js application.
3. Requires **exact raw source SHA-256 and byte length from the merged PR #159 audit**, independently of the fresh capture receipt. A changed VEC carrier fails **closed** until reviewed and rebaselined with explicit evidence.
4. Checks the election and source report headers, **all 96 named contests**, their declared number of candidates, all **734 + 303** rows, and unique candidate identity within each contest. An unknown or malformed workbook cannot yield an accepted output.
5. Generates two separate ephemeral 30-day artifacts: original VEC raw evidence (already present in the workflow) and `vec-nominations-candidate-review-only` containing `official-candidates-review.csv`, `official-candidates-review.json`, `candidate-reconciliation-review.json`, and `summary.json`. The derived candidate files omit contact columns entirely.

The roster parser is `scripts/extract_vec_nominations.py`. Its normalised name check compares official `SURNAME, Given` strings with the 305 provisional `Given Surname` names, **without inferring party continuity**. Every official candidate becomes either an exact normalised name match or a human-review identity candidate; every provisional record not matched gets a separate quarantine flag. A name not found on the ballot does **not** prove a withdrawal, and a blank RPP column does not prove independent or ungrouped status.

## Acceptance gate

A green run proves the *same source version* was parsed without releasing the contact information. It **does not** by itself authorise status updates, candidate promotion or forecast inputs.

Before publication or registry admission:

- Independently compare candidates and **Assembly ballot order** with current VEC district pages; source row sequence is not by itself a universally verified ballot-position statement.
- Cross-check each Council region page's **group letter/column, party/unnamed-group and ungrouped presentation**; those fields are **not present** in this XLS.
- Review name differences and party labels (particularly Melbourne One Nation provisional Matthew Collins versus official Phillip Courtis; Ovens Valley Ben/Benjamin Gilbert).
- Check candidate changes, current source version and individual conflicts against the provisional accepted register. Record owner review and separate admission decisions.
- Keep `officialNomination`, polling input, forecast parameters, 2026 predictions and prospective validation seals unchanged until independently governed authorisation.
- Do not mark 9/9 production readiness from source or software completion. Existing model remains **6/9 and experimental**.

**Hard stop:** A changed VEC workbook, failed total, missing contest, duplicate identity, ambiguous alias or missing Council grouping must be marked *incomplete or held*, never silently repaired.

Source: <https://www.vec.vic.gov.au/2026-state-election>.
