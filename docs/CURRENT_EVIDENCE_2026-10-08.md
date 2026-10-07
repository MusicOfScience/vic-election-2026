# Current evidence decision packet

Assessed as of 8 October 2026. Base main: `aaad26fca59a55fea2951e38f92c0fed3dfbdca7` (PR #122).

The newest **model-eligible** Victorian poll remains `roy_morgan_2026-08`, published 8 August with fieldwork ending 7 August. The 21-day critical-source policy now sees a 62-day-old input. No canonical input or forecast changed. Release readiness remains `experimental-blocked`, 4/9 gates passing.

The machine-readable decision packet is `metadata/current-evidence-adjudication-2026-10-08.json`. The existing evidence registries and review dossier contain the new candidates. Original RedBridge PDF and Freshwater XLSX, extracted Freshwater results and live monitoring report are preserved under `metadata/current-evidence/2026-10-08/` and fingerprinted by the existing provenance generator. Owner approvals remain unchanged.

| Evidence | Recommendation | Remaining decision or gap |
| --- | --- | --- |
| September RedBridge/Accent, 1–14 September, full N=2,371 / effective N=2,009 / valid vote base N=2,160 | ACCEPT evidence recommended; HOLD model admission | Respondent reuse and independence from June/MRP and August families remain undisclosed. Owner acceptance and model eligibility are separate decisions. |
| Freshwater, 24–28 September, N=1,030 | ACCEPT evidence recommended; HOLD admission pending explicit decision | Captured first-party tables pass the existing extractor. Owner must approve evidence and separately adjudicate dependency, comparability and model admission. |
| DemosAU, reported 10–20 September, N=1,020 | HOLD | Primary report, publication, complete residual category, mode, undecideds and sample dependence unverified. Primary retrieval encountered captcha/parse misses. |
| Resolve, reported 6–12 September, N=967 | HOLD | Newly discovered 17 September commentary attributes original publication to 14 September. Rounded shares total 101; primary capture and sample/window discrepancies unresolved. This is not a confirmed poll published after 15 September. |

## September RedBridge determination

The publisher and original report establish an online-panel survey with quotas for age, gender, location, education and 2025 federal vote, and rim weighting for age, gender, education, religion and location. Leaners are included and unresolved respondents excluded. The September, August and June fieldwork windows do not intersect; the publisher describes regular snapshots. These support an inference of distinct surveys, but do not demonstrate independent respondents or establish whether June/MRP material was reused or pooled. No panel provider, cross-wave respondent exclusion or quantified dependence is disclosed.

Using the same panel provider would not itself prove double counting. Conversely, disjoint dates do not prove respondent independence. The existing Python overlap diagnostic only detects intersecting same-family windows; an empty diagnostic is not affirmative independence evidence. The promotion audit also requires explicit human acceptance and model eligibility. There is no authorised automatic rule that removes the recorded independence blocker.

The five-category primary composition is comparable in principle, subject to Carroll–Wilson timing, the valid-vote base and district-specific party options. Verified methodology and composition support evidence acceptance beyond mere recency; they do not supply the missing dependency evidence. Cross-tabs, commentary, alternative final pairs and MRP interpretations cannot be extra independent observations.

**Source correction:** visual inspection of Table 2, printed page 7 (PDF page 8), confirms Labor 44% against Coalition and Labor 53% against One Nation. The staged record previously mislabelled the latter as Coalition 53%. It now records Coalition–Labor 56–44 and separately Labor–One Nation 53–47, preserving correction history and the unchanged original report SHA. This corrects evidence only.

**ACCEPT consequence:** admission still requires independence/comparability review and explicit eligibility approval, then one canonical primary observation and a deterministic refresh. On 8 October, the September fieldwork is 24 days old and publication 23 days old; admission alone cannot clear the 21-day critical polling freshness gate. Numerical forecast consequences have not been simulated while the record is ineligible.

**HOLD/REJECT consequence:** preserve the last valid forecast. An explicit owner-recorded exclusion can resolve this particular review item; it cannot refresh stale inputs or resolve the other staged waves.

Exact one-line owner decision requested:

> HOLD redbridge-accent-vic-2026-09-14-primary from model inputs pending documented sample-family independence; evidence acceptance may be recorded separately.

## Newer primary evidence

Freshwater's [first-party page](https://freshwaterstrategy.com/2026/10/02/herald-sun-freshwater-strategy-september-polling-data/) was published 2 October; the poll was first reported by its commissioner on 1 October. Keep those dates separate. The captured workbook gives online-panel invitations, weighting to age-sex, age-education, 2022 state vote, 2025 federal vote and location, leaners included and remaining undecideds removed. Full N=1,030, primary valid base N=977 and TPP base N=956 are distinct; no effective N is disclosed.

The existing extractor gives ALP 24.0121%, Coalition 28.9106%, One Nation 22.1313%, Greens 14.3689% and Other 10.5771%, totalling 100%. Labor–Coalition TPP is 46.5913–53.4087. Method is comparable in principle with approved Freshwater waves and fieldwork is disjoint; repeat-respondent exclusions remain undisclosed. No rolling or MRP pooling is reported. Existing approval covers specific earlier poll IDs, not future waves, so this record remains staged. If explicitly approved, its 28 September effective date is ten days old and could satisfy critical polling freshness. That would justify a separate deterministic refresh.

The DemosAU and Resolve leads remain in the existing secondary-evidence quarantine with missing values explicit. The DemosAU arithmetic residual is not converted into a reported Other category. No Resolve TPP is reconstructed. Primary acquisition gaps are retained rather than filled from another wave's methodology.

## Monitoring and exclusions

Existing live monitoring found two healthy Roy Morgan sources and three changed VEC page fingerprints with all markers valid. No source state was promoted. The VEC roll page still presents 4 September enrolment and August downloads; no newer enrolment payload was established. Candidate nominations remain a November event. Discovery returned the two already-tracked Roy Morgan poll products and 290 quarantined candidate records; this run makes no candidate changes. The dedicated DemosAU extractor found no parseable record.

The primary-source scan was supplemented with Accent, Freshwater, DemosAU, Roy Morgan and VEC pages, targeted Resolve/Pyxis searches and secondary coverage checks. It is a best-effort search, not a claim that inaccessible evidence does not exist.

Roy Morgan's [6 October update](https://www.roymorgan.com/findings/roy-morgan-update-october-6-2026) describes six-month seat analysis and a winnability transformation; it is excluded as an independent poll. Its [15 September three-seat analysis](https://www.roymorgan.com/findings/10323-victorian-state-voting-intention-august-2026) pools 643 respondents over twelve months to August and is excluded from current statewide polling. National polls, federal-intention state breakdowns and commentary are not Victorian Assembly observations. Resilience research remains parked.

## Validation dependency repair

Appending newer quarantined records exposed a latest-by-pollster selection bug in the older shadow tools. Both now pin the original August evidence IDs, so September records cannot silently enter that scenario. The existing generator refreshed the shadow report at its original 2,000 simulations and seed. Its scenario, seat and probability results are unchanged; polling floating-point differences are at most 7.11e-15 percentage points. Input fingerprints changed legitimately. The canonical 2026 forecast was not rerun.

Validation passed: `npm test` (build and 164 JavaScript tests), `python3 -m pytest model/tests` (69 tests), `npm run lint`, source/poll/readiness generated-output checks, candidate validation/review checks, psephology, historical replay/evidence contracts, shadow fingerprint and generator checks, and `git diff --check`. Canonical forecast SHA and frozen historical artefacts are unchanged.

## Gates and next action

Source integrity, deterministic artefacts, historical data readiness and candidate coverage remain passed. Critical-source freshness and unresolved newer model evidence remain blocked. Complete backtest and calibration remain closed under the current protocol; production authorisation remains closed. Updating the assessment date changes source ages, not effective dates or eligibility.

The sole next action is project-owner review of this packet and recording explicit evidence/eligibility decisions. Do not begin a forecast refresh, resilience build or new validation programme in this review batch.
