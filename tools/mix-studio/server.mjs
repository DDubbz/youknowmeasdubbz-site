#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { buildMediaUrl, buildRemoteVerifyCommand, buildRsyncArgs, DEFAULT_LIGHTSAIL, buildPublishFileList } from './lib/publish-plan.mjs';
import { parseMixMarkdown, serializeMixMarkdown, slugifyTitle, safeAssetName, validateMix } from './lib/mix-data.mjs';
import { isAllowedContentType, json, routeRequest, writeResponse } from './lib/server-utils.mjs';

const ROOT = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));
const MIX_DIR = path.join(ROOT, 'src', 'content', 'mixes');
const PUBLIC_DIR = path.join(ROOT, 'tools', 'mix-studio', 'public');
const HOST = '127.0.0.1';
const PORT = Number(process.env.MIX_STUDIO_PORT || 4322);
const MAX_JSON_BYTES = 1024 * 1024;
const MAX_UPLOAD_BYTES = Number(process.env.MIX_STUDIO_MAX_UPLOAD_BYTES || 900 * 1024 * 1024);
const DRY_RUN = process.env.MIX_STUDIO_DRY_RUN === '1';
const LIGHTSAIL = Object.freeze({
  user: process.env.DUBBZ_LIGHTSAIL_USER || DEFAULT_LIGHTSAIL.user,
  host: process.env.DUBBZ_LIGHTSAIL_HOST || DEFAULT_LIGHTSAIL.host,
  remoteDir: process.env.DUBBZ_LIGHTSAIL_DIR || DEFAULT_LIGHTSAIL.remoteDir,
  publicBaseUrl: process.env.DUBBZ_MEDIA_BASE_URL || DEFAULT_LIGHTSAIL.publicBaseUrl,
});

function fail(message, status = 400, details = {}) {
  return json({ ok: false, error: message, ...details }, status);
}

function run(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { cwd: ROOT, env: process.env, ...options });
    let stdout = '';
    let stderr = '';
    child.stdout?.on('data', (chunk) => { stdout += chunk; });
    child.stderr?.on('data', (chunk) => { stderr += chunk; });
    child.on('error', (error) => resolve({ code: -1, stdout, stderr: `${stderr}${error.message}` }));
    child.on('close', (code) => resolve({ code: code ?? -1, stdout, stderr }));
  });
}

async function runChecked(command, args) {
  const result = await run(command, args);
  if (result.code !== 0) {
    const error = new Error(`${command} failed (${result.code}): ${result.stderr || result.stdout}`);
    error.result = result;
    throw error;
  }
  return result;
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_JSON_BYTES) {
        req.destroy();
        reject(new Error('JSON request is too large.'));
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')); }
      catch { reject(new Error('Request body must be valid JSON.')); }
    });
    req.on('error', reject);
  });
}

function streamToFile(req, target) {
  return new Promise((resolve, reject) => {
    let size = 0;
    let rejected = false;
    const output = fs.createWriteStream(target, { flags: 'wx' });
    const rejectOnce = (error) => {
      if (rejected) return;
      rejected = true;
      output.destroy();
      reject(error);
    };
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_UPLOAD_BYTES) {
        req.destroy();
        rejectOnce(new Error(`Upload exceeds the ${Math.round(MAX_UPLOAD_BYTES / 1024 / 1024)} MB limit.`));
      }
    });
    req.on('error', rejectOnce);
    output.on('error', rejectOnce);
    output.on('finish', () => { if (!rejected) resolve(size); });
    req.pipe(output);
  });
}

async function listMixes() {
  const entries = await fsp.readdir(MIX_DIR, { withFileTypes: true });
  const mixes = [];
  for (const entry of entries.filter((item) => item.isFile() && item.name.endsWith('.md')).sort((a, b) => a.name.localeCompare(b.name))) {
    const id = entry.name.slice(0, -3);
    const text = await fsp.readFile(path.join(MIX_DIR, entry.name), 'utf8');
    mixes.push(parseMixMarkdown(text, id));
  }
  return mixes.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
}

