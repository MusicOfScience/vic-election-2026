import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const readJson = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const writeJson = (path, value) => writeFileSync(resolve(root, path), `${JSON.stringify(value, null, 2)}\n`);
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

if (approval.evidenceDecisions.length !== dossier.reviews.length) throw new Error("approval must decide every dossier record");
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
    modelEligible: modelDecision?.decision === "eligible", reviewedAt: approval.approvedAt, reviewerRole: approval.reviewerRole };
});
writeJson(acceptedPath, accepted);

writeJson("metadata/discovery-review-decisions.json", { schemaVersion: 1, policy: "explicit-human-review-required",
  decisions: approval.evidenceDecisions.map((item) => { const record = byId.get(item.evidenceId); return {
    evidenceId: item.evidenceId, recordHash: hash(record), kind: record.kind, decision: item.decision,
    reviewer: approval.reviewerRole, reviewedAt: approval.approvedAt, note: recommendationById.get(item.evidenceId).rationale,
    modelInputsChanged: false }; }) });
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
  const existing = events.rows.find((row) => row.poll_id === decision.pollId);
  const event = existing ?? Object.fromEntries(events.headers.map((header) => [header, ""]));
  Object.assign(event, { poll_id: decision.pollId, pollster: record.pollster, commissioner: record.commissioner ?? "",
    fieldwork_start: record.fieldworkStart, fieldwork_end: record.fieldworkEnd, publication_date: record.pollPublicationDate,
    sample_size: record.sampleSize, effective_sample_size: record.effectiveSampleSize ?? "", method: record.method,
    geography: record.geography, population: "Victorian voters", vote_base: "decided_reallocated",
    undecided_treatment: "leaners included; unresolved undecideds excluded", one_nation_prompted: "True",
    questionnaire_regime: "explicit_multi_party", leader_regime: record.fieldworkEnd < "2026-06-01" ? "Allan-Wilson" : "Carroll-Wilson",
    source_tier: "primary_publisher", verification_status: "verified", model_eligible: "True", source_url: record.sourceUrl,
    notes: `Human-reviewed primary workbook; SHA-256 ${record.workbookSha256}. Exact five-way values retained.`,
    sample_family: "", source_document_title: `Freshwater Strategy ${decision.pollId.slice(-7)} Victorian polling workbook` });
  if (!existing) events.rows.push(event);
  estimates.rows = estimates.rows.filter((row) => row.poll_id !== decision.pollId);
  for (const [key, partyId] of Object.entries(partyMap)) estimates.rows.push({ poll_id: decision.pollId, party_id: partyId,
    primary_pct: record.primaryVote[key], estimate_status: "reported",
    notes: `Primary workbook SHA-256 ${record.workbookSha256}` });
}
events.rows.sort((a, b) => a.fieldwork_end.localeCompare(b.fieldwork_end) || a.poll_id.localeCompare(b.poll_id));
const eventOrder = new Map(events.rows.map((row, index) => [row.poll_id, index]));
estimates.rows.sort((a, b) => eventOrder.get(a.poll_id) - eventOrder.get(b.poll_id));
writeFileSync(eventsPath, csv(events));
writeFileSync(estimatesPath, csv(estimates));

const coverage = readJson("metadata/poll-coverage-ledger-2026.json");
const freshwater = coverage.sourceFamilies.find((family) => family.id === "freshwater");
Object.assign(freshwater, { coverageClass: "canonical-current",
  canonicalModelEligiblePollIds: ["freshwater_2026-02", "freshwater_2026-03", "freshwater_2026-06", "freshwater_2026-08"],
  nextAction: "Continue live monitoring; primary-workbook evidence is human-reviewed and the four current comparable waves are canonical." });
delete freshwater.registeredButNotEligiblePollIds; delete freshwater.stagedEvidence; delete freshwater.actionableGaps;
writeJson("metadata/poll-coverage-ledger-2026.json", coverage);

console.log(`Applied ${accepted.polls.length} accepted evidence records and ${approval.modelEligibilityDecisions.filter((item) => item.decision === "eligible").length} separate model-eligibility decisions.`);
