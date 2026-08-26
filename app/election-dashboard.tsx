"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownUp,
  BarChart3,
  Check,
  CircleHelp,
  Database,
  FlaskConical,
  MapPinned,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { districts, validationFolds } from "./data.generated";

const regions = [...new Set(districts.map((district) => district.region))].sort();

const validationChart = validationFolds.map((fold) => ({
  cycle: fold.cycle,
  "Uniform-swing baseline": Number(fold.baselineMae.toFixed(2)),
  "Demographic candidate": Number(fold.candidateMae.toFixed(2)),
}));

const number = new Intl.NumberFormat("en-AU");

function Metric({
  icon: Icon,
  value,
  label,
  note,
}: {
  icon: typeof Database;
  value: string;
  label: string;
  note: string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon" aria-hidden="true">
        <Icon size={18} strokeWidth={1.8} />
      </div>
      <div>
        <p className="metric-value">{value}</p>
        <p className="metric-label">{label}</p>
        <p className="metric-note">{note}</p>
      </div>
    </article>
  );
}

function GateNotice() {
  return (
    <section className="gate-notice" aria-labelledby="gate-title">
      <div className="gate-stripe" aria-hidden="true" />
      <div className="gate-icon" aria-hidden="true">
        <AlertTriangle size={22} />
      </div>
      <div className="gate-copy">
        <div className="gate-heading">
          <h2 id="gate-title">Production forecast gate closed</h2>
          <Badge className="gate-badge">No 2026 probabilities published</Badge>
        </div>
        <p>
          The historical data foundation is ready, but the preregistered demographic
          residual model performed worse than the simple baseline. Publishing seat
          probabilities now would create false precision, so this dashboard exposes the
          verified evidence and the failed test instead.
        </p>
      </div>
    </section>
  );
}

function Overview() {
  return (
    <div className="tab-stack">
      <GateNotice />

      <section className="metric-grid" aria-label="Project status">
        <Metric icon={MapPinned} value="88 + 8" label="Districts and regions" note="Current 2022 electoral boundaries" />
        <Metric icon={FlaskConical} value="4 cycles" label="Held-out validation" note="2010, 2014, 2018 and 2022" />
        <Metric icon={ShieldCheck} value="415 / 415" label="Automated tests passed" note="Sealed checkpoint result" />
        <Metric icon={Database} value="118 / 118" label="Sources verified" note="Size and SHA-256 provenance" />
      </section>

      <section className="two-column">
        <article className="surface feature-surface">
          <p className="eyebrow">What the evidence says</p>
          <h2>A useful negative result</h2>
          <p className="lead-copy">
            Housing tenure and age structure are politically plausible—but this frozen
            seven-feature model did not improve whole-election prediction out of sample.
          </p>
          <div className="comparison-line">
            <div><span>Baseline MAE</span><strong>2.78 pp</strong></div>
            <div className="comparison-arrow" aria-hidden="true">→</div>
            <div><span>Candidate MAE</span><strong className="worse">2.81 pp</strong></div>
          </div>
          <p className="fine-print">Winner errors also increased from 21 to 24 across 340 district transitions.</p>
        </article>

        <article className="surface next-surface">
          <p className="eyebrow">Next eligible modelling work</p>
          <h2>Test a genuinely new signal family</h2>
          <ol className="step-list">
            <li><span>1</span><div><strong>Preserve the failed result</strong><p>No post-hoc tuning against the same folds.</p></div></li>
            <li><span>2</span><div><strong>Build independent evidence</strong><p>Candidate, incumbency or contest-structure features.</p></div></li>
            <li><span>3</span><div><strong>Clear a new held-out gate</strong><p>Only then estimate 2026 uncertainty and seats.</p></div></li>
          </ol>
        </article>
      </section>
    </div>
  );
}

function TppBar({ value }: { value: number | null }) {
  if (value === null) return <span className="muted">Not in 2022 ordinary-election file</span>;

  return (
    <div className="tpp-cell">
      <div className="tpp-track" aria-hidden="true">
        <span className="tpp-midline" />
        <span className="tpp-fill" style={{ width: `${value}%` }} />
      </div>
      <strong>{value.toFixed(1)}%</strong>
    </div>
  );
}

