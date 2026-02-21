"""Shared pytest fixtures."""

import pytest


@pytest.fixture()
def sample_dir(tmp_path):
    """Create a temporary directory with a mix of files for testing."""
    files = [
        "IMG_001.jpg",
        "IMG_002.jpg",
        "IMG_003.jpg",
        "report_2024-01-15.txt",
        "report_2024-03-22.txt",
        "notes.txt",
        "backup(1).docx",
        "backup(2).docx",
        "desktop.ini",  # hidden system file — should be excluded
        ".hidden_file",  # dot-file — should be excluded
    ]
    for name in files:
        (tmp_path / name).write_text("")

    # Create a subdirectory — should be excluded from list_files
    (tmp_path / "subdir").mkdir()

    return tmp_path
