# Issue #1 — Add config file for user defaults
https://github.com/mrcurrie21/renametool/issues/1

## Decisions
- Format: TOML (stdlib `tomllib` Python 3.11+, fallback `tomli` dependency)
- Location: alongside script — `Path(__file__).parent / "renametool.toml"`
- Add `renametool.toml` to `.gitignore`

## Key files to touch
- `renamer.py` — add `load_config()`, thread config into `ask_folder()`, `ask_extension_filter()`, `list_files()`
- `renametool.toml.example` — new example config with comments
- `requirements.txt` — add `tomli` as optional/fallback
- `.gitignore` — exclude `renametool.toml`

## Approach
1. `load_config()` reads TOML; returns empty dict on missing file, logs warning on parse error
2. Pass config down through main() (or read once into a module-level singleton)
3. `ask_folder()` uses `config.get("default_folder", str(Path.cwd()))` as questionary default
4. `ask_extension_filter()` pre-selects if `default_extension_filter` is set
5. `list_files()` excludes names in `config.get("excluded_files", [])`
