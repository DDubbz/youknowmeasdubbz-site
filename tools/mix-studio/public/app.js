const GENRES = [
  'house', 'deep-house', 'tech-house', 'hip-hop', 'r&b', 'afrobeats', 'amapiano',
  'dancehall', 'reggaeton', 'bachata', 'latin', 'top-40', 'open-format', 'trap',
  'kompa', 'bounce', 'slow-jams', 'classics', 'throwbacks', 'edm', 'pop', 'disco',
  'funk', 'soul', 'jazz', 'reggae', 'afro-house', 'techno', 'dnb', 'lo-fi',
];

const state = {
  mixes: [],
  selectedId: null,
  draft: null,
  newRecord: false,
  dirty: false,
  search: '',
  filter: 'all',
  files: { audio: null, cover: null },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
}

function slugify(value) {
  return String(value ?? '').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').replace(/-{2,}/g, '-');
}

function clone(value) { return JSON.parse(JSON.stringify(value)); }

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({ ok: false, error: 'The local studio returned an invalid response.' }));
  if (!response.ok || payload.ok === false) {
    const error = new Error(payload.error || `Request failed (${response.status})`);
    error.details = payload;
    throw error;
  }
  return payload;
}

function toast(title, message = '', type = 'success') {
  const node = document.createElement('div');
  node.className = `toast ${type}`;
  node.innerHTML = `<strong>${esc(title)}</strong>${message ? `<span>${esc(message)}</span>` : ''}`;
  $('#toast-region').append(node);
  setTimeout(() => node.remove(), 5200);
}

function setSaveStatus(message, tone = '') {
  const node = $('#save-status');
  node.textContent = message;
  node.style.color = tone === 'error' ? 'var(--red)' : tone === 'success' ? 'var(--green)' : '';
}

function renderLibrary() {
  const query = state.search.trim().toLowerCase();
  const filtered = state.mixes.filter((mix) => {
    if (state.filter === 'featured' && !mix.featured) return false;
    if (state.filter === 'live' && !mix.live) return false;
    if (!query) return true;
    return [mix.title, mix.description, ...(mix.tags || []), ...(mix.genre || [])].join(' ').toLowerCase().includes(query);
  });
  $('#mix-count').textContent = String(state.mixes.length).padStart(2, '0');
  $('#featured-count').textContent = state.mixes.filter((mix) => mix.featured).length;
  $('#live-count').textContent = state.mixes.filter((mix) => mix.live).length;
  const list = $('#mix-list');
  if (!filtered.length) {
    list.innerHTML = '<div class="empty-library">No mixes match that filter.</div>';
    return;
  }
  list.innerHTML = filtered.map((mix) => {
    const cover = mix.coverImage ? `<img class="mix-cover" src="${esc(mix.coverImage)}" alt="" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'mix-cover no-cover',textContent:'D'}))">` : '<div class="mix-cover no-cover">D</div>';
    const genre = (mix.genre || [])[0] || 'Uncategorized';
    return `<button class="mix-card ${state.selectedId === mix.id ? 'is-selected' : ''}" data-mix-id="${esc(mix.id)}" type="button">
      ${cover}<span class="mix-card-copy"><span class="mix-card-title">${esc(mix.title || mix.id)}</span><span class="mix-card-meta"><span>${esc(mix.date || 'No date')}</span><span class="bullet">·</span><span>${esc(genre)}</span></span></span>
      <span class="mix-card-flags"><i class="flag ${mix.featured ? 'featured' : ''}" title="${mix.featured ? 'Featured' : ''}"></i><i class="flag ${mix.live ? 'live' : ''}" title="${mix.live ? 'Live' : ''}"></i></span>
    </button>`;
  }).join('');
  $$('.mix-card').forEach((card) => card.addEventListener('click', () => selectMix(card.dataset.mixId)));
}

function setField(id, value) { const field = document.getElementById(id); if (field) field.value = value ?? ''; }
function getField(id) { return document.getElementById(id)?.value ?? ''; }

function renderGenres() {
  const selected = state.draft?.genre || [];
  $('#genre').innerHTML = GENRES.map((genre) => `<button type="button" class="genre-chip ${selected.includes(genre) ? 'is-selected' : ''}" data-genre="${esc(genre)}">${esc(genre)}</button>`).join('');
  $$('#genre .genre-chip').forEach((chip) => chip.addEventListener('click', () => {
    chip.classList.toggle('is-selected');
    syncDraftFromForm();
    markDirty();
  }));
}

