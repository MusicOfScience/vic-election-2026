#!/usr/bin/env node
/**
 * Evidence-locked, output-only audit of the 2026 experimental district model.
 * No modelling parameters, canonical poll files, ballots or forecasts are edited.
 *
 * Use: node scripts/audit-2026-model-mechanics.mjs [--output FILE]
 */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
export const PARTIES = ["ALP", "LIB_NAT", "ONP", "GRN", "OTH_IND"];

const sha = (buffer) => createHash("sha256").update(buffer).digest("hex");
const num = (n, label) => {
  const v = Number(n);
  if (!Number.isFinite(v)) throw new Error("Non-finite " + label);
  return v;
};

export function parseCsv(text) {
  let cell = "", row = [], quote = false;
  const rows = [];
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"' && quote && text[i + 1] === '"') { cell += '"'; i++; }
    else if (c === '"') quote = !quote;
    else if (c === "," && !quote) { row.push(cell); cell = ""; }
    else if ((c === "\n" || c === "\r") && !quote) {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell);
      if (row.some((v) => v !== "")) rows.push(row);
      row = [];
      cell = "";
    } else cell += c;
  }
  if (quote) throw new Error("Unclosed CSV quote");
  if (row.length || cell) rows.push([...row, cell]);
  if (!rows.length) throw new Error("Empty CSV");
  const [header, ...data] = rows;
  return data.map((r) => {
    if (r.length !== header.length) throw new Error("Unexpected CSV width");
    return Object.fromEntries(header.map((x, i) => [x, r[i]]));
  });
}

export function familyFromRegisteredParty(party) {
  const p = String(party ?? "");
  if (p === "Australian Labor Party - Victorian Branch") return "ALP";
  if (p === "Liberal Party of Australia - Victorian Division" ||
      p === "National Party of Australia - Victoria") return "LIB_NAT";
  if (p === "One Nation Victoria") return "ONP";
  if (p === "Australian Greens Victoria") return "GRN";
  // The source's "no registered party" field cannot be classified as
  // "independent" merely from absence of a name. OTH_IND is the *model family*.
  return "OTH_IND";
}

export function preferencePriorFromSource(source) {
  const m = String(source).match(/PREFERENCE_PRIOR = np\.array\(\[([\s\S]*?)\]\)/);
  if (!m) throw new Error("Cannot find the frozen preference mean matrix");
  const matrix = JSON.parse("[" + m[1].replace(/,\\s*$/, "") + "]");
  if (matrix.length !== 5 || !matrix.every((row) => row.length === 5))
    throw new Error("Unexpected preference mean matrix size");
  for (let i = 0; i < 5; i++) {
    const row = matrix[i];
    if (row.some((v) => v < 0 || v > 1 || !Number.isFinite(v)) ||
        Math.abs(row.reduce((a, b) => a + b, 0) - 1) > 1e-7 || row[i] !== 0)
      throw new Error("Invalid preference mean row " + i);
  }
  return matrix;
}

export function meanPathCount(primary, preference) {
  const votes = [...primary];
  let continuing = [0, 1, 2, 3, 4];
  const eliminations = [];
  while (continuing.length > 2) {
    let lowest = continuing[0];
    for (const p of continuing) if (votes[p] < votes[lowest]) lowest = p;
    continuing = continuing.filter((p) => p !== lowest);
    const denom = continuing.reduce((sum, p) => sum + preference[lowest][p], 0);
    if (!(denom > 0)) throw new Error("Invalid mean preference transfer destinations");
    const amount = votes[lowest];
    for (const p of continuing) votes[p] += amount * preference[lowest][p] / denom;
    votes[lowest] = 0;
    eliminations.push(PARTIES[lowest]);
  }
  continuing.sort((a, b) => votes[b] - votes[a]);
  return {
    winner: PARTIES[continuing[0]],
    loser: PARTIES[continuing[1]],
    finalWinnerSharePercent: 100 * votes[continuing[0]] / (votes[continuing[0]] + votes[continuing[1]]),
    eliminations,
    explanation: "One illustrative deterministic count using average model primaries and mean transfer priors, NOT the model's joint simulated winning probability or a survey 2CP."
  };
}

