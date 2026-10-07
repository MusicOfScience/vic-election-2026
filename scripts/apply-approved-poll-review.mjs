import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { auditPollPromotion } from "./build-poll-promotion-audit.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const plannedWrites = new Map();
const writeJson = (path, value) => plannedWrites.set(resolve(root, path), `${JSON.stringify(value, null, 2)}\n`);
const hash = (value) => createHash("sha256").update(JSON.stringify(value)).digest("hex");

function parseCsv(text) {
  const rows = []; let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i += 1) { const ch = text[i]; if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i += 1; } else if (ch === '"') quoted = !quoted; else if (ch === "," && !quoted) { row.push(cell); cell = ""; } else if ((ch === "\n" || ch === "\r") && !quoted) { if (ch === "\r" && text[i + 1] === "\n") i += 1; row.push(cell); cell = ""; if (row.some((value) => value !== "")) rows.push(row); row = []; } else cell += ch; }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows; return { headers, rows: data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""]))) };
}
function csvCell(value) { const text = String(value ?? ""); return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text; }
function csv({ headers, rows }) { return `${headers.join(",")}\n${rows.map((row) => headers.map((header) => csvCell(row[header])).join(",")).join("\n")}\n`; }

const approval = readJson("metadata/poll-review-approval-2026.json");
const dossier = readJson("metadata/poll-review-dossier-2026.json");
const evidenceFiles = ["metadata/manual-source-evidence-2026.json", "metadata/primary-source-evidence-2026.json", "metadata/research-source-evidence-2026.json"];
const records = evidenceFiles.flatMap((path) => readJson(path).records ?? []);
const byId = new Map(records.map((record) => [record.id, record]));
const recommendationById = new Map(dossier.reviews.map((review) => [review.evidenceId, review]));
const priorAccepted = readJson("metadata/accepted-polls-2026.json");
const priorReviews = readJson("metadata/discovery-review-decisions.json");
const reviewDate = (id) => priorReviews.decisions.find((item) => item.evidenceId === id)?.reviewedAt ?? approval.approvedAt;

if (approval.evidenceDecisions.length !== dossier.reviews.length) throw new Error("approval must decide every dossier record");
if (new Set(approval.evidenceDecisions.map((item) => item.evidenceId)).size !== approval.evidenceDecisions.length) throw new Error("duplicate evidence decision");
for (const item of approval.evidenceDecisions) {
  const recommendation = recommendationById.get(item.evidenceId);
  if (!recommendation || !byId.has(item.evidenceId)) throw new Error(`unknown evidence decision: ${item.evidenceId}`);
  const expected = recommendation.evidenceRecommendation === "accept" ? "approve" : recommendation.evidenceRecommendation === "hold" ? "hold" : "defer";
  if (item.decision !== expected) throw new Error(`${item.evidenceId}: decision does not match approved recommendation`);
}

const acceptedPath = "metadata/accepted-polls-2026.json";
const accepted = readJson(acceptedPath);
accepted.polls = approval.evidenceDecisions.filter((item) => item.decision === "approve").map((item) => {
  const record = byId.get(item.evidenceId);
  const modelDecision = approval.modelEligibilityDecisions.find((decision) => decision.evidenceId === item.evidenceId);
  return { evidenceId: record.id, kind: record.kind, pollster: record.pollster, fieldworkStart: record.fieldworkStart,
    fieldworkEnd: record.fieldworkEnd, publicationDate: record.pollPublicationDate ?? null, sampleSize: record.sampleSize,
    method: record.method ?? null, geography: record.geography, primaryVote: record.primaryVote ?? null,
    twoPartyPreferred: record.twoPartyPreferred ?? null, sourceUrl: record.sourceUrl, sourceId: record.sourceId,
    sourceTier: record.sourceTier ?? null, verificationStatus: "human-reviewed-source-evidence",
    modelEligible: modelDecision?.decision === "eligible", reviewedAt: priorAccepted.polls.find((poll) => poll.evidenceId === record.id)?.reviewedAt ?? approval.approvedAt, reviewerRole: approval.reviewerRole,
    ...(record.workbookPath ? { sourceFamily: record.sourceFamily, workbookPath: record.workbookPath,
      workbookSha256: record.workbookSha256, extractor: record.extractor, primaryReleaseDate: record.primaryReleaseDate,
      primaryVoteRounded: record.primaryVoteRounded, primaryVoteUnweightedBase: record.primaryVoteUnweightedBase,
      twoPartyPreferredUnweightedBase: record.twoPartyPreferredUnweightedBase, sampleOverlapAssessment: record.sampleOverlapAssessment } : {}) };
});
writeJson(acceptedPath, accepted);

