import test from "node:test";
import assert from "node:assert/strict";
import { buildLiveFeed, discoverArticles } from "../scripts/build-analyst-live-feed.mjs";

const source = {
  id: "example",
  displayName: "Example Analyst",
  url: "https://example.test/victoria/",
  titlePattern: "Victoria|Victorian|Newspoll",
};

test("discoverArticles extracts matching article titles, links and dates", () => {
  const html = `
    <article>
      <h2><a href="/2026/10/26/victorian-newspoll/">Victorian Newspoll update</a></h2>
      <time datetime="2026-10-26T08:30:00+11:00">26 October 2026</time>
    </article>
    <article>
      <h2><a href="/2026/10/25/federal-only/">Federal polling note</a></h2>
      <time datetime="2026-10-25">25 October 2026</time>
    </article>`;

  assert.deepEqual(discoverArticles(html, source), [{
    sourceId: "example",
    sourceName: "Example Analyst",
    publishedDate: "2026-10-26",
    title: "Victorian Newspoll update",
    sourceUrl: "https://example.test/2026/10/26/victorian-newspoll/",
    status: "discovered-pending-review",
  }]);
});

test("discoverArticles falls back to dated links when no article markup is available", () => {
  const html = `<main><a href="/2026/10/13/victoria-polls/">Victoria polls: fresh numbers</a><a href="/about/">About</a></main>`;
  const result = discoverArticles(html, source);
  assert.equal(result.length, 1);
  assert.equal(result[0].publishedDate, "2026-10-13");
  assert.equal(result[0].sourceUrl, "https://example.test/2026/10/13/victoria-polls/");
});

test("buildLiveFeed excludes reviewed URLs and preserves recent baseline records when a source fails", async () => {
  const now = new Date("2026-10-29T00:00:00Z");
  const reviewedUrl = "https://example.test/2026/10/28/reviewed-victoria/";
  const fetcher = async () => `
    <article><h2><a href="/2026/10/28/reviewed-victoria/">Reviewed Victoria item</a></h2><time datetime="2026-10-28"></time></article>
    <article><h2><a href="/2026/10/27/new-victoria/">New Victoria item</a></h2><time datetime="2026-10-27"></time></article>`;

  const good = await buildLiveFeed({
    sources: [source],
    reviewedRecords: [{ sourceUrl: reviewedUrl }],
    existing: { records: [{
      sourceId: "baseline",
      sourceName: "Baseline",
      publishedDate: "2026-10-20",
      title: "Existing Victoria lead",
      sourceUrl: "https://baseline.test/2026/10/20/existing/",
      status: "discovered-pending-review",
    }] },
    now,
    fetcher,
  });

  assert.equal(good.refreshStatus.sourcesSucceeded, 1);
  assert.equal(good.records.some((record) => record.sourceUrl === reviewedUrl), false);
  assert.equal(good.records.some((record) => record.title === "New Victoria item"), true);
  assert.equal(good.records.some((record) => record.title === "Existing Victoria lead"), true);

  const failed = await buildLiveFeed({
    sources: [source],
    reviewedRecords: [],
    existing: {
      records: [
        {
          sourceId: "baseline",
          sourceName: "Baseline",
          publishedDate: "2026-10-20",
          title: "Recent baseline",
          sourceUrl: "https://baseline.test/recent",
          status: "discovered-pending-review",
        },
        {
          sourceId: "baseline",
          sourceName: "Baseline",
          publishedDate: "2026-08-01",
          title: "Stale baseline",
          sourceUrl: "https://baseline.test/stale",
          status: "discovered-pending-review",
        },
      ],
    },
    now,
    fetcher: async () => { throw new Error("network down"); },
  });

  assert.equal(failed.refreshStatus.mode, "partial-live-refresh");
  assert.equal(failed.refreshStatus.sourcesFailed, 1);
  assert.deepEqual(failed.records.map((record) => record.title), ["Recent baseline"]);
});
