# Psephology and analyst evidence

The forecast distinguishes **observations** from **analysis of observations**.

A published poll can be a quantitative model observation after validation. An analyst's poll average, seat model or interpretation is usually a transformation of polling and other evidence. Counting both as independent inputs would double-count the same information and create false confidence.

## Core analyst registry

The initial reviewed source set is:

- Antony Green
- Ben Raue / The Tally Room
- Dr Kevin Bonham
- Casey Briggs / ABC Elections
- Kos Samaras / RedBridge-related published analysis
- Mark the Ballot

`metadata/psephology-sources.json` defines the source families. The Tally Room and Ben Raue are deliberately one family. Kos Samaras analysis that relies on RedBridge polling is explicitly dependent on that polling family.

## Evidence classes

The registry is designed to capture evidence such as seat assessments, vote-to-seat models, preference-flow estimates, redistribution interpretation, by-election analysis, demographic and regional patterns, Upper House analysis, poll aggregation and methodological comparisons.

Each structured evidence record must identify its source, publication date, geography, evidence type, upstream evidence, independence assessment, review state and intended model usage.

## Model-use rule

The default is `reference_only` or `comparison_only`.

Poll-derived analyst output **cannot be inserted directly into the forecast as another model observation**. If an analyst uses a RedBridge poll, for example, the forecast may use the underlying validated poll and separately compare the analyst's modelling implications. It must not count both as two independent measurements of voter intention.

A future model contribution must have an explicit transformation, provenance, validation/backtest and approval. This allows analyst work to improve preference priors, uncertainty, seat-specific diagnostics and model comparison without silently overweighting commentary.

## Initial reviewed evidence

The foundation includes reference/comparison records for Ben Raue's July 2026 Victorian vote-to-seat work, Kevin Bonham's July 2026 Victorian polling/seat analysis, Casey Briggs's Nepean by-election analysis and a published Kos Samaras/RedBridge interpretation. These records do not change current forecast weights or outputs.

Antony Green and Mark the Ballot are registered now so subsequent discovery can attach suitable Victoria-specific structured evidence without inventing a second identity for the same source or bypassing review.
