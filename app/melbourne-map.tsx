"use client";

import { useRef, useState } from "react";
import { parties, partyMeta, type Party } from "./assembly-parties";
import type { modelOutput } from "./model-output.generated";
import map from "./melbourne-map.generated.json";
import "./melbourne-map.css";

type District = (typeof modelOutput.districts)[number];
type Layer = "held" | "contest" | "forecast";
const layers: { id: Layer; label: string }[] = [
  { id: "held", label: "Held going in" },
  { id: "contest", label: "Contest" },
  { id: "forecast", label: "Forecast" },
];
const holder = {
  ALP: { label: "Labor", colour: partyMeta.ALP.colour },
  LIB: { label: "Liberal", colour: partyMeta.LIB_NAT.colour },
  NAT: { label: "Nationals", colour: "#237a86" },
  GRN: { label: "Greens", colour: partyMeta.GRN.colour },
};
const competition = [
  { label: "Under 55%", colour: "#925425" },
  { label: "55% to under 70%", colour: "#d9944d" },
  { label: "70% and above", colour: "#eee0c7" },
];
const percent = (share: number) => new Intl.NumberFormat("en-AU", { style: "percent", maximumFractionDigits: 2 }).format(share);

export default function MelbourneMap({ districts, forecastDate, openDistrict }: {
  districts: readonly District[];
  forecastDate: string;
  openDistrict: (district: District) => void;
}) {
  const [layer, setLayer] = useState<Layer>("held");
  const [zoom, setZoom] = useState(false);
  const [selected, setSelected] = useState("");
  const detailsButton = useRef<HTMLButtonElement>(null);
  const byId = new Map<string, District>(districts.map((district) => [district.district_id, district]));
  const districtOptions = map.map((seat) => {
    const district = byId.get(seat.id);
    return district ? [{ ...seat, district }] : [];
  }).flat().sort((a, b) => a.district.district_name.localeCompare(b.district.district_name, "en-AU"));
  const legend = layer === "held" ? Object.values(holder) : layer === "contest" ? competition : parties.map((party) => partyMeta[party]);

  return <section className="surface metro-map" aria-labelledby="metro-map-title">
    <h2 id="metro-map-title">Greater Melbourne electorate map</h2>
    <p>Tap an electorate to open its forecast, voting history and candidates.</p>
    <div className="metro-map-layers" role="group" aria-label="Map layer">
      {layers.map(({ id, label }) => <button type="button" key={id} aria-pressed={layer === id} onClick={() => setLayer(id)}>{label}</button>)}
    </div>
    <p className="metro-map-note">{layer === "held"
      ? "Party credited with holding the seat entering the election, from the ABC pendulum."
      : layer === "contest"
        ? `How often the leading group wins in simulations from ${forecastDate}. Darker seats are closer contests.`
        : `Group that wins most often in simulations from ${forecastDate}.`}</p>
    <ul className="metro-map-legend" aria-label="Map colour key">
      {legend.map(({ label, colour }) => <li key={label}><i style={{ backgroundColor: colour }} aria-hidden="true" />{label}</li>)}
    </ul>
    <div className="metro-map-tools">
      <button type="button" aria-pressed={zoom} onClick={() => setZoom(!zoom)}>{zoom ? "Show Greater Melbourne" : "Zoom to inner Melbourne"}</button>
      <label>Electorate<select value={selected} onChange={(event) => setSelected(event.target.value)}>
        <option value="">Choose an electorate</option>
        {districtOptions.map(({ id, district }) => <option key={id} value={id}>{district.district_name}</option>)}
      </select></label>
      <button ref={detailsButton} type="button" aria-disabled={!selected} onClick={() => {
        const district = byId.get(selected);
        if (district) openDistrict(district);
      }}>Open seat details</button>
    </div>
    <svg className="metro-map-figure" viewBox={zoom ? "195 255 360 390" : "0 0 724 780"} role="img" aria-label="Geographic map of Greater Melbourne state electorates. Use the electorate selector to open a seat using the keyboard.">
      {districtOptions.map(({ id, path, held, district }) => {
        const current = holder[held as keyof typeof holder];
        const party = partyMeta[district.favoured_party as Party];
        const share = district.favoured_probability;
        const band = competition[share < .55 ? 0 : share < .70 ? 1 : 2];
        const fill = layer === "held" ? current.colour : layer === "contest" ? band.colour : party.colour;
        return <path key={id} d={path} fill={fill} fillRule="evenodd" data-selected={selected === id} onClick={() => {
          setSelected(id);
          detailsButton.current?.focus({ preventScroll: true });
          openDistrict(district);
        }}><title>{district.district_name} · Held by {current.label} · {party.label} wins {percent(share)} of runs</title></path>;
      })}
    </svg>
    <p className="metro-map-note">The map shows the parts of {districtOptions.length} Assembly districts within the Australian Bureau of Statistics’ 2021 Greater Melbourne boundary. District details cover the whole seat.</p>
    <p className="metro-map-note"><a href="https://discover.data.vic.gov.au/dataset/vicmap-admin-state-assembly-polygon-2022">State of Victoria, Vicmap district boundaries</a> · <a href="https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/GCCSA/MapServer">Australian Bureau of Statistics, Greater Melbourne</a> · <a href="https://www.abc.net.au/news/elections/vic/2026/guide/pendulum">ABC election pendulum</a>. Boundaries clipped and simplified · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></p>
  </section>;
}
