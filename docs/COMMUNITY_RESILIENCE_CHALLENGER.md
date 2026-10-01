# Community resilience / service-deficit challenger

**Status:** experimental research specification  
**Central model weight:** 0  
**Production use:** forbidden pending independent replication and sealed historical validation  
**Created:** 2026-10-01

## Why this exists

Kos Samaras' 1 October 2026 article, *The One Nation vote is a map of government neglect*, links the Zurich Australian Resilience Index to RedBridge/Accent's May 2026 federal MRP. The article reports a strong association between health resilience and the MRP One Nation vote and uses Meadow Heights, Craigieburn, Mickleham and Wallan as Victorian examples of places where financial, health, social and service pressures accumulate.

This is useful as a **hypothesis generator**, not as evidence that the causal claim is established.

The project therefore creates a separate challenger family:

`community_resilience_service_deficit`

The challenger must remain distinct from:

1. RedBridge/Accent polling observations;
2. Samaras' analyst commentary;
3. the existing rejected demographic challenger; and
4. the central 2026 forecast.

No forecast probability, primary-vote estimate, preference parameter or seat probability changes merely because this hypothesis is recorded.

## Research question

Does accumulated household/community vulnerability explain incremental variation in Victorian electoral behaviour after accounting for conventional demographic, geographic and historical electoral predictors?

The target concept is **political availability / electoral volatility**, not a presupposed party effect.

Potential manifestations include:

- changes in major-party primary vote;
- support for minor parties or independents where they are on the ballot;
- fragmentation / effective number of contenders;
- turnout and informal voting;
- anti-incumbent movement;
- preference-flow changes; and
- contest-specific final-two composition.

A One Nation-specific relationship may be tested where ballot availability permits it, but it must not define the challenger.

## Why the Zurich score is not a direct model input

Zurich describes four resilience domains at SA2 level: financial, health, social and environmental. The published material identifies example variables and relative categories, but does not currently expose a complete downloadable SA2 table, full weighting recipe or enough model diagnostics to independently reproduce the index.

There is also an important dependency issue. The index includes proprietary RedBridge/Accent field-survey data, while the article tests the index against a RedBridge/Accent MRP. That does not prove target leakage, but it means the reported electoral association is not an independent validation result.

Accordingly:

- do **not** scrape or infer hidden Zurich scores;
- do **not** translate the reported 63% association into a model coefficient;
- do **not** count the article as another polling observation;
- do **not** use 2026 resilience measurements in historical election replays unless the underlying component is demonstrably time-appropriate.

## Transparent Victorian analogue

Build a public-data analogue at SA2 level and preserve each component separately before any composite is considered.

### Financial buffer

Candidate variables:

- household income distribution;
- unemployment / labour-force non-participation;
- housing tenure;
- mortgage and rent stress;
- reliance on government payments;
- household debt or defensible local proxies;
- emergency-buffer proxies where a reusable source exists;
- insurance penetration only if geographically valid, reusable and independent of the target election evidence.

### Health burden and access

Candidate variables:

- long-term health conditions;
- need for assistance;
- smoking;
- obesity / physical inactivity where historically and geographically valid;
- GP and primary-care access;
- hospital and emergency-care access;
- mental-health service access.

Raw facility counts within a fixed radius should not be used without density and population controls. Prefer travel time, service capacity or per-capita accessibility measures where feasible.

### Social resilience

Candidate variables:

- volunteering;
- community participation;
- residential stability;
- single-parent households;
- social isolation / belonging where a historically valid source exists;
- crime victimisation or defensible local proxies.

### Built environment / service deficit

Candidate variables:

- commute duration and car dependence;
- public-transport accessibility;
- distance/travel time to essential services;
- open-space access;
- growth-corridor population change;
- infrastructure provision relative to population growth;
- broadband / communications access;
- emergency-service accessibility.

## Geography

Use SA2 as the working unit where source data permit it.

Translate SA2 measures into the relevant Victorian Assembly geography through the project's governed geography stack rather than suburb-name matching. Where an SA2 crosses district boundaries, use population-weighted or smaller-area crosswalks consistent with the canonical ABS/VEC geography pipeline.

Boundary changes must be handled cycle-by-cycle in historical replays.

## Historical validation and leakage discipline

The existing walk-forward rule applies without exception:

