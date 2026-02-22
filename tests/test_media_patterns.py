"""Tests for media filename parsing (TV and Movie patterns)."""

from patterns import parse_movie_filename, parse_tv_filename

# --- parse_tv_filename ---


class TestParseTvFilename:
    def test_standard_format(self):
        result = parse_tv_filename("Breaking.Bad.S01E01.720p.BluRay.mkv")
        assert result == {"show": "Breaking Bad", "season": 1, "episode": 1, "title": ""}

    def test_with_episode_title(self):
        result = parse_tv_filename("Breaking.Bad.S01E01.Pilot.720p.BluRay.mkv")
        assert result is not None
        assert result["show"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["title"] == "Pilot"

    def test_underscores(self):
        result = parse_tv_filename("the_office_s02e03.mp4")
        assert result is not None
        assert result["show"] == "The Office"
        assert result["season"] == 2
        assert result["episode"] == 3

    def test_hyphens(self):
        result = parse_tv_filename("Game-of-Thrones-S03E09.mkv")
        assert result is not None
        assert result["show"] == "Game Of Thrones"
        assert result["season"] == 3
        assert result["episode"] == 9

    def test_spaces(self):
        result = parse_tv_filename("Breaking Bad S01E01.mkv")
        assert result is not None
        assert result["show"] == "Breaking Bad"

    def test_lowercase_se(self):
        result = parse_tv_filename("show.s01e01.mkv")
        assert result is not None
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_uppercase_se(self):
        result = parse_tv_filename("show.S01E01.mkv")
        assert result is not None
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_double_digit_season_episode(self):
        result = parse_tv_filename("Show.S12E24.mkv")
        assert result is not None
        assert result["season"] == 12
        assert result["episode"] == 24

    def test_with_web_dl_source(self):
        result = parse_tv_filename("Show.S01E01.WEB-DL.x265.mkv")
        assert result is not None
        assert result["show"] == "Show"
        assert result["title"] == ""

    def test_with_hevc_codec(self):
        result = parse_tv_filename("Show.S01E01.1080p.HEVC.mkv")
        assert result is not None
        assert result["title"] == ""

    def test_no_junk_tags(self):
        result = parse_tv_filename("My.Show.S05E10.mkv")
        assert result is not None
        assert result["show"] == "My Show"
        assert result["season"] == 5
        assert result["episode"] == 10

    def test_returns_none_for_non_tv(self):
        assert parse_tv_filename("random_file.txt") is None

    def test_returns_none_for_movie(self):
        assert parse_tv_filename("The.Matrix.1999.1080p.mkv") is None

    def test_stem_only_no_extension(self):
        result = parse_tv_filename("Show.S01E01")
        assert result is not None
        assert result["show"] == "Show"


# --- parse_movie_filename ---


class TestParseMovieFilename:
    def test_standard_format(self):
        result = parse_movie_filename("The.Matrix.1999.1080p.mkv")
        assert result == {"title": "The Matrix", "year": 1999}

    def test_with_parenthesized_year(self):
        result = parse_movie_filename("Inception (2010).mp4")
        assert result is not None
        assert result["title"] == "Inception"
        assert result["year"] == 2010

    def test_underscores(self):
        result = parse_movie_filename("The_Dark_Knight_2008.mkv")
        assert result is not None
        assert result["title"] == "The Dark Knight"
        assert result["year"] == 2008

    def test_hyphens(self):
        result = parse_movie_filename("Blade-Runner-2049.mkv")
        assert result is not None
        assert result["title"] == "Blade Runner"
        assert result["year"] == 2049

    def test_with_quality_tags(self):
        result = parse_movie_filename("Interstellar.2014.2160p.BluRay.x265.mkv")
        assert result is not None
        assert result["title"] == "Interstellar"
        assert result["year"] == 2014

    def test_year_1900s(self):
        result = parse_movie_filename("Casablanca.1942.mkv")
        assert result is not None
        assert result["year"] == 1942

    def test_year_2000s(self):
        result = parse_movie_filename("Avatar.2009.mkv")
        assert result is not None
        assert result["year"] == 2009

    def test_returns_none_for_no_year(self):
        assert parse_movie_filename("random_file.txt") is None

    def test_returns_none_for_plain_name(self):
        assert parse_movie_filename("mydocument.pdf") is None
