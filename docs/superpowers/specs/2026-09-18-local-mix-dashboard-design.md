# Local Mix Studio Design

**Date:** 2026-09-18
**Status:** Approved for implementation

## Objective

Replace the existing browser-only `/admin` mix page with a local-only dashboard that lets Wedly create, edit, tag, preview, upload, and publish mixes without manually copying Markdown or using separate media commands.

## Constraints

- The dashboard must bind to `127.0.0.1` and must not be deployed to Cloudflare Pages.
- Keep media on the existing Lightsail server at `media.youknowmeasdubbz.com` for now.
- Do not place SSH credentials or deployment commands in browser JavaScript.
- Preserve the existing Astro content collection and GitHub → Cloudflare Pages workflow.
- Do not overwrite unrelated uncommitted site changes.
- New uploaded audio and cover assets go to `/srv/dubbz-media/public/mixes/` and are referenced with absolute `https://media.youknowmeasdubbz.com/mixes/...` URLs.

## User Experience

The dashboard is a dark Dubbz Studio workspace: cyan primary actions, gold publish state, strong outlines, compact cards, and a split layout with a mix library on the left and an editor panel on the right. The top bar shows Local Studio, connection status, mix count, and the publish action. The editor supports drag-and-drop audio/cover files, tag chips, metadata fields, audio preview, and a deploy summary before execution.

The main workflow is:

1. Open the local studio.
2. Select an existing mix or create a new one.
3. Edit metadata and tags.
4. Choose audio and cover files.
5. Save draft locally to the content Markdown file.
6. Click Upload & Publish.
7. Confirm the file summary.
8. The server uploads media, verifies public URLs, builds Astro, stages only selected mix files, commits, and pushes.

## Architecture

`tools/mix-studio/server.mjs` is a Node HTTP server using only Node built-ins for the API and static file serving. The browser UI is plain HTML/CSS/ES modules under `tools/mix-studio/public/`. The server owns filesystem reads/writes and invokes `rsync`, `ssh`, `curl`, `npm`, and `git` through controlled argument arrays. `tools/mix-studio/lib/` contains pure, testable helpers for frontmatter, validation, filenames, and publish planning.

The dashboard API exposes:

- `GET /api/mixes` — load current Markdown entries.
- `POST /api/mixes/save` — validate and atomically write one Markdown entry.
- `POST /api/mixes/upload` — upload selected media to Lightsail and verify it.
- `POST /api/publish` — build and publish a selected mix file.
- `GET /api/health` — local server and configuration status.

The browser sends multipart uploads using `fetch`; no remote credentials are ever returned to the browser.

## Data Policy

The existing frontmatter fields remain the source of truth. New entries use the existing schema and add no runtime database. Drafts are written directly to `src/content/mixes/<slug>.md` only after validation. Uploads are staged in a temporary local directory and removed after success or failure.

## Failure Handling

- Reject unsupported file types before any remote action.
- Reject duplicate slugs and missing required fields.
- Never write Markdown until requested uploads pass remote verification.
- Never push if the Astro build fails.
- Never run `git add -A`; stage only the exact selected mix Markdown file.
- Return structured error details to the UI and preserve the editor state.

## Verification

Unit tests cover parsing, serialization, slug safety, validation, publish-file selection, and command argument construction. Integration checks start the local server, load the mix list, save a fixture mix, and run `npm run build`. Remote upload verification is available as a dry-run and requires existing SSH access before live execution.
