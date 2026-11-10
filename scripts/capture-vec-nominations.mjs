#!/usr/bin/env node
/**
 * Capture the current VEC 2026 state-election candidate spreadsheet for
 * human reconciliation. No candidate registration or model mutation.
 *
 * Output is an ephemeral GitHub Actions artifact until a separate review
 * explicitly accepts the source carrier and its provenance.
 */
import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const VEC_LANDING = 'https://www.vec.vic.gov.au/2026-state-election';
const MAX_BYTES = 20 * 1024 * 1024;
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');

function decodeHtml(value) {
  return String(value).replace(/&amp;/gi, '&').replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'").replace(/&nbsp;/gi, ' ')
    .replace(/&#(\d+);/g, (_, number) => String.fromCodePoint(Number(number)));
}
function labelText(value) {
  return decodeHtml(String(value).replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
}
export function isVecUrl(value) {
  try {
    const u = new URL(value);
    return u.protocol === 'https:' && (u.hostname === 'vec.vic.gov.au' ||
      u.hostname.endsWith('.vec.vic.gov.au')) && !u.username && !u.password;
  } catch {
    return false;
  }
}
export function findCandidateSpreadsheet(html, landingUrl = VEC_LANDING) {
  if (!isVecUrl(landingUrl)) throw new Error('Landing URL must be VEC HTTPS');
  const candidates = [];
  for (const match of String(html).matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a\s*>/gi)) {
    const attrs = match[1];
    const hrefMatch = attrs.match(/\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i);
    if (!hrefMatch) continue;
    const rawHref = decodeHtml(hrefMatch[1] ?? hrefMatch[2] ?? hrefMatch[3]);
    const label = labelText(match[2]).toLowerCase();
    const mention = (label + ' ' + rawHref).toLowerCase();
    // Avoid VEC's unrelated voting-centre, venue and ballot-software spreadsheets.
    const likely = /spreadsheet of all (the )?candidates|candidate(s)? spreadsheet|spreadsheet of candidate/i.test(label) ||
      (/\.(xlsx|xls|csv)(?:[?#]|$)/i.test(rawHref) && /candidat|nomination/i.test(mention));
    if (!likely) continue;
    const target = new URL(rawHref, landingUrl).href;
    if (!isVecUrl(target)) throw new Error('Candidate spreadsheet points outside VEC HTTPS; manual review required: ' + target);
    if (!candidates.includes(target)) candidates.push(target);
  }
  if (candidates.length !== 1) {
    throw new Error('Expected one unambiguous official candidate spreadsheet link; found ' + candidates.length +
      '. Inspect the VEC landing page; never guess a workbook URL.');
  }
  return candidates[0];
}
export function determineCarrierFormat(bytes, type = '') {
  const data = Buffer.from(bytes);
  if (data.length === 0 || data.length > MAX_BYTES) throw new Error('Empty/oversized candidate carrier');
  if (data.subarray(0, 4).equals(Buffer.from([0x50, 0x4b, 0x03, 0x04]))) return 'xlsx';
  if (data.subarray(0, 8).toString('utf8').startsWith('<!DOCTYPE') ||
      /^\s*<(?:html|!doctype)/i.test(data.subarray(0, 200).toString('utf8'))) {
    throw new Error('VEC candidate link returned HTML, not candidate data');
  }
  if (/pdf/i.test(type) || data.subarray(0, 4).toString('ascii') === '%PDF') {
    throw new Error('Unexpected PDF instead of candidate spreadsheet');
  }
  const text = data.toString('utf8');
  if (!text.includes('\ufffd') && /[,\t]/.test(text.split(/\r?\n/, 1)[0]) &&
      text.split(/\r?\n/).length > 2) return 'csv';
  throw new Error('Unrecognised spreadsheet carrier; do not admit uninspected data');
}
async function getVec(url) {
  let current = url;
  for (let i = 0; i < 5; i++) {
    if (!isVecUrl(current)) throw new Error('Redirect escaped approved VEC hosts');
    const response = await fetch(current, {
      redirect: 'manual',
      headers: { 'Accept': 'text/html,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,*/*',
        'User-Agent': 'vic-election-2026-evidence-capture/1.0 (+https://github.com/MusicOfScience/vic-election-2026)' }
    });
    if ([301, 302, 303, 307, 308].includes(response.status)) {
      const location = response.headers.get('location');
      if (!location) throw new Error('Redirect without Location');
      current = new URL(location, current).href;
      continue;
    }
    if (!response.ok) throw new Error('VEC HTTP ' + response.status + ' at ' + current);
    const reportedSize = Number(response.headers.get('content-length') || 0);
    if (reportedSize > MAX_BYTES) throw new Error('VEC carrier exceeds size limit');
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length > MAX_BYTES) throw new Error('VEC response exceeds size limit');
    return { bytes, url: current, status: response.status,
      type: response.headers.get('content-type') || '',
      etag: response.headers.get('etag'), lastModified: response.headers.get('last-modified') };
  }
  throw new Error('Too many VEC redirects');
}
async function main() {
  const args = process.argv.slice(2);
  const value = (name, fallback) => {
    const i = args.indexOf(name);
    if (i < 0) return fallback;
    if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error(name + ' requires a value');
    return args[i + 1];
  };
  const landing = value('--landing', VEC_LANDING);
  const suppliedFileUrl = value('--file-url', null);
  const output = resolve(value('--output', 'vec-nominations-capture'));
  if (!isVecUrl(landing)) throw new Error('Landing page is not VEC HTTPS');
  const page = await getVec(landing);
  const fileUrl = suppliedFileUrl || findCandidateSpreadsheet(page.bytes.toString('utf8'), page.url);
  if (!isVecUrl(fileUrl)) throw new Error('Workbook URL is not VEC HTTPS');
  const workbook = await getVec(fileUrl);
  const format = determineCarrierFormat(workbook.bytes, workbook.type);
  const filename = 'vec-2026-candidates-raw.' + format;
  const receipt = {
    schemaVersion: 1,
    mode: 'raw-official-carrier-capture-review-only',
    candidateStatusAccepted: false,
    modelInputsChanged: false,
    sourceAuthority: 'Victorian Electoral Commission',
    sourceLandingUrl: page.url,
    sourceFileUrl: workbook.url,
    discovery: suppliedFileUrl ? 'operator-provided-VEC-file-url' : 'official-landing-page-link',
    capturedAt: new Date().toISOString(),
    sourceLandingSha256: hash(page.bytes),
    sourceFileSha256: hash(workbook.bytes),
    sourceBytes: workbook.bytes.length,
    sourceFormat: format,
    http: { status: workbook.status, contentType: workbook.type,
      etag: workbook.etag, lastModified: workbook.lastModified },
    file: filename,
    caveat: 'Source capture and file-format detection only; publication finality, contents, candidate counts, candidate identities and official ballot order must be validated independently before admission.'
  };
  await mkdir(output, { recursive: true });
  await writeFile(resolve(output, filename), workbook.bytes, { flag: 'wx' });
  await writeFile(resolve(output, 'source-landing.html'), page.bytes, { flag: 'wx' });
  await writeFile(resolve(output, 'capture-receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ receipt: resolve(output, 'capture-receipt.json'),
    format, bytes: receipt.sourceBytes, sha256: receipt.sourceFileSha256, status: 'REVIEW_REQUIRED' }));
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
