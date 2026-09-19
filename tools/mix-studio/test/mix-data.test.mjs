import test from 'node:test';
import assert from 'node:assert/strict';
import {
  slugifyTitle,
  parseMixMarkdown,
  serializeMixMarkdown,
  validateMix,
  safeAssetName,
} from '../lib/mix-data.mjs';

test('slugifyTitle creates stable URL-safe slugs', () => {
  assert.equal(slugifyTitle('  Cultural Council — Open Format Mix!  '), 'cultural-council-open-format-mix');
  assert.equal(slugifyTitle('R&B / Summer 2024'), 'r-b-summer-2024');
});

test('parseMixMarkdown reads the existing mix frontmatter shape', () => {
  const mix = parseMixMarkdown(`---
title: "Avacado Cantina - Saturday Sessions"
description: "Weekly residency set"
date: 2024-09-05
genre: ["afrobeats", "latin", "classics"]
duration: "88:32"
trackCount: 68
featured: true
downloadable: false
tags: ["residency", "weekly"]
coverImage: "/mixes/avacado.webp"
audioFile: "/mixes/avacado.mp3"
---`, 'avacado-saturday');

  assert.deepEqual(mix, {
    id: 'avacado-saturday',
    title: 'Avacado Cantina - Saturday Sessions',
    description: 'Weekly residency set',
    date: '2024-09-05',
    genre: ['afrobeats', 'latin', 'classics'],
    duration: '88:32',
    trackCount: 68,
    featured: true,
    downloadable: false,
    tags: ['residency', 'weekly'],
    coverImage: '/mixes/avacado.webp',
    audioFile: '/mixes/avacado.mp3',
  });
});

test('serializeMixMarkdown round-trips parsed metadata', () => {
  const source = {
    id: 'test-mix',
    title: 'Test Mix',
    description: 'A mix with, punctuation',
    date: '2026-09-18',
    genre: ['house', 'r&b'],
    duration: '01:02:03',
    bpmRange: '100-128',
    trackCount: 12,
    live: false,
    venue: '',
    address: '',
    coverImage: 'https://media.youknowmeasdubbz.com/mixes/test-mix.webp',
    audioFile: 'https://media.youknowmeasdubbz.com/mixes/test-mix.mp3',
    downloadable: true,
    featured: true,
    tags: ['summer', 'test'],
    youtubeUrl: '',
    soundcloudUrl: '',
    spotifyUrl: '',
    mixcloudUrl: '',
  };
  const markdown = serializeMixMarkdown(source);
  assert.match(markdown, /^date: 2026-09-18$/m);
  assert.doesNotMatch(markdown, /^date: \"2026-09-18\"$/m);
  const roundTrip = parseMixMarkdown(markdown, 'test-mix');
  assert.deepEqual(roundTrip, source);
});

test('validateMix returns actionable errors for missing required data', () => {
  const result = validateMix({ title: '', description: '', date: '', genre: [], coverImage: '' });
  assert.equal(result.valid, false);
  assert.deepEqual(result.errors, [
    'Title is required.',
    'Description is required.',
    'Date is required.',
    'Choose at least one genre.',
    'Cover image is required.',
  ]);
});

test('safeAssetName preserves extension and prevents path traversal', () => {
  assert.equal(safeAssetName('summer-set', '../My Cover.WEBP', ['.webp']), 'summer-set.webp');
  assert.equal(safeAssetName('summer-set', 'mix.MP3', ['.mp3', '.wav']), 'summer-set.mp3');
  assert.throws(() => safeAssetName('summer-set', 'cover.gif', ['.webp']), /Unsupported asset type/);
});