function DistrictExplorer() {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("all");
  const [sort, setSort] = useState("marginal");

  const filtered = useMemo(() => {
    const normalisedQuery = query.trim().toLowerCase();
    const selected = districts.filter(
      (district) =>
        (region === "all" || district.region === region) &&
        (!normalisedQuery || district.name.toLowerCase().includes(normalisedQuery)),
    );

    return [...selected].sort((a, b) => {
      if (sort === "name") return a.name.localeCompare(b.name);
      if (sort === "enrolment") return (b.enrolment ?? 0) - (a.enrolment ?? 0);
      return (a.marginFromFifty ?? 999) - (b.marginFromFifty ?? 999);
    });
  }, [query, region, sort]);

  return (
    <div className="tab-stack">
      <section className="explorer-intro">
        <div>
          <p className="eyebrow">Verified reference data</p>
          <h2>District explorer</h2>
          <p>Search all 88 districts. The vote figure is the official 2022 ALP two-party-preferred measure—not a 2026 prediction.</p>
        </div>
        <Badge variant="outline" className="reference-badge">2022 result · June 2026 enrolment</Badge>
      </section>

      <div className="filter-bar">
        <label className="search-field">
          <span className="sr-only">Search districts</span>
          <Search size={17} aria-hidden="true" />
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search a district…" className="border-0 bg-transparent shadow-none focus-visible:ring-0" />
        </label>

        <Select value={region} onValueChange={(value) => setRegion(value ?? "all")}>
          <SelectTrigger className="filter-select" aria-label="Filter by region"><SelectValue placeholder="All regions" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All regions</SelectItem>
            {regions.map((item) => <SelectItem value={item} key={item}>{item}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={sort} onValueChange={(value) => setSort(value ?? "marginal")}>
          <SelectTrigger className="filter-select" aria-label="Sort districts"><ArrowDownUp size={15} /><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="marginal">Closest to 50% in 2022</SelectItem>
            <SelectItem value="name">District name</SelectItem>
            <SelectItem value="enrolment">Largest enrolment</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="result-count" aria-live="polite">{filtered.length} {filtered.length === 1 ? "district" : "districts"}</div>

      <section className="surface district-table-wrap">
        <div className="desktop-table">
          <Table>
            <TableHeader><TableRow><TableHead>District</TableHead><TableHead>Region</TableHead><TableHead>June 2026 enrolment</TableHead><TableHead className="tpp-heading">2022 ALP 2PP</TableHead></TableRow></TableHeader>
            <TableBody>
              {filtered.map((district) => (
                <TableRow key={district.id}>
                  <TableCell className="district-name">{district.name}</TableCell>
                  <TableCell className="region-name">{district.region}</TableCell>
                  <TableCell>
                    {district.enrolment === null ? "—" : number.format(district.enrolment)}
                    {district.enrolmentVariance !== null && <span className="variance">{district.enrolmentVariance >= 0 ? "+" : ""}{district.enrolmentVariance.toFixed(1)}%</span>}
                  </TableCell>
                  <TableCell><TppBar value={district.alpTpp2022} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="mobile-districts">
          {filtered.map((district) => (
            <article className="district-card" key={district.id}>
              <div><h3>{district.name}</h3><p>{district.region}</p></div>
              <dl>
                <div><dt>Enrolment</dt><dd>{district.enrolment === null ? "—" : number.format(district.enrolment)}</dd></div>
                <div><dt>2022 ALP 2PP</dt><dd>{district.alpTpp2022 === null ? "Not available" : `${district.alpTpp2022.toFixed(1)}%`}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <p className="data-note">
        “Closest to 50%” ranks historical ALP-versus-Coalition two-party share. It does not identify every seat’s actual final pair, current holder or 2026 competitiveness. Narracan’s ordinary 2022 row is absent because its supplementary election occurred in 2023.
      </p>
    </div>
  );
}

function Validation() {
  return (
    <div className="tab-stack">
      <section className="explorer-intro">
        <div><p className="eyebrow">Preregistered held-out test</p><h2>Did demographics improve prediction?</h2><p>No. Lower MAE is better; the candidate only beat the baseline in 2014.</p></div>
        <Badge variant="destructive" className="failed-badge">Promotion gate failed</Badge>
      </section>

      <section className="surface chart-surface" aria-labelledby="chart-title">
        <div className="chart-heading">
          <div><h3 id="chart-title">Mean absolute error by held-out election</h3><p>Percentage points · lower is better</p></div>
          <div className="chart-summary"><strong>+0.03 pp</strong><span>candidate pooled MAE</span></div>
        </div>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={validationChart} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d8d6cf" />
              <XAxis dataKey="cycle" tickLine={false} axisLine={false} tick={{ fill: "#42454b", fontSize: 12 }} />
              <YAxis domain={[0, 4]} tickLine={false} axisLine={false} tick={{ fill: "#6d7076", fontSize: 11 }} tickFormatter={(value) => `${value} pp`} />
              <Tooltip cursor={{ fill: "rgba(17, 31, 51, 0.04)" }} formatter={(value) => [`${Number(value).toFixed(2)} pp`]} contentStyle={{ borderRadius: 4, border: "1px solid #cbc8bf", boxShadow: "0 12px 28px rgba(21,27,34,.1)" }} />
              <Legend iconType="square" wrapperStyle={{ fontSize: 12, paddingTop: 14 }} />
              <Bar dataKey="Uniform-swing baseline" fill="#173d64" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Demographic candidate" fill="#dc6a32" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="surface validation-table">
        <Table>
          <TableHeader><TableRow><TableHead>Held-out cycle</TableHead><TableHead>Districts</TableHead><TableHead>Baseline MAE</TableHead><TableHead>Candidate MAE</TableHead><TableHead>Winner errors</TableHead></TableRow></TableHeader>
          <TableBody>
            {validationFolds.map((fold) => (
              <TableRow key={fold.cycle}>
                <TableCell className="district-name">{fold.cycle}</TableCell><TableCell>{fold.districts}</TableCell><TableCell>{fold.baselineMae.toFixed(2)} pp</TableCell><TableCell className={fold.candidateMae < fold.baselineMae ? "better" : "worse-text"}>{fold.candidateMae.toFixed(2)} pp</TableCell><TableCell>{fold.baselineWinnerErrors} → <strong>{fold.candidateWinnerErrors}</strong></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <section className="finding-grid">
        <article><span className="finding-icon no"><AlertTriangle size={17} /></span><div><strong>MAE did not improve</strong><p>2.78 pp baseline versus 2.81 pp candidate.</p></div></article>
        <article><span className="finding-icon no"><AlertTriangle size={17} /></span><div><strong>RMSE did not improve</strong><p>3.69 pp baseline versus 3.72 pp candidate.</p></div></article>
        <article><span className="finding-icon no"><AlertTriangle size={17} /></span><div><strong>Interval constraint failed</strong><p>Candidate uncertainty calibration was materially worse.</p></div></article>
        <article><span className="finding-icon yes"><Check size={17} /></span><div><strong>The process worked</strong><p>A weak model was stopped before publication.</p></div></article>
      </section>
    </div>
  );
}

function Methodology() {
  const stages = [
    ["01", "Canonical data", "Official electoral, enrolment, Census and boundary-alignment sources remain separate from estimates."],
    ["02", "Historical reconstruction", "Four boundary-aligned Assembly outcome cycles and four demographic surfaces are complete."],
    ["03", "Frozen specification", "Seven housing and age features were specified before the final test payload was available."],
    ["04", "Whole-election holdouts", "Each election was held out in turn; the model trained only on the other three cycles."],
    ["05", "Promotion gate", "Accuracy, winner errors and interval calibration had to clear explicit thresholds."],
  ];

  return (
    <div className="tab-stack">
      <section className="method-intro"><p className="eyebrow">Transparent by design</p><h2>How the forecasting laboratory works</h2><p>The project is designed to earn a forecast rather than manufacture one. Observed data, model estimates and uncertainty are kept distinct at every stage.</p></section>

      <section className="method-grid">
        <div className="stage-list">
          {stages.map(([index, title, copy]) => <article key={index}><span>{index}</span><div><h3>{title}</h3><p>{copy}</p></div></article>)}
        </div>
        <aside className="surface integrity-card">
          <div className="integrity-icon"><ShieldCheck size={25} /></div><p className="eyebrow">Sealed checkpoint</p><h3>14 August 2026</h3>
          <dl>
            <div><dt>Repository integrity</dt><dd>OK</dd></div><div><dt>Automated tests</dt><dd>415 passed</dd></div><div><dt>Provenance records</dt><dd>118 verified</dd></div><div><dt>Historical transitions</dt><dd>340 rows</dd></div><div><dt>Forecast distribution</dt><dd>Unauthorised</dd></div>
          </dl>
        </aside>
      </section>

      <section className="surface faq-card"><div className="faq-icon"><CircleHelp size={22} /></div><div><h3>Why not show a “best guess” anyway?</h3><p>A seat projection needs both a central estimate and a defensible error distribution. The checkpoint authorises neither. A visually polished number would still be an unsupported number—and could mislead precisely because it looks authoritative.</p></div></section>
    </div>
  );
}

export function ElectionDashboard() {
  return (
    <main className="site-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <a href="#content" className="brand" aria-label="Victorian Election Forecast home"><span className="brand-mark" aria-hidden="true">V</span><span><strong>Victorian Election</strong><small>Forecasting laboratory · 2026</small></span></a>
          <div className="status-cluster"><span className="status-dot" aria-hidden="true" /><span>Model gate closed</span></div>
        </div>
      </header>

      <div className="content-shell" id="content">
        <section className="page-heading">
          <div><p className="eyebrow">Evidence before prediction</p><h1>Victorian Election Forecast 2026</h1><p className="page-deck">A transparent view of the data, historical testing and decision gates behind the developing Legislative Assembly and Council model.</p></div>
          <div className="snapshot-stamp"><span>Latest verified model checkpoint</span><strong>14 AUG 2026 · 14:55 AEST</strong></div>
        </section>

        <Tabs defaultValue="overview" className="dashboard-tabs">
          <div className="tabs-rail"><TabsList variant="line" className="dashboard-tabs-list" aria-label="Dashboard sections"><TabsTrigger value="overview"><BarChart3 />Overview</TabsTrigger><TabsTrigger value="districts"><MapPinned />Districts</TabsTrigger><TabsTrigger value="validation"><FlaskConical />Validation</TabsTrigger><TabsTrigger value="method"><Database />Method</TabsTrigger></TabsList></div>
          <TabsContent value="overview"><Overview /></TabsContent><TabsContent value="districts"><DistrictExplorer /></TabsContent><TabsContent value="validation"><Validation /></TabsContent><TabsContent value="method"><Methodology /></TabsContent>
        </Tabs>
      </div>

      <footer><div><strong>Victorian Election Forecasting Laboratory</strong><span>Independent · reproducible · fail-closed</span></div><p>Historical reference data are not a current voting-intention forecast.</p></footer>
    </main>
  );
}