function renderEditor() {
  const mix = state.draft;
  const hasDraft = Boolean(mix);
  $('#editor-empty').classList.toggle('is-hidden', hasDraft);
  $('#editor-content').classList.toggle('is-hidden', !hasDraft);
  if (!hasDraft) return;
  setField('title', mix.title);
  setField('date', mix.date);
  setField('duration', mix.duration);
  setField('bpm-range', mix.bpmRange);
  setField('track-count', mix.trackCount || '');
  setField('description', mix.description);
  setField('tags', (mix.tags || []).join(', '));
  setField('venue', mix.venue);
  setField('address', mix.address);
  setField('youtube-url', mix.youtubeUrl);
  setField('soundcloud-url', mix.soundcloudUrl);
  setField('spotify-url', mix.spotifyUrl);
  setField('mixcloud-url', mix.mixcloudUrl);
  $('#featured').checked = Boolean(mix.featured);
  $('#downloadable').checked = Boolean(mix.downloadable);
  $('#live').checked = Boolean(mix.live);
  $('#live-fields').classList.toggle('is-hidden', !mix.live);
  $('#editor-title').textContent = mix.title || 'New mix';
  $('#editor-subtitle').textContent = state.newRecord ? 'New local draft · ready for your details' : `${mix.date || 'Undated'} · local Markdown source`;
  $('#editor-id').textContent = mix.id;
  $('#dirty-badge').classList.toggle('is-hidden', !state.dirty);
  renderGenres();
  updateMediaPreview();
}

function selectMix(id) {
  const mix = state.mixes.find((item) => item.id === id);
  if (!mix) return;
  state.selectedId = id;
  state.draft = clone(mix);
  state.newRecord = false;
  state.dirty = false;
  state.files = { audio: null, cover: null };
  renderLibrary();
  renderEditor();
  setSaveStatus('Draft changes stay local until you publish.');
}

function newMix() {
  const today = new Date().toISOString().slice(0, 10);
  state.selectedId = null;
  state.draft = { id: 'new-mix', title: 'New Mix', description: '', date: today, genre: [], duration: '', bpmRange: '', trackCount: 0, live: false, venue: '', address: '', coverImage: '', audioFile: '', downloadable: false, featured: false, tags: [], youtubeUrl: '', spotifyUrl: '', soundcloudUrl: '', mixcloudUrl: '' };
  state.newRecord = true;
  state.dirty = true;
  state.files = { audio: null, cover: null };
  renderLibrary();
  renderEditor();
  markDirty();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function syncDraftFromForm() {
  if (!state.draft) return;
  const draft = state.draft;
  draft.title = getField('title').trim();
  if (state.newRecord) draft.id = slugify(draft.title) || 'new-mix';
  draft.date = getField('date');
  draft.duration = getField('duration').trim();
  draft.bpmRange = getField('bpm-range').trim();
  draft.trackCount = Number(getField('track-count')) || 0;
  draft.description = getField('description').trim();
  draft.tags = getField('tags').split(',').map((tag) => tag.trim()).filter(Boolean);
  draft.venue = getField('venue').trim();
  draft.address = getField('address').trim();
  draft.youtubeUrl = getField('youtube-url').trim();
  draft.soundcloudUrl = getField('soundcloud-url').trim();
  draft.spotifyUrl = getField('spotify-url').trim();
  draft.mixcloudUrl = getField('mixcloud-url').trim();
  draft.featured = $('#featured').checked;
  draft.downloadable = $('#downloadable').checked;
  draft.live = $('#live').checked;
  draft.genre = $$('#genre .genre-chip.is-selected').map((chip) => chip.dataset.genre);
  $('#editor-title').textContent = draft.title || 'New mix';
  $('#editor-id').textContent = draft.id;
}

function markDirty() {
  state.dirty = true;
  $('#dirty-badge').classList.remove('is-hidden');
  setSaveStatus('Unsaved local changes.');
}

function clientValidation(mix) {
  const errors = [];
  if (!mix.title) errors.push('Title is required.');
  if (!mix.description) errors.push('Description is required.');
  if (!mix.date) errors.push('Date is required.');
  if (!mix.genre?.length) errors.push('Choose at least one genre.');
  if (!mix.coverImage && !state.files.cover) errors.push('Choose a cover image or upload cover art.');
  return errors;
}

async function saveDraft({ silent = false } = {}) {
  syncDraftFromForm();
  const errors = clientValidation(state.draft);
  if (errors.length) { toast('Draft needs attention', errors[0], 'error'); setSaveStatus(errors[0], 'error'); return false; }
  try {
    const payload = await api('/api/mixes/save', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(state.draft) });
    state.draft = payload.mix;
    state.newRecord = false;
    state.selectedId = payload.mix.id;
    const index = state.mixes.findIndex((mix) => mix.id === payload.mix.id);
    if (index >= 0) state.mixes[index] = clone(payload.mix); else state.mixes.push(clone(payload.mix));
    state.dirty = false;
    renderLibrary();
    renderEditor();
    setSaveStatus('Draft saved to src/content/mixes.', 'success');
    if (!silent) toast('Draft saved', 'Markdown updated locally.');
    return true;
  } catch (error) {
    toast('Could not save draft', error.message, 'error');
    setSaveStatus(error.message, 'error');
    return false;
  }
}

