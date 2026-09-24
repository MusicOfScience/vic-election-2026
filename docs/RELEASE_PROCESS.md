# Forecast update and release process

The project follows a fail-closed, pull-request-based release process. Automation may detect a change, regenerate outputs and report readiness, but it never promotes an experimental forecast to production by itself.

## Normal update

1. Update the canonical source registry and its local source artefacts. Preserve the original source URL, effective date, verification status and caveats.
2. Run `npm run forecast:refresh`. This reruns the seeded model and rebuilds the website-facing poll, model, provenance and readiness artefacts.
3. Review the Git diff. A timestamp-only or no-op update is not a material release.
4. Run `python -m pytest model/tests`, `npm test` and `npm run lint`.
5. Submit the change through a pull request. Publish only the reviewed commit that passed all checks.
6. If the material forecast changed, append an immutable snapshot with `npm run snapshot:create` before release.

## Automated checks

- **Forecast quality gates** run on pull requests and `main`. They regenerate every deterministic artefact and fail if the committed outputs differ.
- **Source freshness and live-source monitor** runs twice weekly and can also be started manually. It assesses critical-source staleness, validates live source contracts and uploads machine-readable reports.
- **Live-source quarantine** fingerprints canonical upstream responses. Changed or invalid sources are retained for review and never silently promoted into model inputs.
- **Candidate validation** enforces provisional versus VEC-official candidate states and rejects invalid official status claims.
- For a targeted update, `npm run forecast:refresh:changed -- BASE_REF` uses content changes—not file timestamps—to rerun only affected forecast, public-data and provenance stages.

## Live-source promotion

A valid changed source is not automatically accepted. Review `live-source-report.json`, confirm that the publisher, date, semantics and parsed values are what the model expects, then run `npm run sources:promote -- --id <adapter-id> --report live-source-report.json`. Commit the resulting state change through a pull request before adapting any canonical model input.

## Production gates

The readiness report deliberately separates historical **data availability** from predictive **model validation**. A four-cycle ledger proves that the historical substrate exists; it does not certify the complete 2026 probability model.

A production release requires all of the following:

- current source fingerprints and critical-source age checks;
- no newer reviewed evidence left unresolved outside the canonical model input;
- matching model output and configuration hashes;
- the four-cycle historical dataset;
- walk-forward backtesting of the complete multi-party seat model;
- probability calibration and interval-coverage tests;
- sufficient 2026 candidate evidence across all 88 Assembly districts; and
- explicit production authorisation.

Feature experiments are recorded separately. The demographic challenger failed its sealed promotion test and remains at zero central weight. That rejection is an honest modelling result, not a failed requirement that prevents a simpler validated model from eventually reaching production.

`metadata/model-validation-evidence-contract.json` records the evidence required to test the complete system. The four-cycle TPP residual ledger satisfies the two-party benchmark component, and the official Assembly primary outcome component is now complete. Leakage-safe specifications are frozen for 2010, 2014, 2018 and 2022, but they remain deliberately unrunnable. A version-pinned candidate polling series establishes 200 observations across the four cycles, yet it is quarantined because fieldwork midpoint cannot substitute for publication date and sample, explicit method, observation-level source and reuse-licence fields are absent. Ballot timing/incumbency, preference/final-pair and frozen historical configurations remain partial; Council evidence is complete.

`metadata/model-validation-evidence-inventory.json` is the fingerprinted, machine-audited account of progress against that contract. It records three complete components and four partial components, with no component wholly missing. Official Assembly primary outcomes comprise 2,296 candidate rows and 1,760 five-family rows: 351 general-election district-cycle outcomes plus the separately dated 28 January 2023 Narracan supplementary contest. Narracan is excluded from the November 2022 cycle score and all pre-cutoff inputs. The remaining partial evidence includes the quarantined 200-row polling candidate series; final ballot identities whose pre-cutoff timing and incumbent/challenger states remain unresolved; 39 indicative Assembly preference distributions; and deliberately unrunnable historical model configurations. Council evidence is now complete: official primaries and full published count-total sequences cover all 32 region-cycle contests in 2010, 2014, 2018 and 2022, comprising 1,394 candidate rows, 5,975 count events, 296,087 count-total rows and 160 elected candidates. The exact authorised Electoral Act 2002 versions effective on each election day pin the common ballot, quota, transfer, exclusion, tie and termination rules for all four cycles. Four deterministic historical cycle specifications continue to enforce election-eve cutoffs, scoring-only outcomes and zero weight for the rejected demographic challenger. Component completion is not production authorisation: the complete-model gates remain closed.

`model/config/historical-party-family-crosswalk.json` freezes the only five historical primary families accepted by the complete model: ALP, Coalition, Greens, One Nation and Other/Independent. Matching is exact after conservative whitespace and case normalisation. Unknown labels fail closed and require an evidence-backed adjudication; missing parties remain missing until non-contestation is verified, rather than being silently converted to zero. Every completed district import must map each formal vote exactly once and reconcile family totals to the official formal-vote total.

`metadata/historical-public-source-audit.json`, `metadata/historical-source-acquisition-plan.json` and `metadata/historical-source-residual-gaps.json` enforce a supplied-and-first-party-source-first workflow. The supplied 1,088-page VEC 2010 report and 267 fingerprinted public 2014-2022 sources yield complete, reconciled Assembly primary outcomes for all four cycles. The VEC request is therefore closed as not required. The frozen 200-row polling file remains a lead list while original pollster and publisher records are reconstructed. Dated first-party publications now provide observation URLs and samples for 64 leads—33 Essential, seven Newspoll and 24 SMS Morgan—with explicit method evidence for 41. Eight Essential, 32 Newspoll and nine SMS Morgan leads remain unresolved. Archive capture dates determine evidence availability. Cumulative Newspoll rows without observation-specific samples remain excluded, as does a Roy Morgan election-eve page captured after the local cutoff. No formal reusable-data licence has been established; that fact is recorded separately from independently reconstructed factual observations under the three-gate policy. No action is currently required from the project owner. All acquired material remains quarantined until every acceptance rule passes. One Newspoll source is an archived contemporaneous mirror of a branded pollster PDF. The May-June 2015 publisher graphic has a cutoff-safe archived article confirming its link and sample, but that capture does not preserve the image binary: its current method text remains corroborating only and is excluded from the verified method count.

If any required gate fails, retain the last valid forecast and do not publish new probabilities as production-ready.
