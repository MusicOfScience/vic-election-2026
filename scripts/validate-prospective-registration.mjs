import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, lstatSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve, isAbsolute } from "node:path";
import { gunzipSync } from "node:zlib";

const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const sorted = (v) => Array.isArray(v) ? v.map(sorted) : v && typeof v === "object"
  ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, sorted(v[k])])) : v;
const canonicalHash = (v) => hash(JSON.stringify(sorted(v)));
const REGISTRATION_SHA = "6ffdd7f47ef45c43b039425424889638c571ccb5136181bc28508f759dc24a64";

// Operational registry reconciliation only. The frozen Python verifier separately
// reconstructs predictions/comparators from archived carriers, without outcomes.
export function validateProspectiveRegistration(protocol, root, receiptOverride = null) {
  const read = (p) => JSON.parse(readFileSync(resolve(root, p), "utf8"));
  assert.equal(hash(readFileSync(resolve(root, "metadata/prospective-registration-2026-10-08.json"))), "210ba1e583bba2769fbcecb57deb8727647743d38feca6dbd28ba782178d9e2b", "first registration receipt is immutable");
  const first = read("metadata/prospective-registration-2026-10-08.json");
  const receipt = receiptOverride ?? first;
  const initial = receipt.snapshotId === "post_freshwater_registration";
  if (!receiptOverride) {
    assert.deepEqual(protocol.sealing.currentlySealedSnapshots[0], first, "first registry entry is immutable");
    const ids = protocol.sealing.currentlySealedSnapshots.map((s) => s.snapshotId);
    assert.equal(new Set(ids).size, ids.length, "snapshot registry is append-only; duplicate ID");
    for (const entry of protocol.sealing.currentlySealedSnapshots.slice(1)) validateProspectiveRegistration(protocol, root, entry);
  }
  assert.equal(receipt.kind, "prospective-live", "fixtures/simulations cannot register");
  const specification = protocol.snapshots.find((s) => s.id === receipt.snapshotId);
  assert.ok(specification, "unregistered milestone");
  assert.equal(receipt.role, specification.role);
  assert.equal(receipt.electionUnit, "vic_2026_general_election");
  assert.equal(receipt.additionalIndependentElectionReplications, 0);
  assert.equal(receipt.scoringAuthorised, false);
  assert.equal(receipt.productionAuthorised, false);
  if (initial) assert.equal(receipt.manifestSha256, REGISTRATION_SHA, "existing seal is immutable");
  assert.equal(receipt.archivePath, `model/data/validation/prospective-snapshots/${receipt.snapshotId}`);
  assert.equal(receipt.manifestPath, `${receipt.archivePath}/manifest.json`);
  const bytes = readFileSync(resolve(root, receipt.manifestPath));
  assert.equal(hash(bytes), receipt.manifestFileSha256);
  const manifest = JSON.parse(bytes), body = structuredClone(manifest);
  delete body.manifestSha256;
  assert.equal(canonicalHash(body), receipt.manifestSha256);
  assert.equal(manifest.manifestSha256, receipt.manifestSha256);
  for (const k of ["snapshotId", "role", "electionUnit", "kind", "witnessedAt", "protocolId", "protocolSha256", "forecastSha256", "scoringAuthorised", "productionAuthorised"]) assert.equal(receipt[k], manifest[k], k);
  assert.equal(manifest.registered, true);
  assert.equal(manifest.independentElectionCount, 1);
  assert.equal(manifest.gitCommit, receipt.sourceCommit);
  assert.match(receipt.sourceCommit, /^[0-9a-f]{40}$/);
  if (initial) assert.equal(receipt.sourceCommit, "9b40186f203ca8aba77d9afbee71ba5a59c46dc9");
  assert.match(receipt.sealCommit, /^[0-9a-f]{40}$/);
  assert.notEqual(receipt.sealCommit, receipt.sourceCommit);
  assert.equal(manifest.mergeProof.remoteMain, receipt.sourceCommit);
  assert.equal(manifest.mergeProof.approvalAlreadyInCommittedMain, true);
  const witness = Date.parse(receipt.witnessedAt);
  assert.ok(Number.isFinite(witness) && witness >= Date.parse(receipt.sourceMainMergedAt) && witness > Date.parse(protocol.approval.recordedAt));
  assert.equal(Date.parse(receipt.witnessedAtMelbourne), witness);
  if (initial) assert.equal(Date.parse(manifest.cutoff), witness, "registration cutoff is actual witness, not forecast date");
  else {
    const cutoff = Date.parse(specification.cutoff);
    assert.equal(Date.parse(manifest.cutoff), cutoff);
    assert.ok(witness <= cutoff && witness >= cutoff - 60000, "milestone witness outside registered window");
    const index = protocol.sealing.currentlySealedSnapshots.indexOf(receipt);
    assert.ok(witness > Date.parse(protocol.sealing.currentlySealedSnapshots[index - 1].witnessedAt), "registry chronology");
  }
  assert.ok(Date.parse(receipt.registeredAt) >= witness && Date.parse(receipt.registeredAt) <= Date.now());
  assert.equal(receipt.protocolSha256, protocol.approval.approvedProtocolSha256);
  if (initial) assert.equal(receipt.forecastSha256, protocol.model.baselineForecastSha256);
  assert.equal(manifest.files["archive/model/data/processed/experimental_forecast_2026.json"].sha256, receipt.forecastSha256);
  const packageRoot = resolve(root, receipt.archivePath), actual = [];
  function walk(dir, prefix = "") {
    for (const name of readdirSync(dir)) {
      const member = resolve(dir, name), path = prefix + name;
      assert.equal(lstatSync(member).isSymbolicLink(), false, "archive symlink forbidden");
      if (lstatSync(member).isDirectory()) walk(member, path + "/"); else actual.push(path);
    }
  }
  walk(packageRoot);
  assert.deepEqual(actual.sort(), [...Object.keys(manifest.files), "manifest.json"].sort(), "extra/missing archive member");
  assert.equal(Object.keys(manifest.files).length, receipt.memberCount);
  for (const [path, expected] of Object.entries(manifest.files)) {
    assert.ok(!isAbsolute(path) && !path.split("/").includes(".."));
    const member = readFileSync(resolve(packageRoot, path));
    assert.equal(hash(member), expected.sha256, `archived member changed: ${path}`);
    assert.equal(member.length, expected.bytes);
  }
  const impl = JSON.parse(readFileSync(resolve(packageRoot, "archive/metadata/prospective-validation-implementation.json")));
  assert.equal(receipt.comparatorImplementationSha256, impl.comparatorImplementations.prior_result);
  assert.equal(receipt.comparatorImplementationSha256, impl.comparatorImplementations.uniform_swing);
  assert.equal(receipt.scorerSha256, impl.scorerSha256);
  // The sealed file is canonical Python JSON: 1.0 and 1 are distinct bytes.
  // Hash each exact canonical object slice instead of reserialising JS numbers.
  const predictionBytes = readFileSync(resolve(packageRoot, "predictions.json"), "utf8").trimEnd();
  const priorStart = predictionBytes.indexOf('"prior_result":') + '"prior_result":'.length;
  const swingStart = predictionBytes.indexOf('"uniform_swing":') + '"uniform_swing":'.length;
  assert.ok(priorStart > 0 && swingStart > priorStart);
  assert.equal(hash(predictionBytes.slice(priorStart, swingStart - ',"uniform_swing":'.length)), receipt.comparatorPredictionSha256.prior_result);
  assert.equal(hash(predictionBytes.slice(swingStart, -1)), receipt.comparatorPredictionSha256.uniform_swing);
  const calendarBytes = readFileSync(resolve(root, receipt.calendarReceiptPath));
  assert.equal(hash(calendarBytes), receipt.calendarReceiptSha256);
  const calendar = JSON.parse(calendarBytes);
  assert.equal(calendar.conflict, false);
  assert.ok(Date.parse(calendar.retrievedAt) <= witness && witness - Date.parse(calendar.retrievedAt) <= 86400000);
  assert.deepEqual(calendar.dates, read("metadata/prospective-validation-calendar-check.json").dates);
  assert.deepEqual(calendar.sources, read("metadata/prospective-validation-calendar-check.json").sources);
  const carrier = readFileSync(resolve(root, receipt.calendarReceiptPath, "..", calendar.carrierPath));
  assert.equal(hash(carrier), calendar.carrierSha256);
  assert.equal(hash(gunzipSync(carrier)), calendar.uncompressedSha256);
  return { sealedSnapshots: protocol.sealing.currentlySealedSnapshots.length, additionalIndependentElectionReplications: 0 };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = resolve(process.argv[2] ?? new URL("..", import.meta.url).pathname);
  console.log(JSON.stringify(validateProspectiveRegistration(JSON.parse(readFileSync(resolve(root, "metadata/model-vnext-validation-protocol.json"))), root)));
}
