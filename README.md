# Rename Tool

A lightweight Python TUI tool for batch-renaming files on Windows.

## Features

- Interactive wizard — no CLI flags to memorize
- **Find/Replace** (plain text or regex)
- **Add Prefix / Suffix** (suffix inserts before extension)
- **Pattern Detection** — auto-detects dates, sequence codes, parentheticals, etc. across your files
- Stack multiple operations in one session
- Color-coded preview table before any changes hit disk
- Skips hidden/system files (dotfiles, `desktop.ini`, `thumbs.db`)
- Per-file error handling — one locked file won't abort the batch

## Configuration

Copy `renametool.toml.example` to `renametool.toml` in the same directory as `renamer.py` and edit it to set your defaults:

```toml
# Pre-fill the folder prompt
default_folder = "C:/Users/alice/Movies"

# Pre-select this extension in the filter prompt (include the leading dot)
default_extension_filter = ".mkv"

# Hide these filenames from the file list (case-insensitive)
excluded_files = ["sample.mkv", "readme.txt"]
```

All keys are optional. If the file doesn't exist the tool behaves exactly as it does today.
`renametool.toml` is excluded from Git so your personal settings are never committed.

## Requirements

- Python 3.11+
- Windows 11 (tested), should work on other platforms

## Setup

```
cd renametool
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```
python renamer.py
```

The wizard walks you through:

1. Select a folder
2. Optionally filter by file extension
3. Pick files (checkbox with Select All)
4. Choose operations (find/replace, prefix, suffix, pattern detection)
5. Stack additional operations if needed
6. Review the preview table
7. Confirm or abort
