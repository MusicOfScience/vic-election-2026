import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

function parseCsv(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
    else if (ch === '"') quoted = !quoted;
    else if (ch === "," && !quoted) { row.push(cell); cell = ""; }
    else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [headers, ...data] = rows;
  return data.map((values) => Object.fromEntries(headers.map((header, i) => [header, values[i] ?? ""])));
}

export function proposedEstimateRows(record) {
  const mapping = [
    ["coalition", "LIB_NAT"],
    ["alp", "ALP"],
    ["oneNation", "ONP"],
    ["greens", "GRN"],
    ["independents", "IND"],
    ["otherParties", "OTH"],
  ];
  return mapping.flatMap(([key, partyId]) => record.primaryVote?.[key] == null ? [] : [{
    poll_id: record.proposedModelPollId,
    party_id: partyId,
    primary_pct: Number(record.primaryVote[key]),
    estimate_status: "reported",
    notes: "preview only; not written by promotion audit",
  }]);
}

export function auditPollPromotion(record, { modelEvents, acceptedPolls }) {
  const accepted = acceptedPolls.find((poll) => poll.evidenceId === record.id) ?? null;
  const estimateRows = proposedEstimateRows(record);
  const primaryTotal = estimateRows.reduce((sum, row) => sum + row.primary_pct, 0);
  const duplicateId = modelEvents.some((poll) => poll.poll_id === record.proposedModelPollId);
  const sourceTier = record.sourceTier ?? (record.captureMode === "manual-primary-source-capture" ? "primary_pollster" : "unclassified");
  const verification = String(record.verificationStatus ?? "");
  const secondaryReconciled = /primary-(?:reconciled|exception-approved)/i.test(verification);
  const awaitingPrimary = sourceTier === "reputable_secondary" ? !secondaryReconciled : verification.includes("awaiting-primary") || !record.pollPublicationDate;
  const blockers = [];
  if (!record.proposedModelPollId) blockers.push("canonical-poll-id-required");
  if (!accepted) blockers.push("human-evidence-acceptance-required");
  if (accepted && accepted.modelEligible !== true) blockers.push("explicit-model-eligibility-required");
  if (sourceTier === "reputable_secondary" && awaitingPrimary) blockers.push("primary-source-reconciliation-or-reviewed-exception-required");
  if (!record.pollPublicationDate) blockers.push("canonical-poll-publication-date-required");
  if (Math.abs(primaryTotal - 100) > 0.01) blockers.push("primary-vote-total-must-equal-100");
  if (duplicateId) blockers.push("canonical-poll-id-already-exists");

  return {
    evidenceId: record.id,
    pollster: record.pollster,
    proposedModelPollId: record.proposedModelPollId ?? null,
    sourceTier,
    evidenceStatus: record.status,
    acceptedEvidence: Boolean(accepted),
    modelEligibleDecision: accepted?.modelEligible === true,
    duplicateId,
    primaryVoteTotal: primaryTotal,
    canPromoteNow: blockers.length === 0,
    blockers,
    proposedChanges: {
      pollEvent: {
        poll_id: record.proposedModelPollId ?? null,
        pollster: record.pollster,
        commissioner: record.commissioner ?? "",
        fieldwork_start: record.fieldworkStart,
        fieldwork_end: record.fieldworkEnd,
        publication_date: record.pollPublicationDate ?? null,
        sample_size: record.sampleSize,
        effective_sample_size: record.effectiveSampleSize ?? null,
        method: record.method ?? null,
        geography: record.geography,
        source_tier: sourceTier,
        verification_status: accepted ? accepted.verificationStatus : (record.verificationStatus ?? "awaiting-human-review"),
        model_eligible: true,
        source_url: record.sourceUrl,
      },
      pollEstimateRows: estimateRows,
    },
  };
}

export function buildPromotionAudit({ records, modelEvents, acceptedPolls, asOf }) {
  const audits = records.filter((record) => record.kind === "poll").map((record) => auditPollPromotion(record, { modelEvents, acceptedPolls }));
  return {
    schemaVersion: 1,
    assessedAsOf: asOf,
    mode: "preview-only",
    automaticWriteEnabled: false,
    policy: "This report may describe proposed model rows but never writes model inputs. Evidence acceptance and model eligibility are separate explicit decisions.",
    summary: {
      stagedPolls: audits.length,
      promotableNow: audits.filter((audit) => audit.canPromoteNow).length,
      blocked: audits.filter((audit) => !audit.canPromoteNow).length,
    },
    audits,
  };
}

function main() {
  const asOf = arg("--as-of", new Date().toISOString().slice(0, 10));
  const output = resolve(root, arg("--output", "poll-promotion-audit.json"));
  const modelEvents = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
  const accepted = JSON.parse(readFileSync(resolve(root, "metadata/accepted-polls-2026.json"), "utf8"));
  const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));
  const primary = JSON.parse(readFileSync(resolve(root, "metadata/primary-source-evidence-2026.json"), "utf8"));
  const research = JSON.parse(readFileSync(resolve(root, "metadata/research-source-evidence-2026.json"), "utf8"));
  const report = buildPromotionAudit({ records: [...(manual.records ?? []), ...(primary.records ?? []), ...(research.records ?? [])], modelEvents, acceptedPolls: accepted.polls ?? [], asOf });
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Poll promotion audit: ${report.summary.stagedPolls} staged; ${report.summary.promotableNow} promotable; ${report.summary.blocked} blocked. No model files written.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
