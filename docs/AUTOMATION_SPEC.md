# Victorian Election 2026 Forecasting Platform — Automation Specification

## Purpose

Continuous operation is a first-class subsystem of the project.

The production system must not depend on ChatGPT, a local developer machine, a Codespace remaining open, or an active browser session to remain current.

GitHub is the persistent execution and orchestration environment.

The public browser application should consume validated generated data. It should not scrape upstream sources, execute the election model, hold privileged credentials, or perform production data mutation.

---

## 1. Required automation architecture

Use this architecture:

```text
UPSTREAM SOURCES
      │
      ▼
GitHub Actions scheduler / manual dispatch
      │
      ▼
source acquisition
      │
      ▼
change detection
      │
      ├── unchanged → record successful check → stop affected branch
      │
      └── changed
             │
             ▼
       archive raw source
             │
             ▼
       parser + validation
             │
             ▼
       processed dataset
             │
             ▼
       affected model stages
             │
             ▼
       validation / forecast gate
             │
        PASS │       FAIL
             ▼         │
     publish new       └── retain previous valid forecast
       artefacts             + log/alert failure
             │
             ▼
         web build
             │
             ▼
          deploy
```

---

## 2. Source-state registry

Persist the operational state of every monitored source.

Create a machine-readable source-state registry containing at minimum:

```text
source_id
source_name
source_url
last_checked_at
last_successful_fetch_at
last_changed_at
last_content_hash
last_parser_success_at
data_version
status
staleness_threshold
critical_to_forecast
```

Do not confuse:

- checked;
- changed;
- successfully parsed;
- incorporated into modelling;
- published.

These are separate states.

---

## 3. Change detection before computation

Do not rerun the entire production pipeline merely because a scheduled workflow started.

For each source:

1. request source metadata/content;
2. compare stable identifiers where available:
   - ETag;
   - Last-Modified;
   - release identifier;
   - document checksum;
   - content hash;
3. determine whether there is a material change;
4. record the check;
5. only trigger downstream processing when warranted.

Avoid commits containing timestamp-only noise unless the timestamp itself is an intentionally tracked operational artefact.

---

## 4. Raw source versioning

When a material source changes:

- preserve the previous source version;
- archive the new version;
- assign retrieval metadata;
- calculate checksum;
- retain canonical source URL;
- retain retrieval time;
- preserve enough history to reconstruct previous forecasts where storage permits.

Never overwrite historical raw inputs in a way that makes an old forecast irreproducible.

---

## 5. Incremental pipeline execution

Structure processing as dependency-aware stages.

Example:

```text
new poll
  → polling dataset
  → polling aggregation
  → Assembly forecast
  → Council forecast where relevant
  → hotspots
  → statewide outputs
  → frontend artefacts
```

A candidate announcement should not unnecessarily rerun unrelated ABS ingestion.

A new ABS dataset should not cause upstream polling retrieval to be treated as changed.

A full rebuild must remain available as a manual/debug operation.

---

## 6. Distinguish acquisition from model inclusion

Successfully retrieving information does not automatically make it a production-model input.

Use explicit statuses such as:

```text
discovered
retrieved
validated
accepted
excluded
experimental
production
```

For polling, candidate information, analyst estimates and other non-official material, preserve the distinction between:

- we found this;
- the production model uses this.

Document exclusion reasons.

---

## 7. Forecast immutability on failure

The public application must always prefer the last known valid production forecast over a newly generated invalid forecast.

If any critical validation step fails:

- do not overwrite current production forecast artefacts;
- retain previous production files;
- set model status to degraded/failed;
- report the failing stage;
- report the affected source;
- report last successful forecast timestamp.

Never turn a temporary scraper failure into an apparent political event.

---

## 8. Operational metadata exposed by the app

Expose these separately in the web application:

```text
Sources last checked
Latest source change detected
Latest source successfully processed
Latest production model run
Latest valid forecast
Latest deployment
Model version
Data version
Automation status
```

Do not collapse these into one ambiguous "last updated" timestamp.

---

## 9. Update history / audit view

Provide an Update History or System Status view showing recent automated activity.

Each event should record, where relevant:

```text
timestamp
source
event type
change detected?
records affected
pipeline stages triggered
model rerun?
forecast changed?
validation result
deployment result
commit SHA
```

This should make the system auditable without needing to inspect GitHub Actions logs for routine questions.

---

## 10. Workflow controls

All scheduled workflows must also support:

```yaml
workflow_dispatch:
```

Provide manual controls for:

