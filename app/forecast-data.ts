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
