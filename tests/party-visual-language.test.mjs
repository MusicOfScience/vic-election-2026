import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/party-visual-language.css", import.meta.url), "utf8");
const key = readFileSync(new URL("../app/party-visual-key.tsx", import.meta.url), "utf8");
const select = readFileSync(new URL("../components/ui/select.tsx", import.meta.url), "utf8");

function hexRgb(hex) {
  const raw = hex.replace("#", "");
  return [0, 2, 4].map((index) => Number.parseInt(raw.slice(index, index + 2), 16));
}

function relativeLuminance(hex) {
  const channel = (value) => {
    const srgb = value / 255;
    return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
  };
  const [r, g, b] = hexRgb(hex).map(channel);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [high, low] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

test("Labor crimson and One Nation amber are deliberately separated", () => {
  assert.match(css, /--party-labor:\s*#d9475b/i);
  assert.match(css, /--party-one-nation:\s*#f29a00/i);
  const labor = hexRgb("#d9475b");
  const onp = hexRgb("#f29a00");
  const rgbDistance = Math.hypot(...labor.map((value, index) => value - onp[index]));
  assert.ok(rgbDistance > 110, `Labor/ONP RGB separation too small: ${rgbDistance}`);
});

test("party colour roles include accessible dark inks and bright dark-surface companions", () => {
  assert.match(css, /--party-labor-ink:\s*#a12438/i);
  assert.match(css, /--party-one-nation-ink:\s*#925300/i);
  assert.match(css, /--party-labor-light:\s*#ff8292/i);
  assert.match(css, /--party-one-nation-light:\s*#ffb43b/i);
  assert.ok(contrast("#a12438", "#ffffff") >= 4.5);
  assert.ok(contrast("#925300", "#ffffff") >= 4.5);
  assert.match(css, /seat-totals \.labor strong[\s\S]*party-labor-light/);
  assert.match(css, /seat-totals \.onp strong[\s\S]*party-one-nation-light/);
  assert.match(css, /party-chip\.onp[\s\S]*party-one-nation-ink/);
  assert.match(css, /seat-verdict\.onp[\s\S]*party-one-nation-ink/);
});

test("One Nation retains orange identity and a secondary non-colour cue", () => {
  assert.match(css, /\[fill="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /\[stroke="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /poll-series-chart[\s\S]*stroke="#6e4da0"[\s\S]*stroke-dasharray:\s*6 3/i);
  assert.match(css, /seat-arc circle\[fill="#6e4da0"\][\s\S]*stroke-width:\s*1\.15/i);
});

test("Other and independent use a cool neutral distinct from One Nation orange", () => {
  assert.match(css, /--party-other-independent:\s*#9aa3ab/i);
  assert.match(css, /\[fill="#d19b2a"\].*party-other-independent/s);
});

test("forecast chamber graphic does not imply meaning with decorative centre lines", () => {
  assert.match(css, /forecast-hero::after\s*\{\s*display:\s*none/i);
  assert.match(css, /majority-line\s*\{\s*display:\s*none/i);
  assert.match(css, /Each dot = one electorate/i);
  assert.match(css, /modal forecast winner/i);
  assert.match(css, /not an expected chamber seat count/i);
  assert.match(css, /party can appear in the key with zero dots/i);
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
