#!/usr/bin/env python3
"""semacro - explore and expand SELinux policy macros, interfaces, and templates."""

import argparse
import os
import re
import signal
import sys
from dataclasses import dataclass, field
from pathlib import Path


# --- Data model ---

@dataclass
class MacroDef:
    """A parsed macro definition (interface, template, or define)."""
    name: str
    kind: str          # "interface", "template", or "define"
    body: str
    source_file: str   # path relative to include root
    line_number: int

    def display_body(self) -> str:
        return f"{self.kind}(`{self.name}',`\n{self.body}\n')"


# --- Color helpers ---

class Color:
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    DIM = "\033[2m"
    RESET = "\033[0m"

_use_color = True

def colored(text: str, *codes: str) -> str:
    if not _use_color:
        return text
    return "".join(codes) + text + Color.RESET


# --- M4 parser ---

def _find_m4_block_end(text: str, start: int) -> int:
    """Find the matching closing quote for an M4 backtick-quoted block.

    Starting after the opening backtick at `start`, tracks nesting of
    backtick/single-quote pairs and returns the index of the closing
    single quote.  Returns -1 if unmatched.
    """
    depth = 1
    i = start
    while i < len(text):
        ch = text[i]
        if ch == '`':
            depth += 1
        elif ch == "'":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


_MACRO_START = re.compile(
    r"^(interface|template|define)\(\s*`([^']+)'\s*,\s*`",
    re.MULTILINE,
)


def parse_file(filepath: str, rel_path: str) -> list[MacroDef]:
    """Parse a .if or .spt file, extracting all macro definitions."""
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    results: list[MacroDef] = []
    for m in _MACRO_START.finditer(text):
        kind = m.group(1)
        name = m.group(2)
        body_start = m.end()
        body_end = _find_m4_block_end(text, body_start)
        if body_end == -1:
            continue

        body = text[body_start:body_end]

        # Strip one leading/trailing newline from body if present
        if body.startswith("\n"):
            body = body[1:]
        if body.endswith("\n"):
            body = body[:-1]

        line_number = text[:m.start()].count("\n") + 1
        results.append(MacroDef(
            name=name,
            kind=kind,
            body=body,
            source_file=rel_path,
            line_number=line_number,
        ))

    return results


# --- Index: scan all .if and .spt files ---

_STANDARD_PATHS = [
    "/usr/share/selinux/devel/include",
]


def _has_policy_files(path: str) -> bool:
    """Check if a directory tree contains any .if or .spt files."""
    for dirpath, _dirs, filenames in os.walk(path):
        for f in filenames:
            if f.endswith(".if") or f.endswith(".spt"):
                return True
    return False


def detect_include_path() -> str | None:
    """Find the SELinux policy include directory.

    Returns a path only if it actually contains .if or .spt files.
    """
    for p in _STANDARD_PATHS:
        if os.path.isdir(p) and _has_policy_files(p):
            return p
    return None


def build_index(include_path: str) -> dict[str, MacroDef]:
    """Walk include_path, parse all .if and .spt files, return name -> MacroDef."""
    index: dict[str, MacroDef] = {}
    for dirpath, _dirnames, filenames in os.walk(include_path):
        for fname in filenames:
            if not (fname.endswith(".if") or fname.endswith(".spt")):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, include_path)
            for macro in parse_file(full, rel):
                index[macro.name] = macro
    return index


# --- Commands ---

def cmd_lookup(index: dict[str, MacroDef], name: str) -> int:
    """Look up a macro by exact name and print its definition."""
    macro = index.get(name)
    if not macro:
        print(f"semacro: macro '{name}' not found", file=sys.stderr)
        return 1

    header = colored(f"{macro.kind}", Color.DIM) + " " + colored(macro.name, Color.BOLD, Color.CYAN)
    source = colored(f"# {macro.source_file}:{macro.line_number}", Color.DIM)
    print(f"{header}  {source}")
    print(macro.display_body())
    return 0


def cmd_find(index: dict[str, MacroDef], pattern: str) -> int:
    """Search for macros whose name matches a regex pattern."""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"semacro: invalid regex '{pattern}': {e}", file=sys.stderr)
        return 1

    matches = sorted(
        ((name, m) for name, m in index.items() if regex.search(name)),
        key=lambda pair: pair[0],
    )

    if not matches:
        print(f"semacro: no macros matching '{pattern}'", file=sys.stderr)
        return 1

    for name, macro in matches:
        source = colored(macro.source_file, Color.DIM)
        kind_tag = colored(f"[{macro.kind[0]}]", Color.YELLOW)
        print(f"  {kind_tag} {source}: {colored(name, Color.BOLD)}")

    print(colored(f"\n{len(matches)} result(s)", Color.DIM))
    return 0


