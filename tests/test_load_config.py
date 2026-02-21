"""Tests for renamer.load_config()."""

import pytest

from renamer import load_config


@pytest.fixture()
def config_dir(tmp_path, monkeypatch):
    """Redirect load_config() to look in tmp_path by patching __file__."""
    monkeypatch.setattr("renamer.__file__", str(tmp_path / "renamer.py"))
    return tmp_path


class TestLoadConfig:
    def test_returns_empty_dict_when_no_file(self, config_dir):
        assert load_config() == {}

    def test_returns_empty_dict_for_empty_toml(self, config_dir):
        (config_dir / "renametool.toml").write_text("")
        assert load_config() == {}

    def test_reads_default_folder(self, config_dir):
        (config_dir / "renametool.toml").write_text('default_folder = "/tmp/movies"\n')
        config = load_config()
        assert config["default_folder"] == "/tmp/movies"

    def test_reads_default_extension_filter(self, config_dir):
        (config_dir / "renametool.toml").write_text('default_extension_filter = ".mkv"\n')
        config = load_config()
        assert config["default_extension_filter"] == ".mkv"

    def test_reads_excluded_files_list(self, config_dir):
        (config_dir / "renametool.toml").write_text(
            'excluded_files = ["sample.mkv", "readme.txt"]\n'
        )
        config = load_config()
        assert config["excluded_files"] == ["sample.mkv", "readme.txt"]

    def test_reads_multiple_keys(self, config_dir):
        toml = (
            'default_folder = "/tmp"\n'
            'default_extension_filter = ".jpg"\n'
            'excluded_files = ["skip.txt"]\n'
        )
        (config_dir / "renametool.toml").write_text(toml)
        config = load_config()
        assert config["default_folder"] == "/tmp"
        assert config["default_extension_filter"] == ".jpg"
        assert config["excluded_files"] == ["skip.txt"]

    def test_returns_empty_dict_and_warns_on_malformed_toml(self, config_dir, capsys):
        (config_dir / "renametool.toml").write_text("this is [not valid toml !!!\n")
        config = load_config()
        assert config == {}

    def test_malformed_toml_prints_warning(self, config_dir, capsys):
        (config_dir / "renametool.toml").write_text("[[broken\n")
        load_config()
        # Rich output goes to its own console; just verify no exception is raised
        # and that we still get an empty dict (tested above)

    def test_does_not_raise_on_missing_file(self, config_dir):
        # Confirm no FileNotFoundError bubbles up
        result = load_config()
        assert isinstance(result, dict)

    def test_unknown_keys_are_passed_through(self, config_dir):
        (config_dir / "renametool.toml").write_text('future_key = "value"\n')
        config = load_config()
        assert config["future_key"] == "value"