function generateMarkdown(mix) {
  const quote = (value) => JSON.stringify(String(value ?? ''));
  const arr = (items) => `[${(items || []).map(quote).join(', ')}]`;
  const lines = ['---', `title: ${quote(mix.title)}`, `description: ${quote(mix.description)}`, `date: ${mix.date || ''}`, `genre: ${arr(mix.genre)}`];
  for (const key of ['duration', 'bpmRange']) if (mix[key] !== undefined) lines.push(`${key}: ${quote(mix[key])}`);
  lines.push(`trackCount: ${Number(mix.trackCount || 0)}`, `live: ${Boolean(mix.live)}`, `venue: ${quote(mix.venue)}`, `address: ${quote(mix.address)}`, `coverImage: ${quote(mix.coverImage)}`, `audioFile: ${quote(mix.audioFile)}`, `downloadable: ${Boolean(mix.downloadable)}`, `featured: ${Boolean(mix.featured)}`, `tags: ${arr(mix.tags)}`);
  for (const key of ['youtubeUrl', 'spotifyUrl', 'soundcloudUrl', 'mixcloudUrl']) if (mix[key]) lines.push(`${key}: ${quote(mix[key])}`);
  return `${lines.join('\n')}\n---`;
}

function showModal(id) { document.getElementById(id).classList.remove('is-hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('is-hidden'); }

function previewMarkdown() {
  syncDraftFromForm();
  $('#markdown-preview').textContent = generateMarkdown(state.draft);
  showModal('preview-modal');
}

function updateMediaPreview() {
  if (!state.draft) return;
  const coverPreview = $('#cover-preview');
  const coverSource = state.files.cover ? URL.createObjectURL(state.files.cover) : state.draft.coverImage;
  if (coverSource) coverPreview.innerHTML = `<img src="${esc(coverSource)}" alt="Cover preview" onerror="this.parentElement.innerHTML='<span>ART</span>'">`;
  else coverPreview.innerHTML = '<span>ART</span>';
  const audio = $('#audio-preview');
  if (state.files.audio) audio.src = URL.createObjectURL(state.files.audio); else if (state.draft.audioFile) audio.src = state.draft.audioFile; else audio.removeAttribute('src');
}

function setFile(kind, file) {
  if (!file) return;
  state.files[kind] = file;
  const isAudio = kind === 'audio';
  const drop = $(`#${kind}-drop`);
  drop.classList.add('has-file');
  $(`#${kind}-file-name`).textContent = `${file.name} · ready to upload`;
  updateMediaPreview();
  markDirty();
}

async function uploadFile(kind, file) {
  const response = await api(`/api/mixes/upload?id=${encodeURIComponent(state.draft.id)}&kind=${kind}`, {
    method: 'POST', headers: { 'content-type': file.type || 'application/octet-stream', 'x-file-name': file.name }, body: file,
  });
  if (kind === 'audio') state.draft.audioFile = response.upload.publicUrl;
  if (kind === 'cover') state.draft.coverImage = response.upload.publicUrl;
  return response.upload;
}

function openPublishConfirmation() {
  syncDraftFromForm();
  const errors = clientValidation(state.draft);
  if (errors.length) { toast('Cannot publish yet', errors[0], 'error'); setSaveStatus(errors[0], 'error'); return; }
  const rows = [
    ['Mix file', `src/content/mixes/${state.draft.id}.md`],
    ['Audio', state.files.audio ? `${state.files.audio.name} → /mixes/${state.draft.id}${extension(state.files.audio.name)}` : state.draft.audioFile || 'Existing asset'],
    ['Cover art', state.files.cover ? `${state.files.cover.name} → /mixes/${state.draft.id}${extension(state.files.cover.name)}` : state.draft.coverImage || 'Existing asset'],
    ['Destination', 'Lightsail → media.youknowmeasdubbz.com'],
    ['Website', 'GitHub main → Cloudflare Pages'],
  ];
  $('#publish-summary').innerHTML = rows.map(([label, value]) => `<div class="summary-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('');
  showModal('publish-modal');
}

function extension(name) { const match = String(name).match(/\.[a-z0-9]+$/i); return match ? match[0].toLowerCase() : ''; }

async function publishNow() {
  const button = $('#confirm-publish');
  button.disabled = true;
  button.innerHTML = 'Publishing…';
  setSaveStatus('Uploading media and building the site…');
  try {
    const uploads = [];
    if (state.files.audio) uploads.push(await uploadFile('audio', state.files.audio));
    if (state.files.cover) uploads.push(await uploadFile('cover', state.files.cover));
    const payload = await api('/api/publish', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ mix: state.draft }) });
    state.draft = payload.result.mix;
    state.newRecord = false;
    state.selectedId = state.draft.id;
    const index = state.mixes.findIndex((mix) => mix.id === state.draft.id);
    if (index >= 0) state.mixes[index] = clone(state.draft); else state.mixes.push(clone(state.draft));
    state.files = { audio: null, cover: null };
    state.dirty = false;
    closeModal('publish-modal');
    renderLibrary();
    renderEditor();
    setSaveStatus(payload.result.message, 'success');
    toast('Mix published', payload.result.commit ? `Commit ${payload.result.commit.slice(0, 7)} pushed to GitHub.` : payload.result.message);
  } catch (error) {
    toast('Publish stopped', error.message, 'error');
    setSaveStatus(error.message, 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = 'Confirm upload & publish <span>↗</span>';
  }
}

async function load() {
  try {
    const health = await api('/api/health');
    const status = $('#connection-status');
    status.textContent = health.dryRun ? 'Lightsail · dry run' : `Lightsail · ${health.lightsail.host}`;
    status.style.color = 'var(--green)';
  } catch {
    $('#connection-status').textContent = 'Local server issue';
    $('#connection-status').style.color = 'var(--red)';
  }
  try {
    const payload = await api('/api/mixes');
    state.mixes = payload.mixes;
    renderLibrary();
    if (state.mixes[0]) selectMix(state.mixes[0].id);
  } catch (error) {
    toast('Could not load mix library', error.message, 'error');
  }
}

$('#mix-search').addEventListener('input', (event) => { state.search = event.target.value; renderLibrary(); });
$$('[data-filter]').forEach((button) => button.addEventListener('click', () => {
  state.filter = button.dataset.filter;
  $$('[data-filter]').forEach((item) => item.classList.toggle('is-active', item === button));
  renderLibrary();
}));
$('#new-mix-button').addEventListener('click', newMix);
$('#empty-new-button').addEventListener('click', newMix);
$('#refresh-button').addEventListener('click', load);
$('#save-button').addEventListener('click', () => saveDraft());
$('#preview-button').addEventListener('click', previewMarkdown);
$('#publish-button').addEventListener('click', openPublishConfirmation);
$('#confirm-publish').addEventListener('click', publishNow);
$('#copy-markdown').addEventListener('click', async () => { await navigator.clipboard.writeText($('#markdown-preview').textContent); toast('Copied', 'Markdown is ready on your clipboard.'); });
$$('[data-close-modal]').forEach((button) => button.addEventListener('click', () => closeModal(button.dataset.closeModal)));
$$('.modal-backdrop').forEach((modal) => modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(modal.id); }));
$('#mix-form').addEventListener('input', () => { syncDraftFromForm(); markDirty(); });
$('#mix-form').addEventListener('change', () => { syncDraftFromForm(); $('#live-fields').classList.toggle('is-hidden', !state.draft.live); markDirty(); });
$('#audio-file').addEventListener('change', (event) => setFile('audio', event.target.files[0]));
$('#cover-file').addEventListener('change', (event) => setFile('cover', event.target.files[0]));
for (const kind of ['audio', 'cover']) {
  const drop = $(`#${kind}-drop`);
  ['dragenter', 'dragover'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add('is-dragging'); }));
  ['dragleave', 'drop'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove('is-dragging'); }));
  drop.addEventListener('drop', (event) => setFile(kind, event.dataTransfer.files[0]));
}

load();
