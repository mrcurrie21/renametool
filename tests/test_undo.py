"""Tests for renamer.save_undo_map(), load_undo_map(), and apply_undo()."""

import json

from renamer import UNDO_FILE, apply_undo, load_undo_map, save_undo_map

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_undo_entry(old: str, new: str) -> dict:
    return {"old": old, "new": new}


# ---------------------------------------------------------------------------
# save_undo_map
# ---------------------------------------------------------------------------


class TestSaveUndoMap:
    def test_creates_undo_file(self, tmp_path):
        save_undo_map(tmp_path, [make_undo_entry("a.txt", "b.txt")])
        assert (tmp_path / UNDO_FILE).exists()

    def test_file_is_valid_json(self, tmp_path):
        save_undo_map(tmp_path, [make_undo_entry("a.txt", "b.txt")])
        content = (tmp_path / UNDO_FILE).read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, list)

    def test_single_entry_round_trips(self, tmp_path):
        entries = [make_undo_entry("original.txt", "renamed.txt")]
        save_undo_map(tmp_path, entries)
        data = json.loads((tmp_path / UNDO_FILE).read_text(encoding="utf-8"))
        assert data == entries

    def test_multiple_entries_preserved(self, tmp_path):
        entries = [
            make_undo_entry("a.txt", "x.txt"),
            make_undo_entry("b.jpg", "y.jpg"),
        ]
        save_undo_map(tmp_path, entries)
        data = json.loads((tmp_path / UNDO_FILE).read_text(encoding="utf-8"))
        assert data == entries

    def test_overwrites_existing_file(self, tmp_path):
        save_undo_map(tmp_path, [make_undo_entry("old1.txt", "new1.txt")])
        save_undo_map(tmp_path, [make_undo_entry("old2.txt", "new2.txt")])
        data = json.loads((tmp_path / UNDO_FILE).read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["old"] == "old2.txt"

    def test_empty_list_is_valid(self, tmp_path):
        save_undo_map(tmp_path, [])
        data = json.loads((tmp_path / UNDO_FILE).read_text(encoding="utf-8"))
        assert data == []

    def test_dot_prefix_hides_undo_file_from_list_files(self, tmp_path):
        from renamer import list_files

        (tmp_path / "file.txt").write_text("")
        save_undo_map(tmp_path, [make_undo_entry("file.txt", "renamed.txt")])
        names = [f.name for f in list_files(tmp_path)]
        assert UNDO_FILE not in names


# ---------------------------------------------------------------------------
# load_undo_map
# ---------------------------------------------------------------------------


class TestLoadUndoMap:
    def test_returns_none_when_no_file(self, tmp_path):
        assert load_undo_map(tmp_path) is None

    def test_returns_list_when_file_exists(self, tmp_path):
        entries = [make_undo_entry("a.txt", "b.txt")]
        save_undo_map(tmp_path, entries)
        result = load_undo_map(tmp_path)
        assert result == entries

    def test_returns_none_on_malformed_json(self, tmp_path):
        (tmp_path / UNDO_FILE).write_text("not valid json", encoding="utf-8")
        assert load_undo_map(tmp_path) is None

    def test_returns_empty_list_for_empty_array(self, tmp_path):
        save_undo_map(tmp_path, [])
        result = load_undo_map(tmp_path)
        assert result == []

    def test_multiple_entries_loaded_correctly(self, tmp_path):
        entries = [
            make_undo_entry("alpha.txt", "bravo.txt"),
            make_undo_entry("charlie.jpg", "delta.jpg"),
        ]
        save_undo_map(tmp_path, entries)
        result = load_undo_map(tmp_path)
        assert result == entries


# ---------------------------------------------------------------------------
# apply_undo
# ---------------------------------------------------------------------------


class TestApplyUndo:
    def test_renames_file_back(self, tmp_path):
        new_file = tmp_path / "renamed.txt"
        new_file.write_text("content")
        undo_map = [make_undo_entry("original.txt", "renamed.txt")]
        apply_undo(tmp_path, undo_map)
        assert (tmp_path / "original.txt").exists()
        assert not new_file.exists()

    def test_skips_missing_file_without_crash(self, tmp_path):
        undo_map = [make_undo_entry("original.txt", "ghost.txt")]
        # Should not raise even though ghost.txt doesn't exist
        apply_undo(tmp_path, undo_map)

    def test_processes_multiple_entries(self, tmp_path):
        (tmp_path / "new_a.txt").write_text("")
        (tmp_path / "new_b.jpg").write_text("")
        undo_map = [
            make_undo_entry("old_a.txt", "new_a.txt"),
            make_undo_entry("old_b.jpg", "new_b.jpg"),
        ]
        apply_undo(tmp_path, undo_map)
        assert (tmp_path / "old_a.txt").exists()
        assert (tmp_path / "old_b.jpg").exists()
        assert not (tmp_path / "new_a.txt").exists()
        assert not (tmp_path / "new_b.jpg").exists()

    def test_continues_after_missing_file(self, tmp_path):
        (tmp_path / "new_b.txt").write_text("")
        undo_map = [
            make_undo_entry("old_a.txt", "missing.txt"),
            make_undo_entry("old_b.txt", "new_b.txt"),
        ]
        apply_undo(tmp_path, undo_map)
        # The second entry should still be processed
        assert (tmp_path / "old_b.txt").exists()

    def test_empty_undo_map_is_a_no_op(self, tmp_path):
        # Nothing in the folder; should not crash
        apply_undo(tmp_path, [])

    def test_original_file_content_preserved(self, tmp_path):
        new_file = tmp_path / "renamed.txt"
        new_file.write_text("hello world")
        undo_map = [make_undo_entry("original.txt", "renamed.txt")]
        apply_undo(tmp_path, undo_map)
        assert (tmp_path / "original.txt").read_text() == "hello world"
