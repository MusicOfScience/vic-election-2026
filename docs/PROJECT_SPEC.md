# Victorian Election 2026 Forecasting Platform — Project Specification

## Purpose

This repository is the canonical codebase for a production-quality Victorian state election forecasting and election-intelligence platform.

The system must not be reduced to a simple polling dashboard. It should provide a transparent, reproducible and continuously improving model covering:

- all 88 Legislative Assembly electorates;
- all 8 Legislative Council regions;
- statewide voting intention;
- seat-level probabilities and predicted outcomes;
- upper-house modelling;
- hotspot electorates;
- candidate/incumbency effects;
- redistribution effects;
- polling aggregation;
- demographic and geographic inputs;
- historical election results;
- preference flows and TCP/2CP structures;
- uncertainty intervals;
- model diagnostics;
- historical backtesting;
- automated data updating;
- transparent methodology and provenance.

---

## 1. Repository audit

Before substantial changes are made:

1. Read the complete repository structure.
2. Read all README, docs, metadata, manifests, methodology, data dictionaries, tests and workflow files.
3. Identify the current application entrypoint and deployment architecture.
4. Identify all model code and data-processing pipelines.
5. Identify incomplete, placeholder, stub, mocked or disconnected functionality.
6. Run the complete test suite.
7. Build and run the application.
8. Inspect current GitHub Actions workflows.
9. Inspect deployment configuration.
10. Identify any current GitHub Pages deployment failure.

Do not discard working code merely to rewrite it.

Preserve existing provenance and historical work wherever valid.

---

## 2. Repository architecture

Maintain or migrate toward a clear data-first structure where compatible with the existing repository:

```text
app/
data/
  raw/
  processed/
  derived/
metadata/
models/
pipelines/
scripts/
tests/
docs/
.github/
  workflows/
```

Requirements:

- raw source material should remain immutable where practicable;
- processed data must be reproducible from source inputs;
- model outputs must remain separate from source data;
- provenance must exist for every important input;
- manual overrides must be explicit rather than hidden in code;
- metadata should be machine-readable;
- builds must be reproducible.

Do not place important data or modelling assumptions directly inside UI components.

---

## 3. Preserve canonical historical state

The repository may already contain validated canonical project state, test expectations, manifests and provenance artefacts.

Where existing checksums, receipts, manifests or provenance files exist:

- validate them;
- preserve them;
- identify missing source files;
- distinguish historical canonical data from newly acquired live data.

Do not manufacture missing raw data.

If an upstream historical artefact cannot be reacquired, preserve its expected metadata and clearly flag the gap.

---

## 4. Legislative Assembly model

Build or complete a model covering all 88 Victorian Legislative Assembly districts.

Each seat should have a structured record containing, where available:

- electorate name;
- region;
- incumbent;
- incumbent party;
- candidate status;
- 2022 primary vote by party/candidate;
- 2022 TCP/2CP;
- margin;
- redistribution-adjusted baseline;
- predecessor electorate or seat lineage where relevant;
- enrolment;
- demographic variables;
- housing tenure variables;
- renter share;
- mortgage-holder share;
- geographic type;
- urban/suburban/regional/rural classification;
- historical volatility;
- historical election results;
- by-election results where applicable;
- incumbent retirement/new candidate indicator;
- sophomore effect;
- candidate/personal vote effects where defensible;
- independent susceptibility;
- Greens susceptibility;
- One Nation susceptibility;
- preference-flow assumptions;
- current polling implications;
- model probability by party/candidate;
- predicted winner;
- uncertainty.

Do not use statewide uniform swing alone as the final forecasting method.

Uniform swing may be a baseline component, but it must be augmented by seat-level information.

---

## 5. Redistribution

Victorian electoral redistribution effects must be treated explicitly.

Implement a redistribution-aware baseline rather than simply applying current polling to old seat margins.

Where booth-level or geographic transfer data is available:

- use booth or spatial transfer methodology;
- document mappings between old and new electorates;
- preserve lineage;
- quantify estimated redistribution effect;
- provide confidence/quality metadata.

Do not silently treat renamed or redrawn seats as unchanged electorates.

---

## 6. Poll-of-polls

Implement a genuine poll aggregation system.

Do not display only the latest Roy Morgan poll.

Create a polling dataset containing:

