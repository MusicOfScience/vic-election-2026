import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, mkdtempSync, mkdirSync, cpSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { monitoringCadence } from "../scripts/monitoring-cadence.mjs";
import { monitoringActions } from "../scripts/build-monitoring-action-report.mjs";
import { candidateFromDiscovery } from "../scripts/apply-discovery-decision.mjs";
import { discoveryStatus, isKnown } from "../scripts/discover-live-source-records.mjs";
import { validateProspectiveRegistration } from "../scripts/validate-prospective-registration.mjs";
const root = new URL("..", import.meta.url).pathname;
const protocol = JSON.parse(readFileSync(`${root}/metadata/model-vnext-validation-protocol.json`));
const healthy = () => Object.fromEntries(["release-readiness-report", "live-source-report", "source-discovery-report", "source-discovery-quarantine", "discovery-review-manifest", "analyst-comparison-report", "evidence-freshness-report", "poll-promotion-audit", "poll-coverage-report", "freshwater-primary-report"].map((k) => [k, {}]));

test("cadence uses Melbourne date and stages daily acquisition only during campaign", () => {
  assert.equal(monitoringCadence(new Date("2026-10-08T20:17:00Z")).run, true); // Friday Melbourne
  assert.equal(monitoringCadence(new Date("2026-10-09T20:17:00Z")).run, false);
  assert.equal(monitoringCadence(new Date("2026-11-02T20:17:00Z")).phase, "campaign-daily");
  assert.equal(monitoringCadence(new Date("2026-11-27T20:17:00Z")).run, true);
  assert.equal(monitoringCadence(new Date("2026-11-28T20:17:00Z")).run, false);
  assert.equal(monitoringCadence(new Date("2026-10-09T20:17:00Z"), "workflow_dispatch").run, true);
});

test("no action and timestamp-only checks have identical material fingerprints", () => {
  const a = healthy(), b = healthy(); a["live-source-report"].checkedAt = "old"; b["live-source-report"].checkedAt = "new";
  assert.deepEqual(monitoringActions(a), monitoringActions(b));
  assert.deepEqual(monitoringActions(a).statuses, ["NO_ACTION"]);
});

test("signals preserve quarantine, freshness and failures without model updates", () => {
  const r = healthy();
  r["release-readiness-report"].sources = [{ id: "polls", critical: true, stale: true, dataEffectiveDate: "old" }];
  r["live-source-report"].observations = [{ id: "vec", status: "changed-quarantined", observedFingerprint: "abc" }];
  r["source-discovery-quarantine"].records = [{ id: "p", kind: "poll", sourceId: "pollster" }, { id: "c", kind: "candidate", sourceId: "party" }];
  r["source-discovery-report"].observations = [{ sourceId: "broken", status: "extract-failed" }];
  const a = monitoringActions(r);
  assert.deepEqual(a.statuses.sort(), ["CANDIDATE_REVIEW_REQUIRED", "FRESHNESS_WARNING", "POLL_REVIEW_REQUIRED", "SOURCE_CHANGE_REVIEW_REQUIRED", "WORKFLOW_FAILURE"]);
  assert.equal(a.modelInputsChanged, false); assert.equal(a.automaticPromotion, false); assert.equal(a.forecastRefreshed, false);
  assert.equal(discoveryStatus(false), "quarantined-awaiting-review");
  assert.equal(discoveryStatus(true), "already-tracked");
});

test("missing report and failed silent stages cannot become NO_ACTION", () => {
  assert.ok(monitoringActions({}).statuses.includes("WORKFLOW_FAILURE"));
  assert.ok(monitoringActions(healthy(), [], { candidates: { outcome: "failure" } }).statuses.includes("WORKFLOW_FAILURE"));
});

