# Issue #4 — Add case transformation operations
https://github.com/mrcurrie21/renametool/issues/4

## Decisions
- Applied to stem only (extension unchanged)
- 4 modes: UPPERCASE, lowercase, Title Case, snake_case

## Key files to touch
- `renamer.py` — add `apply_case()`, extend `ask_operation()` and `compute_new_name()`

## Approach
1. Extend `ask_operation()`: add "Change Case" to the menu
2. Sub-prompt: select from UPPERCASE / lowercase / Title Case / snake_case
3. Return `{"type": "case", "mode": "snake_case"}`
4. `apply_case(stem, mode)`:
   - uppercase: `stem.upper()`
   - lowercase: `stem.lower()`
   - title: `stem.title()`
   - snake_case: `re.sub(r'[\s\-]+', '_', stem.lower())`
5. Handle in `compute_new_name()` under `elif op["type"] == "case"`
