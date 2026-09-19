import path from 'node:path';

export const DEFAULT_LIGHTSAIL = Object.freeze({
  user: 'ubuntu',
  host: '44.216.14.49',
  remoteDir: '/srv/dubbz-media/public/mixes',
  publicBaseUrl: 'https://media.youknowmeasdubbz.com/mixes',
});

export function buildMediaUrl(filename, config = DEFAULT_LIGHTSAIL) {
  return `${config.publicBaseUrl}/${path.basename(filename)}`;
}

export function buildRsyncArgs(localPath, filename, config = DEFAULT_LIGHTSAIL) {
  const remote = `${config.user}@${config.host}:${config.remoteDir}/${path.basename(filename)}`;
  return ['-av', '--progress', localPath, remote];
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

export function buildRemoteVerifyCommand(remotePath) {
  if (!remotePath || remotePath.includes('\n') || remotePath.includes('\r')) {
    throw new Error('Remote path is invalid.');
  }
  return `test -s ${shellQuote(remotePath)}`;
}

export function buildPublishFileList(mixFile, _repoStatus = []) {
  const normalized = String(mixFile ?? '').replaceAll('\\', '/');
  if (!/^src\/content\/mixes\/[a-z0-9][a-z0-9-]*\.md$/.test(normalized)) {
    return { allowed: false, files: [], reason: 'Only a mix Markdown file can be published.' };
  }
  return { allowed: true, files: [normalized] };
}