writeJson("metadata/discovery-review-decisions.json", { schemaVersion: 1, policy: "explicit-human-review-required",
  decisions: [...approval.evidenceDecisions.map((item) => { const record = byId.get(item.evidenceId); return {
    evidenceId: item.evidenceId, recordHash: hash(record), kind: record.kind, decision: item.decision,
    reviewer: approval.reviewerRole, reviewedAt: reviewDate(item.evidenceId), note: item.reason ?? recommendationById.get(item.evidenceId).rationale,
    modelInputsChanged: false }; }), ...priorReviews.decisions.filter((item) => item.kind !== "poll")] });
writeJson("metadata/poll-model-eligibility-decisions.json", { schemaVersion: 1,
  policy: "Model eligibility is decided separately from evidence acceptance. Eligible records enter the canonical registry only through an explicit canonical action.",
  decidedAt: approval.approvedAt, reviewerRole: approval.reviewerRole, decisions: approval.modelEligibilityDecisions });

const eventsPath = resolve(root, "model/data/processed/poll_events_seed.csv");
const estimatesPath = resolve(root, "model/data/processed/poll_estimates_seed.csv");
const events = parseCsv(readFileSync(eventsPath, "utf8"));
const estimates = parseCsv(readFileSync(estimatesPath, "utf8"));
const partyMap = { alp: "ALP", coalition: "LIB_NAT", oneNation: "ONP", greens: "GRN", otherParties: "OTH" };