- pollster;
- fieldwork start/end;
- publication date;
- sample size;
- mode;
- population;
- ALP;
- Coalition/L-NP;
- Greens;
- One Nation;
- independents;
- others;
- published 2PP/TPP if available;
- undecided treatment where stated;
- source URL;
- retrieval timestamp.

The aggregation model should consider:

- poll recency;
- sample size;
- pollster house effects where estimable;
- methodological differences;
- uncertainty;
- poll clustering;
- trend rather than naïve averaging.

Where only sparse Victorian polling exists, use an explicitly labelled prior rather than pretending precision.

National polling may be used as a contextual predictor only where modelling demonstrates value.

Clearly distinguish:

- Victorian polls;
- national polling signals;
- model-derived estimates.

---

## 7. Additional model inputs

Design the model so diverse predictors can be incorporated and tested rather than hardcoded.

Potential predictors include:

- Victorian state polling;
- federal polling;
- leader approval/satisfaction;
- government approval;
- economic indicators;
- unemployment;
- inflation;
- interest rates;
- mortgage exposure;
- housing tenure;
- rents;
- household income;
- demographic composition;
- education;
- age;
- population growth;
- migration;
- incumbency;
- retirement;
- candidate quality where systematically measurable;
- historical electorate behaviour;
- federal/state voting divergence;
- regional political effects;
- by-election results.

Do not assume every available variable improves prediction.

Use historical validation and backtesting to determine whether predictors belong in the production model.

---

## 8. Historical backtesting

Create a repeatable historical backtesting framework.

Where adequate historical data exists, simulate forecasts from previous Victorian elections using information that would have been available before each election.

Evaluate:

- seat winner accuracy;
- statewide vote error;
- 2PP error;
- Brier score;
- probability calibration;
- log loss where appropriate;
- MAE/RMSE;
- seat-count error;
- regional error;
- performance by seat type.

Compare at minimum:

1. simple uniform swing baseline;
2. polling-only model;
3. polling + fundamentals;
4. seat-level model;
5. final ensemble model.

Do not promote a more complicated model unless it improves out-of-sample performance.

---

## 9. Forecast production gate

Retain an explicit production forecast gate.

The application must distinguish between:

- raw descriptive data;
- experimental model output;
- validated production forecast.

A model should not automatically become the public production forecast merely because code runs.

Create explicit validation criteria, for example:

```text
data validation PASS
poll ingestion PASS
seat mapping PASS
historical backtest PASS
probability calibration PASS
model sanity checks PASS
integration tests PASS
```

Only then may the production forecast artefact be updated.

If a gate fails:

- retain the last valid forecast;
- flag the failure;
- log the reason;
- do not publish misleading new probabilities.

---

## 10. Legislative Council

Implement all 8 Legislative Council regions separately.

Model:

- regional primary votes;
- major-party vote;
- Greens;
- One Nation;
- Legalise Cannabis;
- independents;
- minor parties;
- known candidates;
- preference structures where legally relevant;
- quota probabilities;
- expected seats by party;
- uncertainty.

Reflect Victorian electoral rules applicable to the 2026 election.

Do not assume the former group-voting-ticket system if electoral law has changed.

Electoral-law assumptions must be source-controlled and documented.

Display:

- expected seats;
- probability distribution for seats;
- most likely regional composition;
- statewide Council composition;
- balance-of-power probabilities.

---

## 11. Hotspot system

Create a dynamic hotspot ranking rather than relying only on manually nominated seats.

Score seats using variables such as:

- probability near 50%;
- low margin;
- high polling sensitivity;
- strong independent challenge;
- Greens opportunity;
- One Nation opportunity;
- candidate retirement;
- redistribution disruption;
- unusual preference structure;
- high model uncertainty.

Allow filtering by:

- ALP–Coalition contest;
- Greens contest;
- independent contest;
- One Nation;
- regional;
- metropolitan;
- confidence level.

---

## 12. Automated source monitoring

Build an extensible source registry.

Create a machine-readable configuration such as:

```yaml
sources:
  - id:
    name:
    type:
    url:
    parser:
    update_frequency:
    enabled:
    reliability:
    notes:
```

Sources may include:

- VEC;
- Victorian Electoral Boundaries Commission;
- ABS;
- pollster publications;
- Roy Morgan;
- Resolve;
- RedBridge;
- Freshwater;
- DemosAU;
- YouGov;
- Essential;
- reputable election analysts;
- candidate announcements;
- party websites;
- official election information.

