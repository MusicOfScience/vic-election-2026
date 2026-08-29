import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
}

export function summariseRecord(record) {
  if (record.kind === "candidate") {
    return {
      id: record.id,
      kind: record.kind,
      label: `${record.name} — ${record.contest}`,
      detail: `${record.party ?? "Independent / unlabelled"} · ${record.officialStatus ?? "provisional"}`,
      sourceId: record.sourceId,
      sourceUrl: record.sourceUrl,
      proposedAction: "Review identity, electorate/region and endorsement; approve into candidate registry or reject.",
    };
  }
  const vote = record.primaryVote
    ? `ALP ${record.primaryVote.alp ?? "?"}% · Coalition ${record.primaryVote.coalition ?? "?"}% · ON ${record.primaryVote.oneNation ?? "?"}% · Greens ${record.primaryVote.greens ?? "?"}%`
    : record.seatProjection
      ? `Seat projection: Coalition ${record.seatProjection.coalition ?? "?"}, ON ${record.seatProjection.oneNation ?? "?"}, ALP ${record.seatProjection.alp ?? "?"}`
      : "Structured poll evidence";
  return {
    id: record.id,
    kind: record.kind,
    label: `${record.pollster} — ${record.fieldworkStart} to ${record.fieldworkEnd}`,
    detail: `n=${record.sampleSize ?? "?"} · ${vote}`,
    sourceId: record.sourceId,
    sourceUrl: record.sourceUrl,
    proposedAction: "Review source/methodology and figures; accept as evidence or reject. Model eligibility remains separate.",
  };
}

export function buildManifest(quarantine) {
  const entries = (quarantine.records ?? []).map(summariseRecord);
  return {
    schemaVersion: 1,
    generatedAt: quarantine.checkedAt ?? new Date().toISOString(),
    policy: "human-review-before-promotion",
    automaticPromotion: false,
    summary: {
      total: entries.length,
      candidates: entries.filter((item) => item.kind === "candidate").length,
      polls: entries.filter((item) => item.kind.startsWith("poll")).length,
    },
    instructions: [
      "Approve only after opening the cited primary source and checking the structured fields.",
      "Candidate approval may enter the candidate registry, but only VEC evidence can confer an official nomination status.",
      "Poll approval accepts the evidence record only; it does not make the poll model-eligible.",
    ],
    entries,
  };
}

function main() {
  const input = resolve(arg("--input", "source-discovery-quarantine.json"));
  const output = resolve(arg("--output", "discovery-review-manifest.json"));
  const manifest = buildManifest(JSON.parse(readFileSync(input, "utf8")));
  writeFileSync(output, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`Discovery review manifest: ${manifest.summary.total} records (${manifest.summary.candidates} candidates, ${manifest.summary.polls} polls).`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