> each historical cycle may use only evidence available on or before that cycle's information cutoff.

The relevant cycles are 2010, 2014, 2018 and 2022.

A current 2026 SA2 measurement cannot be back-projected into those cycles simply because the underlying concept is structurally plausible. Historical versions, contemporaneous Census measures or defensible time-aligned proxies are required.

The first test should therefore be **incremental prediction over a baseline**, not recreation of Zurich's 2026 ranking.

## Challenger construction

Start with component variables, not a single hand-weighted resilience score.

Recommended sequence:

1. standardise component variables within cycle;
2. inspect missingness, skew and geographic clustering;
3. quantify collinearity with SEIFA and existing demographic variables;
4. fit regularised or partially pooled challenger specifications;
5. retain domain-level coefficients/importance rather than collapsing prematurely;
6. test interactions only when they have a pre-specified mechanism.

Priority interactions worth testing include:

- growth corridor × housing stress;
- growth corridor × commute burden;
- financial stress × health access;
- financial stress × social isolation;
- service deficit × population growth;
- incumbent tenure × accumulated local stress.

Interactions are hypotheses, not guaranteed additions.

## Outcomes and controls

To distinguish resilience from generic socioeconomic disadvantage, compare against at least:

- SEIFA or equivalent socioeconomic baseline;
- age structure;
- education;
- housing tenure;
- migrant / language composition;
- urbanity/remoteness;
- population growth;
- prior electoral result and prior swing;
- incumbent/candidate state;
- party ballot availability.

The challenger should be evaluated on multiple electoral outcomes rather than optimised to a single party's vote.

## Promotion test

This feature family inherits the project's fail-closed approach.

It remains at zero central weight unless a **pre-specified sealed test** shows material incremental value across historical cycles.

At minimum examine:

- MAE / RMSE for district primary vote where comparable;
- Brier score and log loss for probabilistic outcomes;
- winner/final-pair accuracy where appropriate;
- calibration;
- performance by metropolitan, growth-corridor and regional contest type;
- stability across cycles;
- sensitivity to alternative domain constructions;
- degradation in seats or cohorts not expected to respond to the mechanism.

One strong fold is insufficient. A result that merely re-encodes SEIFA is insufficient.

## Specific replication target from the Samaras article

The article's reported 63% health-resilience association should be treated as an external claim to replicate, not a benchmark the Victorian model should be forced to match.

Replication requires, at minimum:

- the exact dependent variable definition;
- electorate-level MRP values or another auditable target;
- full resilience scores or a transparent reconstruction;
- model form;
- weighting;
- controls;
- uncertainty intervals;
- residual diagnostics; and
- sensitivity to urban density, age, income, education, housing tenure, regionality and other plausible confounders.

Until those are available, the claim remains **hypothesis-generating evidence**.

## Decision states

- **REFERENCE_ONLY:** current state. Analyst claim recorded with dependency labels.
- **CHALLENGER_READY:** transparent Victorian feature table built and provenance-complete.
- **VALIDATION_ONLY:** historical replay can run leakage-safely.
- **REJECTED:** no stable incremental value, or effect collapses under controls.
- **CANDIDATE_FOR_MODEL:** sealed test passes and effect is interpretable and stable.
- **MODEL_INPUT:** requires separate explicit approval; never follows automatically from a challenger result.

## Immediate implementation order

1. Register the Samaras article as dependency-labelled analyst evidence.
2. Inventory reusable public SA2 variables by domain and historical availability.
3. Build a source/provenance table before constructing any composite.
4. Create time-aligned SA2 → Assembly crosswalk outputs for each validation cycle.
5. Run univariate diagnostics and collinearity checks against existing demographic predictors.
6. Freeze the challenger specification.
7. Run the four-cycle sealed promotion test.
8. Record acceptance or rejection without altering the central forecast unless separately authorised.

## Primary references

- Kos Samaras, “The One Nation vote is a map of government neglect”, *Pearls and Irritations*, 1 October 2026: https://johnmenadue.com/post/2026/10/the-one-nation-vote-is-a-map-of-government-neglect/
- Zurich Australia, “The Australian Resilience Index”: https://www.zurich.com.au/latest-news/australian-resilience-index
- Zurich Australia, launch release, 29 September 2026: https://www.zurich.com.au/latest-news/media-releases/2026/2026-09-29-australian-resilience-index
