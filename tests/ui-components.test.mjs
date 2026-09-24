import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const vite = await createServer({
  appType: "custom",
  configFile: false,
  root,
  resolve: { alias: { "@": root } },
  server: { middlewareMode: true },
});

after(async () => {
  await vite.close();
});

async function readCssTree(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const contents = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        return readCssTree(entryPath);
      }
      return entry.name.endsWith(".css") ? readFile(entryPath, "utf8") : "";
    }),
  );
  return contents.join("\n");
}

test("emits responsive dashboard and accessibility utilities", async () => {
  const css = await readCssTree(path.join(root, "dist"));

  assert.match(css, /scrollbar-width:\s*none/);
  assert.match(css, /\.forecast-hero/);
  assert.match(css, /\.model-layer-grid/);
  assert.match(css, /\.polling-layout/);
  // Lightning CSS modernises max-width media queries in the production bundle.
  assert.match(css, /@media\s*\((?:max-width:\s*650px|width<=650px)\)/);
  assert.match(css, /prefers-reduced-motion:\s*reduce/);
  assert.match(css, /\.skip-link/);
  assert.match(css, /\.tabs-scroll-cue/);
  assert.match(css, /\.seat-tile\{height:48px/);
});

test("forwards progress semantics to the primitive", async () => {
  const { Progress } = await vite.ssrLoadModule("/components/ui/progress.tsx");
  const html = renderToStaticMarkup(React.createElement(Progress, { value: 37 }));

  assert.match(html, /aria-valuenow="37"/);
  assert.match(html, /aria-valuetext="37%"/);
  assert.match(html, /data-state="loading"/);
});

test("emits chart themes for the starter's media dark mode", async () => {
  const { ChartStyle } = await vite.ssrLoadModule("/components/ui/chart.tsx");
  const html = renderToStaticMarkup(
    React.createElement(ChartStyle, {
      id: "contract",
      config: {
        latency: { theme: { light: "#ffffff", dark: "#000000" } },
      },
    }),
  );

  assert.match(html, /\[data-chart=contract\]/);
  assert.match(html, /@media \(prefers-color-scheme: dark\)/);
  assert.doesNotMatch(html, /\.dark/);
});

test("renders sidebar skeletons deterministically", async () => {
  const { SidebarMenuSkeleton } = await vite.ssrLoadModule(
    "/components/ui/sidebar.tsx",
  );
  const first = renderToStaticMarkup(React.createElement(SidebarMenuSkeleton));
  const second = renderToStaticMarkup(React.createElement(SidebarMenuSkeleton));

  assert.equal(first, second);
  assert.match(first, /--skeleton-width:70%/);
});

test("ships comparable historical swing series for the current districts", async () => {
  const { historicalDistricts } = await vite.ssrLoadModule(
    "/app/historical-data.generated.ts",
  );
  const albertPark = historicalDistricts.find(
    (district) => district.districtId === "albert-park",
  );

  assert.equal(historicalDistricts.length, 87);
  assert.equal(albertPark.cycles.length, 5);
  assert.equal(albertPark.cycles.at(-1).cycle, "2018–22");
  assert.equal(albertPark.cycles.at(-1).comparison, "Estimated on 2022 boundaries");
});

test("ships official ordinary-booth results without mixing in vote modes", async () => {
  const { boothData } = await vite.ssrLoadModule(
    "/app/booth-data.generated.ts",
  );
  const brunswick = boothData.districts.find(
    (district) => district.districtId === "brunswick",
  );
  const narracan = boothData.districts.find(
    (district) => district.districtId === "narracan",
  );
  const allBooths = boothData.districts.flatMap((district) => district.booths);

  assert.equal(boothData.districts.length, 88);
  assert.equal(allBooths.length, 1729);
  assert.ok(brunswick.booths.some((booth) => booth.name === "Blyth"));
  assert.ok(allBooths.every((booth) => !/postal|early|absent|provisional/i.test(booth.name)));
  assert.equal(narracan.status, "supplementary-election-source-required");
});

test("keeps the majority label in a high-contrast capsule above the columns", async () => {
  const { MajorityMarkerLabel } = await vite.ssrLoadModule(
    "/app/election-dashboard.tsx",
  );
  const html = renderToStaticMarkup(
    React.createElement(MajorityMarkerLabel, {
      viewBox: { x: 220, y: 40, width: 0, height: 210 },
    }),
  );

  assert.match(html, /45 SEATS · MAJORITY/);
  assert.match(html, /fill="#fffdf8"/);
  assert.match(html, /translate\(220, 13\)/);
});

test("ships the Batch 6 navigation and chart accessibility pass", async () => {
  const { ElectionDashboard } = await vite.ssrLoadModule(
    "/app/election-dashboard.tsx",
  );
  const html = renderToStaticMarkup(React.createElement(ElectionDashboard));

  assert.match(html, /Skip to forecast navigation/);
  assert.match(html, /aria-label="Forecast sections"/);
  assert.match(html, /Party colour key/);
  assert.match(html, /majority threshold is 45 seats/);
  assert.match(html, /26 Aug 2026/);
  assert.match(html, /Experimental forecast snapshot from 26 Aug 2026/);
  assert.match(html, /Snapshot date/);
  assert.doesNotMatch(html, /updated 26 August/);
});

test("ships a complete checksummed source-provenance registry", async () => {
  const { sourceProvenance } = await vite.ssrLoadModule(
    "/app/source-provenance.generated.ts",
  );
  const artifacts = sourceProvenance.sources.flatMap((source) => source.artifacts);

  assert.equal(sourceProvenance.summary.sourceGroups, 9);
  assert.equal(sourceProvenance.summary.officialSourceGroups, 7);
  assert.equal(sourceProvenance.summary.tracedArtifacts, 22);
  assert.equal(sourceProvenance.summary.automationStatus, "scheduled-freshness-monitoring");
  assert.equal(artifacts.length, 22);
  assert.ok(artifacts.every((artifact) => /^[a-f0-9]{64}$/.test(artifact.sha256)));
  assert.equal(new Set(sourceProvenance.sources.map((source) => source.id)).size, 9);
});

test("ships explicit fail-closed release gates", async () => {
  const { releaseReadiness } = await vite.ssrLoadModule(
    "/app/release-readiness.generated.ts",
  );
  const { DataSources } = await vite.ssrLoadModule("/app/election-dashboard.tsx");
  const html = renderToStaticMarkup(React.createElement(DataSources));

  assert.equal(releaseReadiness.status, "experimental-blocked");
  assert.equal(releaseReadiness.gates.sourceIntegrity.passed, true);
  assert.equal(releaseReadiness.gates.criticalSourceFreshness.passed, false);
  assert.equal(releaseReadiness.sources.find((source) => source.id === "vec-2026-enrolment")?.stale, false);
  assert.equal(releaseReadiness.sources.find((source) => source.id === "vic-2026-poll-registry")?.stale, true);
  assert.equal(releaseReadiness.gates.productionAuthorisation.passed, false);
  assert.equal(releaseReadiness.automation.automaticProductionPublish, false);
  assert.match(html, /Automation may check the work/i);
  assert.match(html, /Experimental · gate closed/i);
  assert.match(html, /Immutable forecast snapshots/);
  assert.match(html, /2 recorded/);
  assert.match(html, /Historical VEC results are available—but they are outcomes/);
  assert.match(html, /Narracan supplementary result stays outside the November 2022 cycle/);
  assert.match(html, /Historical replay readiness/);
  assert.match(html, /1\/4 cycles runnable/);
});

test("renders the governed candidate review dossier without implying nomination", async () => {
  const { CandidateReviewDossier } = await vite.ssrLoadModule(
    "/app/candidate-review-dossier.tsx",
  );
  const html = renderToStaticMarkup(React.createElement(CandidateReviewDossier));

  assert.match(html, /194 candidate records now cover all 88 Assembly districts/i);
  assert.match(html, /Approval recorded/i);
  assert.match(html, /88\/88/);
  assert.match(html, /Assembly coverage is complete/i);
  assert.match(html, /does not make a candidate VEC-nominated/i);
});

test("generates the public poll series from the canonical model registry", async () => {
  const { pollSeries } = await vite.ssrLoadModule("/app/poll-data.generated.ts");

  assert.equal(pollSeries.length, 12);
  assert.equal(pollSeries.at(-1).id, "roy_morgan_2026-08");
  assert.ok(pollSeries.every((poll) => Math.abs(poll.alp + poll.coalition + poll.onp + poll.greens + poll.other - 100) < .01));
  assert.ok(pollSeries.every((poll) => poll.verificationStatus === "verified" || poll.verificationStatus === "partially_verified"));
});

test("ships Batch 3 polling and electorate diagnostics", async () => {
  const { modelOutput } = await vite.ssrLoadModule("/app/model-output.generated.ts");
  const seat = modelOutput.districts[0];

  assert.deepEqual(Object.keys(modelOutput.manifest.polling.sensitivity_by_half_life_days), ["21", "45", "90"]);
  assert.ok(seat.effective_contenders >= 1);
  assert.ok(seat.win_entropy >= 0 && seat.win_entropy <= 1);
  assert.ok(Number.isFinite(seat.baseline_alp));
  assert.ok(Number.isFinite(seat.change_alp));
});

test("ships Batch 4 Upper House uncertainty diagnostics", async () => {
  const { modelOutput } = await vite.ssrLoadModule("/app/model-output.generated.ts");
  const region = modelOutput.councilRegions[0];

  assert.equal(modelOutput.councilRegions.length, 8);
  assert.ok(region.effective_outcomes >= 1);
  assert.ok(region.outcome_entropy >= 0 && region.outcome_entropy <= 1);
  assert.ok(region.at_least_one_alp >= 0 && region.at_least_one_alp <= 1);
  assert.ok(Number.isFinite(region.primary_alp));
  assert.ok(modelOutput.manifest.council.major_party_no_control_probability >= 0);
});
