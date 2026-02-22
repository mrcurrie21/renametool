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

from patterns import detect_patterns, parse_movie_filename, parse_tv_filename

console = Console()

HIDDEN_NAMES = {"desktop.ini", "thumbs.db"}
INVALID_CHARS = set('<>:"/\\|?*')
MAX_NAME_LEN = 255
UNDO_FILE = ".renametool_undo.json"
BACK = "BACK"
GO_BACK = "<< Go back"


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


def ask_media_rename(selected_files: list) -> list[dict] | None:  # pragma: no cover
    """Run media library rename sub-flow. Returns a list of per-file operations."""
    media_type = questionary.select(
        "Media type:",
        choices=["TV Show", "Movie"],
    ).ask()
    if media_type is None:
        sys.exit(0)

    if media_type == "TV Show":
        return _ask_tv_rename(selected_files)
    else:
        return _ask_movie_rename(selected_files)


def _ask_tv_rename(selected_files: list) -> list[dict] | None:  # pragma: no cover
    """Parse TV filenames, show detected components, let user confirm."""
    parsed = []
    for f in selected_files:
        info = parse_tv_filename(f.name)
        parsed.append((f, info))

    # Show detection results
    table = Table(title="Detected TV Components")
    table.add_column("File", style="cyan")
    table.add_column("Show")
    table.add_column("Season", justify="right")
    table.add_column("Episode", justify="right")
    table.add_column("Title")
    table.add_column("Status")

    has_any = False
    for f, info in parsed:
        if info:
            has_any = True
            table.add_row(
                f.name,
                info["show"],
                str(info["season"]),
                str(info["episode"]),
                info["title"] or "(none)",
                "[green]detected[/green]",
            )
        else:
            table.add_row(f.name, "", "", "", "", "[yellow]not detected[/yellow]")
    console.print(table)

    if not has_any:
        console.print("[yellow]No TV patterns detected in selected files.[/yellow]")
        return None

    confirm = questionary.confirm("Apply TV rename to detected files?", default=True).ask()
    if confirm is None:
        sys.exit(0)
    if not confirm:
        return None

    # Build one operation per file (only for detected files)
    operations = []
    for f, info in parsed:
        if info:
            operations.append({"type": "media_tv", "info": info, "file": f.name})
    return operations


def _ask_movie_rename(selected_files: list) -> list[dict] | None:  # pragma: no cover
    """Parse movie filenames, let user confirm or override title/year."""
    # Try to detect from the first file
    first_info = parse_movie_filename(selected_files[0].name) if selected_files else None

    default_title = first_info["title"] if first_info else ""
    default_year = str(first_info["year"]) if first_info else ""

    title = questionary.text("Movie title:", default=default_title).ask()
    if title is None:
        sys.exit(0)
    year_str = questionary.text("Movie year:", default=default_year).ask()
    if year_str is None:
        sys.exit(0)

    try:
        year = int(year_str)
    except ValueError:
        console.print("[red]Invalid year.[/red]")
        return None

    info = {"title": title, "year": year}
    # Apply the same movie info to all selected files
    return [{"type": "media_movie", "info": info, "file": f.name} for f in selected_files]


def apply_find_replace(stem: str, find: str, replace: str, use_regex: bool) -> str:
    if use_regex:
        return re.sub(find, replace, stem)
    return stem.replace(find, replace)


def apply_prefix(stem: str, prefix: str) -> str:
    return prefix + stem


def apply_suffix(stem: str, suffix: str) -> str:
    return stem + suffix


def apply_case(stem: str, mode: str) -> str:
    if mode == "uppercase":
        return stem.upper()
    elif mode == "lowercase":
        return stem.lower()
    elif mode == "title":
        return stem.title()
    elif mode == "snake_case":
        return re.sub(r"[\s\-]+", "_", stem.lower())
    return stem


def format_tv_name(info: dict, ext: str) -> str:
    """Build a Plex/Jellyfin-compatible TV episode filename.

    Format: Show - S01E01 - Episode Title.ext (title omitted if empty).
    """
    name = f"{info['show']} - S{info['season']:02d}E{info['episode']:02d}"
    if info.get("title"):
        name += f" - {info['title']}"
    return name + ext


def format_movie_name(info: dict, ext: str) -> str:
    """Build a Plex/Jellyfin-compatible movie filename.

    Format: Title (Year).ext
    """
    return f"{info['title']} ({info['year']}){ext}"


def normalize_extension(raw: str) -> str:
    """Normalize user input to a single leading-dot extension (e.g. '..jpg' → '.jpg')."""
    stripped = raw.lstrip(".")
    return "." + stripped if stripped else ""


