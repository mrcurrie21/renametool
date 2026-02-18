"""Pattern detection for batch file renaming."""

import re

PATTERNS = {
    "ISO date (YYYY-MM-DD)": r"\d{4}-\d{2}-\d{2}",
    "US date (MM-DD-YYYY)": r"\d{2}-\d{2}-\d{4}",
    "Compact date (YYYYMMDD)": r"\d{8}",
    "Sequence code (IMG_001, DSC00234)": r"[A-Z]{2,5}[_-]?\d{3,6}",
    "Parenthetical (copy), (1)": r"\([^)]+\)",
    "Bracketed [draft], [v2]": r"\[[^\]]+\]",
    "Trailing numbers (_01, -3)": r"[-_ ]\d{1,4}$",
}

THRESHOLD = 2


def detect_patterns(filenames: list[str]) -> list[dict]:
    """Detect common patterns across filenames.

    Returns a list of dicts with keys: name, regex, matches, examples.
    Only patterns matching in THRESHOLD or more files are returned.
    """
    from pathlib import Path

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
            results.append({
                "name": name,
                "regex": regex,
                "match_count": len(matches),
                "examples": examples,
            })

    return results
