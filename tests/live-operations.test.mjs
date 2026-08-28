import test from "node:test";
import assert from "node:assert/strict";
import { canonicaliseHtml, classifyObservation, validateMarkers } from "../scripts/monitor-live-sources.mjs";

test("live source canonicalisation removes volatile script/style content", () => {
  const html = "<html><style>.x{color:red}</style><body>  Victorian   election <script>nonce='abc'</script></body></html>";
  const canonical = canonicaliseHtml(html);
  assert.equal(canonical.includes("nonce"), false);
  assert.equal(canonical.includes("color:red"), false);
  assert.equal(canonical.includes("Victorian election"), true);
});

test("marker validation is case-insensitive and reports missing markers", () => {
  assert.deepEqual(validateMarkers("Victorian State Election 2026", ["state election", "2026"]), { passed: true, missing: [] });
  assert.deepEqual(validateMarkers("Victorian State Election", ["28 November"]), { passed: false, missing: ["28 November"] });
});

test("changed valid sources quarantine rather than auto-promote", () => {
  assert.equal(classifyObservation({ valid: true, acceptedFingerprint: "old", observedFingerprint: "new" }), "changed-quarantined");
  assert.equal(classifyObservation({ valid: false, acceptedFingerprint: "old", observedFingerprint: "new" }), "invalid-quarantined");
  assert.equal(classifyObservation({ valid: true, acceptedFingerprint: "same", observedFingerprint: "same" }), "healthy");
});
