"""Batch file rename TUI wizard."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import questionary
import tomllib
from rich.console import Console
from rich.table import Table

from patterns import detect_patterns

console = Console()

HIDDEN_NAMES = {"desktop.ini", "thumbs.db"}
INVALID_CHARS = set('<>:"/\\|?*')
MAX_NAME_LEN = 255
UNDO_FILE = ".renametool_undo.json"


def load_config() -> dict:
    """Load renametool.toml from alongside the script.

    Returns an empty dict if the file does not exist, and prints a warning
    (then returns an empty dict) if the file cannot be parsed.
    """
    config_path = Path(__file__).parent / "renametool.toml"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        console.print(f"[yellow]Warning: could not parse renametool.toml: {e}[/yellow]")
        return {}


def ask_folder(default_folder: str = "") -> Path:  # pragma: no cover
    """Prompt for a folder path and validate it exists."""
    path_str = questionary.text(
        "Enter folder path:",
        default=default_folder or str(Path.cwd()),
    ).ask()
    if path_str is None:
        sys.exit(0)
    folder = Path(path_str).resolve()
    if not folder.is_dir():
        console.print(f"[red]Not a valid directory: {folder}[/red]")
        sys.exit(1)
    return folder


def list_files(
    folder: Path,
    ext_filter: str | None = None,
    excluded_names: frozenset[str] = frozenset(),
) -> list[Path]:
    """Return non-hidden files in folder, filtered by extension if given, sorted alphabetically."""
    files = []
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        name = entry.name
        if name.startswith(".") or name.lower() in HIDDEN_NAMES:
            continue
        if name.lower() in excluded_names:
            continue
        if ext_filter and entry.suffix.lower() != ext_filter.lower():
            continue
        files.append(entry)
    files.sort(key=lambda p: p.name.lower())
    return files


def ask_extension_filter(
    files: list[Path],
    default_ext: str | None = None,
) -> str | None:  # pragma: no cover
    """Show available extensions and optionally filter."""
    extensions = sorted({f.suffix.lower() for f in files if f.suffix})
    if not extensions:
        return None

    choices = ["No filter (all files)"] + extensions
    default_choice = default_ext if (default_ext and default_ext in choices) else choices[0]
    answer = questionary.select(
        "Filter by extension?",
        choices=choices,
        default=default_choice,
    ).ask()
    if answer is None:
        sys.exit(0)
    if answer == choices[0]:
        return None
    return answer


def select_files(files: list[Path]) -> list[Path]:  # pragma: no cover
    """Checkbox prompt to select files, with a Select All option."""
    if not files:
        console.print("[yellow]No files found.[/yellow]")
        sys.exit(0)

    file_names = [f.name for f in files]
    choices = [questionary.Choice("Select All", value="__ALL__")] + [
        questionary.Choice(name, value=name) for name in file_names
    ]

    selected = questionary.checkbox(
        "Select files to rename:",
        choices=choices,
    ).ask()
    if selected is None:
        sys.exit(0)

    if "__ALL__" in selected:
        return list(files)

    name_set = set(selected)
    return [f for f in files if f.name in name_set]


def ask_operation() -> dict:  # pragma: no cover
    """Prompt user to pick an operation and collect its parameters."""
    op_type = questionary.select(
        "Choose operation:",
        choices=[
            "Find/Replace (plain text)",
            "Find/Replace (regex)",
            "Add Prefix",
            "Add Suffix (before extension)",
            "Pattern Group Detection",
        ],
    ).ask()
    if op_type is None:
        sys.exit(0)

    if op_type.startswith("Find/Replace"):
        use_regex = "regex" in op_type
        find = questionary.text("Find what:").ask()
        if find is None:
            sys.exit(0)
        replace = questionary.text("Replace with (leave empty to delete):").ask()
        if replace is None:
            sys.exit(0)
        return {"type": "find_replace", "find": find, "replace": replace, "regex": use_regex}

    if op_type == "Add Prefix":
        prefix = questionary.text("Prefix to add:").ask()
        if prefix is None:
            sys.exit(0)
        return {"type": "prefix", "prefix": prefix}

    if op_type.startswith("Add Suffix"):
        suffix = questionary.text("Suffix to add (before extension):").ask()
        if suffix is None:
            sys.exit(0)
        return {"type": "suffix", "suffix": suffix}

    # Pattern Group Detection — handled separately
    return {"type": "pattern"}


def ask_pattern_operation(filenames: list[str]) -> dict | None:  # pragma: no cover
    """Run pattern detection, let user pick a pattern, and choose action."""
    detected = detect_patterns(filenames)

    if detected:
        table = Table(title="Detected Patterns")
        table.add_column("#", style="dim")
        table.add_column("Pattern")
        table.add_column("Matches", justify="right")
        table.add_column("Examples")
        for i, p in enumerate(detected, 1):
            table.add_row(str(i), p["name"], str(p["match_count"]), ", ".join(p["examples"]))
        console.print(table)

    choices = [p["name"] for p in detected] + ["Enter custom regex"]
    if not detected:
        console.print("[yellow]No common patterns detected. You can enter a custom regex.[/yellow]")
        choices = ["Enter custom regex"]

    pick = questionary.select("Select a pattern:", choices=choices).ask()
    if pick is None:
        sys.exit(0)

    if pick == "Enter custom regex":
        regex_str = questionary.text("Enter regex pattern:").ask()
        if regex_str is None:
            sys.exit(0)
        try:
            re.compile(regex_str)
        except re.error as e:
            console.print(f"[red]Invalid regex: {e}[/red]")
            return None
    else:
        regex_str = next(p["regex"] for p in detected if p["name"] == pick)

    action = questionary.select(
        "What to do with matched text?",
        choices=["Delete (remove it)", "Replace with text"],
    ).ask()
    if action is None:
        sys.exit(0)

    replace = ""
    if action.startswith("Replace"):
        replace = questionary.text("Replace with:").ask()
        if replace is None:
            sys.exit(0)

    return {"type": "find_replace", "find": regex_str, "replace": replace, "regex": True}


def collect_operations(filenames: list[str]) -> list[dict]:  # pragma: no cover
    """Collect one or more operations from the user."""
    operations = []
    while True:
        op = ask_operation()

        if op["type"] == "pattern":
            pattern_op = ask_pattern_operation(filenames)
            if pattern_op is None:
                continue
            operations.append(pattern_op)
        else:
            operations.append(op)

        another = questionary.confirm("Add another operation?", default=False).ask()
        if another is None or not another:
            break
    return operations


def apply_find_replace(stem: str, find: str, replace: str, use_regex: bool) -> str:
    if use_regex:
        return re.sub(find, replace, stem)
    return stem.replace(find, replace)


def apply_prefix(stem: str, prefix: str) -> str:
    return prefix + stem


def apply_suffix(stem: str, suffix: str) -> str:
    return stem + suffix


def compute_new_name(file: Path, operations: list[dict]) -> str:
    """Apply all operations sequentially to the stem, reattach extension."""
    stem = file.stem
    ext = file.suffix

    for op in operations:
        if op["type"] == "find_replace":
            stem = apply_find_replace(stem, op["find"], op["replace"], op["regex"])
        elif op["type"] == "prefix":
            stem = apply_prefix(stem, op["prefix"])
        elif op["type"] == "suffix":
            stem = apply_suffix(stem, op["suffix"])

    return stem + ext


def validate_new_names(pairs: list[tuple[Path, str]]) -> list[dict]:
    """Check each rename for conflicts, invalid chars, no-change, empty names.

    Returns a list of dicts with keys: original, new_name, status.
    """
    results = []
    new_name_counts: dict[str, int] = {}

    # Count occurrences of each new name (case-insensitive for Windows)
    for _, new_name in pairs:
        key = new_name.lower()
        new_name_counts[key] = new_name_counts.get(key, 0) + 1

    for original, new_name in pairs:
        status = "OK"

        if new_name == original.name:
            status = "NO CHANGE"
        elif (
            not new_name
            or new_name == original.suffix
            or not new_name.removesuffix(original.suffix).rstrip(".")
        ):
            status = "INVALID (empty name)"
        elif len(new_name) > MAX_NAME_LEN:
            status = "INVALID (name too long)"
        elif any(c in INVALID_CHARS for c in Path(new_name).stem):
            status = "INVALID (illegal characters)"
        elif new_name_counts.get(new_name.lower(), 0) > 1:
            status = "CONFLICT"
        elif (original.parent / new_name).exists() and new_name.lower() != original.name.lower():
            status = "CONFLICT"

        results.append(
            {
                "original": original,
                "new_name": new_name,
                "status": status,
            }
        )

    return results


def show_preview(results: list[dict]) -> None:
    """Display a rich table with color-coded status per row."""
    table = Table(title="Rename Preview")
    table.add_column("Original", style="cyan")
    table.add_column("New Name", style="white")
    table.add_column("Status")

    style_map = {
        "OK": "green",
        "NO CHANGE": "yellow",
        "CONFLICT": "red",
    }

    for r in results:
        status = r["status"]
        # Any status starting with INVALID is red
        if status.startswith("INVALID"):
            style = "red"
        else:
            style = style_map.get(status, "red")
        table.add_row(r["original"].name, r["new_name"], f"[{style}]{status}[/{style}]")

    console.print(table)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    skip_count = len(results) - ok_count
    console.print(f"\n[green]{ok_count} file(s) will be renamed.[/green]", end="  ")
    console.print(f"[yellow]{skip_count} skipped.[/yellow]")


def write_log(folder: Path, results: list[dict]) -> None:
    """Append a timestamped rename record to .renametool.log in folder.

    All results (OK, NO CHANGE, CONFLICT, INVALID) are recorded so the log
    is a complete audit trail of every rename attempt in the session.
    """
    log_path = folder / ".renametool.log"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"=== {ts} ===\n")
        for r in results:
            f.write(f"{r['original'].name} -> {r['new_name']} [{r['status']}]\n")
        f.write("\n")
    console.print(f"[dim]Log written to {log_path}[/dim]")


def save_undo_map(folder: Path, undo_map: list[dict]) -> None:
    """Write rename pairs to UNDO_FILE in folder.

    undo_map is a list of {"old": "original.txt", "new": "renamed.txt"} dicts,
    representing the rename that was just applied (old → new).  The file can
    later be read by load_undo_map() to reverse those renames.
    """
    undo_path = folder / UNDO_FILE
    with open(undo_path, "w", encoding="utf-8") as f:
        json.dump(undo_map, f, indent=2)


def load_undo_map(folder: Path) -> list[dict] | None:
    """Read and return the undo map from folder, or None if not found/unreadable."""
    undo_path = folder / UNDO_FILE
    if not undo_path.exists():
        return None
    try:
        with open(undo_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def apply_undo(folder: Path, undo_map: list[dict]) -> None:
    """Reverse each rename in undo_map (new → old); skip missing files with a warning."""
    success = 0
    skipped = 0
    for entry in undo_map:
        src = folder / entry["new"]
        dst = folder / entry["old"]
        if not src.exists():
            console.print(f"[yellow]Skipping (not found): {entry['new']}[/yellow]")
            skipped += 1
            continue
        try:
            src.rename(dst)
            success += 1
        except OSError as e:
            console.print(f"[red]Error undoing {entry['new']}: {e}[/red]")
            skipped += 1

    console.print(f"\n[green]{success} file(s) restored.[/green]")
    if skipped:
        console.print(f"[yellow]{skipped} skipped.[/yellow]")


def confirm_and_apply(results: list[dict]) -> None:  # pragma: no cover
    """Confirm and rename valid files. Skip CONFLICT/INVALID/NO CHANGE."""
    ok_items = [r for r in results if r["status"] == "OK"]
    if not ok_items:
        console.print("[yellow]Nothing to rename.[/yellow]")
        return

    confirm = questionary.confirm("Apply renames?", default=False).ask()
    if confirm is None or not confirm:
        console.print("[yellow]Aborted. No files were changed.[/yellow]")
        return

    success = 0
    errors = 0
    for r in ok_items:
        src: Path = r["original"]
        dst = src.parent / r["new_name"]
        try:
            src.rename(dst)
            success += 1
        except OSError as e:
            console.print(f"[red]Error renaming {src.name}: {e}[/red]")
            errors += 1

    console.print(f"\n[green]{success} file(s) renamed successfully.[/green]")
    if errors:
        console.print(f"[red]{errors} file(s) failed.[/red]")

    if success > 0:
        write_log(ok_items[0]["original"].parent, results)
        undo_map = [{"old": r["original"].name, "new": r["new_name"]} for r in ok_items]
        save_undo_map(ok_items[0]["original"].parent, undo_map)


def main():  # pragma: no cover
    console.print("[bold blue]═══ Batch File Rename Tool ═══[/bold blue]\n")

    config = load_config()
    excluded_names = frozenset(n.lower() for n in config.get("excluded_files", []))

    folder = ask_folder(default_folder=config.get("default_folder", ""))

    # Offer undo if a previous rename map exists in this folder
    undo_map = load_undo_map(folder)
    if undo_map:
        do_undo = questionary.confirm("Undo file found. Undo last rename?", default=False).ask()
        if do_undo is None:
            sys.exit(0)
        if do_undo:
            apply_undo(folder, undo_map)
            (folder / UNDO_FILE).unlink()
            console.print("[green]Undo complete. Undo file deleted.[/green]")
            sys.exit(0)

    # List all eligible files first
    all_files = list_files(folder, excluded_names=excluded_names)
    if not all_files:
        console.print(f"[yellow]No eligible files found in {folder}[/yellow]")
        sys.exit(0)

    # Optional extension filter
    ext_filter = ask_extension_filter(all_files, default_ext=config.get("default_extension_filter"))
    if ext_filter:
        all_files = list_files(folder, ext_filter, excluded_names=excluded_names)
        if not all_files:
            console.print(f"[yellow]No {ext_filter} files found.[/yellow]")
            sys.exit(0)

    # Show file list
    table = Table(title=f"Files in {folder}")
    table.add_column("#", style="dim")
    table.add_column("Filename")
    table.add_column("Size", justify="right")
    for i, f in enumerate(all_files, 1):
        size = f.stat().st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        table.add_row(str(i), f.name, size_str)
    console.print(table)
    console.print()

    # Select files
    selected = select_files(all_files)
    if not selected:
        console.print("[yellow]No files selected.[/yellow]")
        sys.exit(0)

    console.print(f"\n[green]{len(selected)} file(s) selected.[/green]\n")

    # Collect operations
    filenames = [f.name for f in selected]
    operations = collect_operations(filenames)
    if not operations:
        console.print("[yellow]No operations defined.[/yellow]")
        sys.exit(0)

    # Compute new names and validate
    pairs = [(f, compute_new_name(f, operations)) for f in selected]
    results = validate_new_names(pairs)

    # Preview
    console.print()
    show_preview(results)
    console.print()

    # Confirm and apply
    confirm_and_apply(results)


if __name__ == "__main__":  # pragma: no cover
    main()