test("review resolution requires exact carrier, not a previously reviewed ID", () => {
  const r = healthy(), record = { id: "p", kind: "poll", value: 30 };
  r["source-discovery-quarantine"].records = [record];
  const decisions = [{ evidenceId: "p", decision: "hold", recordHash: createHash("sha256").update(JSON.stringify(record)).digest("hex") }];
  assert.deepEqual(monitoringActions(r, decisions).statuses, ["NO_ACTION"]);
  record.value = 31;
  assert.deepEqual(monitoringActions(r, decisions).statuses, ["POLL_REVIEW_REQUIRED"]);
});

test("registry rejects mutation, duplicate records and fixtures while live forecast is separate", () => {
  assert.equal(validateProspectiveRegistration(protocol, root).sealedSnapshots, 1);
  for (const change of [
    (p) => { p.sealing.currentlySealedSnapshots[0].scorerSha256 = "replacement"; },
    (p) => { p.sealing.currentlySealedSnapshots.push(structuredClone(p.sealing.currentlySealedSnapshots[0])); },
    (p) => { p.sealing.currentlySealedSnapshots.push({ snapshotId: "fixture/writ_roll_close", kind: "fixture-non-empirical" }); },
  ]) { const p = structuredClone(protocol); change(p); assert.throws(() => validateProspectiveRegistration(p, root)); }
  // Validation obtains the sealed forecast from archived members, not current output.
  const implementation = readFileSync(`${root}/scripts/validate-prospective-registration.mjs`, "utf8");
  assert.ok(implementation.includes('archive/model/data/processed/experimental_forecast_2026.json'));
  assert.ok(!implementation.includes('read("model/data/processed/experimental_forecast_2026.json")'));
});

test("party evidence cannot spoof official nomination authority", () => {
  const r = { name: "Fixture", contest: "Footscray", sourceAuthority: "VEC", officialStatus: "nominated", sourceUrl: "https://party.example/candidate" };
  assert.equal(candidateFromDiscovery(r, "fixture").status, "endorsed");
  r.sourceUrl = "https://www.vec.vic.gov.au/candidates";
  assert.equal(candidateFromDiscovery(r, "fixture").status, "nominated");
});

test("workbook byte change is actionable even with unchanged rounded figures", () => {
  const r = healthy(); r["freshwater-primary-report"] = { allValid: true, records: [{ id: "workbook", url: "source", sha256: "new" }] };
  assert.deepEqual(monitoringActions(r, [], {}, [{ workbookUrl: "source", workbookSha256: "old" }]).statuses, ["SOURCE_CHANGE_REVIEW_REQUIRED"]);
});

test("a later live forecast cannot reinterpret an earlier seal", () => {
  const temporary = mkdtempSync(join(tmpdir(), "vic-live-seal-boundary-"));
  try {
    cpSync(`${root}/metadata`, `${temporary}/metadata`, { recursive: true });
    const destination = `${temporary}/${protocol.sealing.currentlySealedSnapshots[0].archivePath}`;
    cpSync(`${root}/${protocol.sealing.currentlySealedSnapshots[0].archivePath}`, destination, { recursive: true });
    mkdirSync(`${temporary}/model/data/processed`, { recursive: true });
    writeFileSync(`${temporary}/model/data/processed/experimental_forecast_2026.json`, '{"fixture":"later live forecast, not electoral evidence"}');
    assert.equal(validateProspectiveRegistration(protocol, temporary).sealedSnapshots, 1);
  } finally { rmSync(temporary, { recursive: true, force: true }); }
});

test("a known endorsed candidate's later VEC nomination still requires review", () => {
  const old = { name: "Fixture", contest: "Footscray", party: "Example", status: "endorsed", sourceAuthority: "Example" };
  const fresh = { ...old, kind: "candidate", candidateStatus: "nominated", sourceAuthority: "VEC", sourceUrl: "https://www.vec.vic.gov.au/candidates" };
  assert.equal(isKnown(fresh, [old], []), false);
  assert.equal(candidateFromDiscovery(fresh, "fixture").status, "nominated");
});
