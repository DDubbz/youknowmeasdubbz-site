# Local Mix Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-only Dubbz Studio dashboard that edits mix Markdown, uploads media to Lightsail, and safely publishes selected mix changes through the existing GitHub/Cloudflare Pages pipeline.

**Architecture:** A Node built-in HTTP server under `tools/mix-studio/` serves a static dark dashboard on `127.0.0.1:4322` and owns all filesystem, SSH, media, build, and Git operations. Pure helpers isolate frontmatter, validation, safe filenames, and publish planning for unit tests.

**Tech Stack:** Node 20 built-ins, browser HTML/CSS/ES modules, Node `node:test`, existing Astro 5 project, `rsync`, `ssh`, `curl`, GitHub Actions → Cloudflare Pages.

**Spec:** `docs/superpowers/specs/2026-09-18-local-mix-dashboard-design.md`

## Global Constraints

- Bind only to `127.0.0.1`; never expose the dashboard publicly.
- Keep media on Lightsail at `media.youknowmeasdubbz.com` for now.
- Preserve the existing Astro content collection and Cloudflare Pages workflow.
- Never stage unrelated files; never use `git add -A` in the dashboard.
- Do not overwrite existing unrelated uncommitted changes.
- New media references use absolute `https://media.youknowmeasdubbz.com/mixes/<filename>` URLs.

---

### Task 1: Pure mix data helpers

**Files:**
- Create: `tools/mix-studio/lib/mix-data.mjs`
- Test: `tools/mix-studio/test/mix-data.test.mjs`
- Modify: `package.json` to add `test:mix-studio`

**Interfaces:**
- `slugifyTitle(title) -> string`
- `parseMixMarkdown(text, id) -> MixRecord`
- `serializeMixMarkdown(mix) -> string`
- `validateMix(mix) -> { valid: boolean, errors: string[] }`
- `safeAssetName(slug, originalName, allowedExtensions) -> string`

- [ ] Write tests for slug normalization, round-trip frontmatter, required fields, and safe asset names.
- [ ] Run `node --test tools/mix-studio/test/mix-data.test.mjs`; verify the missing module causes the expected failure.
- [ ] Implement a narrow frontmatter parser for the existing scalar, boolean, number, and quoted-array fields.
- [ ] Implement deterministic YAML-like serialization matching current mix Markdown.
- [ ] Implement validation requiring `title`, `description`, `date`, `genre`, and `coverImage`; reject unsafe filenames and unsupported extensions.
- [ ] Run the focused tests and then `npm run test:mix-studio`.

### Task 2: Lightsail and publish command planning

**Files:**
- Create: `tools/mix-studio/lib/publish-plan.mjs`
- Test: `tools/mix-studio/test/publish-plan.test.mjs`

**Interfaces:**
- `buildMediaUrl(filename) -> string`
- `buildRsyncArgs(localPath, remotePath, config) -> string[]`
- `buildRemoteVerifyCommand(remotePath) -> string`
- `buildPublishFileList(mixFile, repoStatus) -> { allowed: boolean, files: string[], reason?: string }`

- [ ] Write tests proving media URLs target `media.youknowmeasdubbz.com`, rsync uses the configured remote path, and publish stages only the selected mix file.
- [ ] Run the focused tests and observe failure before implementation.
- [ ] Implement command-array builders with shell-safe values and a publish planner that ignores unrelated dirty files rather than staging them.
- [ ] Run focused tests and confirm all pass.

### Task 3: Local API server

**Files:**
- Create: `tools/mix-studio/server.mjs`
- Create: `tools/mix-studio/lib/server-utils.mjs`
- Test: `tools/mix-studio/test/server-utils.test.mjs`
- Modify: `package.json` with `mix-studio` script

**Interfaces:**
- `GET /api/health`
- `GET /api/mixes`
- `POST /api/mixes/save`
- `POST /api/mixes/upload`
- `POST /api/publish`

- [ ] Write tests for URL routing, JSON response helpers, and request-size rejection.
- [ ] Run tests to verify the helpers fail before implementation.
- [ ] Implement static serving from `tools/mix-studio/public/` and JSON APIs on the Node built-in server.
- [ ] Load existing `src/content/mixes/*.md`, map each file to its ID, and return sorted records.
- [ ] Write validated Markdown atomically through a temporary sibling file and rename.
- [ ] Add a small multipart parser sufficient for two named file fields (`audio`, `cover`) with a bounded request size.
- [ ] Stage uploads under the OS temp directory, call `rsync` through `spawn`, verify with `ssh` and public `curl`, and remove staged files in `finally` blocks.
- [ ] Add publish flow: save selected mix, run `npm run build`, then `git add -- <selected-file>`, `git commit`, and `git push origin main`; return command output and commit hash.
- [ ] Refuse publish if the selected file is outside the repository or required configuration is missing.
- [ ] Run focused tests and start the server for a smoke check.

### Task 4: Pleasant dashboard UI

**Files:**
- Create: `tools/mix-studio/public/index.html`
- Create: `tools/mix-studio/public/styles.css`
- Create: `tools/mix-studio/public/app.js`

**Interfaces:**
- Consumes the APIs from Task 3.
- Produces an accessible local studio UI with library, editor, upload dropzones, preview player, status log, and publish confirmation.

- [ ] Write a browser smoke test fixture or scripted DOM checks for mix loading, edit selection, validation errors, and publish confirmation copy.
- [ ] Implement the layout: header status bar, KPI rail, searchable mix library, responsive editor, and sticky action footer.
- [ ] Implement visual language: navy background, cyan focus/action states, gold publish state, 2px outlines, compact 8px corners, and responsive mobile stacking.
- [ ] Implement mix cards with cover art, tags, media status, dirty state, and selected state.
- [ ] Implement editor fields, genre/tag chips, audio player, cover preview, drag/drop and file input handling.
- [ ] Implement Save Draft, Upload & Publish, Cancel, and refresh behavior with clear status messages.
- [ ] Add a confirmation modal that lists exact media destinations and the selected Markdown file before publishing.
- [ ] Run the browser smoke check against the local server and verify no console errors.

### Task 5: Documentation and repository integration

**Files:**
- Modify: `README.md` or create `tools/mix-studio/README.md`
- Modify: `.gitignore` only if local staging artifacts require an ignore rule
- Modify: `public/admin/README.md` to point users to the local studio

- [ ] Document setup, start command, required SSH key access, Lightsail destination, and dry-run behavior.
- [ ] Document that the old public dashboard is not the publishing tool.
- [ ] Add `.mix-studio-tmp/` or equivalent ignore rule only if the implementation creates a repository-local staging directory.
- [ ] Run the full project test suite and `npm run build`.

### Task 6: End-to-end verification

**Files:**
- Test: `tools/mix-studio/test/e2e-smoke.mjs`

- [ ] Start the server on an ephemeral test port with a fixture repository path.
- [ ] Verify `GET /api/health` returns local-only status.
- [ ] Verify `GET /api/mixes` returns the current mix count.
- [ ] Save a fixture mix and assert the generated Markdown fields.
- [ ] Run `npm run build` from the repository.
- [ ] Run the server's dry-run upload path and assert no SSH or rsync command is executed.
- [ ] Confirm `git diff --check` is clean for new files.
- [ ] Report any unavailable live Lightsail credential or SSH access as a pending setup item instead of claiming a remote upload occurred.
