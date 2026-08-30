# Discovery review

Live discovery remains fail-closed. The scheduled source-monitor workflow now produces `discovery-review-manifest.json` beside the raw discovery and quarantine reports.

Party-announced candidate discoveries that have survived structural validation are also preserved in `metadata/provisional-candidate-evidence-2026.json`. This is a durable quarantine ledger, not the accepted candidate registry. Its records may be reviewed individually even when the source page later changes or disappears.

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

Approved candidate evidence enters `metadata/candidates-2026.json`. Party evidence can only produce an `endorsed` candidate; only VEC evidence can confer official nomination/election lifecycle states.

Approved poll evidence enters `metadata/accepted-polls-2026.json` with `modelEligible: false`. Acceptance of a source record is deliberately separate from permission to change forecast inputs.

Every decision is appended to `metadata/discovery-review-decisions.json` with the evidence ID, record hash, reviewer, timestamp and note.
