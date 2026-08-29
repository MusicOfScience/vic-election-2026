import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const component = readFileSync("app/analyst-evidence-guide.tsx", "utf8");
const css = readFileSync("app/analyst-evidence.css", "utf8");
const layout = readFileSync("app/layout.tsx", "utf8");

test("analyst evidence is exposed through the horizontal navigation", () => {
  assert.match(component, />Analysts<\/button>/);
  assert.match(component, /document\.querySelector\("\.dashboard-tabs-list"\)/);
  assert.match(layout, /<AnalystEvidenceGuide \/>/);
  assert.match(component, /Model vs analysts/);
});

test("analyst surface explains comparison rather than averaging", () => {
  assert.match(component, /Comparison, not averaging/i);
  assert.match(component, /zero direct analyst model inputs/i);
  assert.match(component, /do not become forecast weights/i);
});

test("external YouGov MRP is a visible seat-model comparison rather than a hidden weight", () => {
  assert.match(component, /External seat model/);
  assert.match(component, /YouGov \/ Common Threads MRP/);
  assert.match(component, /Comparison only · not a forecast input/);
  assert.match(component, /same survey\/model family and are never counted as two independent signals/i);
  assert.match(component, /current model median seats/i);
  assert.match(component, /5,000 simulations/);
});

test("analyst evidence dialog is mobile contained rather than a floating strap", () => {
  assert.match(css, /\.analyst-evidence-dialog/);
  assert.match(css, /max-height: calc\(100dvh - 16px\)/);
  assert.doesNotMatch(css, /position:\s*fixed/);
});
