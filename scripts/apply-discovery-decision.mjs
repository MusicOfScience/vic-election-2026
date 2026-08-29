import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

export function candidateIdentity(record) {
  return `${record.contest}|${record.name}`.trim().toLowerCase();
}

export function candidateFromDiscovery(record, reviewedAt, note = "") {
  const official = record.sourceAuthority === "VEC" && ["nominated", "withdrawn", "elected", "not-elected"].includes(record.officialStatus);
  return {
    name: record.name,
    contest: record.contest,
    party: record.party ?? null,
    status: official ? record.officialStatus : "endorsed",
    sourceUrl: record.sourceUrl,
    sourceAuthority: record.sourceAuthority ?? record.party ?? "primary-source",
    evidenceId: record.id,
    reviewedAt,
    ...(note ? { reviewNote: note } : {}),
  };
}

export function acceptedPollFromDiscovery(record, reviewedAt, note = "") {
  return {
    evidenceId: record.id,
    kind: record.kind,
    pollster: record.pollster,
    fieldworkStart: record.fieldworkStart,
    fieldworkEnd: record.fieldworkEnd,
    sampleSize: record.sampleSize,
    method: record.method ?? null,
    geography: record.geography,
    primaryVote: record.primaryVote ?? null,
    twoPartyPreferred: record.twoPartyPreferred ?? null,
    seatProjection: record.seatProjection ?? null,
    sourceUrl: record.sourceUrl,
    sourceId: record.sourceId,
    verificationStatus: "human-reviewed-source-evidence",
    modelEligible: false,
    reviewedAt,
    ...(note ? { reviewNote: note } : {}),
  };
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`);
}

function main() {
  const inputPath = resolve(root, arg("--input", "source-discovery-quarantine.json"));
  const id = arg("--id");
  const decision = arg("--decision");
  const reviewer = arg("--reviewer");
  const note = arg("--note", "");
  if (!id || !["approve", "reject"].includes(decision) || !reviewer) {
    throw new Error("usage: --id <record-id> --decision approve|reject --reviewer <name> [--note <text>] [--input <quarantine.json>]");
  }

  const quarantine = readJson(inputPath);
  const record = (quarantine.records ?? []).find((item) => item.id === id);
  if (!record) throw new Error(`discovery record not found: ${id}`);

  const decisionsPath = resolve(root, "metadata/discovery-review-decisions.json");
  const decisions = readJson(decisionsPath);
  if ((decisions.decisions ?? []).some((item) => item.evidenceId === id)) throw new Error(`record already reviewed: ${id}`);

  const reviewedAt = new Date().toISOString();
  if (decision === "approve" && record.kind === "candidate") {
    const candidatesPath = resolve(root, "metadata/candidates-2026.json");
    const registry = readJson(candidatesPath);
    const identity = candidateIdentity(record);
    if ((registry.candidates ?? []).some((item) => candidateIdentity(item) === identity)) throw new Error(`candidate already accepted: ${record.name} / ${record.contest}`);
    registry.candidates.push(candidateFromDiscovery(record, reviewedAt, note));
    writeJson(candidatesPath, registry);
  } else if (decision === "approve" && record.kind.startsWith("poll")) {
    const pollsPath = resolve(root, "metadata/accepted-polls-2026.json");
    const registry = readJson(pollsPath);
    if ((registry.polls ?? []).some((item) => item.evidenceId === id)) throw new Error(`poll evidence already accepted: ${id}`);
    registry.polls.push(acceptedPollFromDiscovery(record, reviewedAt, note));
    writeJson(pollsPath, registry);
  }

  decisions.decisions.push({
    evidenceId: id,
    recordHash: sha256(JSON.stringify(record)),
    kind: record.kind,
    decision,
    reviewer,
    reviewedAt,
    note,
    modelInputsChanged: false,
  });
  writeJson(decisionsPath, decisions);
  console.log(`${decision === "approve" ? "Approved" : "Rejected"} ${record.kind} ${id}; model inputs unchanged.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
