"""Tests for the Change Extension feature."""

from pathlib import Path

from renamer import compute_new_name, normalize_extension, validate_extension, validate_new_names


def make_file(name: str) -> Path:
    """Create a fake Path object with the given filename (no real file needed)."""
    return Path("/fake/dir") / name


class TestNormalizeExtension:
    def test_adds_leading_dot(self):
        assert normalize_extension("jpg") == ".jpg"

    def test_preserves_single_dot(self):
        assert normalize_extension(".jpg") == ".jpg"

    def test_strips_multiple_dots(self):
        assert normalize_extension("..jpg") == ".jpg"
        assert normalize_extension("...jpg") == ".jpg"

    def test_empty_string(self):
        assert normalize_extension("") == ""

    def test_only_dots(self):
        assert normalize_extension("...") == ""


class TestValidateExtension:
    def test_valid_extension(self):
        assert validate_extension(".jpg") is None
        assert validate_extension(".mp4") is None
        assert validate_extension(".tar.gz") is None

    def test_empty_string(self):
        assert validate_extension("") is not None

    def test_just_dot(self):
        assert validate_extension(".") is not None

    def test_invalid_chars(self):
        assert validate_extension(".<jpg") is not None
        assert validate_extension(".jp>g") is not None
        assert validate_extension('.jp"g') is not None
        assert validate_extension(".jp?g") is not None
        assert validate_extension(".jp*g") is not None

    def test_spaces_rejected(self):
        assert validate_extension(". jpg") is not None


class TestComputeNewNameExtChange:
    def test_basic_ext_change(self):
        f = make_file("photo.jpeg")
        op = {"type": "ext_change", "ext": ".jpg"}
        assert compute_new_name(f, [op]) == "photo.jpg"

    def test_ext_change_txt_to_md(self):
        f = make_file("readme.txt")
        op = {"type": "ext_change", "ext": ".md"}
        assert compute_new_name(f, [op]) == "readme.md"

    def test_ext_change_ts_to_mp4(self):
        f = make_file("video.ts")
        op = {"type": "ext_change", "ext": ".mp4"}
        assert compute_new_name(f, [op]) == "video.mp4"

    def test_ext_change_stacked_with_prefix(self):
        f = make_file("photo.jpeg")
        ops = [
            {"type": "prefix", "prefix": "2024_"},
            {"type": "ext_change", "ext": ".jpg"},
        ]
        assert compute_new_name(f, ops) == "2024_photo.jpg"

    def test_ext_change_stacked_with_suffix(self):
        f = make_file("photo.jpeg")
        ops = [
            {"type": "suffix", "suffix": "_edited"},
            {"type": "ext_change", "ext": ".jpg"},
        ]
        assert compute_new_name(f, ops) == "photo_edited.jpg"

    def test_ext_change_stacked_with_find_replace(self):
        f = make_file("old_photo.jpeg")
        ops = [
            {"type": "find_replace", "find": "old", "replace": "new", "regex": False},
            {"type": "ext_change", "ext": ".jpg"},
        ]
        assert compute_new_name(f, ops) == "new_photo.jpg"

    def test_ext_change_stacked_with_case(self):
        f = make_file("My Photo.jpeg")
        ops = [
            {"type": "case", "mode": "snake_case"},
            {"type": "ext_change", "ext": ".jpg"},
        ]
        assert compute_new_name(f, ops) == "my_photo.jpg"

    def test_multiple_ext_changes_last_one_wins(self):
        f = make_file("file.txt")
        ops = [
            {"type": "ext_change", "ext": ".md"},
            {"type": "ext_change", "ext": ".rst"},
        ]
        assert compute_new_name(f, ops) == "file.rst"

    def test_ext_change_on_file_without_extension(self):
        f = make_file("Makefile")
        op = {"type": "ext_change", "ext": ".bak"}
        assert compute_new_name(f, [op]) == "Makefile.bak"

    def test_ext_change_preserves_stem(self):
        f = make_file("complex.name.with.dots.txt")
        op = {"type": "ext_change", "ext": ".md"}
        result = compute_new_name(f, [op])
        assert result == "complex.name.with.dots.md"


class TestValidateNewNamesExtChange:
    def test_ext_change_shows_ok(self, tmp_path):
        (tmp_path / "photo.jpeg").write_text("")
        pairs = [(tmp_path / "photo.jpeg", "photo.jpg")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "OK"

    def test_ext_change_no_change(self, tmp_path):
        (tmp_path / "photo.jpg").write_text("")
        pairs = [(tmp_path / "photo.jpg", "photo.jpg")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "NO CHANGE"

    def test_ext_change_conflict_with_existing(self, tmp_path):
        (tmp_path / "photo.jpeg").write_text("")
        (tmp_path / "photo.jpg").write_text("")
        pairs = [(tmp_path / "photo.jpeg", "photo.jpg")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "CONFLICT"

    def test_empty_stem_after_ext_change_is_invalid(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [(tmp_path / "file.txt", ".jpg")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "INVALID (empty name)"
