import { appendFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function monitoringCadence(now, event = "schedule") {
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: "Australia/Melbourne", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
  const weekday = new Intl.DateTimeFormat("en-US", { timeZone: "Australia/Melbourne", weekday: "short" }).format(now);
  const campaign = day >= "2026-11-03" && day <= "2026-11-28";
  return { day, phase: campaign ? "campaign-daily" : "routine-twice-weekly", run: event !== "schedule" || campaign || ["Tue", "Fri"].includes(weekday) };
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const value = monitoringCadence(new Date(), process.env.GITHUB_EVENT_NAME);
  if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, Object.entries(value).map(([k,v]) => `${k}=${v}\n`).join(""));
  console.log(JSON.stringify(value));
}
