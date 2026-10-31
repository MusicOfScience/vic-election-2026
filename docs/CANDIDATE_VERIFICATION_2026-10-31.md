# Candidate verification continuation — 31 October 2026

Merged #147 deployed successfully from `bce09fdbb7dddfbd90ed38e4eb3b3e08445029cc`.

Source-monitor run `41146907115` is green because its acquisition job was skipped by cadence. It is not evidence that the One Nation/Family First runner failures recovered. The cadence script now writes an explicit NOT CHECKED summary when no acquisition is scheduled. When acquisition is scheduled it explicitly defers health assessment to the acquisition job.

The 20 pending candidate carriers concern 19 distinct first-party URLs. Each URL returned HTTP 200 during the new direct requests. `metadata/candidate-verification-2026-10-31/primary-page-checks.json` preserves response hashes, retrieval times, final URLs, heading extracts and per-record checks. Eight names occur in headings; no record has both its supplied name and contest confirmed by these heading checks. These simple checks do not assess full page content and do not establish endorsement, continued candidacy, or the absence of an access challenge. They cannot justify automatic acceptance or rejection. Full responses are not archived; this is supporting evidence alongside the earlier roster captures.

The accepted candidate registry, decisions, model inputs, forecast and prospective archive remain unchanged. Candidate identity/status reconciliation still needs full primary carrier review. Actual iOS/Android visual testing remains outstanding.

Validation: 28 targeted JavaScript tests pass, including skipped versus manual cadence summaries and candidate discovery safeguards. Generated readiness remains current at 6/9. No statistical gate changes.
