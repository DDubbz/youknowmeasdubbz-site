# Dubbz Mix Studio — Local Dashboard

The real mix-management dashboard now runs locally and is intentionally not deployed with the public Astro site.

## Start it

From the repository root:

```bash
npm run mix-studio
```

Open `http://127.0.0.1:4322`.

For a safe local test that never contacts Lightsail or pushes GitHub:

```bash
MIX_STUDIO_DRY_RUN=1 npm run mix-studio
```

## Workflow

1. Select an existing mix or click **New mix**.
2. Edit title, description, date, duration, BPM, genres, tags, and release settings.
3. Drag in audio and cover art, or use the file controls.
4. Use **Save Draft** to update `src/content/mixes/<slug>.md` locally.
5. Use **Preview Markdown** to inspect the exact frontmatter.
6. Use **Upload & Publish** to confirm the destination, upload selected media to Lightsail, verify the public URL, run the Astro build, and push only the selected mix Markdown file to `main`.

## Storage and publishing

- Media destination: `ubuntu@44.216.14.49:/srv/dubbz-media/public/mixes/`
- Public media base: `https://media.youknowmeasdubbz.com/mixes/`
- Site deployment: GitHub Actions → Cloudflare Pages
- The browser never receives SSH credentials or runs remote commands.

The dashboard reads the defaults above from `tools/mix-studio/lib/publish-plan.mjs`. Override them with `DUBBZ_LIGHTSAIL_USER`, `DUBBZ_LIGHTSAIL_HOST`, `DUBBZ_LIGHTSAIL_DIR`, and `DUBBZ_MEDIA_BASE_URL` when needed.

## Requirements

- Node 20+
- `rsync`, `ssh`, and `curl` available on the Mac
- SSH key access to the Lightsail host for live uploads
- GitHub push access for publishing

## Important safety behavior

- The server binds only to `127.0.0.1`.
- `git add -A` is never used.
- Publishing pauses if unrelated files are already staged.
- A failed upload, media verification, build, or push is reported as a failure; it is never presented as published.
- Existing relative media paths are preserved until an asset is explicitly replaced.

The legacy `/admin/index.html` page is not the publishing tool; use the local studio instead.
