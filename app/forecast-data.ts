export const MODEL_VINTAGE = "26 August 2026";
export const POLL_ANCHOR_DATE = "7 August 2026";
export const DEFAULT_ALP_TPP = 49;
export const HISTORICAL_BASELINE_RMSE = 3.69;

export const pollingBenchmark = {
  asOf: "9 August 2026",
  pollCount: 9,
  method: "Sample-size and recency weighted primary-vote benchmark",
  halfLives: [21, 45, 90] as const,
  estimates: {
    21: { alp: 26.1112, coalition: 27.0396, onp: 23.2745, greens: 12.8143, other: 10.7604 },
    45: { alp: 25.7347, coalition: 26.8548, onp: 23.8162, greens: 13.0550, other: 10.5393 },
    90: { alp: 25.4677, coalition: 26.5550, onp: 24.1079, greens: 13.2199, other: 10.6494 },
  },
} as const;

export const pollSeries = [
  { date: "10 Feb", pollster: "DemosAU", alp: 23, coalition: 29, onp: 21, greens: 15, other: 12, n: 1274 },
  { date: "16 Feb", pollster: "Roy Morgan", alp: 25.5, coalition: 21.5, onp: 26.5, greens: 13.5, other: 13, n: 2462 },
  { date: "27 Feb", pollster: "RedBridge / Accent", alp: 25, coalition: 28, onp: 24, greens: 13, other: 10, n: 2165 },
  { date: "24 Apr", pollster: "Roy Morgan", alp: 25.5, coalition: 24, onp: 24.5, greens: 13.5, other: 12.5, n: 1707 },
  { date: "8 Jun", pollster: "Freshwater", alp: 23, coalition: 27, onp: 25, greens: 14, other: 11, n: 1034 },
  { date: "11 Jun", pollster: "DemosAU", alp: 21, coalition: 30, onp: 23, greens: 15, other: 11, n: 1056 },
  { date: "28 Jun", pollster: "RedBridge / Accent", alp: 26, coalition: 26, onp: 27, greens: 13, other: 8, n: 5516 },
  { date: "26 Jul", pollster: "Newspoll / Pyxis", alp: 28, coalition: 31, onp: 19, greens: 13, other: 9, n: 1035 },
  { date: "7 Aug", pollster: "Roy Morgan", alp: 26, coalition: 26, onp: 23.5, greens: 12.5, other: 12, n: 2084 },
] as const;

export const modelLayers = [
  { layer: "Polls", status: "Live experimental input", detail: "Nine eligible polls are combined with recency, sample size and estimated pollster lean taken into account." },
  { layer: "Election baseline", status: "Working", detail: "Official VEC results anchor all 88 Lower House electorates and eight Upper House regions, with boundary changes handled explicitly." },
  { layer: "Demography + housing", status: "Tested and excluded", detail: "The added demographic layer was tested across four past election cycles and made predictions slightly worse, so its central weight is zero." },
  { layer: "Preferences + local contests", status: "Experimental", detail: "Official preference files inform transfers. The model can discover different final-two pairings rather than assuming Labor versus Coalition." },
  { layer: "Upper House", status: "Experimental", detail: "Each five-member regional count is simulated under the 2026 voter-directed preference rules, without group voting tickets." },
  { layer: "Public forecast", status: "Research release", detail: "The app shows a reproducible experimental estimate with uncertainty; it has not been approved as a production forecasting system." },
] as const;

export const validationSummary = {
  cycles: 4,
  districtTransitions: 340,
  featureCells: 2464,
  baselineMae: 2.7804,
  candidateMae: 2.8121,
  baselineRmse: 3.6938,
  candidateRmse: 3.7190,
  baselineWinnerErrors: 21,
  candidateWinnerErrors: 24,
} as const;

export const latestPrimary = [
  { party: "Labor", value: 26, key: "alp" },
  { party: "Coalition", value: 26, key: "coalition" },
  { party: "One Nation", value: 23.5, key: "onp" },
  { party: "Greens", value: 12.5, key: "greens" },
  { party: "Independents", value: 8, key: "independent" },
  { party: "Other", value: 4, key: "other" },
] as const;

export const pollTrend = [
  { date: "Feb 2026", alp: 52, coalition: 48 },
  { date: "Apr 2026", alp: 51, coalition: 49 },
  { date: "Aug 2026", alp: 49, coalition: 51 },
] as const;

export const greenSeatMargins: Record<string, number> = {
  Brunswick: 55.15,
  Melbourne: 60.19,
  Richmond: 57.32,
};

export const upperHouseRegions = [
  { region: "Northern Metropolitan", alp: 2, coalition: 1, onp: 1, greens: 1, other: 0, undecided: 0, alpVote: 39, coalitionVote: 13, onpVote: 12, greensVote: 22 },
  { region: "Southern Metropolitan", alp: 1, coalition: 2, onp: 1, greens: 0, other: 0, undecided: 1, alpVote: 25.5, coalitionVote: 36, onpVote: 14.5, greensVote: 11 },
  { region: "Western Metropolitan", alp: 1, coalition: 1, onp: 2, greens: 0, other: 1, undecided: 0, alpVote: 22.5, coalitionVote: 16, onpVote: 29.5, greensVote: 11 },
  { region: "North-Eastern Metropolitan", alp: 1, coalition: 1, onp: 1, greens: 1, other: 0, undecided: 1, alpVote: 26.5, coalitionVote: 26.5, onpVote: 23, greensVote: 12.5 },
  { region: "South-Eastern Metropolitan", alp: 1, coalition: 1, onp: 2, greens: 0, other: 0, undecided: 1, alpVote: 21.5, coalitionVote: 22, onpVote: 36.5, greensVote: 6 },
  { region: "Eastern Victoria", alp: 1, coalition: 2, onp: 1, greens: 0, other: 0, undecided: 1, alpVote: 21, coalitionVote: 32.5, onpVote: 26.5, greensVote: 9.5 },
  { region: "Northern Victoria", alp: 1, coalition: 2, onp: 1, greens: 0, other: 0, undecided: 1, alpVote: 22, coalitionVote: 30.5, onpVote: 27, greensVote: 11 },
  { region: "Western Victoria", alp: 1, coalition: 1, onp: 1, greens: 0, other: 0, undecided: 2, alpVote: 28, coalitionVote: 26, onpVote: 28.5, greensVote: 8 },
] as const;

export const sources = {
  lowerHousePoll: "https://www.roymorgan.com/findings/10303-victorian-state-voting-intention-august-2026",
  upperHousePoll: "https://www.roymorgan.com/findings/victorian-state-voting-intention-l-np-coalition-and-one-nation-set-for-a-majority-in-victorias-upper-house-in-november",
  prahran: "https://www.vec.vic.gov.au/results/state-election-results/state-by-elections-timeline/prahran-district-results/results-by-district/prahran-district-results",
  werribee: "https://www.vec.vic.gov.au/results/state-election-results/state-by-elections-timeline/werribee-district-results/results-by-district/werribee-district-results",
} as const;
