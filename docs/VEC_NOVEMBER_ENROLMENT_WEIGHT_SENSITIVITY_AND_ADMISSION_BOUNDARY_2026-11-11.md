# 11 November 2026 — accepted source freshness 6/9 → 5/9, and proposed restoration

## What is actually true

The owner and project achieved **6/9 on 31 October 2026**. That is documented in `metadata/release-readiness.generated.json` (as-of 31 Oct). It had exactly three blocks: **completeForecastBacktest**, **probabilityCalibration**, **productionAuthorisation**.

On 11 November the unchanged accepted VEC 4 September enrolment input was **68 days old**, exceeding the separately preregistered **62-day** critical-source policy. The live assessment therefore correctly reported **5/9**: an operational source-freshness failure, *not* revocation of the earlier three-cycle historical validation work. PR #168 merged source capture and review but did **not** update the model's existing September source references, approval or freshness ledger, so 5/9 remains accurate until a new source is admitted and integrated.

## Exact official October VEC evidence

- VEC official <https://www.vec.vic.gov.au/enrolment/electoral-roll-statistics>, October workbooks extracted **5 November 2026**.
- October district raw XLS: `https://www.vec.vic.gov.au/-/media/4739cbf7670546dcb4b7b3427b278383.xls`, SHA-256 `bd0cb3ceee05b9abbb2f507b0a0cb522e6c589a55e5a453cda600ef710420fb1`.
- October region raw XLS: `https://www.vec.vic.gov.au/-/media/ff6250a17186410aa98e545b11f9e8e4.xls`, SHA-256 `50f9d64690fe98b47cd0f6425aa40c8fe92f04f4b6453d7c884aea5bb40f7c8d`.
- Review-only CSV digests: district `aea0784a3a18a85d57e2e42b265289aa7feaa9187e0a6ad3d7af56e10aac1e7d`; region `c778a069dd0a171073a33c179e4c6cba98a7fab5e90e9ca5d16db998ac452f21`.
- Exactly **88 districts** and **eight Council regions**, identical names and order, consistent extraction dates, totals agreeing **4,725,477**. Previous approved September total **4,683,403**; net **+42,074 (+0.898%)**.
- Spatial variation is material for a weighting change: **Kalkallo +1,667 (+2.427%)**, **Berwick +1,348 (+2.054%)**, **Tarneit +1,248 (+2.098%)**, **Werribee +1,191 (+1.934%)**, **Pakenham +1,010 (+1.840%)**, compared with **Mill Park +135 (+0.280%)**. Every district increased, but not at a uniform rate.
- Source evidence: [PR #168 acquisition and successful 88/8 reconciliation](https://github.com/MusicOfScience/vic-election-2026/actions/runs/42866354349), artifact ID `13788245341`, retained 30 days.

## Deterministic forecast-impact test before any admission

`model/scripts/shadow_vec_november_enrolment.py` runs the *same frozen 31 October five-party engine* twice, using **5,000 elections per run**, identical seed `20260826` and unchanged approved poll corpus. The only change is **in-memory substitution** of the two existing September enrolment CSV reads with exact audited 5 November CSV bytes. Raw XLS and derived CSV hashes must match known source receipts; 88/8 names and totals are checked again. No canonical model files are edited. The original baseline must reproduce the exact published 31 October party mean seats before examining the variant.

The complete research artifact contains:
- all **88 seat winner-frequency shifts**, any changed modal winning families, ranked largest shifts, threshold ≥5 percentage points;
- **all eight Council regional mean-seat changes**, as well as Assembly expected seat shifts and hung/majority differences;
- evidence fingerprints and explicit **review-only / no owner approval** status.

The study is a sensitivity to enrolment weighting, **not** proof that the latest enrolments improve predictions, a new forecast date, or an authorisation. A 5 Nov VEC source cannot make November public polls eligible by implication.

## Acceptance and authorisation

A separate, explicit owner decision can approve the exact source bundle following a green read-only impact run; that decision must be bound to raw XLS checksums, date, 88/8 rows and numerical effect. Only *after* that approval may a separate implementation PR update:
1. canonical district and Council-region enrolment inputs;
2. explicit model engine references, dashboard source date and weight values, source provenance hashes and effective dates;
3. exactly unchanged model architecture and other eligible polling inputs, fixed seed and deterministic results, with an **as-of date prospectively recorded**;
4. checksums/tests, model deltas, readiness report and website output; existing historical seals and retrospective backtests immutable.

Then re-evaluate the gate. **At most this action restores 6/9**. It does *not* make the incomplete 2018 complete-model evidence, unreliable probability calibration or production authorisation magically valid. A 9/9 target requires independent statistical evidence beyond freshness.

**Do not merge a later model-input promotion without owner authorisation.** This review PR remains safe to merge as it does not promote data, alter the forecast, or edit historical research.
