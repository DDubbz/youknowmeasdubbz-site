import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const dir = path.resolve('tools/mix-studio/public');
function read(name) { return fs.readFileSync(path.join(dir, name), 'utf8'); }

test('dashboard UI exposes the approved local studio workflow', () => {
  const html = read('index.html');
  assert.match(html, /Dubbz Mix Studio/);
  assert.match(html, /id="mix-library"/);
  assert.match(html, /id="mix-editor"/);
  assert.match(html, /id="publish-modal"/);
  assert.match(html, /Upload & Publish/);
});

test('dashboard UI includes media inputs and metadata fields', () => {
  const html = read('index.html');
  for (const field of ['title', 'description', 'date', 'genre', 'tags', 'audio-file', 'cover-file', 'featured', 'downloadable']) {
    assert.match(html, new RegExp(`(?:id|name)="${field}"`));
  }
  assert.match(html, /Save Draft/);
  assert.match(html, /Preview Markdown/);
});

test('dashboard UI is wired to local APIs and Dubbz visual tokens', () => {
  const js = read('app.js');
  const css = read('styles.css');
  assert.match(js, /\/api\/mixes/);
  assert.match(js, /\/api\/publish/);
  assert.match(css, /--cyan:\s*#00d4ff/i);
  assert.match(css, /--gold:\s*#ffd700/i);
});
