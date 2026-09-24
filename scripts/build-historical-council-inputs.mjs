import { existsSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);

export function buildHistoricalCouncilInputs(cycleId, projectRoot = root) {
  const contracts = {
    vic_la_2014: { cutoff: "2014-11-28", priorCouncil: "model/data/validation/historical-replay-2014-council-prior.csv" },
    vic_la_2018: { cutoff: "2018-11-23", priorCouncil: "model/data/processed/vec_2014_council_candidate_primaries.csv" },
  };
  const contract = contracts[cycleId];
  const cutoff = contract?.cutoff;
  if (!cutoff) throw new Error(`no historical Council-input contract for ${cycleId}`);
  const modernPoll = "model/data/processed/upper_house_region_poll_2026-08.csv";
  const priorCouncil = contract.priorCouncil;
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
    reason: existsSync(resolve(projectRoot, priorCouncil))
      ? (cycleId === "vic_la_2014" ? "dated pre-election new-boundary Council prior supplies all eight target regions; no target-cycle regional poll is fabricated" : "2014 Council regional first-preference structure supplies a governed broad prior; no target-cycle regional poll is fabricated")
      : "prior-election Council regional structure is absent",
    outcomeCountSequences: "scoring-only",
    predictionInputs: existsSync(resolve(projectRoot, priorCouncil)) ? [priorCouncil] : [],
  };
}

if (process.argv[1]?.endsWith("build-historical-council-inputs.mjs")) console.log(JSON.stringify(buildHistoricalCouncilInputs(process.argv[2] ?? "vic_la_2018"), null, 2));
