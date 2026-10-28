import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const component = readFileSync("app/analyst-evidence-guide.tsx", "utf8");
const css = readFileSync("app/analyst-evidence.css", "utf8");
const layout = readFileSync("app/layout.tsx", "utf8");
const externalModels = JSON.parse(readFileSync("metadata/analyst-external-models.json", "utf8"));

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

test("external seat models are registry-backed comparisons with explicit crossbench allocation", () => {
  assert.match(component, /analyst-external-models\.json/);
  assert.match(component, /External seat models &amp; scenarios/);
  assert.match(component, /never averaged into the forecast/i);
  assert.match(component, /Other \/ independent/);
  assert.match(component, /current model median seats/i);
  assert.match(component, /5,000 simulations/);

  const youGov = externalModels.models.find((model) => model.id === "yougov-common-threads-victoria-mrp-2026-08-09");
  assert.ok(youGov, "YouGov/Common Threads MRP must remain in the comparison registry");
  assert.equal(youGov.projection.otherIndependent, 0);
  assert.equal(
    youGov.projection.coalition + youGov.projection.labor + youGov.projection.oneNation + youGov.projection.greens + youGov.projection.otherIndependent,
    88,
  );
  assert.match(youGov.caution, /14% Others/i);
  assert.equal(externalModels.policy, "comparison-only-not-forecast-input");
});

test("analyst evidence dialog is mobile contained rather than a floating strap", () => {
  assert.match(css, /\.analyst-evidence-dialog/);
  assert.match(css, /max-height: calc\(100dvh - 16px\)/);
  assert.doesNotMatch(css, /position:\s*fixed/);
});

test("analyst view exposes the governed full-election shadow without presenting it as the forecast", () => {
  assert.match(component, /What if the two newest staged polls were admitted\?/);
  assert.match(component, /Shadow only/);
  assert.match(component, /it does not accept either poll, change the published forecast or open the production gate/);
  assert.match(component, /Most fragile calls/);
});

test("live analyst discoveries remain visibly quarantined from reviewed evidence and forecast inputs", () => {
  assert.match(component, /New since the reviewed evidence snapshot/);
  assert.match(component, /pending governed review/i);
  assert.match(component, /discovery never changes the forecast or promotes evidence automatically/i);
  assert.match(component, /analyst-live\.generated\.json/);
});
