# Approved protocol and pre-sealing infrastructure

The project owner explicitly approved `vic-2026-prospective-observational-v1`.
The record is [prospective-validation-approval.json](../metadata/prospective-validation-approval.json).
Its `recordedAt` is the actual time the instruction was recorded, not a backdated
proposal or forecast-generation time. PR #125 proposal identity and byte hash are
preserved in the receipt. Scoring and production remain unauthorised.

## Immutable rules and implementation

[Approved rules](../metadata/prospective-validation-approved-rules.json) preserve
PR #125's methodological content without changes. Their SHA256 is
`747449970bf4a0bb4304e528c9e2ec37dd77420fffb1e1ee056fd0b4af4bdb01`.
The fingerprint uses recursively sorted compact UTF-8 JSON with literal Unicode.
Operational status, approval receipt, next action, scoring state and the snapshot
registry are excluded from that projection; excluding them does **not** grant
permission to change scoring state or enter fixtures. Dedicated guards enforce
those decisions separately. Both the validator and sealer pin the approved hash.

[Implementation fingerprints](../metadata/prospective-validation-implementation.json)
freeze the comparators, scorer, package builder, CLI, governance code and input
contract. `node scripts/freeze-prospective-validation-implementation.mjs --check`
verifies them. The generator records fingerprints; it does not approve changes.
A changed implementation requires reviewed amendment before a new seal; changed
methodological rules require a prospectively versioned protocol. Earlier packages
keep their original code. The live forecasting engine is untouched.

## Package contents

The directory package contains `manifest.json`, canonical `predictions.json`,
`source-ledger.json`, `runtime.json` and `archive/` with actual carrier bytes:

- approved protocol/rules/approval and implementation receipts;
- frozen engine source, runner, configuration, Python constraints/project metadata
  and npm dependency lock; actual runtime versions;
- both canonical polling tables and the eligible/held evidence registries;
- AEC local district/region surfaces, official enrolment, district-region mapping,
  2022 indicative candidate evidence and recent by-election signal carrier;
- the exact regional poll consumed by the Council model;
- comparator 2022 official district-family primaries/winners, Council candidate
  primaries/elected names and family mappings;
- captured September Freshwater workbook/publication/extraction and RedBridge PDF,
  with held material clearly excluded from the model;
- source/provenance, current candidate context, contamination, readiness and
  model-validation records, and the fresh VEC calendar-review receipt;
- every committed forecast export: full district winner vectors, primary estimates,
  chamber summaries, exported ALP seat marginal, Council outputs and exported
  ordered likely-final-pair probability.

The manifest hashes every member, records sizes and mandatory paths, ties inputs
and outputs to code/config/seed/simulations, and carries its own canonical hash.
Verification rejects missing/extra files, symlinks, changed bytes, material-rule
changes and generated predictions/comparators that do not reconcile with archived
carriers. References to unavailable original legacy poll web captures remain
explicit: the extracted canonical registry is the archived model input, not a
claim to have recovered those pages. Recorded Git carrier times are labelled
repository availability bounds, not invented original capture/owner decision
instants. Existing decision-record timestamps are distinct from unknown original
per-observation admission timestamps. Actual package capture is witnessed now.

The current engine uses no official 2026 candidate ballot mask. It models five
families everywhere; this is archived as a model assumption, not invented ballot
verification. Current candidate registrations are contextual, while prior
candidate votes and by-election winner signals are quantitative inputs.

Unavailable exports remain unavailable: full joint seat draws, Council regional
interval bounds and conditional final-pair winner probabilities are not exported
by this engine. No new simulation or forecast rerun manufactures them. Council
regional means can be scored, but their interval coverage cannot. Exported ordered
winner-runner pair occurrence probability can support a binary event score;
conditional preference accuracy cannot be reconstructed later.

## Live chronology and witness

Live sealing requires a clean checkout named `main` at the exact remotely verified
main SHA, with approval and implementation already committed there. Thus this
approval feature branch cannot seal itself. The code gets start/final witness
instants from the actual system UTC clock. There is no historical `--captured-at`
or witness-time override. Git SHA and remote-main verification receipt accompany
the archive. This is an actual runtime-clock witness, not a claim of independently
signed time attestation; preserve the package's manifest hash in the subsequent
reviewed repository receipt for durable audit.

For registration, the cutoff is the actual final witness instant and the exact
8 October forecast hash must still match. The registration seal must precede the
first later milestone. For scheduled freezes the package must complete no later
than the registered cutoff, within its final 60 seconds; an earlier invocation is
refused as not due. Prepare dependencies and evidence ahead of time. A missed
cutoff stays unavailable, never backfilled. Source publications, capture/commit
bounds and admission records must not exceed the cutoff. Carrier mutation during
copying, config/output mismatch and existing destination paths are refused.

Reverify both current VEC primary calendar pages before each seal, updating the
calendar receipt prospectively. Live sealing rejects a conflicting, future or
older-than-24-hour review. Current verified dates remain roll close 3 November
8pm, nominations 9 November noon, early voting 18 November, election 28 November.
An authoritative date change requires the registered prospective amendment; a
receipt alone cannot alter a cutoff.

After this approval PR is merged, the next run may execute, with the pinned Python
runtime and fresh calendar review:

```bash
python model/scripts/prospective_snapshot.py --output /path/to/new-registration-package
python model/scripts/prospective_snapshot.py --verify /path/to/new-registration-package
```

