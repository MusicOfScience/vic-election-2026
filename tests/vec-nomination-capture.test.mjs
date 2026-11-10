import test from 'node:test';
import assert from 'node:assert/strict';
import { findCandidateSpreadsheet, isVecUrl, determineCarrierFormat } from '../scripts/capture-vec-nominations.mjs';

test('candidate workbook discovered from official election page, preserving query encoding', () => {
  const html = '<a href="/-/media/files/candidates-se2026.xlsx?x=1&amp;y=2">spreadsheet of all the candidates</a>' +
    '<a href="/files/venues.xlsx">venues spreadsheet</a>';
  assert.equal(findCandidateSpreadsheet(html), 'https://www.vec.vic.gov.au/-/media/files/candidates-se2026.xlsx?x=1&y=2');
});
test('untrusted hosts, duplicate spreadsheet links and missing evidence fail closed', () => {
  assert.equal(isVecUrl('https://vec.vic.gov.au/SE2026'), true);
  assert.equal(isVecUrl('https://evil.vec.vic.gov.au.example.org/xlsx'), false);
  assert.equal(isVecUrl('http://vec.vic.gov.au/xlsx'), false);
  assert.throws(() => findCandidateSpreadsheet('<a href="https://evil.invalid/file.xlsx">spreadsheet of all the candidates</a>'), /outside VEC/);
  const a = '<a href="/one.xlsx">spreadsheet of all the candidates</a>';
  assert.throws(() => findCandidateSpreadsheet(a + '<a href="/two.xlsx">candidate spreadsheet</a>'), /unambiguous/);
  assert.throws(() => findCandidateSpreadsheet('<h1>2026 candidates</h1>'), /unambiguous/);
});
test('carrier detection accepts ZIP container and CSV, rejects HTML/PDF', () => {
  assert.equal(determineCarrierFormat(Buffer.from([0x50,0x4b,0x03,0x04,0x10])), 'xlsx');
  assert.equal(determineCarrierFormat(Buffer.from('Name,Contest,Party\nA,B,C\nD,E,F\n')), 'csv');
  assert.throws(() => determineCarrierFormat(Buffer.from('<!doctype html><html>blocked</html>')), /HTML/);
  assert.throws(() => determineCarrierFormat(Buffer.from('%PDF not a workbook')), /PDF/);
  assert.throws(() => determineCarrierFormat(Buffer.alloc(0)), /Empty/);
});
