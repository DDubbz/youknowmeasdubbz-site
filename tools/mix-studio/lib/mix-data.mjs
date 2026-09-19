import path from 'node:path';

const FIELD_ORDER = [
  'title', 'description', 'date', 'genre', 'duration', 'bpmRange', 'trackCount',
  'live', 'venue', 'address', 'coverImage', 'audioFile', 'downloadable', 'featured',
  'tags', 'youtubeUrl', 'spotifyUrl', 'soundcloudUrl', 'mixcloudUrl',
];

const REQUIRED_FIELDS = [
  ['title', 'Title is required.'],
  ['description', 'Description is required.'],
  ['date', 'Date is required.'],
  ['genre', 'Choose at least one genre.'],
  ['coverImage', 'Cover image is required.'],
];

export function slugifyTitle(title) {
  return String(title ?? '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-');
}

function parseArray(value) {
  if (value === '[]') return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return value
      .slice(1, -1)
      .split(',')
      .map((item) => item.trim().replace(/^['"]|['"]$/g, ''))
      .filter(Boolean);
  }
}

function parseValue(key, value) {
  if (key === 'genre' || key === 'tags') return parseArray(value);
  if (value === 'true' || value === 'false') return value === 'true';
  if (/^-?\d+$/.test(value)) return Number(value);
  if (value.startsWith('"') && value.endsWith('"')) {
    try { return JSON.parse(value); } catch { return value.slice(1, -1); }
  }
  if (value.startsWith("'") && value.endsWith("'")) return value.slice(1, -1).replace(/''/g, "'");
  return value;
}

export function parseMixMarkdown(text, id = '') {
  const match = String(text).match(/^---\s*\n([\s\S]*?)\n---/);
  if (!match) throw new Error('Mix Markdown is missing frontmatter.');
  const mix = { id };
  for (const line of match[1].split('\n')) {
    const separator = line.indexOf(':');
    if (separator < 1) continue;
    const key = line.slice(0, separator).trim();
    const value = line.slice(separator + 1).trim();
    mix[key] = parseValue(key, value);
  }
  return mix;
}

function quote(value) {
  return JSON.stringify(String(value ?? ''));
}

function arrayValue(values) {
  return `[${(Array.isArray(values) ? values : []).map(quote).join(', ')}]`;
}

function optionalString(mix, key) {
  return mix[key] === undefined ? null : `${key}: ${quote(mix[key])}`;
}

export function serializeMixMarkdown(mix) {
  const lines = ['---'];
  for (const key of FIELD_ORDER) {
    if (mix[key] === undefined) continue;
    if (key === 'genre' || key === 'tags') lines.push(`${key}: ${arrayValue(mix[key])}`);
    else if (['trackCount'].includes(key)) lines.push(`${key}: ${Number(mix[key] || 0)}`);
    else if (['live', 'downloadable', 'featured'].includes(key)) lines.push(`${key}: ${Boolean(mix[key])}`);
    else if (key === 'date' && /^\d{4}-\d{2}-\d{2}$/.test(String(mix[key]))) lines.push(`${key}: ${mix[key]}`);
    else {
      const line = optionalString(mix, key);
      if (line) lines.push(line);
    }
  }
  lines.push('---', '');
  return lines.join('\n');
}

export function validateMix(mix) {
  const errors = [];
  for (const [key, message] of REQUIRED_FIELDS) {
    const value = mix?.[key];
    const missing = key === 'genre'
      ? !Array.isArray(value) || value.length === 0
      : !String(value ?? '').trim();
    if (missing) errors.push(message);
  }
  if (mix?.audioFile && !/^https:\/\/media\.youknowmeasdubbz\.com\/mixes\/[a-z0-9][a-z0-9._-]*$/i.test(mix.audioFile) && !/^\/mixes\/[a-z0-9][a-z0-9._-]*$/i.test(mix.audioFile)) {
    errors.push('Audio file must be a local /mixes path or a media.youknowmeasdubbz.com URL.');
  }
  return { valid: errors.length === 0, errors };
}

export function safeAssetName(slug, originalName, allowedExtensions) {
  const extension = path.extname(String(originalName ?? '')).toLowerCase();
  const allowed = new Set(allowedExtensions.map((item) => item.toLowerCase()));
  if (!allowed.has(extension)) throw new Error(`Unsupported asset type: ${extension || 'missing extension'}`);
  const safeSlug = slugifyTitle(slug);
  if (!safeSlug) throw new Error('A non-empty slug is required.');
  return `${safeSlug}${extension}`;
}
