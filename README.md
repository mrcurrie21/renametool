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

## Requirements

- Python 3.10+
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
