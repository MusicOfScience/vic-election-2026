# Production readiness path — 31 October 2026

## Decision

The owner requested progress to 9/9 after merging #145. The current score is **6/9**, and the three remaining gates cannot be closed by software completion or owner approval alone. This request authorises work towards readiness; it is not evidence that the statistical criteria have passed.

The public experimental app is deployed from merged commit `0419843fa3a0fa704cb107c72cd0febc6e6ed1d0`. Its quality gates and both staged-poll sensitivity workflows passed. The custom Pages deployment passed and the public HTML serves the 31 October snapshot with the experimental hung-parliament headline.

## Exact remaining gates

| Gate | Evidence deficit | Legitimate closure path |
| --- | --- | --- |
| Complete forecast backtest | Only 2010, 2014 and 2022 are certifying v2 cycles. The 2018 defect and post-hoc diagnostic are permanently non-certifying. | A separately governed validation design with demonstrably eligible independent evidence, frozen model identity, inputs, comparators, metrics and stopping rules before target exposure. No such replacement evidence is established in the current audit. |
| Probability calibration | Required cycle-clustered evidence is incomplete; final-pair and regional-primary probability products are unavailable. | Produce and evaluate the specified probability products on eligible frozen evidence, including reliability, slope/intercept, interval coverage and final-pair calibration. Districts, simulation draws and repeated snapshots must not be counted as independent elections. |
| Production authorisation | Both statistical gates remain closed and the forecast is production-incompatible. | Explicit release review after both prerequisites pass. User permission cannot substitute for empirical validation. |

The existing prospective protocol explicitly states that **one 2026 election cannot supply the missing historical replication or establish multi-election calibration**. Waiting for 28 November is therefore not a promised route to 9/9 either. Historical scores must remain unchanged; renaming versions or rerunning consumed outcomes does not make them unseen. A new model identity does not erase target exposure.

Authoritative references: `metadata/model-validation-status.json`, `model/data/validation/historical-replays/historical-four-cycle-validation-status.json`, `metadata/model-vnext-validation-protocol.json`, and `docs/NEXT_VALIDATION_PATH.md`. The older component evidence contract is a historical inventory, not a current completion checklist or permission to reopen the historical programme.

## Work that can advance usability now

These are operational tasks; completing them does not open statistical gates.

1. **Restore primary-source acquisition.** The post-merge monitor run `41143280032` failed because `one-nation-victoria-candidates` and `family-first-victoria-coverage-gaps` returned HTTP 403. All workflow stages executed, Freshwater parsed four valid workbooks, and critical-source freshness passed. The summary correctly failed closed on the two inaccessible sources. Check accessible first-party candidate carriers, preserve provenance and test any adapter repair. Until verified, report incomplete acquisition; do not remove the sources, suppress the failures or infer that no announcements occurred.
2. **Review changed carriers and quarantined candidate records.** The run reports three changed live carriers and a 213-record review manifest (201 candidate and 12 poll records). These are discovery counts, not counts of new accepted facts. Reconcile exact carrier hashes and existing identities before any acceptance. Existing polling holds remain holds.
3. **Prepare the next registered snapshot.** `writ_roll_close` is 3 November 2026 at 8pm Melbourne. Preparation and fixture testing may happen beforehand. Only seal at the registered window from clean remote-verified main with fresh VEC verification; never backfill a missed window or overwrite the first seal.
4. **Reconcile official nominations after VEC publication.** Current accepted candidate evidence is not the final official ballot universe. Preserve announcement/endorsement versus official nomination distinctions and validate all 88 districts and eight Council regions.
5. **Obtain current Council regional evidence.** The refreshed statewide polling does not make August regional inputs current. Do not substitute subscriber-only figures that have not been obtained and captured.
6. **Complete real-device usability review.** Test mobile navigation, seat search, source/evidence inspection, preference/final-pair explanations and experimental labelling on the deployed app. Static build success is not device QA.

## Evidence preserved

The source-monitor artifact is `13019187373`, named `operational-readiness-reports`, retained by GitHub for 90 days. It contains source discovery, quarantine, review, freshness and action reports. Durable accepted carrier evidence must be captured into reviewed commits before admission; an expiring artifact is not a replacement archive.

This audit changes no model input, parameter, forecast, threshold, release flag or prospective archive. It does not seal a snapshot, score 2026 or authorise production. A fully usable experimental app and a statistically certified production probability model are different deliverables; the former can improve now while the latter remains blocked.
