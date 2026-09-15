import assert from "node:assert/strict";
import test from "node:test";

import { commandArguments, parseDuration } from "../scripts/run-with-timeout.mjs";

test("portable timeout parses bounded build durations", () => {
  assert.equal(parseDuration("250ms"), 250);
  assert.equal(parseDuration("10s"), 10_000);
  assert.equal(parseDuration("3m"), 180_000);
  assert.throws(() => parseDuration("3"), /Invalid duration/);
});

test("portable timeout keeps the command after the separator intact", () => {
  assert.deepEqual(
    commandArguments(["--timeout", "3m", "--kill-after", "10s", "--", "/tmp/vinext", "build"]),
    { timeoutMs: 180_000, killAfterMs: 10_000, command: "/tmp/vinext", args: ["build"] },
  );
});
