"""Tests for renamer.list_files()."""

from renamer import list_files


def test_returns_only_files(sample_dir):
    results = list_files(sample_dir)
    assert all(f.is_file() for f in results)


def test_excludes_directories(sample_dir):
    results = list_files(sample_dir)
    names = [f.name for f in results]
    assert "subdir" not in names


def test_excludes_dot_files(sample_dir):
    names = [f.name for f in list_files(sample_dir)]
    assert ".hidden_file" not in names


def test_excludes_hidden_names(sample_dir):
    # desktop.ini is in HIDDEN_NAMES
    names = [f.name for f in list_files(sample_dir)]
    assert "desktop.ini" not in names


def test_returns_normal_files(sample_dir):
    names = [f.name for f in list_files(sample_dir)]
    assert "IMG_001.jpg" in names
    assert "notes.txt" in names


def test_sorted_alphabetically_case_insensitive(sample_dir):
    results = list_files(sample_dir)
    names = [f.name for f in results]
    assert names == sorted(names, key=str.lower)


def test_ext_filter_includes_matching(sample_dir):
    results = list_files(sample_dir, ext_filter=".jpg")
    assert all(f.suffix.lower() == ".jpg" for f in results)


def test_ext_filter_excludes_others(sample_dir):
    results = list_files(sample_dir, ext_filter=".jpg")
    names = [f.name for f in results]
    assert "notes.txt" not in names


def test_ext_filter_none_returns_all(sample_dir):
    all_files = list_files(sample_dir)
    no_filter = list_files(sample_dir, ext_filter=None)
    assert len(all_files) == len(no_filter)


def test_ext_filter_case_insensitive(tmp_path):
    # Use distinct base names to avoid Windows case-insensitive filesystem collision
    (tmp_path / "upper.JPG").write_text("")
    (tmp_path / "lower.jpg").write_text("")
    results = list_files(tmp_path, ext_filter=".jpg")
    assert len(results) == 2


def test_empty_directory(tmp_path):
    assert list_files(tmp_path) == []
