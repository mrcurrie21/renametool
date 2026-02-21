"""Tests for renamer.apply_find_replace(), apply_prefix(), apply_suffix()."""

import pytest

from renamer import apply_find_replace, apply_prefix, apply_suffix


class TestApplyFindReplace:
    def test_plain_text_match(self):
        assert apply_find_replace("hello_world", "world", "earth", False) == "hello_earth"

    def test_plain_text_no_match(self):
        assert apply_find_replace("hello_world", "xyz", "abc", False) == "hello_world"

    def test_plain_text_delete(self):
        assert apply_find_replace("hello_world", "_world", "", False) == "hello"

    def test_plain_text_replaces_all_occurrences(self):
        assert apply_find_replace("aaa", "a", "b", False) == "bbb"

    def test_regex_basic(self):
        assert apply_find_replace("file_001", r"\d+", "999", True) == "file_999"

    def test_regex_capture_group(self):
        result = apply_find_replace("2024-01-15", r"(\d{4})-(\d{2})-(\d{2})", r"\3-\2-\1", True)
        assert result == "15-01-2024"

    def test_regex_delete(self):
        assert apply_find_replace("file (copy)", r"\s*\(copy\)", "", True) == "file"

    def test_regex_no_match(self):
        assert apply_find_replace("hello", r"\d+", "X", True) == "hello"

    def test_invalid_regex_raises(self):
        with pytest.raises(Exception):
            apply_find_replace("hello", r"[invalid", "X", True)


class TestApplyPrefix:
    def test_adds_prefix(self):
        assert apply_prefix("world", "hello_") == "hello_world"

    def test_empty_prefix(self):
        assert apply_prefix("world", "") == "world"

    def test_empty_stem(self):
        assert apply_prefix("", "prefix_") == "prefix_"


class TestApplySuffix:
    def test_adds_suffix(self):
        assert apply_suffix("hello", "_world") == "hello_world"

    def test_empty_suffix(self):
        assert apply_suffix("hello", "") == "hello"

    def test_empty_stem(self):
        assert apply_suffix("", "_suffix") == "_suffix"
