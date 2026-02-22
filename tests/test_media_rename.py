"""Tests for media library rename operations in renamer.py."""

from pathlib import Path

from renamer import compute_new_name, format_movie_name, format_tv_name


class TestFormatTvName:
    def test_with_title(self):
        info = {"show": "Breaking Bad", "season": 1, "episode": 1, "title": "Pilot"}
        assert format_tv_name(info, ".mkv") == "Breaking Bad - S01E01 - Pilot.mkv"

    def test_without_title(self):
        info = {"show": "Breaking Bad", "season": 1, "episode": 1, "title": ""}
        assert format_tv_name(info, ".mkv") == "Breaking Bad - S01E01.mkv"

    def test_double_digit_season_episode(self):
        info = {"show": "Lost", "season": 3, "episode": 22, "title": "Finale"}
        assert format_tv_name(info, ".mp4") == "Lost - S03E22 - Finale.mp4"

    def test_zero_pads_single_digits(self):
        info = {"show": "Show", "season": 1, "episode": 5, "title": ""}
        result = format_tv_name(info, ".avi")
        assert "S01E05" in result

    def test_preserves_extension(self):
        info = {"show": "Show", "season": 1, "episode": 1, "title": ""}
        assert format_tv_name(info, ".avi").endswith(".avi")


class TestFormatMovieName:
    def test_standard(self):
        info = {"title": "The Matrix", "year": 1999}
        assert format_movie_name(info, ".mkv") == "The Matrix (1999).mkv"

    def test_preserves_extension(self):
        info = {"title": "Inception", "year": 2010}
        assert format_movie_name(info, ".mp4") == "Inception (2010).mp4"


class TestComputeNewNameMedia:
    def test_media_tv_operation(self):
        f = Path("/tmp/Breaking.Bad.S01E01.720p.mkv")
        ops = [
            {
                "type": "media_tv",
                "info": {
                    "show": "Breaking Bad",
                    "season": 1,
                    "episode": 1,
                    "title": "Pilot",
                },
            }
        ]
        result = compute_new_name(f, ops)
        assert result == "Breaking Bad - S01E01 - Pilot.mkv"

    def test_media_movie_operation(self):
        f = Path("/tmp/The.Matrix.1999.1080p.mkv")
        ops = [{"type": "media_movie", "info": {"title": "The Matrix", "year": 1999}}]
        result = compute_new_name(f, ops)
        assert result == "The Matrix (1999).mkv"

    def test_media_tv_with_file_match(self):
        f = Path("/tmp/Show.S01E01.mkv")
        ops = [
            {
                "type": "media_tv",
                "info": {
                    "show": "Show",
                    "season": 1,
                    "episode": 1,
                    "title": "",
                },
                "file": "Show.S01E01.mkv",
            },
        ]
        result = compute_new_name(f, ops)
        assert result == "Show - S01E01.mkv"

    def test_media_tv_skips_non_matching_file(self):
        f = Path("/tmp/Other.S02E03.mkv")
        ops = [
            {
                "type": "media_tv",
                "info": {
                    "show": "Show",
                    "season": 1,
                    "episode": 1,
                    "title": "",
                },
                "file": "Show.S01E01.mkv",
            },
        ]
        # Should fall through and return original stem + ext
        result = compute_new_name(f, ops)
        assert result == "Other.S02E03.mkv"

    def test_media_movie_with_file_match(self):
        f = Path("/tmp/Inception.2010.mkv")
        ops = [
            {
                "type": "media_movie",
                "info": {
                    "title": "Inception",
                    "year": 2010,
                },
                "file": "Inception.2010.mkv",
            },
        ]
        result = compute_new_name(f, ops)
        assert result == "Inception (2010).mkv"

    def test_media_tv_without_title(self):
        f = Path("/tmp/Show.S05E10.mkv")
        ops = [
            {
                "type": "media_tv",
                "info": {
                    "show": "My Show",
                    "season": 5,
                    "episode": 10,
                    "title": "",
                },
            }
        ]
        result = compute_new_name(f, ops)
        assert result == "My Show - S05E10.mkv"
