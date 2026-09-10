import { getCollection } from 'astro:content';

export async function GET({ url }) {
  const upcoming = url.searchParams.get('upcoming') === 'true';
  const limit = parseInt(url.searchParams.get('limit') || '50');

  const allGigs = await getCollection('gigs');

  let filtered = allGigs
    .filter(gig => gig.data.published !== false)
    .sort((a, b) => new Date(a.data.date).getTime() - new Date(b.data.date).getTime());

  if (upcoming) {
    const now = new Date();
    filtered = filtered.filter(gig => new Date(gig.data.date) >= now);
  }

  const limited = filtered.slice(0, limit);

  return new Response(JSON.stringify(limited.map(gig => ({
    id: gig.id,
    title: gig.data.title,
    venue: gig.data.venue,
    address: gig.data.address,
    date: gig.data.date.toISOString().split('T')[0],
    startTime: gig.data.startTime,
    endTime: gig.data.endTime,
    status: gig.data.status,
    fee: gig.data.fee,
    feeType: gig.data.feeType,
    contactName: gig.data.contactName,
    contactPhone: gig.data.contactPhone,
    contactEmail: gig.data.contactEmail,
    notes: gig.data.notes,
    recordingUrl: gig.data.recordingUrl,
    debriefUrl: gig.data.debriefUrl,
    isRecurring: gig.data.isRecurring,
    recurringPattern: gig.data.recurringPattern,
    featured: gig.data.featured
  }))), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600'
    }
  });
}