import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server.mjs';

test('local studio serves health, mix data, and the dashboard', async (t) => {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const { port } = server.address();
  const base = `http://127.0.0.1:${port}`;

  const health = await fetch(`${base}/api/health`).then((response) => response.json());
  assert.equal(health.ok, true);
  assert.equal(health.localOnly, true);

  const mixes = await fetch(`${base}/api/mixes`).then((response) => response.json());
  assert.equal(mixes.ok, true);
  assert.ok(mixes.mixes.length >= 1);
  assert.ok(mixes.mixes.every((mix) => mix.title && mix.id));

  const page = await fetch(`${base}/`).then((response) => response.text());
  assert.match(page, /Dubbz Mix Studio/);
  assert.match(page, /Upload &amp; Publish|Upload & Publish/);
});
