import { getCollection } from 'astro:content';

export async function GET({ url }) {
  const featured = url.searchParams.get('featured') === 'true';
  const limit = parseInt(url.searchParams.get('limit') || '50');

  const allMixes = await getCollection('mixes');

  let filtered = allMixes
    .filter(mix => mix.data.published !== false)
    .sort((a, b) => {
      const da = a.data.date ? new Date(a.data.date).getTime() : 0;
      const db = b.data.date ? new Date(b.data.date).getTime() : 0;
      return db - da;
    });

  if (featured) {
    filtered = filtered.filter(mix => mix.data.featured);
  }

  const limited = filtered.slice(0, limit);

  return new Response(JSON.stringify(limited.map(mix => ({
    id: mix.id,
    title: mix.data.title,
    description: mix.data.description,
    date: mix.data.date ? mix.data.date.toISOString().split('T')[0] : undefined,
    genre: mix.data.genre,
    duration: mix.data.duration,
    bpmRange: mix.data.bpmRange,
    trackCount: mix.data.trackCount,
    youtubeUrl: mix.data.youtubeUrl,
    spotifyUrl: mix.data.spotifyUrl,
    soundcloudUrl: mix.data.soundcloudUrl,
    mixcloudUrl: mix.data.mixcloudUrl,
    coverImage: mix.data.coverImage,
    audioFile: mix.data.audioFile,
    downloadable: mix.data.downloadable,
    featured: mix.data.featured,
    tags: mix.data.tags
  }))), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }
  });
}