function normalizeMix(input) {
  const mix = { ...input };
  mix.id = slugifyTitle(mix.id || mix.title);
  mix.genre = Array.isArray(mix.genre) ? mix.genre.map(String).map((item) => item.trim()).filter(Boolean) : [];
  mix.tags = Array.isArray(mix.tags) ? mix.tags.map(String).map((item) => item.trim()).filter(Boolean) : [];
  mix.trackCount = mix.trackCount ? Number(mix.trackCount) : 0;
  for (const key of ['live', 'downloadable', 'featured']) mix[key] = Boolean(mix[key]);
  return mix;
}

async function saveMixRecord(input) {
  const mix = normalizeMix(input);
  const result = validateMix(mix);
  if (!result.valid) throw Object.assign(new Error(result.errors.join(' ')), { statusCode: 422, details: { errors: result.errors } });
  if (!/^[a-z0-9][a-z0-9-]*$/.test(mix.id)) throw Object.assign(new Error('Mix slug contains unsupported characters.'), { statusCode: 422 });
  const file = path.join(MIX_DIR, `${mix.id}.md`);
  const relative = path.relative(ROOT, file).replaceAll(path.sep, '/');
  const temp = `${file}.${process.pid}.tmp`;
  await fsp.writeFile(temp, serializeMixMarkdown(mix), { encoding: 'utf8', mode: 0o600 });
  await fsp.rename(temp, file);
  return { mix, file, relative };
}

function mediaConfigFor(kind) {
  if (kind === 'audio') return { extensions: ['.mp3', '.wav', '.m4a', '.aac', '.flac'], contentPrefix: 'audio/' };
  if (kind === 'cover') return { extensions: ['.webp', '.jpg', '.jpeg', '.png'], contentPrefix: 'image/' };
  throw Object.assign(new Error('Upload kind must be audio or cover.'), { statusCode: 422 });
}

async function uploadMedia(url, req) {
  const id = slugifyTitle(url.searchParams.get('id') || '');
  const kind = url.searchParams.get('kind');
  if (!id) throw Object.assign(new Error('A valid mix id is required.'), { statusCode: 422 });
  const config = mediaConfigFor(kind);
  const contentType = String(req.headers['content-type'] || '').toLowerCase();
  if (contentType && !isAllowedContentType(contentType)) throw Object.assign(new Error(`Unsupported content type: ${contentType}`), { statusCode: 415 });
  const originalName = String(req.headers['x-file-name'] || `${id}${config.extensions[0]}`).replaceAll('\n', '').replaceAll('\r', '');
  const filename = safeAssetName(id, originalName, config.extensions);
  const staging = await fsp.mkdtemp(path.join(os.tmpdir(), 'dubbz-mix-'));
  const localPath = path.join(staging, filename);
  try {
    const bytes = await streamToFile(req, localPath);
    if (bytes === 0) throw Object.assign(new Error('The uploaded file is empty.'), { statusCode: 422 });
    const publicUrl = buildMediaUrl(filename, LIGHTSAIL);
    if (DRY_RUN) return { kind, filename, bytes, publicUrl, dryRun: true };
    await runChecked('rsync', buildRsyncArgs(localPath, filename, LIGHTSAIL));
    const remotePath = path.posix.join(LIGHTSAIL.remoteDir, filename);
    const host = `${LIGHTSAIL.user}@${LIGHTSAIL.host}`;
    await runChecked('ssh', [host, buildRemoteVerifyCommand(remotePath)]);
    await runChecked('curl', ['-fsS', '--max-time', '20', '-r', '0-0', '-o', '/dev/null', publicUrl]);
    return { kind, filename, bytes, publicUrl, dryRun: false };
  } finally {
    await fsp.rm(staging, { recursive: true, force: true });
  }
}

