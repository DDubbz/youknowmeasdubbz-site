import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const index = fs.readFileSync('src/pages/index.astro', 'utf8');
const mixes = fs.readFileSync('src/pages/mixes.astro', 'utf8');
const placeholder = fs.readFileSync('public/mix-placeholder.svg', 'utf8');

test('homepage mix cards retain play navigation after server rendering', () => {
  assert.match(index, /class="mix-card-play"/);
  assert.match(index, /querySelectorAll\(['"]\.mix-card-play/);
  assert.match(index, /\/mixes\?play=/);
  assert.doesNotMatch(index, /class=["'][^"']*mix-card-date/);
});

test('mix pages use the shared branded placeholder album art', () => {
  assert.match(index, /\/mix-placeholder\.svg/);
  assert.match(mixes, /\/mix-placeholder\.svg/);
  assert.match(placeholder, /DUBBZ/);
  assert.match(placeholder, /MIX ARCHIVE/);
});
