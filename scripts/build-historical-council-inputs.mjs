import { existsSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

export function buildHistoricalCouncilInputs(cycleId, projectRoot = root) {
  const cutoff = { vic_la_2018: "2018-11-23" }[cycleId];
  if (!cutoff) throw new Error(`no historical Council-input contract for ${cycleId}`);
  const modernPoll = "model/data/processed/upper_house_region_poll_2026-08.csv";
  const priorCouncil = "model/data/processed/vec_2014_council_candidate_primaries.csv";
  return {
    cycleId,
    status: existsSync(resolve(projectRoot, priorCouncil)) ? "pass-with-broad-fallback" : "blocked",
    cutoff,
    requiredArtefact: priorCouncil,
    regionalPollPath: null,
    regionalPollContribution: 0,
    uncertaintyRule: "fixed-broadening-when-regional-poll-absent",
    rejectedModernArtefact: modernPoll,
    modernArtefactPresent: existsSync(resolve(projectRoot, modernPoll)),
    reason: existsSync(resolve(projectRoot, priorCouncil)) ? "2014 Council regional first-preference structure supplies a governed broad prior; no target-cycle regional poll is fabricated" : "prior-election Council regional structure is absent",
    outcomeCountSequences: "scoring-only",
    predictionInputs: existsSync(resolve(projectRoot, priorCouncil)) ? [priorCouncil] : [],
  };
}

if (process.argv[1]?.endsWith("build-historical-council-inputs.mjs")) console.log(JSON.stringify(buildHistoricalCouncilInputs(process.argv[2] ?? "vic_la_2018"), null, 2));
