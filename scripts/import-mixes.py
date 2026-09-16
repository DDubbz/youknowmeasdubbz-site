#!/usr/bin/env python3
"""
Dubbz Studio — Mix Markdown Parser & Updater

Reads an all-mixes.md file (like the one exported from the dashboard)
and updates the individual markdown files in src/content/mixes/.

Usage:
    python3 scripts/import-mixes.py <path-to-all-mixes.md>
    python3 scripts/import-mixes.py ~/Downloads/all-mixes.md

This script:
1. Parses the markdown file into individual mix entries
2. Compares with existing files in src/content/mixes/
3. Creates new files for new mixes
4. Updates existing files with changed data
5. Reports what was added/updated/unchanged
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIXES_DIR = PROJECT_ROOT / "src" / "content" / "mixes"


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a markdown string."""
    match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}
    
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        
        # Parse arrays
        if value.startswith('[') and value.endswith(']'):
            items = re.findall(r'"([^"]*)"', value)
            fm[key] = items
        # Parse booleans
        elif value.lower() in ('true', 'false'):
            fm[key] = value.lower() == 'true'
        # Parse numbers
        elif value.isdigit():
            fm[key] = int(value)
        # Parse quoted strings
        elif value.startswith('"') and value.endswith('"'):
            fm[key] = value[1:-1]
        else:
            fm[key] = value
    
    return fm


def parse_all_mixes(content: str) -> list:
    """Parse an all-mixes markdown file into individual mix entries.
    
    The file format is multiple YAML frontmatter blocks.
    Each block starts with --- and ends with ---, with fields in between.
    Blocks may be separated by blank lines or additional --- lines.
    """
    lines = content.strip().split('\n')
    mixes = []
    current_block = []
    in_frontmatter = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if stripped == '---':
            if in_frontmatter:
                # End of frontmatter block — parse it
                current_block.append(line)
                block_text = '\n'.join(current_block)
                fm = parse_frontmatter(block_text)
                if fm and fm.get('title'):
                    mixes.append(fm)
                current_block = []
                in_frontmatter = False
            else:
                # Check if next non-empty line looks like frontmatter
                # (contains a key: value pattern)
                next_content = ''
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip():
                        next_content = lines[j].strip()
                        break
                
                # Only start a new block if next line looks like frontmatter
                if next_content and ':' in next_content and not next_content.startswith('---'):
                    in_frontmatter = True
                    current_block = [line]
                # Otherwise, skip this --- (it's a separator)
        elif in_frontmatter:
            current_block.append(line)
    
    # Handle last block if not closed
    if current_block and in_frontmatter:
        block_text = '\n'.join(current_block)
        fm = parse_frontmatter(block_text)
        if fm and fm.get('title'):
            mixes.append(fm)
    
    return mixes


def mix_to_markdown(fm: dict) -> str:
    """Convert a mix frontmatter dict to markdown format."""
    lines = ['---']
    
    # Required fields
    lines.append(f'title: "{fm.get("title", "")}"')
    lines.append(f'description: "{fm.get("description", "")}"')
    lines.append(f'date: {fm.get("date", "")}')
    
    # Genre array
    genres = fm.get('genre', [])
    if genres:
        genre_str = ', '.join(f'"{g}"' for g in genres)
        lines.append(f'genre: [{genre_str}]')
    else:
        lines.append('genre: []')
    
    lines.append(f'duration: "{fm.get("duration", "")}"')
    lines.append(f'bpmRange: "{fm.get("bpmRange", "")}"')
    lines.append(f'trackCount: {fm.get("trackCount", 0)}')
    
    # Live info
    lines.append(f'live: {"true" if fm.get("live", False) else "false"}')
    lines.append(f'venue: "{fm.get("venue", "")}"')
    lines.append(f'address: "{fm.get("address", "")}"')
    
    # Media
    lines.append(f'coverImage: "{fm.get("coverImage", "")}"')
    lines.append(f'audioFile: "{fm.get("audioFile", "")}"')
    
    # Display
    lines.append(f'downloadable: {"true" if fm.get("downloadable", False) else "false"}')
    lines.append(f'featured: {"true" if fm.get("featured", False) else "false"}')
    
    # Tags
    tags = fm.get('tags', [])
    if tags:
        tag_str = ', '.join(f'"{t}"' for t in tags)
        lines.append(f'tags: [{tag_str}]')
    else:
        lines.append('tags: []')
    
    # Links
    lines.append(f'youtubeUrl: "{fm.get("youtubeUrl", "https://youtube.com/@youknowmeasdubbz")}"')
    lines.append(f'soundcloudUrl: "{fm.get("soundcloudUrl", "https://soundcloud.com/youknowmeasdubbz")}"')
    
    lines.append('---')
    return '\n'.join(lines)


def get_slug(title: str) -> str:
    """Convert a title to a slug for the filename."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug.strip('-')


def find_existing_file(title: str, existing_files: list) -> Path:
    """Find an existing file that matches the title (by slug or exact match)."""
    slug = get_slug(title)
    title_lower = title.strip().lower()
    
    for f in existing_files:
        # Match by slug
        if f.stem == slug:
            return f
        # Match by exact title in frontmatter
        try:
            content = f.read_text()
            fm = parse_frontmatter(content)
            existing_title = fm.get('title', '').strip().lower()
            if existing_title == title_lower:
                return f
        except Exception:
            pass
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/import-mixes.py <path-to-all-mixes.md>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1]).expanduser()
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    content = input_file.read_text()
    mixes = parse_all_mixes(content)
    
    # Deduplicate by title (keep first occurrence)
    seen_titles = set()
    unique_mixes = []
    for m in mixes:
        title = m.get('title', '').strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_mixes.append(m)
    
    print(f"📋 Found {len(unique_mixes)} unique mixes in {input_file.name}")
    if len(unique_mixes) < len(mixes):
        print(f"   ⚠️  Removed {len(mixes) - len(unique_mixes)} duplicate(s)")
    print()
    
    MIXES_DIR.mkdir(parents=True, exist_ok=True)
    existing_files = list(MIXES_DIR.glob('*.md'))
    
    added = 0
    updated = 0
    unchanged = 0
    
    for fm in unique_mixes:
        title = fm.get('title', '')
        if not title:
            print("   ⚠️  Skipping mix with no title")
            continue
        
        # Try to find existing file by title or slug
        existing = find_existing_file(title, existing_files)
        
        if existing:
            # Update existing file
            old_content = existing.read_text()
            new_content = mix_to_markdown(fm)
            if old_content.strip() == new_content.strip():
                print(f"   ✅ Unchanged: {title}")
                unchanged += 1
            else:
                existing.write_text(new_content)
                print(f"   🔄 Updated: {title}")
                updated += 1
        else:
            # Create new file
            slug = get_slug(title)
            filepath = MIXES_DIR / f"{slug}.md"
            filepath.write_text(mix_to_markdown(fm))
            print(f"   ➕ Added: {title}")
            added += 1
    
    print()
    print(f"📊 Summary: {added} added, {updated} updated, {unchanged} unchanged")
    print()
    print("Next steps:")
    print("  1. Upload any new audio/cover files to public/mixes/")
    print("  2. Run: bash scripts/deploy-mixes.sh")
    print("  3. Or: npm run build && git add -A && git commit -m 'Update mixes' && git push")


if __name__ == '__main__':
    main()
