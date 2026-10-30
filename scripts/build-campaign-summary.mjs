import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const read = (path) => JSON.parse(readFileSync(new URL('../'+path, import.meta.url), 'utf8'));
const reportPath = 'metadata/current-evidence-results-2026-10-31.json';
const report = read(reportPath);
const diagnostic = read('metadata/campaign-preference-diagnostic-2026-10-31.json');
const compact = (summary) => ({ pollCount: summary.polling.pollCount, pollingMean: summary.polling.mean, hungProbability: summary.assembly.hungProbability, parties: summary.assembly.parties });
const result = { asOf: report.asOf, simulations: report.simulationsPerScenario, seed: report.seed, reportSha256: createHash('sha256').update(readFileSync(new URL('../'+reportPath, import.meta.url))).digest('hex'), canonicalReaged: compact(report.canonicalCurrentDate), scenarios: Object.fromEntries(Object.entries(report.scenarios).map(([name, scenario])=>[name,compact(scenario.summary)])), preferenceDiagnostic: diagnostic.comparisons };
const text = JSON.stringify(result, null, 2)+'\n';
const target = new URL('../app/campaign-summary.generated.json', import.meta.url);
if (process.argv.includes('--check')) { if (readFileSync(target,'utf8') !== text) throw new Error('Campaign summary is stale'); } else writeFileSync(target,text);

const admission = read('metadata/poll-admission-sensitivity-2026-10-31.json');
const admissionCompact = { asOf: admission.asOf, simulations: admission.simulationsPerScenario, scenarios: Object.fromEntries(Object.entries(admission.scenarios).map(([name, value]) => [name, { pollCount: value.summary.polling.pollCount, parties: value.summary.assembly.parties, hungProbability: value.summary.assembly.hungProbability }])) };
const admissionText = JSON.stringify(admissionCompact, null, 2)+'\n';
const admissionTarget = new URL('../app/poll-admission-summary.generated.json', import.meta.url);
if (process.argv.includes('--check')) { if (readFileSync(admissionTarget, 'utf8') !== admissionText) throw new Error('Admission summary is stale'); } else writeFileSync(admissionTarget, admissionText);
