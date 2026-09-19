import test from 'node:test';
import assert from 'node:assert/strict';
import { json, routeRequest, isAllowedContentType } from '../lib/server-utils.mjs';

test('routeRequest maps API paths to stable handlers', () => {
  assert.equal(routeRequest('GET', '/api/health'), 'health');
  assert.equal(routeRequest('GET', '/api/mixes'), 'list-mixes');
  assert.equal(routeRequest('POST', '/api/mixes/save'), 'save-mix');
  assert.equal(routeRequest('POST', '/api/mixes/upload'), 'upload-media');
  assert.equal(routeRequest('POST', '/api/publish'), 'publish');
  assert.equal(routeRequest('GET', '/unknown'), null);
});

test('json creates a JSON response payload', () => {
  const response = json({ ok: true, count: 2 });
  assert.equal(response.status, 200);
  assert.equal(response.headers['content-type'], 'application/json; charset=utf-8');
  assert.deepEqual(JSON.parse(response.body), { ok: true, count: 2 });
});

test('isAllowedContentType accepts supported audio and image types only', () => {
  assert.equal(isAllowedContentType('audio/mpeg'), true);
  assert.equal(isAllowedContentType('image/webp'), true);
  assert.equal(isAllowedContentType('application/x-sh'), false);
});
