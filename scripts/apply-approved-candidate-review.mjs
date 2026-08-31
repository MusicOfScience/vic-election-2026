import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const json = (value) => `${JSON.stringify(value, null, 2)}\n`;
const hash = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex");
const identity = (record) => `${record.contest}|${record.name}`.trim().toLowerCase();

function buildExpected() {
  const approval = readJson("metadata/candidate-review-approval-2026.json");
  const dossier = readJson("metadata/candidate-review-dossier-2026.json");
  const provisional = readJson("metadata/provisional-candidate-evidence-2026.json");
  const registry = readJson("metadata/candidates-2026.json");
  const reviewLog = readJson("metadata/discovery-review-decisions.json");

  if (approval.reviewerRole !== "project-owner") throw new Error("candidate approval: reviewerRole must be project-owner");
  if (approval.evidenceAsOf !== provisional.evidenceAsOf || dossier.generatedFromEvidenceAsOf !== provisional.evidenceAsOf) {
    throw new Error("candidate approval: evidence version does not match the reviewed dossier");
  }
  if (!Number.isFinite(Date.parse(approval.approvedAt))) throw new Error("candidate approval: approvedAt must be an ISO timestamp");

  const familyByAuthority = new Map(dossier.families.map((family) => [family.authority, family]));
  const decisions = approval.familyDecisions ?? [];
  if (decisions.length !== dossier.families.length || new Set(decisions.map((item) => item.authority)).size !== decisions.length) {
    throw new Error("candidate approval: every dossier family must have exactly one decision");
  }
  for (const decision of decisions) {
    const family = familyByAuthority.get(decision.authority);
    if (!family) throw new Error(`candidate approval: unknown source family ${decision.authority}`);
    if (family.evidenceRecommendation !== `accept-as-${decision.acceptedStatus}-evidence` || decision.decision !== "approve") {
      throw new Error(`candidate approval: ${decision.authority} does not match the dossier recommendation`);
    }
    if (!["announced", "endorsed"].includes(decision.acceptedStatus) || decision.officialNomination !== false || decision.forecastUse !== "excluded") {
      throw new Error(`candidate approval: ${decision.authority} breaches the provisional-evidence boundary`);
    }
  }

  const approvedAuthorities = new Set(decisions.map((item) => item.authority));
  const decisionByAuthority = new Map(decisions.map((item) => [item.authority, item]));
  const approvedRecords = provisional.records.filter((record) => approvedAuthorities.has(record.sourceAuthority));
  if (approvedRecords.length !== approval.requiredAcceptedRecords || approvedRecords.length !== dossier.summary.recordsRecommendedForAcceptance) {
    throw new Error("candidate approval: accepted record count does not match the dossier");
  }
  if (approvedRecords.some((record) => record.status !== "quarantined-awaiting-review" || record.candidateStatus !== decisionByAuthority.get(record.sourceAuthority)?.acceptedStatus || record.automaticPromotion !== false)) {
    throw new Error("candidate approval: only status-matched, quarantined, non-promotable evidence may be accepted");
  }

  const approvedIds = new Set(approvedRecords.map((record) => record.id));
  if (approvedIds.size !== approvedRecords.length) throw new Error("candidate approval: duplicate evidence id");
  const retainedCandidates = (registry.candidates ?? []).filter((candidate) => !approvedIds.has(candidate.evidenceId));
  const existingCandidateById = new Map((registry.candidates ?? []).map((candidate) => [candidate.evidenceId, candidate]));
  const seenIdentities = new Set(retainedCandidates.map(identity));
  const acceptedCandidates = approvedRecords.map((record) => {
    const key = identity(record);
    if (seenIdentities.has(key)) throw new Error(`candidate approval: duplicate accepted identity ${record.name} / ${record.contest}`);
    seenIdentities.add(key);
    const family = familyByAuthority.get(record.sourceAuthority);
    const existing = existingCandidateById.get(record.id);
    if (existing) {
      const unchanged = existing.name === record.name
        && existing.contest === record.contest
        && existing.party === record.party
        && existing.status === record.candidateStatus
        && existing.sourceUrl === record.sourceUrl
        && existing.sourceAuthority === record.sourceAuthority
        && existing.sourceId === record.sourceId
        && existing.evidenceHash === record.dataHash
        && existing.forecastUse === "excluded"
        && existing.officialNomination === false;
      if (!unchanged) throw new Error(`candidate approval: accepted record drift for ${record.name} / ${record.contest}`);
      return existing;
    }
    return {
      name: record.name,
      contest: record.contest,
      party: record.party,
      status: record.candidateStatus,
      sourceUrl: record.sourceUrl,
      sourceAuthority: record.sourceAuthority,
      sourceId: record.sourceId,
      evidenceId: record.id,
      evidenceHash: record.dataHash,
      reviewedAt: approval.approvedAt,
      reviewerRole: approval.reviewerRole,
      reviewNote: family.rationale,
      forecastUse: "excluded",
      officialNomination: false,
    };
  });
  const candidateSort = (a, b) => a.contest.localeCompare(b.contest) || String(a.party).localeCompare(String(b.party)) || a.name.localeCompare(b.name);
  const expectedRegistry = { ...registry, candidates: [...retainedCandidates, ...acceptedCandidates].sort(candidateSort) };

  const retainedDecisions = (reviewLog.decisions ?? []).filter((item) => !approvedIds.has(item.evidenceId));
  const existingDecisionById = new Map((reviewLog.decisions ?? []).filter((item) => item.kind === "candidate").map((item) => [item.evidenceId, item]));
  const acceptedById = new Map(acceptedCandidates.map((candidate) => [candidate.evidenceId, candidate]));
  const candidateDecisions = approvedRecords
    .map((record) => {
      const recordHash = hash(record);
      const existing = existingDecisionById.get(record.id);
      if (existing) {
        if (existing.recordHash !== recordHash || existing.decision !== "approve" || existing.modelInputsChanged !== false) {
          throw new Error(`candidate approval: review audit drift for ${record.name} / ${record.contest}`);
        }
        return existing;
      }
      return {
        evidenceId: record.id,
        recordHash,
        kind: "candidate",
        decision: "approve",
        reviewer: approval.reviewerRole,
        reviewedAt: approval.approvedAt,
        note: acceptedById.get(record.id).reviewNote,
        modelInputsChanged: false,
      };
    })
    .sort((a, b) => {
      const left = acceptedById.get(a.evidenceId);
      const right = acceptedById.get(b.evidenceId);
      return candidateSort(left, right);
    });
  const expectedReviewLog = { ...reviewLog, decisions: [...retainedDecisions, ...candidateDecisions] };

  return { expectedRegistry, expectedReviewLog, approvedRecords };
}

function main() {
  const checkOnly = process.argv.includes("--check");
  const { expectedRegistry, expectedReviewLog, approvedRecords } = buildExpected();
  const candidatesPath = resolve(root, "metadata/candidates-2026.json");
  const reviewLogPath = resolve(root, "metadata/discovery-review-decisions.json");
  if (checkOnly) {
    if (readFileSync(candidatesPath, "utf8") !== json(expectedRegistry)) throw new Error("candidate approval: accepted registry is stale");
    if (readFileSync(reviewLogPath, "utf8") !== json(expectedReviewLog)) throw new Error("candidate approval: review log is stale");
  } else {
    writeFileSync(candidatesPath, json(expectedRegistry));
    writeFileSync(reviewLogPath, json(expectedReviewLog));
  }
  console.log(`Candidate approval: ${approvedRecords.length} provisional records accepted; forecast use excluded; VEC nomination status unchanged.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
