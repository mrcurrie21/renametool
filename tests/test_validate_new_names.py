"""Tests for renamer.validate_new_names()."""

from pathlib import Path

from renamer import validate_new_names


def make_pair(directory: Path, original_name: str, new_name: str):
    return (directory / original_name, new_name)


class TestValidateNewNames:
    def test_ok_status_for_valid_rename(self, tmp_path):
        (tmp_path / "old.txt").write_text("")
        pairs = [make_pair(tmp_path, "old.txt", "new.txt")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "OK"

    def test_no_change_when_name_unchanged(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [make_pair(tmp_path, "file.txt", "file.txt")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "NO CHANGE"

    def test_conflict_for_duplicate_new_names_in_batch(self, tmp_path):
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")
        pairs = [
            make_pair(tmp_path, "a.txt", "same.txt"),
            make_pair(tmp_path, "b.txt", "same.txt"),
        ]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "CONFLICT"
        assert results[1]["status"] == "CONFLICT"

    def test_conflict_when_target_already_exists_on_disk(self, tmp_path):
        (tmp_path / "source.txt").write_text("")
        (tmp_path / "existing.txt").write_text("")  # target already exists
        pairs = [make_pair(tmp_path, "source.txt", "existing.txt")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "CONFLICT"

    def test_no_conflict_renaming_to_same_case_on_disk(self, tmp_path):
        # Renaming file.TXT → file.txt on the same file is a case-only change — should be OK
        (tmp_path / "FILE.txt").write_text("")
        pairs = [make_pair(tmp_path, "FILE.txt", "file.txt")]
        results = validate_new_names(pairs)
        # case-only rename: existing check uses lower() comparison, so no CONFLICT
        assert results[0]["status"] in ("OK", "NO CHANGE")

    def test_invalid_empty_name(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [make_pair(tmp_path, "file.txt", ".txt")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "INVALID (empty name)"

    def test_invalid_empty_string(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [make_pair(tmp_path, "file.txt", "")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "INVALID (empty name)"

    def test_invalid_name_too_long(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        long_name = "a" * 252 + ".txt"  # 256 chars total > MAX_NAME_LEN (255)
        pairs = [make_pair(tmp_path, "file.txt", long_name)]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "INVALID (name too long)"

    def test_invalid_illegal_characters(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [make_pair(tmp_path, "file.txt", "bad<name>.txt")]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "INVALID (illegal characters)"

    def test_all_illegal_chars_caught(self, tmp_path):
        # '/' and '\\' are path separators — Path() parses them as directory components,
        # so they never appear in the stem and are handled at the OS level instead.
        illegal = list('<>:"|?*')
        for char in illegal:
            (tmp_path / "file.txt").write_text("")
            new_name = f"bad{char}name.txt"
            pairs = [make_pair(tmp_path, "file.txt", new_name)]
            results = validate_new_names(pairs)
            assert results[0]["status"] == "INVALID (illegal characters)", (
                f"Expected INVALID for char: {char!r}"
            )

    def test_result_contains_correct_keys(self, tmp_path):
        (tmp_path / "file.txt").write_text("")
        pairs = [make_pair(tmp_path, "file.txt", "renamed.txt")]
        results = validate_new_names(pairs)
        assert "original" in results[0]
        assert "new_name" in results[0]
        assert "status" in results[0]

    def test_result_order_matches_input_order(self, tmp_path):
        for name in ["a.txt", "b.txt", "c.txt"]:
            (tmp_path / name).write_text("")
        pairs = [
            make_pair(tmp_path, "a.txt", "x.txt"),
            make_pair(tmp_path, "b.txt", "y.txt"),
            make_pair(tmp_path, "c.txt", "z.txt"),
        ]
        results = validate_new_names(pairs)
        assert results[0]["new_name"] == "x.txt"
        assert results[1]["new_name"] == "y.txt"
        assert results[2]["new_name"] == "z.txt"

    def test_conflict_is_case_insensitive_on_windows(self, tmp_path):
        # Two files renaming to names that differ only in case count as conflict
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")
        pairs = [
            make_pair(tmp_path, "a.txt", "Same.txt"),
            make_pair(tmp_path, "b.txt", "same.txt"),
        ]
        results = validate_new_names(pairs)
        assert results[0]["status"] == "CONFLICT"
        assert results[1]["status"] == "CONFLICT"