def validate_extension(ext: str) -> str | None:
    """Return an error message if ext is invalid, or None if OK."""
    if not ext or ext == ".":
        return "Extension cannot be empty."
    body = ext.lstrip(".")
    if not body:
        return "Extension cannot be empty."
    if any(c in INVALID_CHARS for c in body):
        return f"Extension contains invalid characters: {ext}"
    if " " in body:
        return f"Extension contains spaces: {ext}"
    return None


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
        elif op["type"] == "case":
            stem = apply_case(stem, op["mode"])
        elif op["type"] == "ext_change":
            ext = op["ext"]
        elif op["type"] == "media_tv":
            if op.get("file") and op["file"] != file.name:
                continue
            return format_tv_name(op["info"], ext)
        elif op["type"] == "media_movie":
            if op.get("file") and op["file"] != file.name:
                continue
            return format_movie_name(op["info"], ext)

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

        # Check for empty stem: split on the last dot to find the part before
        # the extension. Names like ".txt" or "..." have no meaningful stem.
        parts = new_name.rsplit(".", 1) if new_name else [""]
        stem_before_ext = parts[0] if len(parts) == 2 else new_name
        stem_empty = not new_name or not stem_before_ext.rstrip(".")
        if new_name == original.name:
            status = "NO CHANGE"
        elif stem_empty:
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


def step_folder(state, config, excluded_names):  # pragma: no cover
    """Step 1: Folder selection + undo check. No back option (first step)."""
    default = str(state["folder"]) if state["folder"] else config.get("default_folder", "")
    folder = ask_folder(default_folder=default)

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

    state["folder"] = folder
    return state


def step_ext_filter(state, config, excluded_names):  # pragma: no cover
    """Step 2: Extension filter selection with Go back."""
    folder = state["folder"]
    all_files = list_files(folder, excluded_names=excluded_names)
    if not all_files:
        console.print(f"[yellow]No eligible files found in {folder}[/yellow]")
        sys.exit(0)

    extensions = sorted({f.suffix.lower() for f in all_files if f.suffix})
    if not extensions:
        # No extensions to filter by — skip filter, show all files
        state["ext_filter"] = None
        state["all_files"] = all_files
        return state

    no_filter = "No filter (all files)"
    choices = [GO_BACK, no_filter] + extensions
    prev_ext = state.get("ext_filter")
    default_ext = config.get("default_extension_filter")
    preferred = prev_ext or default_ext
    default_choice = preferred if preferred in choices else no_filter

    answer = questionary.select(
        "Filter by extension?",
        choices=choices,
        default=default_choice,
    ).ask()
    if answer is None:
        sys.exit(0)
    if answer == GO_BACK:
        return BACK

    ext_filter = None if answer == no_filter else answer
    state["ext_filter"] = ext_filter

    if ext_filter:
        all_files = list_files(folder, ext_filter, excluded_names=excluded_names)
        if not all_files:
            console.print(f"[yellow]No {ext_filter} files found.[/yellow]")
            return BACK

    state["all_files"] = all_files

    # Show file table
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

    return state


def step_select_files(state, config, excluded_names):  # pragma: no cover
    """Step 3: File selection via checkboxes with Go back."""
    all_files = state["all_files"]
    if not all_files:
        console.print("[yellow]No files found.[/yellow]")
        return BACK

    previously_selected = {f.name for f in state.get("selected", [])}
    file_names = [f.name for f in all_files]
    choices = [
        questionary.Choice(GO_BACK, value="__BACK__"),
        questionary.Choice("Select All", value="__ALL__"),
    ] + [
        questionary.Choice(name, value=name, checked=name in previously_selected)
        for name in file_names
    ]

    selected = questionary.checkbox(
        "Select files to rename:",
        choices=choices,
    ).ask()
    if selected is None:
        sys.exit(0)

    if "__BACK__" in selected:
        return BACK

    if "__ALL__" in selected:
        state["selected"] = list(all_files)
    else:
        name_set = set(selected)
        state["selected"] = [f for f in all_files if f.name in name_set]

    if not state["selected"]:
        console.print("[yellow]No files selected.[/yellow]")
        return BACK

    console.print(f"\n[green]{len(state['selected'])} file(s) selected.[/green]\n")
    return state


