import assert from "node:assert/strict";
import test from "node:test";

test("renders the joint experimental forecast dashboard", async () => {
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
  assert.match(html, /A forecast you can interrogate/);
  assert.match(html, /Hung parliament leads/);
  assert.match(html, /5,000[^<]*<!-- -->?[^<]*correlated simulations/i);
  assert.match(html, /Experimental forecast/i);
});
