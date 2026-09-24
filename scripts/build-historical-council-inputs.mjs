import { existsSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

export function buildHistoricalCouncilInputs(cycleId, projectRoot = root) {
  const cutoff = { vic_la_2018: "2018-11-23" }[cycleId];
  if (!cutoff) throw new Error(`no historical Council-input contract for ${cycleId}`);
  const modernPoll = "model/data/processed/upper_house_region_poll_2026-08.csv";
  return {
    cycleId,
    status: "blocked",
    cutoff,
    requiredArtefact: "pre-cutoff regional poll or governed broad regional prior",
    rejectedModernArtefact: modernPoll,
    modernArtefactPresent: existsSync(resolve(projectRoot, modernPoll)),
    reason: "the available regional poll is a 2026 input after the frozen cutoff; no historical pre-cutoff regional forecast input is present",
    outcomeCountSequences: "scoring-only",
  };
}

if (process.argv[1]?.endsWith("build-historical-council-inputs.mjs")) console.log(JSON.stringify(buildHistoricalCouncilInputs(process.argv[2] ?? "vic_la_2018"), null, 2));
