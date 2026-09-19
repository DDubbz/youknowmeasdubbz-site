import type { APIRoute } from 'astro';

const paths = [
  '/', '/about/', '/contact/', '/corporate-event-dj-south-florida/', '/gigs/',
  '/journal/', '/journal/wedding-mix-timeline/', '/journal/will-ai-replace-your-event-dj/',
  '/mixes/', '/services/'
];

export const GET: APIRoute = () => {
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${paths.map(path => `  <url><loc>https://youknowmeasdubbz.com${path}</loc></url>`).join('\n')}\n</urlset>\n`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
