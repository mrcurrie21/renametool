# Issue #2 — Add dry-run log output
https://github.com/mrcurrie21/renametool/issues/2

## Decisions
- Log file: `.renametool.log` (hidden dot prefix keeps it out of the file list)
- Append mode so multiple sessions accumulate
- Only write after renames are applied (not on abort)

## Key files to touch
- `renamer.py` — add `write_log(folder, results)`, call from `confirm_and_apply()`

## Format
```
=== 2026-02-20 14:32:01 ===
movie.mkv -> The Matrix (1999).mkv [OK]
show.s01e01.mkv -> Breaking Bad - S01E01.mkv [OK]
duplicate.mkv -> duplicate.mkv [NO CHANGE]
```

## Approach
1. `write_log(folder, results)` — open log in append mode, write timestamp header + one line per result
2. Call after the rename loop in `confirm_and_apply()`, only if `success > 0`
3. Print log file path to console: `[dim]Log written to {log_path}[/dim]`
