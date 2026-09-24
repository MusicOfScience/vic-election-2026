import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL("..", import.meta.url).pathname);
const readJson = (name) => JSON.parse(readFileSync(resolve(root, name), "utf8"));

export function validateHistoricalPollReusePolicy() {
  const policy = readJson("metadata/historical-poll-reuse-policy.json");
  const caseFile = readJson("metadata/historical-poll-reuse-case-2018-essential.json");
  const classes = policy.classes;
  const required = ["explicit_open_licence", "permission_obtained", "official_open_data", "independently_reconstructed_factual_observation", "research_only", "third_party_dataset_unlicensed", "unknown"];
  if (required.some((id) => !classes[id])) throw new Error("historical poll reuse policy: class inventory is incomplete");
  if (!policy.eligibilityRule.allGatesRequired || !policy.eligibilityRule.unknownReuseBasisRejected || !policy.eligibilityRule.thirdPartyUnlicensedRejected) {
    throw new Error("historical poll reuse policy: fail-closed eligibility rules are missing");
  }
  if (caseFile.cycleInformationCutoff < caseFile.evidenceAvailableByDate || !caseFile.notFromQuarantinedDataset) {
    throw new Error("historical poll reuse policy: 2018 case has unsafe provenance");
  }
  if (caseFile.reuseBasis !== "independently_reconstructed_factual_observation" || !caseFile.reuseBasisGate.passed || caseFile.rawSourceStored || caseFile.copiedAuthoredExpression) {
    throw new Error("historical poll reuse policy: independent factual case is not conservatively represented");
  }
  if (!caseFile.methodologicalAdequacyGate.passed || caseFile.replayEligible || !caseFile.modelInputAdmissible) {
    throw new Error("historical poll reuse policy: ballot-aware 2018 case adjudication is inconsistent");
  }
  return { policyClasses: required.length, adjudicatedCases: 1, replayEligibleCases: 0 };
}

if (process.argv[1]?.endsWith("validate-historical-poll-reuse-policy.mjs")) {
  console.log(JSON.stringify(validateHistoricalPollReusePolicy()));
}
