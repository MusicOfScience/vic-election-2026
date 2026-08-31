# Discovery review

Live discovery remains fail-closed. The scheduled source-monitor workflow now produces `discovery-review-manifest.json` beside the raw discovery and quarantine reports.

Party-endorsed and defensibly confirmed public candidate discoveries that have survived structural validation are also preserved in `metadata/provisional-candidate-evidence-2026.json`. This is a durable quarantine ledger, not the accepted candidate registry. Its records may be reviewed individually even when the source page later changes or disappears.

To make an explicit decision, review the cited primary source first, then run:

```bash
node scripts/apply-discovery-decision.mjs \
  --input source-discovery-quarantine.json \
  --id <evidence-id> \
  --decision approve \
  --reviewer <reviewer-name> \
  --note "Checked against primary source"
```

Use `--decision reject` to record a rejection without promoting the record.

Approved candidate evidence enters `metadata/candidates-2026.json` at the status actually supported by the reviewed source: `announced` or `endorsed`. Only VEC evidence can confer official nomination/election lifecycle states.

Approved poll evidence enters `metadata/accepted-polls-2026.json` with `modelEligible: false`. Acceptance of a source record is deliberately separate from permission to change forecast inputs.

For the model-input freshness gate, every staged poll must have an explicit review disposition. `approve`, `defer`, `hold` and `reject` all resolve the review obligation; only separately authorised model eligibility can change forecast inputs. Held, deferred and rejected evidence therefore remains excluded without leaving the freshness gate permanently blocked.

Every decision is appended to `metadata/discovery-review-decisions.json` with the evidence ID, record hash, reviewer, timestamp and note.

## Candidate source-family approval

When a deterministic dossier covers a complete set of reviewed source families, the project owner may record one decision per family in `metadata/candidate-review-approval-2026.json`. Run `npm run candidates:review:apply` to materialise the status-matched records and their per-record audit entries. The verified build runs `npm run candidates:review:check` so later evidence drift cannot silently alter the accepted register.

This approval records public candidacy evidence only. It does not confer VEC nomination status or enable candidate effects in the forecast. The coverage gate opens only when all 88 Assembly districts are represented in the accepted registry.
