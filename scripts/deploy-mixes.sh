#!/bin/bash
# Dubbz Studio — Mix Deployment Pipeline
# Usage: ./scripts/deploy-mixes.sh [--dry-run]
# 
# This script:
# 1. Reads all mix markdown files from src/content/mixes/
# 2. Checks for corresponding audio and cover files in public/mixes/
# 3. Rsyncs media files to the Lightsail server
# 4. Builds the Astro site
# 5. Pushes to git (triggers Cloudflare Pages deploy)

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE — no changes will be made"
fi

# === CONFIG ===
SERVER_USER="ubuntu"
SERVER_HOST="44.216.14.49"
SERVER_MEDIA_PATH="/srv/dubbz-media/public/mixes"
LOCAL_MEDIA_PATH="public/mixes"
CONTENT_PATH="src/content/mixes"

echo "========================================"
echo "  Dubbz Studio — Mix Deployment Pipeline"
echo "========================================"
echo ""

# === STEP 1: Parse mix markdown files ===
echo "📋 Step 1: Scanning mix markdown files..."

declare -a MIX_FILES
declare -a AUDIO_FILES
declare -a COVER_FILES

for mdfile in "$CONTENT_PATH"/*.md; do
    [[ -f "$mdfile" ]] || continue
    MIX_FILES+=("$mdfile")
    
    # Extract audioFile path
    audio=$(grep -E '^audioFile:' "$mdfile" | sed 's/audioFile: *"\?\([^"]*\)"\?/\1/')
    if [[ -n "$audio" ]]; then
        # Remove leading slash and "mixes/" prefix for local path
        local_audio="${audio#/}"
        local_audio="${local_audio#mixes/}"
        if [[ -n "$local_audio" ]]; then
            AUDIO_FILES+=("$local_audio")
        fi
    fi
    
    # Extract coverImage path
    cover=$(grep -E '^coverImage:' "$mdfile" | sed 's/coverImage: *"\?\([^"]*\)"\?/\1/')
    if [[ -n "$cover" ]]; then
        local_cover="${cover#/}"
        local_cover="${local_cover#mixes/}"
        if [[ -n "$local_cover" ]]; then
            COVER_FILES+=("$local_cover")
        fi
    fi
done

echo "   Found ${#MIX_FILES[@]} mix markdown files"
echo "   Found ${#AUDIO_FILES[@]} audio file references"
echo "   Found ${#COVER_FILES[@]} cover image references"
echo ""

# === STEP 2: Check for missing local files ===
echo "🔍 Step 2: Checking for missing local files..."

MISSING=0
for file in "${AUDIO_FILES[@]}" "${COVER_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "   ⚠️  MISSING: $file"
        ((MISSING++))
    fi
done

if [[ $MISSING -gt 0 ]]; then
    echo ""
    echo "   ⚠️  $MISSING files are missing locally."
    echo "   These files may already exist on the server."
    echo "   Proceeding with build + deploy..."
    echo ""
fi
echo ""

# === STEP 3: Sync media to server ===
echo "📤 Step 3: Syncing media files to server..."

if [[ "$DRY_RUN" == true ]]; then
    echo "   [DRY RUN] Would rsync $LOCAL_MEDIA_PATH/ to $SERVER_USER@$SERVER_HOST:$SERVER_MEDIA_PATH/"
else
    # Ensure remote directory exists
    ssh -o BatchMode=yes "$SERVER_USER@$SERVER_HOST" "mkdir -p $SERVER_MEDIA_PATH"
    
    # Rsync with progress, only newer files
    rsync -avz --progress "$LOCAL_MEDIA_PATH/" "$SERVER_USER@$SERVER_HOST:$SERVER_MEDIA_PATH/"
    
    echo "   ✅ Media files synced to server"
fi
echo ""

# === STEP 4: Build the site ===
echo "🏗️  Step 4: Building Astro site..."

if [[ "$DRY_RUN" == true ]]; then
    echo "   [DRY RUN] Would run: npm run build"
else
    npm run build
    
    if [[ $? -eq 0 ]]; then
        echo "   ✅ Build successful"
    else
        echo "   ❌ Build failed"
        exit 1
    fi
fi
echo ""

# === STEP 5: Push to git ===
echo "📦 Step 5: Pushing to git..."

if [[ "$DRY_RUN" == true ]]; then
    echo "   [DRY RUN] Would run: git add -A && git commit -m 'Update mixes' && git push origin main"
else
    git add -A
    
    # Check if there are changes to commit
    if git diff --cached --quiet; then
        echo "   ℹ️  No changes to commit"
    else
        git commit -m "Update mixes — $(date +%Y-%m-%d)"
        git push origin main
        echo "   ✅ Pushed to git"
    fi
fi
echo ""

# === SUMMARY ===
echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo ""
echo "   Mixes: ${#MIX_FILES[@]}"
echo "   Audio files: ${#AUDIO_FILES[@]}"
echo "   Cover images: ${#COVER_FILES[@]}"
echo ""
echo "   Site: https://youknowmeasdubbz.com"
echo "   Dashboard: https://youknowmeasdubbz.com/admin/index.html"
echo ""
echo "   Cloudflare Pages will auto-deploy from git."
echo "   Allow 30-60 seconds for the deploy to complete."
echo ""