Do not scrape sites in violation of their access rules.

Prefer APIs, CSV, JSON, RSS, downloadable spreadsheets and stable HTML sources.

---

## 13. Update detection

Every data source should use change detection.

For each retrieval:

1. fetch source;
2. calculate hash or compare metadata;
3. determine whether content changed;
4. archive new raw version where appropriate;
5. record retrieval timestamp;
6. record source provenance;
7. validate schema;
8. run parser;
9. update processed dataset only if valid.

Avoid unnecessary commits where nothing changed.

Maintain a changelog containing, where appropriate:

```text
timestamp
source
old version/hash
new version/hash
records changed
model affected
forecast changed?
```

---

## 14. GitHub Actions automation

Create GitHub Actions workflows so the repository can maintain itself.

At minimum create:

### validation.yml

Run on pull request and push:

- lint;
- type checks where applicable;
- unit tests;
- integration tests;
- data-schema validation;
- model smoke tests;
- application build.

### data-update.yml

Run on a schedule and manual dispatch.

Suggested baseline:

```yaml
schedule:
  - cron: "15 20 * * *"
```

Document daylight-saving implications.

The workflow should:

```text
checkout
setup runtime
install dependencies
fetch enabled sources
detect changes
validate raw data
process data
run model
run forecast gates
write derived outputs
run tests
commit only legitimate changed artefacts
push update
```

Use a clear bot commit format such as:

```text
data: automated election update YYYY-MM-DD
```

### deploy.yml

Deploy the web application only after:

- validation succeeds;
- required data exists;
- build succeeds.

Repair any current GitHub Pages deployment configuration.

Do not deploy from a broken or partially validated build.

---

## 15. Event-driven update capability

Scheduled checking is the minimum.

Where source feeds support RSS, APIs or stable release endpoints, structure the system so more frequent checking can later be enabled.

Avoid excessive polling.

The application should show:

- last source check;
- last data change;
- last successful model run;
- current forecast timestamp;
- last successful deployment.

---

## 16. Web application

Create a visually outstanding, mobile-first election intelligence application.

It must work well on:

- phone;
- tablet;
- laptop;
- desktop.

Recommended information architecture:

### Forecast

- projected Assembly seats;
- projected Council composition;
- statewide vote;
- 2PP;
- majority/hung-parliament probabilities;
- uncertainty.

### Polling

- poll-of-polls;
- poll history;
- trends;
- individual polls;
- polling uncertainty.

### Seats

Interactive table/map of all 88 Assembly electorates.

### Seat page

For every electorate:

- baseline;
- current prediction;
- probability;
- swing;
- candidates;
- historical results;
- demographic context;
- model contributors;
- uncertainty;
- source provenance.

### Hotspots

Ranked dynamic battlegrounds.

### Legislative Council

Region-level forecasts and statewide composition.

### Model

Explain:

- inputs;
- methodology;
- validation;
- assumptions;
- uncertainty;
- backtesting.

### Data

Expose source provenance and update timestamps.

---

## 17. Visualisation quality

Treat data visualisation as a core part of the product, not decoration.

Aim for the standard of leading professional election-analysis products.

Use:

- uncertainty bands;
- probability distributions;
- seat ranges;
- trend lines;
- swing visualisations;
- electorate matrices;
- region compositions;
- historical comparisons;
- small multiples where useful.

Avoid:

- gratuitous animation;
- misleading axes;
- false precision;
- excessive colour;
- decorative chartjunk.

Make uncertainty obvious.

The user should be able to distinguish:

- what happened;
- what polling says;
- what the model predicts.

---

## 18. Mobile UX

The application must not merely shrink a desktop layout.

Explicitly test:

- iPhone-width viewport;
- iPad/tablet;
- desktop.

Fix:

- overflow;
- clipped labels;
- unusable maps;
- tiny tap targets;
- horizontal scrolling;
- charts that become unreadable;
- overlapping controls.

---

## 19. Data transparency

Every important number displayed by the application should be traceable.

Provide source metadata wherever practical.

For model output expose:

- model version;
- forecast timestamp;
- major assumptions;
- confidence/uncertainty;
- relevant data freshness.

Never present invented data as sourced data.

---

## 20. Candidate tracking

Create a structured candidate dataset.

Track:

```text
electorate/region
candidate
party
incumbent?
announcement date
source
verified?
last checked
```

