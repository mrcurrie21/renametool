"""Tests for patterns.detect_patterns()."""

from patterns import detect_patterns


def test_detects_iso_date():
    files = [
        "report_2024-01-15.txt",
        "report_2024-03-22.txt",
        "notes.txt",
    ]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "ISO date (YYYY-MM-DD)" in names


def test_detects_us_date():
    files = ["file_01-15-2024.txt", "file_03-22-2024.txt", "other.txt"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "US date (MM-DD-YYYY)" in names


def test_detects_sequence_code():
    files = ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "Sequence code (IMG_001, DSC00234)" in names


def test_detects_parenthetical():
    files = ["backup(copy).docx", "backup(1).docx", "other.docx"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "Parenthetical (copy), (1)" in names


def test_detects_bracketed():
    files = ["doc[draft].txt", "doc[v2].txt", "other.txt"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "Bracketed [draft], [v2]" in names


def test_detects_trailing_numbers():
    files = ["photo_01.jpg", "photo_02.jpg", "photo_03.jpg"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "Trailing numbers (_01, -3)" in names


def test_below_threshold_not_returned():
    # Only one file matches — below THRESHOLD of 2
    files = ["report_2024-01-15.txt", "notes.txt", "other.txt"]
    results = detect_patterns(files)
    names = [r["name"] for r in results]
    assert "ISO date (YYYY-MM-DD)" not in names


def test_returns_empty_for_no_matches():
    files = ["alpha.txt", "beta.txt", "gamma.txt"]
    results = detect_patterns(files)
    assert results == []


def test_match_count_is_correct():
    files = ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg"]
    results = detect_patterns(files)
    seq = next(r for r in results if "Sequence" in r["name"])
    assert seq["match_count"] == 3


def test_examples_capped_at_three():
    files = [f"IMG_{i:03d}.jpg" for i in range(1, 8)]
    results = detect_patterns(files)
    seq = next(r for r in results if "Sequence" in r["name"])
    assert len(seq["examples"]) <= 3


def test_examples_are_matched_substrings():
    files = ["IMG_001.jpg", "IMG_002.jpg"]
    results = detect_patterns(files)
    seq = next(r for r in results if "Sequence" in r["name"])
    for example in seq["examples"]:
        assert any(example in f for f in ["IMG_001", "IMG_002"])