export function buildSeatIntegrityAudit(root = ROOT) {
  const paths = {
    model: "model/data/processed/experimental_forecast_2026_districts.csv",
    chamber: "model/data/processed/experimental_forecast_2026_chamber.csv",
    source: "model/src/vicforecast/forecast_2026.py",
    roster: "app/vec-official-candidates-2026.review.json",
    evidence: "metadata/november-poll-evidence-review-2026-11-11.json",
    config: "model/config/experimental_forecast.yml"
  };
  const source = {};
  const contents = {};
  for (const [key, path] of Object.entries(paths)) {
    contents[key] = readFileSync(resolve(root, path));
    source[key] = { path, sha256: sha(contents[key]) };
  }
  const districtRows = parseCsv(contents.model.toString("utf8"));
  const chamber = parseCsv(contents.chamber.toString("utf8"));
  const roster = JSON.parse(contents.roster.toString("utf8"));
  const evidence = JSON.parse(contents.evidence.toString("utf8"));
  const config = contents.config.toString("utf8");
  const referenceAsOf = config.match(/^as_of:\s*(\S+)/m)?.[1];
  if (!referenceAsOf || evidence.baselineForecastAsOf !== referenceAsOf) {
    throw new Error("Poll evidence packet is not aligned to reference forecast date; review as a new input vintage");
  }
  if (roster.sourceFileSha256 !==
     "f5c9505d01abb39bfd4e20cd389c6adea2e524a26423c7c82a51084e21d95c16") {
    throw new Error("Candidate roster no longer has audited source workbook; refresh evidence before reporting");
  }
  if (districtRows.length !== 88 || roster.rows.length !== 1037 || chamber.length !== 5) {
    throw new Error("District, chamber or official source universe incomplete");
  }
  const matrix = preferencePriorFromSource(contents.source.toString("utf8"));
  const names = new Map();
  for (const [chamber, contest, _ordinal, candidate, rpp] of roster.rows) {
    if (chamber !== "Assembly") continue;
    const list = names.get(contest) ?? [];
    list.push({ candidate, rpp, family: familyFromRegisteredParty(rpp) });
    names.set(contest, list);
  }
  const allSeats = [], missingFamilyNominees = [], multipleCoalitionNominees = [];
  for (const d of districtRows) {
    const candidates = names.get(d.district_name);
    if (!candidates?.length) throw new Error("Missing nominated candidates: " + d.district_name);
    const counts = Object.fromEntries(PARTIES.map((p) => [p, candidates.filter((c) => c.family === p).length]));
    const odds = Object.fromEntries(PARTIES.map((p) => [p, num(d["win_" + p.toLowerCase()], d.district_name + " " + p)]));
    const primaries = PARTIES.map((p) => num(d["primary_" + p.toLowerCase()], "primary " + p));
    if (Math.abs(primaries.reduce((a, b) => a + b, 0) - 100) > 1e-6)
      throw new Error("District model primaries do not sum to 100: " + d.district_name);
    if (Math.abs(Object.values(odds).reduce((a,b) => a+b, 0) - 1) > 1e-6)
      throw new Error("District win probabilities do not sum to 1: " + d.district_name);
    for (const p of PARTIES) {
      if (counts[p] === 0) {
        missingFamilyNominees.push({ seat: d.district_name, family: p,
          winFrequency: odds[p] });
      }
    }
    if (counts.LIB_NAT > 1) multipleCoalitionNominees.push({ seat: d.district_name, count: counts.LIB_NAT });
    const flags = [];
    if (odds.ONP >= .80) flags.push("onp-win-frequency-at-least-80-percent");
    if (primaries[4] >= 20 && odds.OTH_IND < .01) flags.push("oth-modelled-primary-at-least-20-percent-but-win-below-1-percent");
    if (counts.OTH_IND > 1 && d.likely_final_pair.includes("OTH_IND"))
      flags.push("aggregated-other-family-in-modal-final-pair");
    if (d.district_name === "Pakenham") flags.push("independent-local-poll-available-not-admitted");
    const label = {
      seat: d.district_name,
      region: d.region_name,
      flags,
      modelledWinner: d.favoured_party,
      modelledWinnerFrequency: num(d.favoured_probability, "winner"),
      modalFinalPair: d.likely_final_pair,
      modalFinalPairFrequency: num(d.final_pair_probability, "pair"),
      primaryVote: Object.fromEntries(PARTIES.map((p,i) => [p, primaries[i]])),
      winFrequency: odds,
      candidateFamilyCounts: counts,
      individualOtherCandidates: candidates.filter((c) => c.family === "OTH_IND").map((c)=>c.candidate),
      meanPreferencePath: meanPathCount(primaries, matrix)
    };
    allSeats.push(label);
  }
  const pakenham = allSeats.find((x) => x.seat === "Pakenham");
  const local = evidence.evidence.find((x) => x.id === "pakenham-2026-11-04-08-demosau-primary");
  if (!pakenham || !local || local.modelEligibility !== "hold") throw new Error("Pakenham source or hold decision missing");
  if (evidence.evidence.some((x) => x.modelEligibility !== "hold")) throw new Error("Unreviewed poll admission would change output meaning");
  const onp80 = allSeats.filter((s) => s.winFrequency.ONP >= .8);
  const collapsedOther = allSeats.filter((s) => s.primaryVote.OTH_IND >=20 && s.winFrequency.OTH_IND < .01);
  const otherPair = allSeats.filter((s) => s.modalFinalPair.includes("OTH_IND") && s.candidateFamilyCounts.OTH_IND > 1);
  return {
    schemaVersion: 1,
    status: "frozen-reference-output-diagnostic-not-calibration-or-forecast-refresh",
    source,
    referenceAsOf,
    candidateRosterAsOf: roster.sourceReportAsAt,
    eligibleNewPolls: 0,
    canonicalDataChanged: false,
    statisticalProductionGatesChanged: false,
    counts: {
      assemblyDistricts: allSeats.length,
      missingNominatedPartyFamilies: missingFamilyNominees.length,
      coalitionNomineeDuplicationSeats: multipleCoalitionNominees,
      onpWinFrequencyAtLeast80Percent: onp80.length,
      largeResidualPrimaryNegligibleResidualWins: collapsedOther.length,
      aggregatedOthersAppearInModalFinalTwo: otherPair.length
    },
    candidateAvailability: { allFiveFamilyRepresentativesPerSeat: missingFamilyNominees.length === 0,
      interpretation: "A family having nominated candidates is a necessary condition only; it does not validate model family-level vote share or independence from other nominees." },
    derivedConditionalPreferenceRatios: {
      "coalitionExclusionToOnpWhenOnlyOnpVsAlp": matrix[1][2] / (matrix[1][2] + matrix[1][0]),
      "laborExclusionToCoalitionWhenOnlyCoalitionVsOther": matrix[0][1] / (matrix[0][1] + matrix[0][4]),
      "onpExclusionToCoalitionWhenOnlyCoalitionVsOther": matrix[2][1] / (matrix[2][1] + matrix[2][4]),
      caveat: "Ratios are conditional arithmetic of the fixed five-family matrix at a specified final pair, not population estimates, conditional survey flows or independent empirically calibrated probabilities."
    },
    pakenhamIndependentDiagnostic: {
      sourceId: local.id, sourceUrl: local.sourceUrl, sample:local.reportedSampleSize,
      effectiveSample: local.effectiveSampleSize,
      primaryOnpLocalPoll: local.reportedCandidatePrimaries.onpPickering,
      primaryOnpOctoberReferenceModel: pakenham.primaryVote.ONP,
      gapInPercentagePoints: local.reportedCandidatePrimaries.onpPickering - pakenham.primaryVote.ONP,
      modelledLiberalWinFrequency: pakenham.winFrequency.LIB_NAT,
      pollTwoCandidatePercentOnp: local.reportedTwoCandidatePreferred.onpPickering,
      caveat: "Independent local poll is later, covers a single electorate, has effective N=289 and a modelled rather than surveyed 2CP. This gap is a diagnostic, not a calibrated polling surprise or an authorised statewide update."
    },
    focusSeats: allSeats.filter((s) => s.flags.length).sort((a,b) => a.seat.localeCompare(b.seat)),
    allSeats
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = buildSeatIntegrityAudit();
  const i = process.argv.indexOf("--output");
  if (i >= 0) {
    if (!process.argv[i + 1]) throw new Error("Missing --output filename");
    writeFileSync(resolve(process.argv[i + 1]), JSON.stringify(result,null,2) + "\n");
  }
  console.log(JSON.stringify({
    referenceAsOf:result.referenceAsOf,
    counts:result.counts,
    pakenhamIndependentDiagnostic:result.pakenhamIndependentDiagnostic,
    conditionalPreferenceRatios:result.derivedConditionalPreferenceRatios,
    focusSeats:result.focusSeats.map(s=>({seat:s.seat,flags:s.flags}))
  },null,2));
}
