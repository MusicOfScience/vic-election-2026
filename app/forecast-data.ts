export const MODEL_VINTAGE = "26 August 2026";
export const POLL_ANCHOR_DATE = "7 August 2026";
export const DEFAULT_ALP_TPP = 49;
export const HISTORICAL_BASELINE_RMSE = 3.69;

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
