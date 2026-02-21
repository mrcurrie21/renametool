# Issue #7 — Add change extension operation
https://github.com/mrcurrie21/renametool/issues/7

## Key files to touch
- `renamer.py` — extend `ask_operation()`, add ext_change handling in `compute_new_name()`

## Approach
1. Add "Change Extension" to the operation menu in `ask_operation()`
2. Prompt: "New extension (e.g. .jpg):" — normalize: strip dots, re-add leading dot
3. Return `{"type": "ext_change", "ext": ".jpg"}`
4. In `compute_new_name()`: when op type is "ext_change", replace the suffix:
   `return stem + op["ext"]` (after all stem ops are done)
5. Validation: reject empty string, reject invalid chars in the extension

## Ordering note
ext_change replaces the *extension* not the stem, so it should be applied last in the operation chain.
Current `compute_new_name()` applies ops sequentially to `stem` then re-attaches `ext` — need to handle
ext_change by updating the `ext` variable instead of `stem`.