- check all sources;
- check one source where practical;
- full data rebuild;
- full model rebuild;
- validation-only run;
- deployment;
- historical backtest.

Do not require editing workflow files merely to trigger routine maintenance.

---

## 11. Normal and election-period frequencies

Make monitoring cadence configurable.

Support at least:

### Normal mode

Low-frequency checks suitable when the election is distant.

### Election-period mode

Higher-frequency checks when:

- polling publication frequency increases;
- nominations open/close;
- preference information changes;
- early voting begins;
- election day approaches.

Do not hardcode excessive requests to every source.

Respect upstream rate limits and terms.

---

## 12. Staleness monitoring

Each critical source should have an expected freshness policy.

Examples include:

- polling registry;
- candidate registry;
- VEC election information;
- economic indicators;
- ABS demographic data.

If a critical source exceeds its expected staleness threshold:

- flag it;
- surface status;
- avoid silently treating stale information as current.

Staleness is not necessarily pipeline failure, but it must be visible.

---

## 13. Automated fault reporting

When automation encounters a persistent material problem, such as:

- upstream HTML structure changed;
- parser failed;
- required field disappeared;
- electorate count is no longer 88;
- Council region mapping fails;
- poll values fail validation;
- production forecast gate fails;
- deployment fails;

produce a durable alert.

Prefer GitHub-native mechanisms such as:

- workflow failure annotation;
- GitHub issue;
- structured job summary.

Avoid creating duplicate issues for the same unresolved fault.

Automatically close or mark resolved faults where appropriate once validation succeeds again.

---

## 14. Safe Git strategy

Routine validated data refreshes may be committed automatically where appropriate.

For code-changing automation, parser modifications, schema migrations or uncertain generated corrections:

- create a branch;
- run tests;
- open a pull request;
- do not silently rewrite production code on `main`.

Do not allow an LLM agent to autonomously merge significant code changes into production without validation.

---

## 15. Secrets and authentication

All privileged credentials must remain server-side in GitHub Actions Secrets or other appropriate secret storage.

Never include credentials in:

- frontend JavaScript;
- generated JSON served publicly;
- repository files;
- build logs.

Use minimum required GitHub token permissions for each workflow.

Explicitly define workflow permissions rather than relying unnecessarily on broad defaults.

---

## 16. Reproducible forecast snapshots

Every published production forecast should be reproducible.

Associate a forecast with:

```text
forecast timestamp
Git commit SHA
model version
data version
source manifest/checksums
configuration version
override version
```

Where practical, maintain historical forecast snapshots so model performance can later be assessed prospectively, not reconstructed only after the election.

---

## 17. Prospective model evaluation

Begin saving each genuine production forecast during the campaign.

This is separate from historical backtesting.

The system should retain enough information to later answer:

- what did the model predict on this date?;
- how did probabilities move?;
- which seats changed?;
- what new information caused the change?;
- how well calibrated were forecasts as election day approached?

Do not rewrite historical forecast snapshots after publication.

---

## 18. GitHub-native independence

Verify that after initial configuration the following can occur while the user is offline:

```text
source monitoring
change detection
data retrieval
validation
processing
model execution
forecast gating
artefact generation
website build
deployment
failure reporting
```

No normal production cycle should require:

- ChatGPT to be open;
- a Codespace to remain running;
- a developer laptop;
- an interactive terminal.

ChatGPT or a coding agent may be used to develop and repair the system, but must not be an operational dependency of the finished application.

---

## 19. Automation acceptance test

Before declaring the automation complete, perform an end-to-end simulation.

### Scenario A — nothing changed

Expected result:

```text
sources checked
no material change
no unnecessary processing
no unnecessary forecast commit
workflow succeeds
```

### Scenario B — valid new poll

Expected result:

```text
change detected
raw source archived
poll parsed
validation passes
poll-of-polls updates
forecast reruns
gates pass
new artefacts generated
site deploys
history records change
```

### Scenario C — malformed source

Expected result:

```text
change detected
parser/validation fails
previous valid processed data retained
previous valid forecast retained
failure recorded
no misleading production deployment
```

### Scenario D — broken critical model input

Expected result:

```text
production gate closes
old forecast remains public
status reports degradation
fault is surfaced
```

### Scenario E — successful recovery

Expected result:

```text
source/parser repaired
validation succeeds
fault resolves
forecast pipeline resumes
new valid production forecast deploys
```

The automation is complete only when these behaviours are demonstrated, not merely when workflow YAML exists.
