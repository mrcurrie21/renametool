"""Pattern detection for batch file renaming."""

import re
from pathlib import Path

PATTERNS = {
    "ISO date (YYYY-MM-DD)": r"\d{4}-\d{2}-\d{2}",
    "US date (MM-DD-YYYY)": r"\d{2}-\d{2}-\d{4}",
    "Compact date (YYYYMMDD)": r"\d{8}",
    "Sequence code (IMG_001, DSC00234)": r"[A-Z]{2,5}[_-]?\d{3,6}",
    "Parenthetical (copy), (1)": r"\([^)]+\)",
    "Bracketed [draft], [v2]": r"\[[^\]]+\]",
    "Trailing numbers (_01, -3)": r"[-_ ]\d{1,4}$",
    "Resolution tag": r"(?:720p|1080p|2160p|4K)",
    "Source tag": r"(?:BluRay|WEB-DL|HDRip|BRRip|WEBRip|HDTV)",
    "Codec tag": r"(?:x264|x265|HEVC|H\.?264|H\.?265|AVC)",
    "Release group": r"\[[^\]]*\]|-[A-Za-z0-9]+$",
}

TV_REGEX = re.compile(
    r"(?P<show>.+?)[.\s_-]+[Ss](?P<season>\d{1,2})[Ee](?P<episode>\d{1,2})"
    r"(?P<remainder>[.\s_-].*)?$",
    re.IGNORECASE,
)

_JUNK_RE = re.compile(
    r"(?:720p|1080p|2160p|4K|BluRay|WEB-DL|HDRip|BRRip|WEBRip|HDTV"
    r"|x264|x265|HEVC|H\.?264|H\.?265|AVC|\[[^\]]*\]|-[A-Za-z0-9]+$).*$",
    re.IGNORECASE,
)

MOVIE_REGEX = re.compile(
    r"(?P<title>.+?)[.\s_-]+\(?(?P<year>(?:19|20)\d{2})\)?",
    re.IGNORECASE,
)

THRESHOLD = 2


def _clean_name(raw: str) -> str:
    """Replace dots, underscores, and hyphens with spaces, strip, and title-case."""
    return re.sub(r"[._-]+", " ", raw).strip().title()


def parse_tv_filename(filename: str) -> dict | None:
    """Parse a TV episode filename and return extracted components.

    Returns a dict with keys: show, season, episode, title.
    Returns None if the filename doesn't match the TV pattern.
    """
    # Strip known media extensions; avoid Path.stem which mishandles e.g. "Show.S01E01"
    name = Path(filename).name
    ext_match = re.search(r"\.(mkv|mp4|avi|mov|wmv|flv|webm|m4v|mpg|mpeg|ts|srt|sub)$", name, re.I)
    stem = name[: ext_match.start()] if ext_match else name
    m = TV_REGEX.match(stem)
    if not m:
        return None
    show = _clean_name(m.group("show"))
    season = int(m.group("season"))
    episode = int(m.group("episode"))
    remainder = m.group("remainder") or ""
    # Strip junk tags from remainder to extract episode title
    title_raw = _JUNK_RE.sub("", remainder).strip(" ._-")
    title = _clean_name(title_raw) if title_raw else ""
    return {"show": show, "season": season, "episode": episode, "title": title}


def parse_movie_filename(filename: str) -> dict | None:
    """Parse a movie filename and return extracted components.

    Returns a dict with keys: title, year.
    Returns None if the filename doesn't match the movie pattern.
    """
    stem = Path(filename).stem
    m = MOVIE_REGEX.match(stem)
    if not m:
        return None
    title = _clean_name(m.group("title"))
    year = int(m.group("year"))
    return {"title": title, "year": year}


def detect_patterns(filenames: list[str]) -> list[dict]:
    """Detect common patterns across filenames.

    Returns a list of dicts with keys: name, regex, matches, examples.
    Only patterns matching in THRESHOLD or more files are returned.
    """
    stems = [Path(f).stem for f in filenames]
    results = []

    for name, regex in PATTERNS.items():
        compiled = re.compile(regex)
        matches = []
        examples = []
        for stem in stems:
            m = compiled.search(stem)
            if m:
                matches.append(stem)
                if len(examples) < 3:
                    examples.append(m.group())

        if len(matches) >= THRESHOLD:
            results.append(
                {
                    "name": name,
                    "regex": regex,
                    "match_count": len(matches),
                    "examples": examples,
                }
            )

    return results
