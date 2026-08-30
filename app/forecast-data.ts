import validationStatus from "../metadata/model-validation-status.json";

export const modelLayers = [
  { layer: "Polls", status: "Live experimental input", detail: "Nine eligible polls are combined with recency, sample size and estimated pollster lean taken into account." },
  { layer: "Election baseline", status: "Working", detail: "Official VEC results anchor all 88 Lower House electorates and eight Upper House regions, with boundary changes handled explicitly." },
  { layer: "Demography + housing", status: "Tested and excluded", detail: "The added demographic layer was tested across four past election cycles and made predictions slightly worse, so its central weight is zero." },
  { layer: "Preferences + local contests", status: "Experimental", detail: "Official preference files inform transfers. The model can discover different final-two pairings rather than assuming Labor versus Coalition." },
  { layer: "Upper House", status: "Experimental", detail: "Each five-member regional count is simulated under the 2026 voter-directed preference rules, without group voting tickets." },
  { layer: "Public forecast", status: "Research release", detail: "The app shows a reproducible experimental estimate with uncertainty; it has not been approved as a production forecasting system." },
] as const;

export const validationSummary = {
  cycles: validationStatus.historicalDataReadiness.cycles.length,
  districtTransitions: validationStatus.historicalDataReadiness.districtTransitions,
  featureCells: validationStatus.historicalDataReadiness.featureCells,
  baselineMae: validationStatus.demographicChallenger.metrics.baselineMae * 100,
  candidateMae: validationStatus.demographicChallenger.metrics.candidateMae * 100,
  baselineRmse: validationStatus.demographicChallenger.metrics.baselineRmse * 100,
  candidateRmse: validationStatus.demographicChallenger.metrics.candidateRmse * 100,
  baselineWinnerErrors: validationStatus.demographicChallenger.metrics.baselineWinnerErrors,
  candidateWinnerErrors: validationStatus.demographicChallenger.metrics.candidateWinnerErrors,
} as const;
