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

test("analyst evidence dialog is mobile contained rather than a floating strap", () => {
  assert.match(css, /\.analyst-evidence-dialog/);
  assert.match(css, /max-height: calc\(100dvh - 16px\)/);
  assert.doesNotMatch(css, /position:\s*fixed/);
});
