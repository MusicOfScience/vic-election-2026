// Review signals only: no registry, model, forecast or Git write permissions.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, appendFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
const hash = (v) => createHash("sha256").update(JSON.stringify(v)).digest("hex");
const required = ["release-readiness-report", "live-source-report", "source-discovery-report", "source-discovery-quarantine", "discovery-review-manifest", "analyst-comparison-report", "evidence-freshness-report", "poll-promotion-audit", "poll-coverage-report", "freshwater-primary-report"];

export function monitoringActions(reports, decisions = [], steps = {}, primaryRecords = []) {
  const actions = [];
  const add = (status, identity, detail) => actions.push({ status, identity, detail });
  for (const name of required) if (!reports[name]) add("WORKFLOW_FAILURE", name, "Required report missing or unreadable; discovery cannot be declared complete.");
  for (const [name, step] of Object.entries(steps)) if (step.outcome === "failure" && (name !== "freshness" || !reports["release-readiness-report"]?.sources?.some((s) => s.critical && s.stale))) add("WORKFLOW_FAILURE", name, "Workflow stage failed; inspect its log.");
  for (const s of reports["release-readiness-report"]?.sources ?? []) if (s.critical && s.stale) add("FRESHNESS_WARNING", s.id, `Effective source date ${s.dataEffectiveDate}; observing a URL does not refresh model inputs.`);
  for (const s of reports["live-source-report"]?.observations ?? []) {
    if (["changed-quarantined", "observed-unbaselined"].includes(s.status)) add("SOURCE_CHANGE_REVIEW_REQUIRED", s.id, `${s.status}: ${s.observedFingerprint}`);
    if (["fetch-failed", "invalid-quarantined"].includes(s.status)) add("WORKFLOW_FAILURE", s.id, s.status);
  }
  for (const s of reports["source-discovery-report"]?.observations ?? []) if (s.status === "extract-failed") add("WORKFLOW_FAILURE", s.sourceId, "Source extraction failed; no absence-of-evidence conclusion permitted.");
  for (const r of reports["source-discovery-quarantine"]?.records ?? []) {
    // Resolve only the exact reviewed carrier, never an ID alone: changed values
    // under a manually stable ID require review again. Holds remain holds.
    const reviewed = decisions.some((d) => d.evidenceId === r.id && d.recordHash === hash(r) && ["approve", "hold", "reject", "defer"].includes(d.decision));
    if (!reviewed) add(r.kind === "candidate" ? "CANDIDATE_REVIEW_REQUIRED" : "POLL_REVIEW_REQUIRED", r.id, `${r.sourceId}: quarantined evidence; model eligibility requires a separate governed decision.`);
  }
  for (const r of reports["freshwater-primary-report"]?.records ?? []) {
    const baseline = primaryRecords.find((p) => p.workbookUrl === r.url);
    if (!baseline?.workbookSha256 || baseline.workbookSha256 !== r.sha256) add("SOURCE_CHANGE_REVIEW_REQUIRED", r.id, `Freshwater carrier ${r.sha256} differs from the captured primary baseline; unchanged rounded figures do not establish unchanged evidence.`);
  }
  if (reports["freshwater-primary-report"]?.allValid === false) add("POLL_REVIEW_REQUIRED", "freshwater-workbooks", "Published workbook figures differ from registered expectations; capture and review before any input update.");
  if (reports["evidence-freshness-report"]?.newerEvidenceAwaitingReview) add("FRESHNESS_WARNING", "model-input-evidence", "Newer evidence awaits review; acquisition does not make it eligible.");
  actions.sort((a,b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
  const statuses = [...new Set(actions.map((a) => a.status))];
  return { schemaVersion: 1, statuses: statuses.length ? statuses : ["NO_ACTION"], actions, materialFingerprint: hash(actions), automaticPromotion: false, modelInputsChanged: false, forecastRefreshed: false };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const reports = {};
  for (const name of required) { try { reports[name] = JSON.parse(readFileSync(`${name}.json`, "utf8")); } catch { /* Report the missing stage below. */ } }
  const decisions = JSON.parse(readFileSync("metadata/discovery-review-decisions.json", "utf8")).decisions;
  const value = monitoringActions(reports, decisions, JSON.parse(process.env.MONITOR_STEPS ?? "{}"), JSON.parse(readFileSync("metadata/primary-source-evidence-2026.json", "utf8")).records);
  writeFileSync("monitoring-action-report.json", `${JSON.stringify(value,null,2)}\n`);
  const escape = (s) => String(s).replace(/[\r\n|]/g, " ").replace(/</g, "&lt;");
  const summary = `## Governed monitoring: ${value.statuses.join(", ")}\n\nAcquisition/review only. **No model inputs changed; no forecast refreshed.**\n\n| Signal | Evidence/source | Action |\n|---|---|---|\n${value.actions.map((a) => `| ${a.status} | ${escape(a.identity)} | ${escape(a.detail)} |`).join("\n")}\n\nDownload operational-readiness-reports for carrier references and review manifests (90-day retention). Capture primary carriers durably before admission. Existing holds are not approvals. See docs/AUTOMATION_SPEC.md.\n`;
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, summary);
  for (const status of value.statuses.filter((s) => s !== "NO_ACTION")) console.log(`::${status === "WORKFLOW_FAILURE" ? "error" : "warning"} title=Governed monitoring::${status}; inspect this run's summary and operational-readiness-reports. No automatic model update.`);
  console.log(JSON.stringify({ statuses: value.statuses, materialFingerprint: value.materialFingerprint }));
  if (value.statuses.includes("WORKFLOW_FAILURE")) process.exitCode = 1;
}