for (const decision of approval.modelEligibilityDecisions.filter((item) => item.decision === "eligible")) {
  const record = byId.get(decision.evidenceId);
  if (!record || !approval.evidenceDecisions.some((item) => item.evidenceId === decision.evidenceId && item.decision === "approve")) throw new Error(`${decision.evidenceId}: evidence acceptance required`);
  const existing = events.rows.find((row) => row.poll_id === decision.pollId);
  if (existing && decision.canonicalAction === "repair-existing" && existing.publication_date === record.pollPublicationDate && Object.entries(partyMap).every(([key, partyId]) => {
    const rows = estimates.rows.filter((row) => row.poll_id === decision.pollId && row.party_id === partyId);
    return rows.length === 1 && Number(rows[0].primary_pct) === record.primaryVote[key];
  })) continue;
  if (existing && decision.canonicalAction === "add") {
    if (existing.source_url !== record.sourceUrl || existing.model_eligible !== "True") throw new Error(`${decision.pollId}: existing poll conflicts with admission`);
    for (const [key, partyId] of Object.entries(partyMap)) {
      const rows = estimates.rows.filter((row) => row.poll_id === decision.pollId && row.party_id === partyId);
      if (rows.length !== 1 || Number(rows[0].primary_pct) !== record.primaryVote[key]) throw new Error(`${decision.pollId}: existing estimates conflict with admission`);
    }
    continue; // An add decision can never overwrite an existing observation.
  }
  if (!existing) {
    const audit = auditPollPromotion(record, { modelEvents: events.rows, acceptedPolls: accepted.polls });
    if (!audit.canPromoteNow) throw new Error(`${decision.pollId}: ${audit.blockers.join(", ")}`);
    if (!record.method || !record.sampleSize || !record.fieldworkStart || !record.fieldworkEnd) throw new Error(`${decision.pollId}: methodology fields required`);
    if (record.workbookPath && createHash("sha256").update(readFileSync(resolve(root, record.workbookPath))).digest("hex") !== record.workbookSha256) throw new Error(`${decision.pollId}: workbook fingerprint mismatch`);
  }
  const event = existing ?? Object.fromEntries(events.headers.map((header) => [header, ""]));
  Object.assign(event, { poll_id: decision.pollId, pollster: record.pollster, commissioner: record.commissioner ?? "",
    fieldwork_start: record.fieldworkStart, fieldwork_end: record.fieldworkEnd, publication_date: record.pollPublicationDate,
    sample_size: record.sampleSize, effective_sample_size: record.effectiveSampleSize ?? "", method: record.method,
    geography: record.geography, population: "Victorian voters", vote_base: "decided_reallocated",
    undecided_treatment: "leaners included; unresolved undecideds excluded", one_nation_prompted: "True",
    questionnaire_regime: "explicit_multi_party", leader_regime: record.fieldworkEnd < "2026-06-01" ? "Allan-Wilson" : "Carroll-Wilson",
    source_tier: "primary_publisher", verification_status: "verified", model_eligible: "True", source_url: record.sourceUrl,
    notes: `Human-reviewed primary workbook; SHA-256 ${record.workbookSha256}. Exact five-way values retained.`,
    sample_family: record.sourceFamily ?? "", source_document_title: `Freshwater Strategy ${decision.pollId.slice(-7)} Victorian polling workbook` });
  if (record.workbookPath && record.primaryVoteUnweightedBase) event.notes += ` Source family ${record.sourceFamily}; full N=${record.sampleSize}; primary valid base N=${record.primaryVoteUnweightedBase}; TPP base N=${record.twoPartyPreferredUnweightedBase}; effective N undisclosed. Data tables released ${record.primaryReleaseDate}. TPP ALP ${record.twoPartyPreferred.alp}, Coalition ${record.twoPartyPreferred.coalition}.`;
  if (!existing) events.rows.push(event);
  estimates.rows = estimates.rows.filter((row) => row.poll_id !== decision.pollId);
  for (const [key, partyId] of Object.entries(partyMap)) estimates.rows.push({ poll_id: decision.pollId, party_id: partyId,
    primary_pct: record.primaryVote[key], estimate_status: "reported",
    notes: `Primary workbook SHA-256 ${record.workbookSha256}` });
}
events.rows.sort((a, b) => a.fieldwork_end.localeCompare(b.fieldwork_end) || a.poll_id.localeCompare(b.poll_id));
const eventOrder = new Map(events.rows.map((row, index) => [row.poll_id, index]));
estimates.rows.sort((a, b) => eventOrder.get(a.poll_id) - eventOrder.get(b.poll_id));
plannedWrites.set(eventsPath, csv(events));
plannedWrites.set(estimatesPath, csv(estimates));

const coverage = readJson("metadata/poll-coverage-ledger-2026.json");
const freshwater = coverage.sourceFamilies.find((family) => family.id === "freshwater");
Object.assign(freshwater, { coverageClass: "canonical-current",
  canonicalModelEligiblePollIds: events.rows.filter((event) => event.pollster === "Freshwater Strategy" && event.model_eligible === "True").map((event) => event.poll_id),
  nextAction: "Continue live monitoring; owner-approved comparable Freshwater waves are canonical, with one pollster family retained." });
delete freshwater.registeredButNotEligiblePollIds; delete freshwater.stagedEvidence; delete freshwater.actionableGaps;
writeJson("metadata/poll-coverage-ledger-2026.json", coverage);

for (const [path, content] of plannedWrites) {
  if (process.argv.includes("--check")) {
    if (readFileSync(path, "utf8") !== content) throw new Error(`approved poll review stale: ${path}`);
  } else writeFileSync(path, content);
}
console.log(`${process.argv.includes("--check") ? "Verified" : "Applied"} ${accepted.polls.length} accepted evidence records and ${approval.modelEligibilityDecisions.filter((item) => item.decision === "eligible").length} separate model-eligibility decisions.`);
