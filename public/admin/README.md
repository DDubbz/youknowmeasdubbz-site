# Dubbz Studio — Legacy Public Mix Dashboard

> The production mix-management dashboard is now local-only. Start it from the repository root with `npm run mix-studio`, then open `http://127.0.0.1:4322`. See `tools/mix-studio/README.md` for the complete workflow.

This legacy page is informational only. It does not upload media, write Markdown, or publish the site.


## What It Does

- Lists all mixes from `/api/mixes.json` with cover art, genres, live status, and metadata
- Edit any mix's title, date, duration, BPM, track count, genres, live/venue info, cover image, audio file, tags, description, featured, and downloadable status
- Toggle genres with click-to-select picker
- Preview the markdown output for any mix
- Export all mixes as a single markdown file
- Add new mixes or delete existing ones

## How to Use

1. **Open the dashboard** at the URL above
2. **Click "Edit"** on any mix card
3. **Change fields** — title, date, duration, genres (click to toggle), live/venue, cover image path, audio file path, tags, description, featured, downloadable
4. **Click "Save"** — saves to browser localStorage
5. **Click "Preview .md"** to see the markdown output
6. **Click "Download .md"** to save the markdown file
7. **Copy the markdown** and paste it into the corresponding file in `src/content/mixes/`
8. **Run `npm run build && git add -A && git commit -m "Update mix" && git push`** to deploy

## Workflow for Adding a New Mix

1. Upload audio to `public/mixes/your-name.mp3`
2. Upload cover image to `public/mixes/your-name.webp` (1200x1200)
3. Click **"+ New Mix"** in the dashboard
4. Fill in all fields
5. Click **"Save"** then **"Download .md"**
6. Save the downloaded file to `src/content/mixes/your-name.md`
7. Build and deploy

## Important Notes

- The dashboard saves to **browser localStorage** only — it does NOT directly write to the markdown files
- You must manually copy the markdown output to the `.md` file and commit
- The dashboard reads from `/api/mixes.json` which is generated from the markdown files at build time
- After editing markdown files, run `npm run build` to regenerate the API
- The dashboard will show the updated data after a rebuild (click "Refresh from API")

## Genre Options

The dashboard includes these genre tags:
`house`, `deep-house`, `tech-house`, `hip-hop`, `r&b`, `afrobeats`, `amapiano`, `dancehall`, `reggaeton`, `bachata`, `latin`, `top-40`, `open-format`, `trap`, `kompa`, `bounce`, `slow-jams`, `classics`, `throwbacks`, `edm`, `pop`, `disco`, `funk`, `soul`, `jazz`, `reggae`, `afro-house`, `techno`, `dnb`, `lo-fi`

You can add custom genres by typing them in the tags field (comma-separated).
