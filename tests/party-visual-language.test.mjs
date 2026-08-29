import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/party-visual-language.css", import.meta.url), "utf8");
const key = readFileSync(new URL("../app/party-visual-key.tsx", import.meta.url), "utf8");

test("One Nation uses orange throughout the app visual language", () => {
  assert.match(css, /--party-one-nation:\s*#e36f14/i);
  assert.match(css, /\[fill="#6e4da0"\].*party-one-nation/s);
});

test("independent and teal-independent remain visually distinct", () => {
  assert.match(css, /--party-independent:/);
  assert.match(css, /--party-teal:/);
  assert.match(css, /teal-independent[\s\S]*linear-gradient/);
  assert.match(key, /Teal-aligned independent/);
  assert.match(key, /remains an independent/i);
});