The command produces a self-contained package and manifest. It never silently
adds it to `currentlySealedSnapshots` or the older operational snapshot index.
The next sealing run must preserve the package and publish its verified manifest
hash/Git/witness receipt in a reviewed registration record. Do not mark registration
complete from a fixture or from an unpreserved temporary directory. No live seal
or registration entry is created in this infrastructure PR.

## Fixture and test path

```bash
python model/scripts/prospective_snapshot.py --fixture --output /tmp/new-non-empirical-fixture
python model/scripts/prospective_snapshot.py --verify /tmp/new-non-empirical-fixture
```

Fixture packages use `fixture/` IDs, `fixture-non-empirical` kind, zero empirical
units and `registered:false`. Synthetic availability bounds are visibly labelled.
Their calendar/window exercise does not assert a live cutoff; dedicated tests
exercise live timing refusals. Fixture construction remains usable after a live
milestone passes. Changing a fixture flag/ID cannot turn its availability receipts
into live evidence. Neither command opens any target outcome file.

## Comparators and scorer

`prior_result` repeats official November 2022 district five-family primaries and
winner families, with one-hot probabilities. Council repeats official regional
primaries and elected-family totals. Exact raw Council party labels are mapped:
Liberal Democrats remain OTH_IND. No substring-based party misclassification.

`uniform_swing` subtracts exact official 2022 statewide shares from the snapshot's
shared five-family statewide mean, separately for Assembly and Council baselines.
It adds that swing to prior local shares, truncates below zero and renormalises.
Assembly uses the unchanged current preference-counting matrix; Council uses the
same fixed group-STV matrix and 0.10 exhaustion. No shocks, fitted parameters,
seed draws or target-year results. Their implementations and dependency policy
are fingerprinted before sealing.

Narracan had no November 2022 general-election outcome. Neither comparator silently
substitutes January 2023 data; that district is unavailable. Consequently its
complete Assembly chamber/hung comparator is unavailable too, not a fabricated
87-seat chamber. Available district metrics have explicit denominators. All eight
Council regions remain available. Missing baseline/mapping evidence is never zero.

The frozen scorer implements multiclass Brier (sum over families, mean over valid
districts), clipped logarithmic loss at epsilon `1e-12`, zero/clipping disclosures,
registered tie-order winner accuracy, district-family MAE, official formal-vote
weighted statewide shares/errors, family-seat mean/median error, inclusive 80%
coverage/width, hung binary scores, Council regional primaries/seats, exported
final-pair occurrence metrics and ten-bin descriptive reliability. Incomplete
statewide universes remain unavailable; missing metrics retain reasons/denominators.

The public scoring entry validates the sealed package before opening a target
file. It requires an approved protocol, live registered manifest, protocol scoring
permission and a separately explicit project-owner scoring action bound to the
manifest/protocol/target hashes. It then requires official certified VEC identity,
the exact 88-district/eight-region universe and reconciled winner/seat totals.
`scoringAuthorised:false` keeps that loader closed now. Tests invoke pure arithmetic
only on toy synthetic values. No electoral target is loaded or scored in this batch.
Every future performance report remains descriptive for one election; neither the
scorer nor protocol approval changes the nine release gates.

Exact next action: review and merge the `post_freshwater_registration` seal PR.

A future scoring action must supply a separately governed operational protocol
copy with explicit scoring authorisation and the original owner receipt. The
scorer checks that its material-rules hash is still the approved hash. The archived
pre-election protocol remains immutable with `scoringAuthorised=false`; it is never
rewritten to enable scoring. Without that future governed copy, scoring continues
to fail closed.

## First live registration (after merged PR #126)

[The operational receipt](../metadata/prospective-registration-2026-10-08.json)
records the actual seal from clean remote-verified main, the later preservation
commit and the later-again registry update. The protocol's operational state is
`approved-registration-sealed`; material rules, creation/comparator/scorer code
and their fingerprints are unchanged. The original pre-registration protocol
inside the archive is preserved, not rewritten to mimic the active registry.

The package was created once, then verified in a separate command. It contains
70 hashed members plus its manifest. Its canonical manifest SHA is
`6ffdd7f47ef45c43b039425424889638c571ccb5136181bc28508f759dc24a64`;
the exact manifest-file byte SHA is separately recorded. Comparator-object hashes
use the exact canonical Python JSON object bytes (including floating-point forms),
not a different language's numeric reserialisation.

Execution-time calendar retrieval at `2026-10-08T06:04:47.030755Z` corroborated the
committed PR #126 calendar receipt, which was still within 24 hours. The package
preserves that committed receipt byte-for-byte so its clean source identity stays
true. The additional execution receipt and exact parsed primary-source retrieval
are preserved alongside it under `metadata/prospective-registration-witness/`;
the registration record hashes both. The retrieved text is losslessly gzipped,
with its compressed and uncompressed hashes. It is not represented as raw HTML.
No live web page is needed for archive verification. No new polling/candidate
review or quantitative admission occurred.

Copied source carriers retain their original bytes, including inherited whitespace.
Git treats `archive/` carriers as byte artefacts; manifest, prediction and registry
records remain textual for review. Both archive verification and governance checks
still hash every member. No frozen source was edited to appease whitespace checks.

Tests exercise the frozen creator against the archived pre-registration source
state in non-empirical fixture mode. Separate tests verify the actual live registry,
detached package, comparator determinism and refusal of premature scoring. This
does not reopen the one-time creator against an active live registry. No scoring
permission, production gate or second election unit is inferred from registration.
