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

function latest(records, dateKey) {
  return [...records]
    .filter((record) => record?.[dateKey])
    .sort((a, b) => String(b[dateKey]).localeCompare(String(a[dateKey])))[0] ?? null;
}

export function buildEvidenceFreshness({ modelPolls, acceptedPolls, stagedPolls, asOf }) {
  const modelEligible = modelPolls.filter((poll) => String(poll.model_eligible).toLowerCase() === "true");
  const latestModel = latest(modelEligible, "publication_date");
  const latestAccepted = latest(acceptedPolls, "publicationDate") ?? latest(acceptedPolls, "fieldworkEnd");
  const latestStaged = latest(stagedPolls, "publicationDate") ?? latest(stagedPolls, "fieldworkEnd");
  const modelDate = latestModel?.publication_date ?? null;
  const acceptedDate = latestAccepted?.publicationDate ?? latestAccepted?.fieldworkEnd ?? null;
  const stagedDate = latestStaged?.publicationDate ?? latestStaged?.fieldworkEnd ?? null;
  const newestEvidenceDate = [acceptedDate, stagedDate].filter(Boolean).sort().at(-1) ?? null;

  return {
    schemaVersion: 1,
    assessedAsOf: asOf,
    policy: "Evidence freshness is informational. Only model-eligible evidence can satisfy the forecast freshness gate.",
    modelInput: modelDate ? {
      latestPublicationDate: modelDate,
      pollId: latestModel.poll_id,
      pollster: latestModel.pollster,
      status: "model-eligible",
    } : null,
    acceptedEvidence: latestAccepted ? {
      latestPublicationDate: acceptedDate,
      pollster: latestAccepted.pollster,
      status: "human-reviewed-not-necessarily-model-eligible",
    } : null,
    stagedEvidence: latestStaged ? {
      latestPublicationDate: stagedDate,
      pollster: latestStaged.pollster,
      evidenceId: latestStaged.id,
      status: latestStaged.status,
      sourceTier: latestStaged.sourceTier ?? "primary-or-manual-capture",
      verificationStatus: latestStaged.verificationStatus ?? "awaiting-review",
    } : null,
    newestEvidenceDate,
    newerEvidenceAwaitingReview: Boolean(stagedDate && (!modelDate || stagedDate > modelDate)),
    modelFreshnessUnchangedByStagedEvidence: true,
  };
}

function main() {
  const asOf = arg("--as-of", new Date().toISOString().slice(0, 10));
  const output = resolve(root, arg("--output", "evidence-freshness-report.json"));
  const modelPolls = parseCsv(readFileSync(resolve(root, "model/data/processed/poll_events_seed.csv"), "utf8"));
  const accepted = JSON.parse(readFileSync(resolve(root, "metadata/accepted-polls-2026.json"), "utf8"));
  const manual = JSON.parse(readFileSync(resolve(root, "metadata/manual-source-evidence-2026.json"), "utf8"));
  const primary = JSON.parse(readFileSync(resolve(root, "metadata/primary-source-evidence-2026.json"), "utf8"));
  const research = JSON.parse(readFileSync(resolve(root, "metadata/research-source-evidence-2026.json"), "utf8"));
  const stagedPolls = [
    ...(manual.records ?? []),
    ...(primary.records ?? []).map((record) => ({ ...record, publicationDate: record.pollPublicationDate ?? record.publicationDate })),
    ...(research.records ?? []),
  ];
  const report = buildEvidenceFreshness({ modelPolls, acceptedPolls: accepted.polls ?? [], stagedPolls, asOf });
  writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Evidence freshness: model=${report.modelInput?.latestPublicationDate ?? "none"}; newest evidence=${report.newestEvidenceDate ?? "none"}; awaiting review=${report.newerEvidenceAwaitingReview}.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
