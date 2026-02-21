# Issue #8 — Add back/undo navigation between wizard steps
https://github.com/mrcurrie21/renametool/issues/8

## Decided approach: Restart from step N
Store all selections in a session state dict. When user goes back, decrement the step index and
re-enter that step, pre-filling prompts with stored values from state.

## Session state shape
```python
state = {
    "folder": None,           # Path
    "ext_filter": None,       # str | None
    "all_files": [],          # list[Path]
    "selected": [],           # list[Path]
    "operations": [],         # list[dict]
}
```
Note: `recursive` and `step_recursive` omitted — issue #5 not implemented yet.

## Wizard step sequence
```
STEPS = [step_folder, step_ext_filter, step_select_files, step_operations, step_preview]
```

Each step function signature: `step_foo(state, config, excluded_names) -> state | "BACK"`

## BACK sentinel
- Constants: `BACK = "BACK"`, `GO_BACK = "<< Go back"`
- `"<< Go back"` added to select/checkbox prompts (not folder — first step)
- When step returns "BACK": clear downstream state keys, decrement step index

## Downstream state clearing
When going back from step N, clear state keys from step N onwards:
```
Step 0 (folder):      ["folder"]
Step 1 (ext_filter):  ["ext_filter", "all_files"]
Step 2 (select):      ["selected"]
Step 3 (operations):  ["operations"]
Step 4 (preview):     []
```

## Pre-filling on re-entry
- step_folder: default to previously selected folder path
- step_ext_filter: default select to previous ext_filter value
- step_select_files: pre-check previously selected files via `checked=True`
- step_operations: start fresh (cleared by downstream clearing)

## Functions removed (replaced by step functions)
- `ask_extension_filter` → inlined into `step_ext_filter`
- `select_files` → inlined into `step_select_files`
- `ask_operation` → inlined into `step_operations`
- `collect_operations` → inlined into `step_operations`
- `confirm_and_apply` → apply logic inlined into `step_preview`

## Functions kept
- `ask_folder` — still used by step_folder
- `ask_pattern_operation` — still used by step_operations
- `show_preview` — still used by step_preview
- All pure functions (compute_new_name, validate_new_names, etc.) — unchanged

## Preview step change
Replace simple confirm with 3-way select: "Apply renames" / "<< Go back" / "Abort"

## Implementation steps
1. Add BACK/GO_BACK constants
2. Create 5 step functions (all `# pragma: no cover`)
3. Rewrite main() as step loop with downstream state clearing
4. Remove unused ask_*/collect_*/confirm_and_apply functions
5. Run existing tests to verify no breakage
