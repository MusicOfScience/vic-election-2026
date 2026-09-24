import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

const CYCLE_REQUIREMENTS = {
  vic_la_2018: {
    cutoff: "2018-11-23",
    baselinePath: "model/data/processed/vec_2014_assembly_family_primaries.csv",
    forbiddenPaths: ["model/data/processed/vec_2014_2018_same_boundary_tpp_swing.csv"],
    baselineDescription: "2014 Assembly family primaries; prior-election local baseline available before the 2018 cutoff",
  },
};

export function buildHistoricalLocalInputs(cycleId, projectRoot = root) {
  const requirement = CYCLE_REQUIREMENTS[cycleId];
  if (!requirement) throw new Error(`no historical local-input contract for ${cycleId}`);
  const baselinePath = resolve(projectRoot, requirement.baselinePath);
  const forbidden = requirement.forbiddenPaths.find((path) => existsSync(resolve(projectRoot, path)));
  if (forbidden) throw new Error(`forbidden target-outcome-derived local input present: ${forbidden}`);
  if (!existsSync(baselinePath)) {
    return {
      cycleId, status: "blocked", cutoff: requirement.cutoff,
      requiredArtefact: requirement.baselinePath,
      reason: "pre-cutoff prior-election local baseline is absent; target-cycle outcomes cannot substitute it",
      sourceOutcomeUse: "forbidden",
    };
  }
  const header = readFileSync(baselinePath, "utf8").split(/\r?\n/, 1)[0];
  if (/2018|swing|share_2018/i.test(header)) throw new Error(`target-cycle outcome field in local baseline: ${requirement.baselinePath}`);
  return {
    cycleId, status: "pass", cutoff: requirement.cutoff, inputPath: requirement.baselinePath,
    inputRole: "prior-election-local-baseline", description: requirement.baselineDescription,
    sourceOutcomeUse: "pre-cutoff-derived-only",
    dependencyAudit: { predictionInputs: [requirement.baselinePath], scoringOnly: ["model/data/processed/vec_2014_2018_same_boundary_tpp_swing.csv"], forbiddenInPrediction: true },
  };
}

if (process.argv[1]?.endsWith("build-historical-local-inputs.mjs")) console.log(JSON.stringify(buildHistoricalLocalInputs(process.argv[2] ?? "vic_la_2018"), null, 2));
