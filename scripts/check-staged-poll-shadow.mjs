import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const reportPath = resolve(root, "metadata/staged-poll-seat-shadow-2026.json");
const report = JSON.parse(readFileSync(reportPath, "utf8"));
const expected = report.inputFingerprint;

if (report.mode !== "full-election-shadow-sensitivity-only") throw new Error("shadow report: unsupported mode");
if (report.canonicalModelInputsChanged || report.canonicalForecastArtifactsWritten || report.scenarioEvidencePromoted) {
  throw new Error("shadow report: canonical isolation flags must remain false");
}
if (!expected?.combinedSha256 || !expected.files) throw new Error("shadow report: input fingerprint missing");

const combined = createHash("sha256");
for (const relative of Object.keys(expected.files).sort()) {
  const payload = readFileSync(resolve(root, relative));
  const actual = createHash("sha256").update(payload).digest("hex");
  if (actual !== expected.files[relative]) throw new Error(`shadow report stale: ${relative} changed`);
  combined.update(relative);
  combined.update("\0");
  combined.update(payload);
  combined.update("\0");
}
if (combined.digest("hex") !== expected.combinedSha256) throw new Error("shadow report: combined fingerprint mismatch");

console.log(`Staged-poll shadow current: ${report.simulationsPerScenario} simulations; ${report.scenario.evidence.length} quarantined polls; canonical forecast untouched.`);
