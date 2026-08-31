import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { classifyContest, loadContestUniverse } from "./candidate-contests.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outputPath = resolve(root, "metadata/candidate-review-dossier-2026.json");

const rationaleByAuthority = {
  "Australian Greens Victoria": "The official Victorian Greens candidate directory supplies named electorate and Council candidates with direct profile links.",
  "Liberal Victoria": "Liberal Victoria's public structured roster explicitly marks candidate records and supplies electorate and profile fields.",
  "One Nation Victoria": "The official Victorian One Nation candidate page publishes named candidates and their contests; Council region aliases are normalised separately.",
  "The Nationals Victoria": "The official Nationals Victoria team page explicitly labels endorsed candidates and electorates, without treating sitting members as new candidates.",
  "Victorian Labor": "Victorian Labor's official paginated roster separates candidates from the existing state team and links each named candidate to an electorate profile.",
};

function readJson(path) {
  return JSON.parse(readFileSync(resolve(root, path), "utf8"));
}

function buildDossier() {
  const provisional = readJson("metadata/provisional-candidate-evidence-2026.json");
  const adapters = readJson("metadata/live-source-adapters.json");
  const universe = loadContestUniverse(root);
  const adapterById = new Map(adapters.adapters.map((adapter) => [adapter.id, adapter]));
  const classified = provisional.records.map((record) => ({ record, contest: classifyContest(record.contest, universe) }));
  const assemblyContests = new Set(classified.filter((item) => item.contest?.chamber === "assembly").map((item) => item.contest.canonicalContest));
  const councilRegions = new Set(classified.filter((item) => item.contest?.chamber === "council").map((item) => item.contest.canonicalContest));
  const unclassified = classified.filter((item) => !item.contest).map((item) => item.record.contest);
  const identities = provisional.records.map((record) => `${record.contest}|${record.name}`.toLowerCase());
  const duplicateIdentities = identities.filter((identity, index) => identities.indexOf(identity) !== index);
  const sourceAuthorities = [...new Set(provisional.records.map((record) => record.sourceAuthority))].sort();
  const families = sourceAuthorities.map((authority) => {
    const records = classified.filter((item) => item.record.sourceAuthority === authority);
    const sourceIds = [...new Set(records.map((item) => item.record.sourceId))];
    const familyAssembly = new Set(records.filter((item) => item.contest?.chamber === "assembly").map((item) => item.contest.canonicalContest));
    const familyCouncil = new Set(records.filter((item) => item.contest?.chamber === "council").map((item) => item.contest.canonicalContest));
    const invalidRecords = records.filter((item) => item.record.status !== "quarantined-awaiting-review" || item.record.candidateStatus !== "endorsed" || item.record.automaticPromotion !== false || !item.contest || !String(item.record.sourceUrl).startsWith("https://"));
    const sourceUrls = sourceIds.map((sourceId) => adapterById.get(sourceId)?.url).filter(Boolean);
    return {
      authority,
      sourceIds,
      sourceUrls,
      records: records.length,
      assemblyContests: familyAssembly.size,
      councilRegions: familyCouncil.size,
      evidenceRecommendation: invalidRecords.length === 0 ? "accept-as-endorsed-evidence" : "hold-for-record-review",
      rationale: rationaleByAuthority[authority] ?? "The cited official party source provides structured candidate evidence.",
      requiredChecks: [
        "Accept only as party-endorsed evidence; do not label the record an official nomination.",
        "Preserve the cited source URL, evidence fingerprint and review date.",
        "Reconcile replacements, withdrawals and official nominations against the VEC when published.",
      ],
    };
  });
  const missingAssemblyContests = [...universe.assembly.values()].filter((contest) => !assemblyContests.has(contest));
  return {
    schemaVersion: 1,
    generatedFromEvidenceAsOf: provisional.evidenceAsOf,
    status: "recommendations-awaiting-human-decision",
    policy: "Evidence acceptance is a separate human decision from candidate-model use and from official VEC nomination status.",
    summary: {
      stagedRecords: provisional.records.length,
      sourceFamilies: families.length,
      recommendEvidenceAcceptance: families.filter((family) => family.evidenceRecommendation === "accept-as-endorsed-evidence").length,
      recordsRecommendedForAcceptance: families.filter((family) => family.evidenceRecommendation === "accept-as-endorsed-evidence").reduce((sum, family) => sum + family.records, 0),
      assemblyContests: assemblyContests.size,
      assemblyDistrictsTotal: universe.assembly.size,
      missingAssemblyContests: missingAssemblyContests.length,
      councilRegions: councilRegions.size,
      councilRegionsTotal: universe.council.size,
      duplicateIdentities: duplicateIdentities.length,
      unclassifiedContests: unclassified.length,
    },
    missingAssemblyContests,
    knownScopeGaps: [
      "No accepted 2026 candidate evidence yet exists in the canonical registry.",
      "Six Assembly districts have no discovered party-endorsed candidate record in the current five-source collection.",
      "Credible independents, teals, retirements, defections and candidate replacements require a separately sourced contest-intelligence layer.",
      "Only VEC evidence may confer nominated, withdrawn or result status after nominations open in November.",
    ],
    families,
  };
}

function main() {
  const checkOnly = process.argv.includes("--check");
  const dossier = buildDossier();
  const json = `${JSON.stringify(dossier, null, 2)}\n`;
  if (checkOnly) {
    if (readFileSync(outputPath, "utf8") !== json) throw new Error("candidate review dossier: generated output is stale");
  } else {
    writeFileSync(outputPath, json);
  }
  console.log(`Candidate review dossier: ${dossier.summary.stagedRecords} records; ${dossier.summary.assemblyContests}/88 Assembly districts; ${dossier.summary.missingAssemblyContests} gaps.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();