def step_operations(state, config, excluded_names):  # pragma: no cover
    """Step 4: Collect rename operations with Go back."""
    filenames = [f.name for f in state["selected"]]
    operations = []

    while True:
        op_choices = [
            GO_BACK,
            "Find/Replace (plain text)",
            "Find/Replace (regex)",
            "Add Prefix",
            "Add Suffix (before extension)",
            "Change Case",
            "Change Extension",
            "Media Library Rename",
            "Pattern Group Detection",
        ]
        op_type = questionary.select(
            "Choose operation:",
            choices=op_choices,
        ).ask()
        if op_type is None:
            sys.exit(0)
        if op_type == GO_BACK:
            return BACK

        if op_type.startswith("Find/Replace"):
            use_regex = "regex" in op_type
            find = questionary.text("Find what:").ask()
            if find is None:
                sys.exit(0)
            replace = questionary.text("Replace with (leave empty to delete):").ask()
            if replace is None:
                sys.exit(0)
            operations.append(
                {"type": "find_replace", "find": find, "replace": replace, "regex": use_regex}
            )
        elif op_type == "Add Prefix":
            prefix = questionary.text("Prefix to add:").ask()
            if prefix is None:
                sys.exit(0)
            operations.append({"type": "prefix", "prefix": prefix})
        elif op_type.startswith("Add Suffix"):
            suffix = questionary.text("Suffix to add (before extension):").ask()
            if suffix is None:
                sys.exit(0)
            operations.append({"type": "suffix", "suffix": suffix})
        elif op_type == "Change Extension":
            raw_ext = questionary.text("New extension (e.g. .jpg):").ask()
            if raw_ext is None:
                sys.exit(0)
            ext = normalize_extension(raw_ext)
            error = validate_extension(ext)
            if error:
                console.print(f"[red]{error}[/red]")
                continue
            operations.append({"type": "ext_change", "ext": ext})
        elif op_type == "Change Case":
            case_mode = questionary.select(
                "Select case mode:",
                choices=["UPPERCASE", "lowercase", "Title Case", "snake_case"],
            ).ask()
            if case_mode is None:
                sys.exit(0)
            mode_map = {
                "UPPERCASE": "uppercase",
                "lowercase": "lowercase",
                "Title Case": "title",
                "snake_case": "snake_case",
            }
            operations.append({"type": "case", "mode": mode_map[case_mode]})
        elif op_type == "Media Library Rename":
            media_ops = ask_media_rename(state["selected"])
            if media_ops is None:
                continue
            operations.extend(media_ops)
            break  # Media rename replaces the entire name; skip "add another?"
        else:
            pattern_op = ask_pattern_operation(filenames)
            if pattern_op is None:
                continue
            operations.append(pattern_op)

        another = questionary.confirm("Add another operation?", default=False).ask()
        if another is None or not another:
            break

    if not operations:
        console.print("[yellow]No operations defined.[/yellow]")
        return BACK

    state["operations"] = operations
    return state


def step_preview(state, config, excluded_names):  # pragma: no cover
    """Step 5: Preview renames and apply, go back, or abort."""
    pairs = [(f, compute_new_name(f, state["operations"])) for f in state["selected"]]
    results = validate_new_names(pairs)

    console.print()
    show_preview(results)
    console.print()

    ok_items = [r for r in results if r["status"] == "OK"]
    if not ok_items:
        console.print("[yellow]Nothing to rename.[/yellow]")
        action = questionary.select(
            "What would you like to do?",
            choices=[GO_BACK, "Abort"],
        ).ask()
        if action is None or action == "Abort":
            sys.exit(0)
        return BACK

    action = questionary.select(
        "What would you like to do?",
        choices=["Apply renames", GO_BACK, "Abort"],
    ).ask()
    if action is None or action == "Abort":
        console.print("[yellow]Aborted. No files were changed.[/yellow]")
        sys.exit(0)
    if action == GO_BACK:
        return BACK

    # Apply renames
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
        folder = ok_items[0]["original"].parent
        write_log(folder, results)
        undo_map = [{"old": r["original"].name, "new": r["new_name"]} for r in ok_items]
        try:
            save_undo_map(folder, undo_map)
            console.print(f"[dim]Undo map saved to {folder / UNDO_FILE}[/dim]")
        except OSError as e:
            console.print(f"[yellow]Warning: could not save undo map: {e}[/yellow]")

    return state


# State keys set by each step (for clearing downstream state on back navigation)
_STEP_FUNCTIONS = [step_folder, step_ext_filter, step_select_files, step_operations, step_preview]
_STEP_STATE_KEYS = [
    ["folder"],  # step 0
    ["ext_filter", "all_files"],  # step 1
    ["selected"],  # step 2
    ["operations"],  # step 3
    [],  # step 4
]
_STATE_DEFAULTS = {
    "folder": None,
    "ext_filter": None,
    "all_files": [],
    "selected": [],
    "operations": [],
}


def main():  # pragma: no cover
    console.print("[bold blue]═══ Batch File Rename Tool ═══[/bold blue]\n")

    config = load_config()
    excluded_names = frozenset(n.lower() for n in config.get("excluded_files", []))
    state = dict(_STATE_DEFAULTS)

    step_idx = 0
    while step_idx < len(_STEP_FUNCTIONS):
        result = _STEP_FUNCTIONS[step_idx](state, config, excluded_names)
        if result == BACK:
            if step_idx > 0:
                # Clear state from current step onwards
                for i in range(step_idx, len(_STEP_FUNCTIONS)):
                    for key in _STEP_STATE_KEYS[i]:
                        state[key] = (
                            None if _STATE_DEFAULTS[key] is None else type(_STATE_DEFAULTS[key])()
                        )
                step_idx -= 1
        else:
            step_idx += 1


if __name__ == "__main__":  # pragma: no cover
    main()