Automated discovery may identify possible candidate changes, but uncertain findings should enter a review queue rather than automatically becoming canonical data.

---

## 21. Source confidence

Assign sources appropriate status:

- official;
- primary;
- reputable secondary;
- analyst;
- provisional;
- unverified.

Official VEC/ABS data should not be silently overwritten by an analyst estimate.

---

## 22. Manual overrides

Some election modelling requires judgement.

Create explicit override files rather than embedding judgments in code.

For example:

```yaml
seat_overrides:
candidate_effects:
preference_assumptions:
data_exclusions:
```

Every override should contain:

- reason;
- author/date where relevant;
- source/evidence;
- expiry/review condition.

---

## 23. Model outputs

Create stable machine-readable forecast artefacts, for example:

```text
data/derived/state_forecast.json
data/derived/assembly_forecast.json
data/derived/council_forecast.json
data/derived/hotspots.json
data/derived/model_status.json
```

The frontend should consume these rather than recalculating expensive models in the browser.

---

## 24. Performance

The public site should load quickly.

Do expensive computation during the update/build pipeline where possible.

The browser should primarily:

- retrieve generated datasets;
- filter;
- sort;
- visualise;
- interact.

Do not make every visitor rerun the election model.

---

## 25. Failure handling

Design graceful failure.

If an upstream source disappears or changes format:

- do not wipe existing data;
- log the failed source;
- retain last known valid data;
- mark its age;
- continue processing unaffected datasets where safe;
- fail the forecast production gate if the missing source materially compromises the model.

---

## 26. Security

Never commit secrets.

Use GitHub Actions Secrets for:

- API keys;
- tokens;
- authenticated services.

Audit the repository for accidental credentials.

Do not expose privileged GitHub tokens in frontend JavaScript.

---

## 27. Tests

Build substantial automated coverage.

Include tests for:

- source parsers;
- data schemas;
- electorate count = 88;
- Council region count = 8;
- party-vote totals;
- probability totals;
- seat lineage;
- redistribution mappings;
- preference calculations;
- model determinism where expected;
- missing-source behaviour;
- malformed source data;
- production forecast gates;
- UI build;
- deployment.

Add regression tests for every defect discovered during development.

---

## 28. Documentation

Update README so another developer can understand:

- what the project does;
- architecture;
- installation;
- development;
- data pipeline;
- model;
- scheduled updating;
- GitHub Actions;
- deployment;
- adding a new source;
- adding a new poll;
- handling candidate updates;
- troubleshooting.

Create or update:

```text
docs/ARCHITECTURE.md
docs/MODEL.md
docs/DATA_SOURCES.md
docs/AUTOMATION.md
docs/DEPLOYMENT.md
docs/BACKTESTING.md
```

---

## 29. Repair the current live site

The live site may currently over-emphasise a Roy Morgan result rather than the intended aggregate forecasting system.

Correct this.

The live product must not imply that Roy Morgan alone is the forecast.

It should expose the full model and polling aggregation system.

Also investigate and repair any GitHub Pages 404, build or deployment failures.

Verify the actual deployed URL with an HTTP request after deployment.

---

## 30. Work autonomously

For each issue:

```text
inspect
diagnose
implement
test
review
refine
```

Do not stop after identifying problems.

Do not ask the user to manually perform coding steps that the coding agent can perform itself.

Do not claim something is complete merely because code was generated.

Completion requires verification.

---

## 31. Final verification

Before declaring completion:

1. clean install from repository;
2. run all tests;
3. run full data pipeline;
4. run historical backtests;
5. run forecast gate;
6. build frontend;
7. test mobile viewport;
8. test desktop viewport;
9. execute update workflow;
10. execute deployment workflow;
11. verify live URL;
12. inspect browser console for errors;
13. inspect GitHub Actions status;
14. confirm all 88 Assembly seats are represented;
15. confirm all 8 Council regions are represented;
16. confirm polling aggregation is operating;
17. confirm source/update timestamps;
18. confirm forecast outputs are reproducible.

Then provide a concise completion report containing:

- changes made;
- bugs repaired;
- tests run and results;
- model status;
- backtesting status;
- automation status;
- deployment status;
- live URL;
- remaining limitations;
- recommended next improvements.

Do not conceal unresolved problems.

The objective is not merely to make the repository compile.

The objective is to create a credible, transparent, continuously updating Victorian election forecasting and election-intelligence platform whose modelling can be examined, tested and improved over time.
