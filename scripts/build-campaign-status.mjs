import { loadCampaignPolls } from "./load-campaign-polls.mjs";
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildReadiness, ageInDays } from './check-release-readiness.mjs';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (path) => JSON.parse(readFileSync(resolve(root, path), 'utf8'));
export function buildCampaignStatus(asOf) {
  const evidence = read('metadata/current-evidence-shadow-2026-10-31.json');
  const campaignPolls=loadCampaignPolls(root);
  const latestReviewedFieldwork=campaignPolls.map(poll=>poll.fieldworkEnd).sort().at(-1);
  const admitted=campaignPolls.filter(poll=>poll.modelEligibilityDecision==='eligible').length;
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
    newerEvidenceOutsideForecast: latestReviewedFieldwork > pollSource.dataEffectiveDate,
    campaignPollsAwaitingAdmission: campaignPolls.filter((poll) => poll.modelEligibilityDecision !== 'eligible').length,
    campaignPollsAdmitted: admitted,
    readiness,
    notice: `${admitted} campaign polls admitted under explicit owner approval; other campaign waves remain held. This is an experimental snapshot. Published probabilities have not passed full production calibration.`,
    council: { regionalInput: 'upper_house_region_poll_2026-08.csv', newerRegionalPublication: evidence.councilEvidence.publicationDate, status: evidence.councilEvidence.status },
  };
}
function main() {
  const i = process.argv.indexOf('--as-of');
  const asOf = i < 0 ? undefined : process.argv[i + 1];
  if (asOf && !/^\d{4}-\d{2}-\d{2}$/.test(asOf)) throw new Error('Invalid assessment date');
  const content = JSON.stringify(buildCampaignStatus(asOf), null, 2) + '\n';
  const evidenceTarget=resolve(root,'app/campaign-evidence.generated.json');
  const evidenceContent=JSON.stringify({reviewedAt:read('metadata/poll-admission-review-2026-10-31.json').reviewedAt,assemblyPolls:loadCampaignPolls(root)},null,2)+'\n';
  if(process.argv.includes('--check')) { if(readFileSync(evidenceTarget,'utf8')!==evidenceContent) throw new Error('Campaign evidence view is stale'); } else writeFileSync(evidenceTarget,evidenceContent);
  const target = resolve(root, 'app/campaign-status.generated.json');
  if (process.argv.includes('--check')) {
    if (readFileSync(target, 'utf8') !== content) throw new Error('Campaign status is stale');
  } else writeFileSync(target, content);
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
