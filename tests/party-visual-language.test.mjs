import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/party-visual-language.css", import.meta.url), "utf8");
const key = readFileSync(new URL("../app/party-visual-key.tsx", import.meta.url), "utf8");
const select = readFileSync(new URL("../components/ui/select.tsx", import.meta.url), "utf8");

test("One Nation uses orange throughout the app visual language", () => {
  assert.match(css, /--party-one-nation:\s*#e36f14/i);
  assert.match(css, /\[fill="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /\[stroke="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /seat-totals \.onp strong[\s\S]*party-one-nation/);
});

test("Other and independent use a cool neutral distinct from One Nation orange", () => {
  assert.match(css, /--party-other-independent:\s*#9aa3ab/i);
  assert.match(css, /\[fill="#d19b2a"\].*party-other-independent/s);
});

test("forecast chamber graphic does not imply meaning with decorative centre lines", () => {
  assert.match(css, /forecast-hero::after\s*\{\s*display:\s*none/i);
  assert.match(css, /majority-line\s*\{\s*display:\s*none/i);
  assert.match(css, /Each dot = one electorate/i);
  assert.match(css, /not geographic/i);
});

test("select portal content has an explicit opaque surface", () => {
  assert.match(select, /backgroundColor:\s*"var\(--white, #fffefa\)"/i);
  assert.match(select, /color:\s*"var\(--ink, #11263b\)"/i);
});

test("independent and teal-independent remain visually distinct", () => {
  assert.match(css, /--party-independent:/);
  assert.match(css, /--party-teal:/);
  assert.match(css, /teal-independent[\s\S]*linear-gradient/);
  assert.match(key, /Teal-aligned independent/);
  assert.match(key, /remains an independent/i);
});
