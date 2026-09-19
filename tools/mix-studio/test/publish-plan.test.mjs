import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildMediaUrl,
  buildRsyncArgs,
  buildRemoteVerifyCommand,
  buildPublishFileList,
} from '../lib/publish-plan.mjs';

test('buildMediaUrl points to the existing Lightsail media domain', () => {
  assert.equal(buildMediaUrl('summer-set.mp3'), 'https://media.youknowmeasdubbz.com/mixes/summer-set.mp3');
});

test('buildRsyncArgs targets the configured Lightsail media directory', () => {
  assert.deepEqual(buildRsyncArgs('/tmp/summer-set.mp3', 'summer-set.mp3', {
    user: 'ubuntu', host: '44.216.14.49', remoteDir: '/srv/dubbz-media/public/mixes',
  }), [
    '-av', '--progress', '/tmp/summer-set.mp3',
    'ubuntu@44.216.14.49:/srv/dubbz-media/public/mixes/summer-set.mp3',
  ]);
});

test('buildRemoteVerifyCommand uses a shell-quoted remote path', () => {
  assert.equal(
    buildRemoteVerifyCommand('/srv/dubbz-media/public/mixes/summer-set.mp3'),
    "test -s '/srv/dubbz-media/public/mixes/summer-set.mp3'",
  );
  assert.equal(
    buildRemoteVerifyCommand("/srv/media/mix's.mp3"),
    "test -s '/srv/media/mix'\\''s.mp3'",
  );
});

test('buildPublishFileList stages only the selected mix file', () => {
  assert.deepEqual(
    buildPublishFileList('src/content/mixes/summer-set.md', ['src/pages/index.astro']),
    { allowed: true, files: ['src/content/mixes/summer-set.md'] },
  );
  assert.equal(buildPublishFileList('../outside.md', []).allowed, false);
});
