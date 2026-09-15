import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import { refreshDashboardEnrolment } from "../scripts/refresh-dashboard-enrolment.mjs";

const root = resolve(import.meta.dirname, "..");

test("dashboard enrolment refresh preserves sealed election and validation evidence", () => {
  const dashboard = readFileSync(resolve(root, "app/data.generated.ts"), "utf8");
  const enrolment = readFileSync(resolve(root, "model/data/processed/vec_enrolment_district_2026-09-04.csv"), "utf8");
  const refreshed = refreshDashboardEnrolment(dashboard, enrolment);

  assert.match(refreshed, /"name": "Albert Park"[\s\S]*?"enrolment": 50488/);
  assert.match(refreshed, /"name": "Yan Yean"[\s\S]*?"enrolment": 56321/);
  assert.match(refreshed, /"alpTpp2022": 61\.150600869342895/);
  assert.match(refreshed, /"cycle": "2010"[\s\S]*?"baselineMae": 2\.538152571009978/);
});
