# Issue #5 — Add recursive subfolder mode
https://github.com/mrcurrie21/renametool/issues/5

## Key files to touch
- `renamer.py` — modify `list_files()`, add recursive prompt to `main()`, update display/conflict logic

## Approach
1. Add `recursive: bool = False` param to `list_files()`; use `folder.rglob("*")` when True
2. After folder selection, add confirm prompt: "Include subfolders?" (default No)
3. Display files with relative paths: `f.relative_to(folder)`
4. Conflict detection: scope conflicts per-directory — use `(file.parent, new_name)` as the key
5. `confirm_and_apply()` already uses `src.parent / new_name` so renames work per-folder naturally

## Edge cases
- Very large folder trees: no pagination, just sort + display (same as current)
- Files with the same name in different subdirs are NOT conflicts (scoped per-dir)
