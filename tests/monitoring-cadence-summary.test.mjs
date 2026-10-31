import test from "node:test";
import assert from "node:assert/strict";
import { monitoringCadence, cadenceSummary } from "../scripts/monitoring-cadence.mjs";
test("skipped acquisition is explicitly not checked", () => {
 const result=monitoringCadence(new Date("2026-10-31T01:00:00Z"),"schedule");
 assert.equal(result.run,false);
 assert.match(cadenceSummary(result), /NOT CHECKED/);
 assert.match(cadenceSummary(result), /does not establish source recovery/);
});
test("manual scheduling does not claim that sources passed", () => {
 const result=monitoringCadence(new Date("2026-10-31T01:00:00Z"),"workflow_dispatch");
 assert.equal(result.run,true);
 assert.match(cadenceSummary(result), /not a source-health check/);
});
