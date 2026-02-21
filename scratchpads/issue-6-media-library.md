# Issue #6 — Add media library naming patterns (Plex/Jellyfin)
https://github.com/mrcurrie21/renametool/issues/6

## Key user decision
Use **named regex capture groups** to auto-detect TV show components from existing filenames.
No manual entry or external API — the regex does the work.

## Named capture group patterns (to add to patterns.py)
```python
# TV show full pattern (combined)
TV_REGEX = re.compile(
    r'(?P<show>.+?)[.\s_-]+[Ss](?P<season>\d{1,2})[Ee](?P<episode>\d{1,2})'
    r'(?:[.\s_-]*(?P<title>[^(\[]+?))?'
    r'(?:[.\s_-]*(?:720p|1080p|2160p|4K|BluRay|WEB-DL|x264|x265|HEVC).*)?$',
    re.IGNORECASE
)

# Movie pattern
MOVIE_REGEX = re.compile(
    r'(?P<title>.+?)[.\s_-]+\(?(?P<year>(?:19|20)\d{2})\)?',
    re.IGNORECASE
)
```

## Additional patterns for patterns.py (junk stripping)
- Resolution: `(720p|1080p|2160p|4K)`
- Source: `(BluRay|WEB-DL|HDRip|BRRip|WEBRip|HDTV)`
- Codec: `(x264|x265|HEVC|H\.?264|H\.?265|AVC)`
- Group: `\[.*?\]` or `-[A-Za-z0-9]+$`

## Key files to touch
- `patterns.py` — add TV_REGEX, MOVIE_REGEX, junk patterns, `parse_tv_filename()`, `parse_movie_filename()`
- `renamer.py` — add "Media Library Rename" operation, wizard sub-flow

## Wizard flow for TV mode
1. Run `parse_tv_filename(stem)` on each selected file
2. Show a table: filename | detected show | season | episode | title
3. User confirms or overrides per-field
4. Construct: `{show} - S{season:02d}E{episode:02d} - {title}.ext` (skip title if empty)

## Wizard flow for Movie mode
1. Prompt for movie title and year (pre-fill from `parse_movie_filename()` if detected)
2. Construct: `{title} ({year}).ext`