async function publishMix(input) {
  const { mix, relative } = await saveMixRecord(input);
  const plan = buildPublishFileList(relative, []);
  if (!plan.allowed) throw Object.assign(new Error(plan.reason), { statusCode: 422 });
  const build = await runChecked('npm', ['run', 'build']);
  const stagedBefore = await run('git', ['diff', '--cached', '--name-only']);
  if (stagedBefore.code !== 0) throw new Error(stagedBefore.stderr || 'Unable to inspect staged Git files.');
  if (stagedBefore.stdout.trim()) throw Object.assign(new Error('Publish paused because unrelated files are already staged in Git.'), { statusCode: 409, details: { staged: stagedBefore.stdout.trim().split('\n') } });
  const status = await runChecked('git', ['status', '--porcelain', '--', relative]);
  if (!status.stdout.trim()) return { mix, relative, built: true, pushed: false, message: 'Build succeeded; no Git change was needed.', buildOutput: build.stdout };
  await runChecked('git', ['add', '--', relative]);
  const staged = await runChecked('git', ['diff', '--cached', '--name-only']);
  if (staged.stdout.trim() !== relative) {
    await run('git', ['reset', '--', relative]);
    throw Object.assign(new Error('Publish stopped because more than the selected mix file became staged.'), { statusCode: 409 });
  }
  const commit = await runChecked('git', ['commit', '-m', `Update mix: ${mix.title}`]);
  const push = await runChecked('git', ['push', 'origin', 'main']);
  const head = await runChecked('git', ['rev-parse', 'HEAD']);
  return { mix, relative, built: true, pushed: true, commit: head.stdout.trim(), message: 'Mix published; Cloudflare Pages deployment triggered.', commitOutput: commit.stdout, pushOutput: push.stdout, buildOutput: build.stdout };
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  return ({ '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml' })[ext] || 'application/octet-stream';
}

async function serveStatic(url, res) {
  const requested = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
  const file = path.resolve(PUBLIC_DIR, `.${requested}`);
  if (!file.startsWith(`${PUBLIC_DIR}${path.sep}`)) return writeResponse(res, fail('Not found.', 404));
  try {
    const stat = await fsp.stat(file);
    if (!stat.isFile()) throw new Error('not file');
    res.writeHead(200, { 'content-type': contentType(file), 'cache-control': 'no-store' });
    fs.createReadStream(file).pipe(res);
  } catch { writeResponse(res, fail('Not found.', 404)); }
}

export function createServer() {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url || '/', `http://${HOST}:${PORT}`);
    const route = routeRequest(req.method || 'GET', url.pathname);
    try {
      if (route === 'health') return writeResponse(res, json({ ok: true, localOnly: true, dryRun: DRY_RUN, root: ROOT, lightsail: { host: LIGHTSAIL.host, remoteDir: LIGHTSAIL.remoteDir, publicBaseUrl: LIGHTSAIL.publicBaseUrl } }));
      if (route === 'list-mixes') return writeResponse(res, json({ ok: true, mixes: await listMixes() }));
      if (route === 'save-mix') return writeResponse(res, json({ ok: true, ...(await saveMixRecord(await readJson(req))) }));
      if (route === 'upload-media') return writeResponse(res, json({ ok: true, upload: await uploadMedia(url, req) }));
      if (route === 'publish') return writeResponse(res, json({ ok: true, result: await publishMix((await readJson(req)).mix) }));
      if (url.pathname.startsWith('/api/')) return writeResponse(res, fail('API route not found.', 404));
      return serveStatic(url, res);
    } catch (error) {
      const status = error.statusCode || 500;
      return writeResponse(res, fail(error.message || 'Unexpected local studio error.', status, error.details || {}));
    }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  createServer().listen(PORT, HOST, () => {
    console.log(`Dubbz Mix Studio running at http://${HOST}:${PORT}`);
    console.log(`Repository: ${ROOT}`);
    console.log(`Lightsail media: ${LIGHTSAIL.publicBaseUrl}`);
    if (DRY_RUN) console.log('Upload mode: DRY RUN');
  });
}
