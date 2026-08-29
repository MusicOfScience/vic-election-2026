import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const allowedEvidenceTypes = new Set([
  "vote_to_seat_model",
  "poll_aggregation_and_seat_analysis",
  "by_election_analysis",
  "poll_interpretation",
  "redistribution",
  "pendulum",
  "preference_flow",
  "seat_analysis",
  "upper_house",
  "demographic_pattern",
  "regional_pattern"
]);
const allowedUsage = new Set(["reference_only", "comparison_only", "candidate_for_model", "model_input"]);
const allowedReview = new Set(["quarantined-awaiting-review", "reviewed-reference-only", "approved-model-input", "rejected"]);
const allowedIndependence = new Set(["independent", "dependent", "partially_dependent", "derived_from_official_results"]);

export function validatePsephologyRegistries(sourceRegistry, evidenceRegistry) {
  const errors = [];
  const sourceIds = new Set();
  const families = new Map();

  for (const source of sourceRegistry.sources ?? []) {
    if (!source.id || !source.displayName || !source.sourceFamily || !source.canonicalUrl) errors.push("psephology sources: incomplete source record");
    if (sourceIds.has(source.id)) errors.push(`psephology sources: duplicate source id ${source.id}`);
    sourceIds.add(source.id);
    if (!String(source.canonicalUrl).startsWith("https://")) errors.push(`psephology sources: ${source.id} requires HTTPS canonicalUrl`);
    const familyMembers = families.get(source.sourceFamily) ?? [];
    familyMembers.push(source.id);
    families.set(source.sourceFamily, familyMembers);
  }

  const evidenceIds = new Set();
  for (const record of evidenceRegistry.records ?? []) {
    if (!record.id || !record.analystSourceId || !record.publishedDate || !record.sourceUrl || !record.evidenceType || !record.geography) {
      errors.push(`psephology evidence: incomplete record ${record.id ?? "<unknown>"}`);
      continue;
    }
    if (evidenceIds.has(record.id)) errors.push(`psephology evidence: duplicate id ${record.id}`);
    evidenceIds.add(record.id);
    if (!sourceIds.has(record.analystSourceId)) errors.push(`psephology evidence: unknown analyst source ${record.analystSourceId}`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(record.publishedDate)) errors.push(`psephology evidence: invalid publishedDate ${record.id}`);
    if (!String(record.sourceUrl).startsWith("https://")) errors.push(`psephology evidence: ${record.id} requires HTTPS sourceUrl`);
    if (!allowedEvidenceTypes.has(record.evidenceType)) errors.push(`psephology evidence: unsupported evidenceType ${record.evidenceType}`);
    if (!allowedUsage.has(record.modelUsage)) errors.push(`psephology evidence: unsupported modelUsage ${record.modelUsage}`);
    if (!allowedReview.has(record.reviewStatus)) errors.push(`psephology evidence: unsupported reviewStatus ${record.reviewStatus}`);
    if (!allowedIndependence.has(record.independenceAssessment)) errors.push(`psephology evidence: unsupported independenceAssessment ${record.independenceAssessment}`);
    if (!Array.isArray(record.upstreamEvidence)) errors.push(`psephology evidence: ${record.id} must declare upstreamEvidence`);
    if (record.pollDerived && (!record.upstreamEvidence || record.upstreamEvidence.length === 0)) errors.push(`psephology evidence: poll-derived ${record.id} must declare upstream evidence`);
    if (record.pollDerived && record.independenceAssessment === "independent") errors.push(`psephology evidence: poll-derived ${record.id} cannot claim independence from its polling inputs`);
    if (record.modelUsage === "model_input" && record.reviewStatus !== "approved-model-input") errors.push(`psephology evidence: ${record.id} cannot enter model without explicit approval`);
    if (record.pollDerived && record.modelUsage === "model_input") errors.push(`psephology evidence: poll-derived analyst output cannot be a direct model input; use underlying polls or a separately approved transformation`);
  }

  return { errors, sourceCount: sourceIds.size, evidenceCount: evidenceIds.size, sourceFamilyCount: families.size };
}

export function independentFamilyCount(sourceRegistry, analystSourceIds) {
  const sourceById = new Map((sourceRegistry.sources ?? []).map((source) => [source.id, source]));
  return new Set(analystSourceIds.map((id) => sourceById.get(id)?.sourceFamily).filter(Boolean)).size;
}

function main() {
  const sources = JSON.parse(readFileSync(resolve(root, "metadata/psephology-sources.json"), "utf8"));
  const evidence = JSON.parse(readFileSync(resolve(root, "metadata/psephology-evidence-2026.json"), "utf8"));
  const result = validatePsephologyRegistries(sources, evidence);
  if (result.errors.length) throw new Error(result.errors.join("\n"));
  console.log(`Psephology evidence valid: ${result.evidenceCount} reviewed records across ${result.sourceCount} analyst sources / ${result.sourceFamilyCount} independent source families.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
