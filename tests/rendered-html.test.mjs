import assert from "node:assert/strict";
import test from "node:test";

test("renders the evidence-synthesis dashboard", async () => {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  const response = await worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );

  assert.equal(response.status, 200);
  assert.match(
    response.headers.get("content-type") ?? "",
    /^text\/html\b/i,
  );
  const html = await response.text();
  assert.match(html, /<title>Victorian Election Forecast 2026<\/title>/);
  assert.match(html, /A living model, not a single number/);
  assert.match(html, /9[^<]*<!-- -->[^<]*eligible polls/i);
  assert.match(html, /Production gate closed/i);
  assert.match(html, /Polls are one signal/i);
});
