"use client";

import { useRef, useState } from "react";
import { parties, partyMeta, type Party } from "./assembly-parties";
import type { modelOutput } from "./election-eve-release/model-output.generated";
import map from "./melbourne-map.generated.json";
import geography from "./election-state-maps.generated.json";
import "./melbourne-map.css";

type District = (typeof modelOutput.districts)[number];
type Layer = "held" | "contest" | "forecast";
type Scope = "metro" | "assembly" | "council";
const scopes: { id: Scope; label: string }[] = [
  { id: "metro", label: "Greater Melbourne" },
  { id: "assembly", label: "Statewide Assembly" },
  { id: "council", label: "Legislative Council" },
];
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

export default function MelbourneMap({ districts, forecastDate, openDistrict, openCouncil }: {
  districts: readonly District[];
  forecastDate: string;
  openDistrict: (district: District) => void;
  openCouncil: () => void;
}) {
  const [layer, setLayer] = useState<Layer>("held");
  const [scope, setScope] = useState<Scope>("metro");
  const [zoom, setZoom] = useState(false);
  const [selected, setSelected] = useState("");
  const detailsButton = useRef<HTMLButtonElement>(null);
  const byId = new Map<string, District>(districts.map((district) => [district.district_id, district]));
  const metro = scope === "metro";
  const activeLayer = !metro && layer === "held" ? "forecast" : layer;
  const assemblyShapes = metro ? map : geography.assembly.areas.map(area => ({ ...area, held: "" }));
  const districtOptions = assemblyShapes.map((seat) => {
    const district = byId.get(seat.id);
    return district ? [{ ...seat, district }] : [];
  }).flat().sort((a, b) => a.district.district_name.localeCompare(b.district.district_name, "en-AU"));
  const legend = activeLayer === "held" ? Object.values(holder) : activeLayer === "contest" ? competition : parties.map((party) => partyMeta[party]);
  const region = geography.council.areas.find(area => area.id === selected);
  const district = byId.get(selected);

  return <section className="surface metro-map" aria-labelledby="metro-map-title">
    <h2 id="metro-map-title">Victorian electorate maps</h2>
    <div className="metro-map-layers" role="group" aria-label="Map area">
      {scopes.map(({ id, label }) => <button type="button" key={id} aria-pressed={scope === id} onClick={() => {
        setScope(id); setSelected(""); setZoom(false);
      }}>{label}</button>)}
    </div>
    {scope === "council" ? <>
      <p>Victoria elects five Legislative Councillors from each of eight regions.</p>
      <div className="metro-map-tools">
        <label>Council region<select value={selected} onChange={event => setSelected(event.target.value)}>
          <option value="">Choose a region</option>
          {geography.council.areas.map(area => <option key={area.id} value={area.id}>{area.name}</option>)}
        </select></label>
        <button type="button" onClick={openCouncil}>Open Upper House analysis</button>
      </div>
      {region && <p role="status"><strong>{region.name}</strong> · Five Council seats</p>}
      <svg className="metro-map-figure" viewBox={geography.council.viewBox} role="img"
        aria-label="Map of Victoria’s eight Legislative Council regions. The region selector also selects each area.">
        {geography.council.areas.map(area => <path key={area.id} d={area.path} fillRule="evenodd"
          fill={selected === area.id ? "#295970" : "#9dbeca"} data-selected={selected === area.id}
          onClick={() => setSelected(area.id)}><title>{area.name}</title></path>)}
      </svg>
    </> : <>
    <p>Choose an electorate to open its forecast, voting history and candidates.</p>
    <div className="metro-map-layers" role="group" aria-label="Map layer">
      {layers.filter(item => metro || item.id !== "held").map(({ id, label }) => <button type="button" key={id} aria-pressed={activeLayer === id} onClick={() => setLayer(id)}>{label}</button>)}
    </div>
    <p className="metro-map-note">{activeLayer === "held"
      ? "Party credited with holding the seat entering the election, from the ABC pendulum."
      : activeLayer === "contest"
        ? `How often the leading group wins in simulations from ${forecastDate}. Darker seats are closer contests.`
        : `Group that wins most often in simulations from ${forecastDate}.`}</p>
    <ul className="metro-map-legend" aria-label="Map colour key">
      {legend.map(({ label, colour }) => <li key={label}><i style={{ backgroundColor: colour }} aria-hidden="true" />{label}</li>)}
    </ul>
    <div className="metro-map-tools">
      {metro && <button type="button" aria-pressed={zoom} onClick={() => setZoom(!zoom)}>{zoom ? "Show Greater Melbourne" : "Zoom to inner Melbourne"}</button>}
      <label>Electorate<select value={selected} onChange={(event) => setSelected(event.target.value)}>
        <option value="">Choose an electorate</option>
        {districtOptions.map(({ id, district }) => <option key={id} value={id}>{district.district_name}</option>)}
      </select></label>
      <button ref={detailsButton} type="button" aria-disabled={!selected} onClick={() => {
        if (district) openDistrict(district);
      }}>Open seat details</button>
    </div>
    {district && <p role="status"><strong>{district.district_name}</strong> · {partyMeta[district.favoured_party as Party].label} wins
      {" "}{percent(district.favoured_probability)} of experimental runs.</p>}
    <svg className="metro-map-figure" viewBox={metro ? (zoom ? "195 255 360 390" : "0 0 724 780") : geography.assembly.viewBox}
      role="img" aria-label={metro ? "State electorates in Greater Melbourne. Use the electorate selector to open a seat." :
        "All 88 Victorian Assembly districts. Use the electorate selector to open a seat."}>
      {districtOptions.map(({ id, path, held, district }) => {
        const current = holder[held as keyof typeof holder];
        const party = partyMeta[district.favoured_party as Party];
        const share = district.favoured_probability;
        const band = competition[share < .55 ? 0 : share < .70 ? 1 : 2];
        const fill = activeLayer === "held" ? current.colour : activeLayer === "contest" ? band.colour : party.colour;
        return <path key={id} d={path} fill={fill} fillRule="evenodd" data-selected={selected === id} onClick={() => {
          setSelected(id);
          detailsButton.current?.focus({ preventScroll: true });
          openDistrict(district);
        }}><title>{district.district_name}{current ? ` · Held by ${current.label}` : ""} · {party.label} wins {percent(share)} of runs</title></path>;
      })}
    </svg>
    {metro && <p className="metro-map-note">The map shows the parts of {districtOptions.length} Assembly districts within the Australian Bureau of Statistics’ 2021 Greater Melbourne boundary. District details cover the whole seat.</p>}
    </>}
    {metro ? <p className="metro-map-note"><a href="https://discover.data.vic.gov.au/dataset/vicmap-admin-state-assembly-polygon-2022">State of Victoria, Vicmap district boundaries</a> · <a href="https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/GCCSA/MapServer">Australian Bureau of Statistics, Greater Melbourne</a> · <a href="https://www.abc.net.au/news/elections/vic/2026/guide/pendulum">ABC election pendulum</a>. Boundaries clipped and simplified · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></p>
      : <p className="metro-map-note"><a href={geography.source}>© Victorian Electoral Commission boundary archive</a> ·
        {" "}<a href={scope === "assembly" ? "https://discover.data.vic.gov.au/dataset/vicmap-admin-state-assembly-polygon-2022" :
          "https://discover.data.vic.gov.au/dataset/vicmap-admin-state-council-polygon-2022"}>State of Victoria, Vicmap</a>.
        Boundaries simplified · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></p>}
  </section>;
}
