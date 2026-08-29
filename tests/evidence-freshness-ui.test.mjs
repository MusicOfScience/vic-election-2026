import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

test("visible freshness status keeps staged evidence separate from the model", () => {
  const component = readFileSync(resolve(root, "app/evidence-freshness-status.tsx"), "utf8");
  const layout = readFileSync(resolve(root, "app/layout.tsx"), "utf8");
  const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));

  assert.match(component, /staged for review, not yet in the model/);
  assert.match(component, /cannot refresh the forecast until evidence acceptance and model eligibility are explicitly approved/);
  assert.match(layout, /<EvidenceFreshnessStatus \/>/);
  assert.equal(manual.records[0].status, "quarantined-awaiting-review");
  assert.equal(manual.records[0].automaticPromotion, false);
});
