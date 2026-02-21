"""Tests for renamer.compute_new_name()."""

from pathlib import Path

from renamer import compute_new_name


def make_file(name: str) -> Path:
    """Create a fake Path object with the given filename (no real file needed)."""
    return Path("/fake/dir") / name


class TestComputeNewName:
    def test_find_replace_plain(self):
        f = make_file("hello_world.txt")
        op = {"type": "find_replace", "find": "world", "replace": "earth", "regex": False}
        assert compute_new_name(f, [op]) == "hello_earth.txt"

    def test_find_replace_regex(self):
        f = make_file("file_001.jpg")
        op = {"type": "find_replace", "find": r"\d+", "replace": "999", "regex": True}
        assert compute_new_name(f, [op]) == "file_999.jpg"

    def test_prefix(self):
        f = make_file("photo.jpg")
        op = {"type": "prefix", "prefix": "2024_"}
        assert compute_new_name(f, [op]) == "2024_photo.jpg"

    def test_suffix(self):
        f = make_file("photo.jpg")
        op = {"type": "suffix", "suffix": "_edited"}
        assert compute_new_name(f, [op]) == "photo_edited.jpg"

    def test_extension_preserved(self):
        f = make_file("document.pdf")
        op = {"type": "prefix", "prefix": "FINAL_"}
        result = compute_new_name(f, [op])
        assert result.endswith(".pdf")

    def test_no_extension_preserved(self):
        f = make_file("Makefile")
        op = {"type": "prefix", "prefix": "OLD_"}
        assert compute_new_name(f, [op]) == "OLD_Makefile"

    def test_chained_ops_applied_in_order(self):
        f = make_file("hello_world.txt")
        ops = [
            {"type": "find_replace", "find": "hello", "replace": "goodbye", "regex": False},
            {"type": "suffix", "suffix": "_v2"},
        ]
        assert compute_new_name(f, ops) == "goodbye_world_v2.txt"

    def test_prefix_then_suffix(self):
        f = make_file("photo.jpg")
        ops = [
            {"type": "prefix", "prefix": "IMG_"},
            {"type": "suffix", "suffix": "_final"},
        ]
        assert compute_new_name(f, ops) == "IMG_photo_final.jpg"

    def test_no_operations_returns_original_name(self):
        f = make_file("unchanged.txt")
        assert compute_new_name(f, []) == "unchanged.txt"

    def test_unknown_op_type_is_ignored(self):
        f = make_file("file.txt")
        op = {"type": "unknown_op"}
        assert compute_new_name(f, [op]) == "file.txt"
