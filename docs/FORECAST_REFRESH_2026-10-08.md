# Owner polling decisions and deterministic refresh

Base: merged PR #123 (`8ddf08a`); branch `codex/approve-freshwater-september-refresh`.

The project owner accepts September Freshwater evidence, declares it model-eligible and authorizes one canonical addition. September RedBridge/Accent evidence is accepted but model eligibility remains pending documented respondent/sample-family independence. September DemosAU and Resolve remain evidence/model holds with their existing source, category and methodology blockers. These decisions are recorded through `metadata/poll-review-approval-2026.json` and the existing application script; discovery-review decisions and model eligibility remain separate.

Existing rules require provenance, composition, methodology/regime, sample-dependency review and explicit admission. They impose no blanket repeat-respondent-exclusion requirement on previously comparable Freshwater waves. No rolling sample or MRP pooling is reported; undisclosed respondent repeats remain a limitation. The wave retains the `freshwater` source family and `Freshwater Strategy` pollster effects. RedBridge's explicit independence blocker is retained. Supporting cross-tabs and commentary create no additional observations.

## Canonical observation

- Eligible observations: **12 → 13**; total registry events: **13 → 14**. Every pre-existing event and estimate row is unchanged.
- New ID: `freshwater_2026-09`; evidence ID `freshwater-2026-09-primary-workbook`.
- Fieldwork: 24–28 September; effective date 28 September. Poll publication: 1 October; first-party tables: 2 October.
- Full N=1,030; primary valid base N=977; TPP base N=956. Effective N is undisclosed and remains blank.
- Exact primaries: ALP 24.0121, Coalition 28.9106, ONP 22.1313, Greens 14.3689, Other 10.5771. Rounded values remain separately preserved in the source/accepted evidence.
- Coalition–Labor TPP: 53.4087–46.5913, retained as evidence and canonical event provenance; no extra observation is constructed from it.
- Original workbook SHA: `e74537ac81246b6e4207963cfcf8a5bffa3f512516370baa917648c85f175e9e`. The existing offline extractor reproduces the retained extraction exactly.

## Forecast comparison

Assessment date advances **26 August → 8 October**. Seed `20260826`, 5,000 simulations, empirical-Bayes aggregation, 45-day half-life, sample cap, pollster effects and every Assembly/Council parameter are unchanged. These are total refresh deltas, including the normal effect of advancing the date on recency and uncertainty; they are not a causal estimate of one poll's impact.

Full precision, all 88 district changes, all eight Council regional changes and gate comparisons are in [`metadata/forecast-refresh-2026-10-08.json`](../metadata/forecast-refresh-2026-10-08.json). Intervals below are frozen 80% model intervals.

| Family | Statewide primary old → new | Change, pp | Primary 80% interval old → new | Assembly expected seats old → new | Median old → new | Assembly 80% range old → new |
| --- | --- | --- | --- | --- | --- | --- |
| ALP | 25.6403 → 25.3356 | −0.3047 | 24.3403–26.8977 → 23.9474–26.6874 | 38.8778 → 38.2896 (−0.5882) | 39 → 38 | 30–48 → 29–48 |
| Coalition | 27.6724 → 27.7978 | +0.1253 | 26.2214–29.1557 → 26.2073–29.4396 | 30.3486 → 31.0216 (+0.6730) | 30 → 31 | 22–39 → 23–40 |
| ONP | 23.2722 → 23.1037 | −0.1685 | 21.8486–24.7170 → 21.5466–24.6567 | 16.4622 → 16.2792 (−0.1830) | 16 → 16 | 10–23 → 10–23 |
| Greens | 13.3737 → 13.5311 | +0.1574 | 12.7048–14.0688 → 12.8100–14.2783 | 2.3076 → 2.4032 (+0.0956) | 2 → 2 | 1–3 → 1–4 |
| Other/independent | 10.0413 → 10.2318 | +0.1905 | 9.3608–10.7582 → 9.3833–11.1290 | 0.0038 → 0.0064 (+0.0026) | 0 → 0 | 0–0 → 0–0 |

