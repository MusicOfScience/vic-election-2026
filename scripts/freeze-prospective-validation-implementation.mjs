// No model outputs are generated. Implementation amendments require review before seal.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const paths = [
  "model/validation/prospective/governance.py", "model/validation/prospective/comparators.py",
  "model/validation/prospective/scoring.py", "model/validation/prospective/package.py",
  "model/scripts/prospective_snapshot.py", "metadata/prospective-validation-input-contract.json",
  "scripts/validate-prospective-registration.mjs",
];
const hash = (p) => createHash("sha256").update(readFileSync(resolve(root,p))).digest("hex");
const approval = JSON.parse(readFileSync(resolve(root,"metadata/prospective-validation-approval.json")));
const value = { schemaVersion: 1, protocolId: approval.protocolId, protocolSha256: approval.approvedProtocolSha256,
  status: "frozen-active-registration-implementation",
  amendmentPurpose: "Operational active-registration and append-only milestone guards; comparator/scorer and approved material rules unchanged. PR #127 archive retains the original implementation.", scoringAuthorised: false, productionAuthorised: false,
  comparatorImplementations: { prior_result: hash(paths[1]), uniform_swing: hash(paths[1]) },
  scorerSha256: hash(paths[2]), files: Object.fromEntries(paths.map((p) => [p,hash(p)])),
  amendmentPolicy: "No casual mutation. Any implementation change needs reviewed fingerprint amendment before a new seal; material rule changes require a prospectively versioned protocol. Earlier sealed packages retain exact code.",
};
const output = resolve(root,"metadata/prospective-validation-implementation.json");
const bytes = `${JSON.stringify(value,null,2)}\n`;
if (process.argv.includes("--check")) {
  if (readFileSync(output,"utf8") !== bytes) throw new Error("prospective implementation manifest drift");
  console.log("Prospective comparator/scorer/sealer fingerprints reconcile; no scoring or production authorised.");
} else writeFileSync(output,bytes);
