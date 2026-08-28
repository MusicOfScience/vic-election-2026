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
  assert.match(html, /5,000[^<]*<!-- -->?[^<]*whole-election simulations/i);
  assert.match(html, /Experimental forecast/i);
  assert.match(html, /What this forecast is saying/i);
  assert.match(html, /How to read the forecast/i);
  assert.match(html, /88 electorates/i);
  assert.match(html, /twelve most uncertain electorates/i);
  assert.match(html, /Three ways a seat becomes a hotspot/i);
  assert.match(html, /Swing history/i);
  assert.match(html, /Data &amp; sources/i);
  assert.match(html, /Skip to forecast navigation/i);
  assert.match(html, /aria-label="Forecast sections"/i);
  assert.match(html, /Party colour key/i);
  assert.match(html, /26 Aug 2026/i);
});
