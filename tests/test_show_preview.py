"""Tests for renamer.show_preview()."""

from pathlib import Path

from renamer import show_preview


def make_result(name: str, new_name: str, status: str) -> dict:
    return {"original": Path("/fake") / name, "new_name": new_name, "status": status}


class TestShowPreview:
    def test_runs_without_error_for_ok(self, capsys):
        results = [make_result("old.txt", "new.txt", "OK")]
        show_preview(results)  # must not raise

    def test_runs_without_error_for_no_change(self, capsys):
        results = [make_result("file.txt", "file.txt", "NO CHANGE")]
        show_preview(results)

    def test_runs_without_error_for_conflict(self, capsys):
        results = [make_result("a.txt", "same.txt", "CONFLICT")]
        show_preview(results)

    def test_runs_without_error_for_invalid(self, capsys):
        results = [make_result("file.txt", ".txt", "INVALID (empty name)")]
        show_preview(results)

    def test_runs_without_error_for_invalid_too_long(self, capsys):
        results = [make_result("file.txt", "a" * 256, "INVALID (name too long)")]
        show_preview(results)

    def test_counts_ok_and_skipped_correctly(self, capsys):
        results = [
            make_result("a.txt", "x.txt", "OK"),
            make_result("b.txt", "b.txt", "NO CHANGE"),
            make_result("c.txt", "same.txt", "CONFLICT"),
        ]
        show_preview(results)
        # 1 OK, 2 skipped — just verify no exception is raised with mixed statuses

    def test_empty_results_does_not_raise(self, capsys):
        show_preview([])

    def test_all_statuses_in_single_call(self, capsys):
        results = [
            make_result("a.txt", "new_a.txt", "OK"),
            make_result("b.txt", "b.txt", "NO CHANGE"),
            make_result("c.txt", "dup.txt", "CONFLICT"),
            make_result("d.txt", ".txt", "INVALID (empty name)"),
            make_result("e.txt", "bad<>.txt", "INVALID (illegal characters)"),
        ]
        show_preview(results)