ALP majority probability: **21.32% → 19.30% (−2.02pp)**. Coalition majority: **2.20% → 3.10% (+0.90pp)**. Other family majority probabilities remain zero. Hung parliament: **76.48% → 77.60% (+1.12pp)**.

A district movement is material if **any family's win probability changes by at least five percentage points**. All districts were checked: **none qualifies**. The maximum is Prahran ALP, 57.54% → 53.90% (−3.64pp). There are **no likely final-pair changes**. All smaller movements remain inspectable in the machine-readable report.

Council is legitimately downstream of statewide polling; its regional evidence and parameters are unchanged.

| Family | Council expected seats old → new | Change | Median old → new | 80% range old → new |
| --- | --- | --- | --- | --- |
| ALP | 11.7344 → 11.5910 | −0.1434 | 12 → 12 | 10–13 → 10–13 |
| Coalition | 12.5480 → 12.5820 | +0.0340 | 13 → 13 | 11–14 → 11–14 |
| ONP | 10.1290 → 9.9918 | −0.1372 | 10 → 10 | 8–12 → 8–12 |
| Greens | 2.8996 → 2.9794 | +0.0798 | 3 → 3 | 2–4 → 2–4 |
| Other/independent | 2.6890 → 2.8558 | +0.1668 | 3 → 3 | 1–4 → 1–5 |

Council majority probabilities remain zero; major-party no-control probability remains 100%. These conditional model outputs do not establish what the election will do.

## Generated release state and integrity

Readiness as of 8 October: **4/9 → 6/9**. Critical-source freshness and model-input freshness change BLOCKED → PASS. Source integrity, deterministic outputs, historical-data readiness and candidate evidence remain PASS. Complete backtest, probability calibration and production authorisation remain BLOCKED. The 21-day rule is unchanged; newest eligible fieldwork is ten days old. All staged poll records have explicit owner decisions, including continued holds.

The August shadow retains 26 August, its original DemosAU/Resolve IDs and the original 2,000 simulations. Updated dependency fingerprints reflect this refresh without admitting September evidence to that scenario. Historical replay artefacts and the deferred resilience/demographic challengers are unchanged.

Previous canonical forecast SHA: `70ed0b9b6abc45ed66dd4ac44ed727d8841d2b19358a473d0eb1c2574a9a1aab`.

Refreshed canonical forecast SHA: `a1b9f98566931293edbcaf7edc320e90778feffff401d8fbc69e3abb2328eff2`.

## Validation

- `npm test`: build and all **167 JavaScript tests pass**.
- `PYTHONDONTWRITEBYTECODE=1 /private/tmp/vic-refresh-20261008-env/bin/python -m pytest model/tests -q`: all **71 Python tests pass**. Python 3.11 environment uses project-declared dependencies with `model/constraints.txt`: NumPy 2.3.5, pandas 2.2.3 and PyYAML 6.0.3.
- `PATH=/private/tmp/vic-refresh-20261008-env/bin:$PATH npm run forecast:refresh`: original deterministic command executed twice; the second run leaves the same canonical SHA and all output hashes.
- Poll generation, owner-promotion idempotence, source provenance, model export and release-readiness checks pass. Both poll and candidate owner-review generators agree on the shared review log; all 194 candidate decisions remain unchanged.
- Existing candidate, psephology, replay-contract and validation-evidence checks pass. Historical readiness remains four runnable / three certifying scored cycles, with backtest and calibration closed.
- `npm run shadow:check` and the original 2,000-simulation shadow generator `--check` pass. Scenario date and evidence IDs are retained; numerical shadow differences are floating-point noise below 1e-12.
- `npm run lint`, comparison-report `--check`, and `git diff --check` pass. All 20 historical replay artefacts are byte-identical; forecast-engine code, historical inputs, candidate inputs, model coefficients and deferred challenger evidence/specification are unchanged.

Exact next action: review this owner-decision and deterministic forecast-refresh PR.
