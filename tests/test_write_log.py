"""Tests for renamer.write_log()."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from renamer import write_log

LOG_NAME = ".renametool.log"

# Fixed timestamp used across tests
FIXED_DT = datetime(2026, 2, 20, 14, 32, 1)
FIXED_TS = "2026-02-20 14:32:01"


def make_result(folder: Path, original: str, new_name: str, status: str) -> dict:
    return {"original": folder / original, "new_name": new_name, "status": status}


@pytest.fixture()
def log_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def fixed_time():
    """Patch datetime.now() to return a deterministic value."""
    with patch("renamer.datetime") as mock_dt:
        mock_dt.now.return_value = FIXED_DT
        yield mock_dt


class TestWriteLog:
    def test_creates_log_file(self, log_dir, fixed_time):
        results = [make_result(log_dir, "old.txt", "new.txt", "OK")]
        write_log(log_dir, results)
        assert (log_dir / LOG_NAME).exists()

    def test_log_file_has_timestamp_header(self, log_dir, fixed_time):
        results = [make_result(log_dir, "old.txt", "new.txt", "OK")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert f"=== {FIXED_TS} ===" in content

    def test_log_contains_ok_entry(self, log_dir, fixed_time):
        results = [make_result(log_dir, "old.txt", "new.txt", "OK")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "old.txt -> new.txt [OK]" in content

    def test_log_contains_no_change_entry(self, log_dir, fixed_time):
        results = [make_result(log_dir, "file.txt", "file.txt", "NO CHANGE")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "file.txt -> file.txt [NO CHANGE]" in content

    def test_log_contains_conflict_entry(self, log_dir, fixed_time):
        results = [make_result(log_dir, "a.txt", "dup.txt", "CONFLICT")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "a.txt -> dup.txt [CONFLICT]" in content

    def test_log_contains_invalid_entry(self, log_dir, fixed_time):
        results = [make_result(log_dir, "f.txt", ".txt", "INVALID (empty name)")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "f.txt -> .txt [INVALID (empty name)]" in content

    def test_log_contains_all_results(self, log_dir, fixed_time):
        results = [
            make_result(log_dir, "a.txt", "x.txt", "OK"),
            make_result(log_dir, "b.txt", "b.txt", "NO CHANGE"),
            make_result(log_dir, "c.txt", "dup.txt", "CONFLICT"),
        ]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "a.txt -> x.txt [OK]" in content
        assert "b.txt -> b.txt [NO CHANGE]" in content
        assert "c.txt -> dup.txt [CONFLICT]" in content

    def test_log_is_appended_on_second_call(self, log_dir, fixed_time):
        r1 = [make_result(log_dir, "first.txt", "one.txt", "OK")]
        r2 = [make_result(log_dir, "second.txt", "two.txt", "OK")]
        write_log(log_dir, r1)
        write_log(log_dir, r2)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        assert "first.txt -> one.txt [OK]" in content
        assert "second.txt -> two.txt [OK]" in content
        assert content.count(f"=== {FIXED_TS} ===") == 2

    def test_log_sessions_separated_by_blank_line(self, log_dir, fixed_time):
        r1 = [make_result(log_dir, "a.txt", "b.txt", "OK")]
        r2 = [make_result(log_dir, "c.txt", "d.txt", "OK")]
        write_log(log_dir, r1)
        write_log(log_dir, r2)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        # Two sessions mean there should be at least two newlines between them
        assert "\n\n" in content

    def test_log_is_plain_text(self, log_dir, fixed_time):
        results = [make_result(log_dir, "old.txt", "new.txt", "OK")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        # No rich markup in the file
        assert "[green]" not in content
        assert "[/green]" not in content

    def test_dot_prefix_hides_log_from_list_files(self, log_dir, fixed_time):
        from renamer import list_files

        results = [make_result(log_dir, "file.txt", "renamed.txt", "OK")]
        (log_dir / "file.txt").write_text("")
        write_log(log_dir, results)
        names = [f.name for f in list_files(log_dir)]
        assert LOG_NAME not in names

    def test_log_uses_original_filename_not_full_path(self, log_dir, fixed_time):
        results = [make_result(log_dir, "photo.jpg", "renamed.jpg", "OK")]
        write_log(log_dir, results)
        content = (log_dir / LOG_NAME).read_text(encoding="utf-8")
        # Should be "photo.jpg" not a full path
        assert "photo.jpg -> renamed.jpg [OK]" in content
        assert str(log_dir) not in content
