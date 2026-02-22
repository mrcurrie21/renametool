"""Tests for renamer.apply_case() and case operations in compute_new_name()."""

from pathlib import Path

from renamer import apply_case, compute_new_name


def make_file(name: str) -> Path:
    return Path("/fake/dir") / name


class TestApplyCase:
    def test_uppercase(self):
        assert apply_case("hello world", "uppercase") == "HELLO WORLD"

    def test_lowercase(self):
        assert apply_case("Hello World", "lowercase") == "hello world"

    def test_title(self):
        assert apply_case("hello world", "title") == "Hello World"

    def test_title_with_underscores(self):
        assert apply_case("my_file_name", "title") == "My_File_Name"

    def test_snake_case_spaces(self):
        assert apply_case("Hello World", "snake_case") == "hello_world"

    def test_snake_case_hyphens(self):
        assert apply_case("hello-world", "snake_case") == "hello_world"

    def test_snake_case_mixed(self):
        assert apply_case("My File - Name", "snake_case") == "my_file_name"

    def test_snake_case_multiple_spaces(self):
        assert apply_case("hello   world", "snake_case") == "hello_world"

    def test_snake_case_multiple_hyphens(self):
        assert apply_case("hello---world", "snake_case") == "hello_world"

    def test_unknown_mode_returns_stem(self):
        assert apply_case("hello", "unknown") == "hello"

    def test_empty_stem(self):
        assert apply_case("", "uppercase") == ""

    def test_already_uppercase(self):
        assert apply_case("HELLO", "uppercase") == "HELLO"

    def test_already_lowercase(self):
        assert apply_case("hello", "lowercase") == "hello"


class TestComputeNewNameCase:
    def test_case_uppercase_preserves_extension(self):
        f = make_file("hello world.txt")
        op = {"type": "case", "mode": "uppercase"}
        assert compute_new_name(f, [op]) == "HELLO WORLD.txt"

    def test_case_lowercase_preserves_extension(self):
        f = make_file("HELLO.TXT")
        op = {"type": "case", "mode": "lowercase"}
        assert compute_new_name(f, [op]) == "hello.TXT"

    def test_case_title(self):
        f = make_file("my file.pdf")
        op = {"type": "case", "mode": "title"}
        assert compute_new_name(f, [op]) == "My File.pdf"

    def test_case_snake(self):
        f = make_file("My File Name.jpg")
        op = {"type": "case", "mode": "snake_case"}
        assert compute_new_name(f, [op]) == "my_file_name.jpg"

    def test_case_stacked_with_prefix(self):
        f = make_file("hello world.txt")
        ops = [
            {"type": "case", "mode": "uppercase"},
            {"type": "prefix", "prefix": "2024_"},
        ]
        assert compute_new_name(f, ops) == "2024_HELLO WORLD.txt"

    def test_case_stacked_with_suffix(self):
        f = make_file("hello world.txt")
        ops = [
            {"type": "case", "mode": "snake_case"},
            {"type": "suffix", "suffix": "_v2"},
        ]
        assert compute_new_name(f, ops) == "hello_world_v2.txt"

    def test_case_stacked_with_find_replace(self):
        f = make_file("hello world.txt")
        ops = [
            {"type": "find_replace", "find": "world", "replace": "earth", "regex": False},
            {"type": "case", "mode": "uppercase"},
        ]
        assert compute_new_name(f, ops) == "HELLO EARTH.txt"

    def test_no_extension(self):
        f = make_file("Makefile")
        op = {"type": "case", "mode": "uppercase"}
        assert compute_new_name(f, [op]) == "MAKEFILE"
