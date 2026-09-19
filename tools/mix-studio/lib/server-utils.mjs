const ROUTES = new Map([
  ['GET /api/health', 'health'],
  ['GET /api/mixes', 'list-mixes'],
  ['POST /api/mixes/save', 'save-mix'],
  ['POST /api/mixes/upload', 'upload-media'],
  ['POST /api/publish', 'publish'],
]);

export function routeRequest(method, pathname) {
  return ROUTES.get(`${method.toUpperCase()} ${pathname}`) ?? null;
}

export function json(payload, status = 200) {
  return {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify(payload),
  };
}

export function isAllowedContentType(contentType = '') {
  return new Set([
    'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/aac', 'audio/flac',
    'image/jpeg', 'image/png', 'image/webp',
  ]).has(contentType.split(';')[0].trim().toLowerCase());
}

export function writeResponse(res, response) {
  res.writeHead(response.status, {
    ...response.headers,
    'cache-control': 'no-store',
  });
  res.end(response.body);
}
