# Issue #3 — Add undo support
https://github.com/mrcurrie21/renametool/issues/3

## Decisions
- Independent from Issue #2 (separate file, no shared code)
- Undo file: `.renametool_undo.json` in the target folder
- Single-level undo only (no history chain)

## Key files to touch
- `renamer.py` — add `save_undo_map()`, `load_undo_map()`, `apply_undo()`, integrate into `main()`

## Approach
1. After folder selection, call `load_undo_map(folder)` — if undo file exists, offer "Undo last rename" first
2. If user picks undo: call `apply_undo()`, show results, delete undo file, exit (or re-run wizard)
3. After each successful rename batch: call `save_undo_map(folder, ok_results)` to write JSON
4. Undo JSON: `[{"old": "original.txt", "new": "renamed.txt"}, ...]`

## Edge cases
- File renamed by undo may no longer exist (deleted externally) — skip with warning
- Undo file from a different folder should not appear (it's folder-scoped)