_CATEGORY_DIRS = {
    "kernel":  {"kernel"},
    "system":  {"system"},
    "admin":   {"admin"},
    "apps":    {"apps"},
    "roles":   {"roles"},
    "services": {"services"},
    "contrib": {"contrib"},
    "support": {"support"},
}


def cmd_list(index: dict[str, MacroDef], category: str | None) -> int:
    """List all macros, optionally filtered by category."""
    entries = []
    for name, macro in index.items():
        if category and category != "all":
            parts = Path(macro.source_file).parts
            cat_dirs = _CATEGORY_DIRS.get(category, {category})
            if not any(p in cat_dirs for p in parts):
                continue
        entries.append((name, macro))

    entries.sort(key=lambda pair: pair[0])

    if not entries:
        print(f"semacro: no macros found for category '{category}'", file=sys.stderr)
        return 1

    width = len(str(len(entries)))
    for i, (name, macro) in enumerate(entries, 1):
        kind_tag = colored(f"[{macro.kind[0]}]", Color.YELLOW)
        source = colored(macro.source_file, Color.DIM)
        num = colored(f"{i:>{width}}", Color.DIM)
        print(f"  {num}  {kind_tag} {colored(name, Color.BOLD)}  {source}")

    print(colored(f"\n{len(entries)} macro(s)", Color.DIM))
    return 0


# --- CLI ---

def main() -> int:
    global _use_color

    parser = argparse.ArgumentParser(
        prog="semacro",
        description="Explore and expand SELinux policy macros, interfaces, and templates.",
        epilog="Policy path resolution (highest priority first):\n"
               "  1. --include-path flag\n"
               "  2. SEMACRO_INCLUDE_PATH environment variable\n"
               "  3. /usr/share/selinux/devel/include (requires selinux-policy-devel)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--include-path", metavar="DIR",
        help="Path to SELinux policy include directory "
             "(overrides SEMACRO_INCLUDE_PATH env var and default path)",
    )

    sub = parser.add_subparsers(dest="command")

    # lookup
    p_lookup = sub.add_parser("lookup", help="Show the definition of a macro")
    p_lookup.add_argument("name", help="Macro name (e.g. files_pid_filetrans)")

    # find
    p_find = sub.add_parser("find", help="Search for macros matching a regex pattern")
    p_find.add_argument("pattern", help="Regex pattern to match against macro names")

    # list
    p_list = sub.add_parser("list", help="List available macros")
    p_list.add_argument(
        "--category", "-c",
        choices=["kernel", "system", "admin", "apps", "roles", "services", "contrib", "support", "all"],
        default="all",
        help="Filter by policy category (default: all)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.no_color or not sys.stdout.isatty():
        _use_color = False

    include_path = args.include_path or os.environ.get("SEMACRO_INCLUDE_PATH") or detect_include_path()
    if not include_path:
        print(
            "semacro: cannot find SELinux policy include directory.\n"
            "  Options:\n"
            "    1. Install selinux-policy-devel (provides the default path)\n"
            "    2. export SEMACRO_INCLUDE_PATH=/path/to/policy  (add to ~/.bashrc)\n"
            "    3. semacro --include-path /path/to/policy ...",
            file=sys.stderr,
        )
        return 1

    if not os.path.isdir(include_path):
        print(f"semacro: include path '{include_path}' does not exist", file=sys.stderr)
        return 1

    index = build_index(include_path)

    if not index:
        print(f"semacro: no macros found under '{include_path}'", file=sys.stderr)
        return 1

    has_support = any(m.kind == "define" for m in index.values())
    has_kernel = any("kernel" in m.source_file for m in index.values())
    if not has_support or not has_kernel:
        missing = []
        if not has_support:
            missing.append("support/*.spt (defines)")
        if not has_kernel:
            missing.append("kernel/*.if (core interfaces)")
        print(
            f"semacro: warning: incomplete policy tree — missing {', '.join(missing)}.\n"
            f"  Install the full selinux-policy-devel package or point --include-path\n"
            f"  to a complete policy source tree.",
            file=sys.stderr,
        )

    if args.command == "lookup":
        return cmd_lookup(index, args.name)
    elif args.command == "find":
        return cmd_find(index, args.pattern)
    elif args.command == "list":
        return cmd_list(index, args.category)

    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(0)
