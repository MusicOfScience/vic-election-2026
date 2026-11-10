"use client";

import { useMemo, useState } from "react";
import { modelOutput } from "./model-output.generated";
import campaignStatus from "./campaign-status.generated.json";
import historicalStatus from "../model/data/validation/historical-replays/historical-four-cycle-validation-status.json";

type Party = "ALP" | "LIB_NAT" | "ONP" | "GRN" | "OTH_IND";
const families: { id: Party; label: string }[] = [
  { id: "ALP", label: "Labor" },
  { id: "LIB_NAT", label: "Coalition" },
  { id: "ONP", label: "One Nation" },
  { id: "GRN", label: "Greens" },
  { id: "OTH_IND", label: "Others / independents" },
];
const probabilityFor = (d: (typeof modelOutput.districts)[number], party: Party): number => {
  if (party === "ALP") return d.win_alp;
  if (party === "LIB_NAT") return d.win_lib_nat;
  if (party === "ONP") return d.win_onp;
  if (party === "GRN") return d.win_grn;
  return d.win_oth_ind;
};
const chamberMean = new Map<string, number>(modelOutput.chamber.map((p) => [p.party, p.mean]));
const decimal = (v: number) => v.toFixed(2);
const percent = (p: number) => `${(100 * p).toFixed(1)}%`;

/**
 * Independent, model-output-only audit. This is an arithmetic diagnostic,
 * not a new forecast, an empirical calibration claim or a scenario rerun.
 */
export function PredictionAudit() {
  const [region, setRegion] = useState("all");
  const regionNames = useMemo(() =>
    [...new Set(modelOutput.districts.map((d) => d.region_name))].sort(), []);
  const diagnostic = useMemo(() => {
    const seats = modelOutput.districts.filter((d) => region === "all" || d.region_name === region);
    const expected = families.map((family) => ({
      ...family,
      seats: seats.reduce((sum, d) => sum + probabilityFor(d, family.id), 0),
      chamberMean: chamberMean.get(family.id),
    }));
    const nonModalExpectation = seats.reduce((sum, d) => sum + (1 - d.favoured_probability), 0);
    const contested = [...seats]
      .sort((a, b) => a.favoured_probability - b.favoured_probability || a.district_name.localeCompare(b.district_name))
      .slice(0, 6);
    const totalExpected = expected.reduce((sum, family) => sum + family.seats, 0);
    const maximumReconciliationDifference = Math.max(...expected.map((p) => Math.abs(p.seats - (p.chamberMean ?? p.seats))));
    return { seats, expected, nonModalExpectation, contested, totalExpected, maximumReconciliationDifference };
  }, [region]);
  const entireState = region === "all";
  const gates = campaignStatus.readiness.summary;
  const reportedAt = modelOutput.manifest.as_of;

  return <section className="surface prediction-audit" aria-label="Prediction diagnostics and statistical limits">
    <div className="prediction-audit-heading">
      <div>
        <p className="eyebrow">Inspect the forecast, not just its headline</p>
        <h3>Prediction audit</h3>
        <p>Explore expected electorate contributions and where the model most frequently changes its mind. These are diagnostics of the existing simulations, not additional independently calibrated forecasts.</p>
      </div>
      <span className="prediction-audit-stage">Experimental · {gates.passedRequiredGates}/{gates.requiredGateCount} gates</span>
    </div>
    <div className="prediction-audit-limit" role="note">
      <strong>Important uncertainty boundary</strong>
      <p>These model frequencies are not empirically certified probabilities. The original 2026 forecast does not use the official nominated-candidate ballot mask, and its Others/independents category aggregates separate candidates. The last generated model is dated {reportedAt}. Newer nominations or polling do not change these numbers until separately reviewed and admitted.</p>
    </div>
    <div className="prediction-audit-filter">
      <label htmlFor="prediction-region">Explore Assembly electorate contributions</label>
      <select id="prediction-region" value={region} onChange={(event) => setRegion(event.target.value)}>
        <option value="all">All 88 districts</option>
        {regionNames.map((name) => <option key={name} value={name}>{name}</option>)}
      </select>
    </div>
    <div className="prediction-audit-metrics">
      <article><span>Districts in view</span><strong>{diagnostic.seats.length}</strong><small>Assembly only, not Council seats</small></article>
      <article><span>Expected non-modal winners</span><strong>{decimal(diagnostic.nonModalExpectation)}</strong><small>Sum of (1 − leading-party probability), not the probability of this many surprises</small></article>
      <article><span>Probability mass reconciles to</span><strong>{decimal(diagnostic.totalExpected)}</strong><small>Should equal the number of districts shown; arithmetic check only</small></article>
    </div>
    <div className="prediction-audit-columns">
      <div>
        <h4>Expected Assembly seats by party</h4>
        <table className="prediction-audit-table">
          <thead><tr><th scope="col">Party family</th><th scope="col">From district chances</th>{entireState && <th scope="col">Simulated mean</th>}</tr></thead>
          <tbody>{diagnostic.expected.map((p) => <tr key={p.id}>
            <th scope="row">{p.label}</th><td>{decimal(p.seats)}</td>{entireState && <td>{p.chamberMean == null ? "Unavailable" : decimal(p.chamberMean)}</td>}
          </tr>)}</tbody>
        </table>
        {entireState && <p className="prediction-audit-caption">
          {diagnostic.maximumReconciliationDifference <= .15
            ? "Cross-check: district win probabilities reconcile closely with statewide simulated seat means (rounding may differ)."
            : "Attention: district win probabilities and chamber simulated means do not reconcile within 0.15 seats; inspect generated outputs before relying on this view."}
        </p>}
        <p className="prediction-audit-caption">An expected seat count is the sum of individual seat-winning probabilities. It is not a predicted integer seat total or a 80% interval. Correlated electoral outcomes mean these totals cannot be converted into a majority probability by multiplying independent seat chances.</p>
      </div>
      <div>
        <h4>Six least-settled seats in this view</h4>
        <ol className="prediction-audit-uncertain">
          {diagnostic.contested.map((seat) => <li key={seat.district_id}>
            <span>{seat.district_name}</span>
            <strong>{percent(seat.favoured_probability)}</strong>
            <small>Top-party model frequency</small>
          </li>)}
        </ol>
        <p className="prediction-audit-caption">Ranking is based only on each district&apos;s leading-party win frequency, not observed electoral volatility, uncertainty in the input polls, or an independent judgement of ballot composition.</p>
      </div>
    </div>
    <div className="prediction-audit-method">
      <h4>What would make these numbers more credible?</h4>
      <p><strong>Verified final ballot:</strong> 734 Assembly and 303 Council candidates must be reconciled and approved before being described as modelled. <strong>Fresh poll evidence:</strong> post-31-October waves need sample-family and source review. <strong>Preference realism:</strong> resolving individual minor-party and independent candidates improved historical final-pair modelling but failed the stronger winner-calibration gate. <strong>Independent calibration:</strong> only {historicalStatus.certifyingScoredCycles} of the required four historical cycles are certifying; 2018 cannot be restored retrospectively.</p>
      <p className="prediction-audit-caption">Current gate status was assessed on {campaignStatus.readiness.assessedAsOf}. A technical consistency check never changes production authorisation.</p>
    </div>
  </section>;
}
