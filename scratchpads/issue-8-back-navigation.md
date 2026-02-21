# Issue #8 — Add back/undo navigation between wizard steps
https://github.com/mrcurrie21/renametool/issues/8

## Decided approach: Restart from step N
Store all selections in a session state dict. When user goes back, decrement the step index and
re-enter that step, pre-filling prompts with stored values from state.

## Session state shape
```python
state = {
    "folder": None,           # Path
    "recursive": False,       # bool
    "ext_filter": None,       # str | None
    "selected_files": [],     # list[Path]
    "operations": [],         # list[dict]
}
```

## Wizard step sequence
```
STEPS = [step_folder, step_recursive, step_ext_filter, step_select_files, step_operations, step_preview]
```

Each step function signature: `step_foo(state: dict) -> dict | Literal["BACK"]`

## BACK sentinel
- Special questionary choice: `"<< Go back"` added to every select/checkbox prompt
- Text prompts: check if returned value == `"<< Go back"` sentinel string
- When step returns "BACK": decrement step index, re-run previous step

## Key files to touch
- `renamer.py` — major refactor of `main()` into step loop + individual step functions

## Timing note
This is a significant refactor of `main()`. Best done after other features are added to avoid
double-refactoring. All step functions should be written to accept and return the shared state dict.
