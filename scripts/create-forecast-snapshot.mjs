import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; }
function hash(path) { return createHash("sha256").update(readFileSync(path)).digest("hex"); }
const id = arg("--id");
const capturedAt = arg("--captured-at");
const commitSha = arg("--commit-sha") ?? process.env.GITHUB_SHA ?? null;
if (!id || !capturedAt) throw new Error("snapshot requires --id and --captured-at");
if (Number.isNaN(Date.parse(capturedAt))) throw new Error("snapshot --captured-at must be an ISO date/time");
const historyPath = resolve(root, "metadata/forecast-snapshots.json");
const history = JSON.parse(readFileSync(historyPath, "utf8"));
if (history.snapshots.some((item) => item.id === id)) throw new Error(`snapshot ${id} already exists`);
const forecastPath = resolve(root, "model/data/processed/experimental_forecast_2026.json");
const readinessPath = resolve(root, "metadata/release-readiness.generated.json");
const forecast = JSON.parse(readFileSync(forecastPath, "utf8"));
const readiness = JSON.parse(readFileSync(readinessPath, "utf8"));
history.snapshots.push({
  id,
  capturedAt,
  commitSha,
  forecastAsOf: forecast.as_of,
  status: readiness.status,
  passedGates: Object.values(readiness.gates).filter((gate) => gate.passed).length,
  totalGates: Object.keys(readiness.gates).length,
  forecastSha256: hash(forecastPath),
  configSha256: forecast.assumptions.config_sha256,
  sourcesSha256: hash(resolve(root, "metadata/sources.json")),
  candidatesSha256: hash(resolve(root, "metadata/candidates-2026.json")),
});
history.snapshots.sort((a, b) => a.capturedAt.localeCompare(b.capturedAt));
writeFileSync(historyPath, `${JSON.stringify(history, null, 2)}\n`);
console.log(`Recorded immutable forecast snapshot ${id}.`);
