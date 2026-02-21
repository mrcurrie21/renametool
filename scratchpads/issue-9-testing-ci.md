# Issue #9 — Establish testing framework and CI pipeline
https://github.com/mrcurrie21/renametool/issues/9

## Decisions
- Framework: pytest + pytest-cov
- CI: GitHub Actions (push + PR on master)
- Linting: ruff (lint + format check)
- Coverage: ≥90% enforced in CI
- TUI approach: business logic only — mark interactive functions with `# pragma: no cover`

## What is testable (pure functions, no questionary)
- `patterns.py`: `detect_patterns()` — fully testable
- `renamer.py`:
  - `list_files()` — use pytest `tmp_path` fixture
  - `apply_find_replace()`, `apply_prefix()`, `apply_suffix()`
  - `compute_new_name()` — chains ops on a mock Path
  - `validate_new_names()` — covers OK, NO CHANGE, CONFLICT, INVALID variants

## What needs `# pragma: no cover`
In `renamer.py`: `ask_folder`, `ask_extension_filter`, `select_files`, `ask_operation`,
`ask_pattern_operation`, `collect_operations`, `confirm_and_apply`, `main`,
and the `if __name__ == "__main__":` block.

## Test file plan
```
tests/
  __init__.py
  conftest.py            # shared fixtures (tmp_path folder with sample files)
  test_detect_patterns.py
  test_list_files.py
  test_apply_ops.py
  test_compute_new_name.py
  test_validate_new_names.py
```

## Dev dependencies (requirements-dev.txt)
```
pytest
pytest-cov
ruff
```

## pyproject.toml config
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=renamer --cov=patterns --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if __name__"]

[tool.ruff]
line-length = 100
```

## GitHub Actions workflow (.github/workflows/ci.yml)
Triggers: push + pull_request on master
Steps: checkout → setup-python 3.13 → pip install -r requirements-dev.txt -r requirements.txt
       → ruff check . → ruff format --check . → pytest

## Relation to other issues
All future features (#1-#8) should add tests alongside their implementation.
Issue #9 is a blocker for all others if we want CI from day one.
