import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildReadiness, ageInDays } from './check-release-readiness.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (path) => JSON.parse(readFileSync(resolve(root, path), 'utf8'));
export function buildCampaignStatus(asOf) {
  const evidence = read('metadata/current-evidence-shadow-2026-10-31.json');
  const assessment = asOf ?? evidence.reviewedAt;
  const readiness = buildReadiness({ asOf: assessment });
  const forecast = read('model/data/processed/experimental_forecast_2026.json');
  const pollSource = readiness.sources.find((source) => source.id === 'vic-2026-poll-registry');
  const latestEvidenceDate = evidence.assemblyPolls.map((poll) => poll.publicationDate).sort().at(-1);
  return {
    schemaVersion: 1, assessedAsOf: assessment,
    forecastDate: forecast.as_of ?? forecast.manifest?.as_of ?? '2026-10-08',
    latestIncludedPollFieldwork: pollSource.dataEffectiveDate,
    latestReviewedPublication: latestEvidenceDate,
    pollAgeDays: ageInDays(pollSource.dataEffectiveDate, assessment),
    freshnessThresholdDays: pollSource.stalenessThresholdDays,
    forecastStale: pollSource.stale,
    newerEvidenceOutsideForecast: latestEvidenceDate > pollSource.dataEffectiveDate,
    campaignPollsAwaitingAdmission: evidence.assemblyPolls.filter((poll) => poll.modelEligibilityDecision !== 'eligible').length,
    readiness,
    notice: 'Retained experimental snapshot. Newer polling has been reviewed for sensitivity analysis but has not been admitted to this forecast. Published probabilities have not passed full production calibration.',
    council: { regionalInput: 'upper_house_region_poll_2026-08.csv', newerRegionalPublication: evidence.councilEvidence.publicationDate, status: evidence.councilEvidence.status },
  };
}
function main() {
  const i = process.argv.indexOf('--as-of');
  const asOf = i < 0 ? undefined : process.argv[i + 1];
  if (asOf && !/^\d{4}-\d{2}-\d{2}$/.test(asOf)) throw new Error('Invalid assessment date');
  const content = JSON.stringify(buildCampaignStatus(asOf), null, 2) + '\n';
  const target = resolve(root, 'app/campaign-status.generated.json');
  if (process.argv.includes('--check')) {
    if (readFileSync(target, 'utf8') !== content) throw new Error('Campaign status is stale');
  } else writeFileSync(target, content);
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
