import { appendFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function monitoringCadence(now, event = "schedule") {
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: "Australia/Melbourne", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
  const weekday = new Intl.DateTimeFormat("en-US", { timeZone: "Australia/Melbourne", weekday: "short" }).format(now);
  const campaign = day >= "2026-11-03" && day <= "2026-11-28";
  return { day, phase: campaign ? "campaign-daily" : "routine-twice-weekly", run: event !== "schedule" || campaign || ["Tue", "Fri"].includes(weekday) };
}
export function cadenceSummary(value) {
  return value.run
    ? `## Source acquisition scheduled\n\nMelbourne date: ${value.day}; cadence: ${value.phase}. Acquisition will run in the freshness job. This scheduling result is not a source-health check.\n`
    : `## NOT CHECKED: source acquisition skipped by cadence\n\nMelbourne date: ${value.day}; cadence: ${value.phase}. No upstream sources were checked in this run. A green scheduling result does not establish source recovery or resolve earlier acquisition failures. Use workflow_dispatch for an immediate check.\n`;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const value = monitoringCadence(new Date(), process.env.GITHUB_EVENT_NAME);
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, Object.entries(value).map(([k,v]) => `${k}=${v}\n`).join(""));
  if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, cadenceSummary(value));
  console.log(JSON.stringify(value));
}
