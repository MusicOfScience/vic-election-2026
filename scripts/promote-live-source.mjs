import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; }

function main() {
  const id = arg("--id");
  if (!id) throw new Error("promotion requires --id <adapter-id>");
  const reportPath = resolve(root, arg("--report") ?? "live-source-report.json");
  const statePath = resolve(root, arg("--state") ?? "metadata/live-source-state.json");
  if (!existsSync(reportPath)) throw new Error(`report not found: ${reportPath}`);
  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const observation = report.observations.find((item) => item.id === id);
  if (!observation) throw new Error(`adapter ${id} not present in report`);
  const valid = observation.validation?.httpOk && observation.validation?.markersPassed && observation.validation?.sizePassed;
  if (!valid || !observation.observedFingerprint) throw new Error(`adapter ${id} did not pass validation; refusing promotion`);
  const state = existsSync(statePath) ? JSON.parse(readFileSync(statePath, "utf8")) : { schemaVersion: 1, sources: [] };
  const sources = (state.sources ?? []).filter((item) => item.id !== id);
  sources.push({
    id,
    acceptedFingerprint: observation.observedFingerprint,
    acceptedAt: new Date().toISOString(),
    sourceCheckedAt: observation.checkedAt,
    url: observation.url,
  });
  sources.sort((a, b) => a.id.localeCompare(b.id));
  writeFileSync(statePath, `${JSON.stringify({ schemaVersion: 1, policy: "manual-review-required", sources }, null, 2)}\n`);
  console.log(`Promoted validated fingerprint for ${id}. Review and commit the state change through a pull request.`);
}

main();
