import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../app/party-visual-language.css", import.meta.url), "utf8");

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
  assert.match(css, /party-chip\.onp[\s\S]*party-one-nation-ink/);
  assert.match(css, /seat-verdict\.onp[\s\S]*party-one-nation-ink/);
});

test("One Nation retains orange identity and a secondary non-colour cue", () => {
  assert.match(css, /\[fill="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /\[stroke="#6e4da0"\].*party-one-nation/s);
  assert.match(css, /poll-series-chart[\s\S]*stroke="#6e4da0"[\s\S]*stroke-dasharray:\s*6 3/i);
});

test("Other and independent use a cool neutral distinct from One Nation orange", () => {
  assert.match(css, /--party-other-independent:\s*#9aa3ab/i);
  assert.match(css, /\[fill="#d19b2a"\].*party-other-independent/s);
});

test("chamber threshold and seat-by-seat leaders describe different quantities", () => {
  const overview = readFileSync(new URL("../app/assembly-overview.tsx", import.meta.url), "utf8");
  const styles = readFileSync(new URL("../app/assembly-overview.css", import.meta.url), "utf8");
  assert.match(styles, /forecast-hero::after\s*\{\s*display:\s*none/i);
  assert.match(overview, /45 · majority/);
  assert.match(overview, /average seats across runs/);
  assert.match(overview, /all 88 seats together in each simulation/);
});
