import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

const CYCLE_REQUIREMENTS = {
  vic_la_2018: {
    cutoff: "2018-11-23",
    baselinePath: "model/data/processed/vec_2014_2018_same_boundary_tpp_swing.csv",
    baselineReport: "model/data/processed/vec_2014_2018_same_boundary_tpp_swing_report.json",
  },
};

export function buildHistoricalLocalInputs(cycleId, projectRoot = root) {
  const requirement = CYCLE_REQUIREMENTS[cycleId];
  if (!requirement) throw new Error(`no historical local-input contract for ${cycleId}`);
  const baselinePath = resolve(projectRoot, requirement.baselinePath);
  const reportPath = resolve(projectRoot, requirement.baselineReport);
  if (!existsSync(baselinePath)) {
    return {
      cycleId, status: "blocked", cutoff: requirement.cutoff,
      requiredArtefact: requirement.baselinePath,
      requiredReport: requirement.baselineReport,
      reason: "boundary-aligned pre-cycle local pattern artefact is absent; target-cycle outcomes cannot substitute it",
      sourceOutcomeUse: "forbidden",
    };
  }
  if (!existsSync(reportPath)) throw new Error(`local-input report missing beside ${requirement.baselinePath}`);
  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  if (report.cycleId && report.cycleId !== cycleId) throw new Error(`local-input report cycle mismatch for ${cycleId}`);
  return { cycleId, status: "pass", cutoff: requirement.cutoff, inputPath: requirement.baselinePath, reportPath: requirement.baselineReport, sourceOutcomeUse: "pre-cutoff-derived-only" };
}

if (process.argv[1]?.endsWith("build-historical-local-inputs.mjs")) console.log(JSON.stringify(buildHistoricalLocalInputs(process.argv[2] ?? "vic_la_2018"), null, 2));
