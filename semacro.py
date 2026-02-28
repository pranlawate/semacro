#!/usr/bin/env python3
"""semacro - explore and expand SELinux policy macros, interfaces, and templates."""

__version__ = "0.2.0"

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


# --- Call parsing and expansion ---

_CALL_PATTERN = re.compile(r"^(\w+)\((.+)\)$", re.DOTALL)

def parse_call(text: str) -> tuple[str, list[str]] | None:
    """Parse 'name(arg1, arg2, ...)' into (name, [arg1, arg2, ...]).

    Returns None if the text is a plain name with no parentheses.
    """
    text = text.strip()
    m = _CALL_PATTERN.match(text)
    if not m:
        return None
    name = m.group(1)
    args_str = m.group(2)
    args = [a.strip() for a in args_str.split(",")]
    return name, args


def substitute_args(body: str, args: list[str]) -> str:
    """Replace $1, $2, ... $N with the provided arguments.

    Unset positional args ($N where N > len(args)) expand to empty string,
    matching M4 behavior.  Also handles $* (all args as comma-separated)
    and leaves $0 as-is (macro name).
    """
    def _replacer(m: re.Match) -> str:
        idx = int(m.group(1))
        if idx == 0:
            return m.group(0)
        if 1 <= idx <= len(args):
            return args[idx - 1]
        return ""

    result = re.sub(r'\$(\d+)', _replacer, body)
    result = result.replace("$*", ",".join(args))
    return result


_BODY_CALL = re.compile(r"\b(\w+)\(([^)]*)\)")

def find_calls_in_body(body: str) -> list[tuple[str, list[str], int, int]]:
    """Find macro calls in a body, returning (name, args, start, end) for each.

    Skips lines that are comments, gen_require blocks, and known
    policy statements that aren't macro calls.
    """
    skip_names = {
        "allow", "dontaudit", "auditallow", "neverallow",
        "type_transition", "type_change", "type_member",
        "role_transition", "range_transition",
        "gen_require", "optional_policy", "tunable_policy",
        "require", "type", "role", "attribute", "bool",
        "ifdef", "ifndef", "refpolicywarn",
    }
    calls = []
    for m in _BODY_CALL.finditer(body):
        name = m.group(1)
        if name in skip_names:
            continue
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_prefix = body[line_start:m.start()].strip()
        if line_prefix.startswith("#"):
            continue
        args = [a.strip() for a in m.group(2).split(",")] if m.group(2).strip() else []
        calls.append((name, args, m.start(), m.end()))
    return calls


@dataclass
class ExpansionNode:
    """A node in the expansion tree."""
    text: str
    children: list["ExpansionNode"] = field(default_factory=list)
    is_leaf: bool = False


_GEN_REQUIRE_BLOCK = re.compile(
    r"\bgen_require\(\s*`[^']*'\s*\)\s*\n?",
    re.DOTALL,
)

def _strip_gen_require(body: str) -> str:
    """Remove gen_require(`...') blocks from a macro body."""
    return _GEN_REQUIRE_BLOCK.sub("", body)


DEFAULT_MAX_DEPTH = 10

_WORD_TOKEN = re.compile(r'\b([a-zA-Z_]\w+)\b')


_NESTED_BRACES = re.compile(r'\{([^{}]*)\{([^{}]*)\}([^{}]*)\}')


def _flatten_braces(text: str) -> str:
    """Flatten nested permission brace sets: { a { b c } d } -> { a b c d }."""
    while _NESTED_BRACES.search(text):
        text = _NESTED_BRACES.sub(r'{ \1 \2 \3 }', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text


def _resolve_defines_in_text(text: str, index: dict[str, MacroDef]) -> str:
    """Inline-expand simple define macros (permission sets, etc.) in a leaf line.

    Only resolves defines whose bodies don't reference positional args ($N).
    Iterates to handle chained defines (e.g. read_file_perms ->
    read_inherited_file_perms), then flattens any nested brace sets.
    """
    for _ in range(5):
        changed = False
        for m in _WORD_TOKEN.finditer(text):
            word = m.group(1)
            macro = index.get(word)
            if macro and macro.kind == "define" and "$" not in macro.body:
                text = text[:m.start()] + macro.body.strip() + text[m.end():]
                changed = True
                break
        if not changed:
            break
    return _flatten_braces(text)


def expand_macro(
    index: dict[str, MacroDef],
    name: str,
    args: list[str],
    depth: int = 0,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> ExpansionNode:
    """Recursively expand a macro call into an ExpansionNode tree."""
    call_str = f"{name}({', '.join(args)})" if args else name
    node = ExpansionNode(text=call_str)

    if depth > max_depth:
        node.children.append(ExpansionNode(text="... (max depth reached)", is_leaf=True))
        return node

    macro = index.get(name)
    if not macro:
        node.is_leaf = True
        return node

    body = substitute_args(macro.body, args) if args else macro.body

    body = _strip_gen_require(body)

    calls = find_calls_in_body(body)
    if not calls:
        for line in body.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                node.children.append(ExpansionNode(
                    text=_resolve_defines_in_text(line, index), is_leaf=True))
        return node

    def _add_leaf_lines(text: str):
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(";") or re.match(
                r"(allow|dontaudit|auditallow|neverallow|type_transition|type_change|type_member|role_transition)\s", line
            ):
                node.children.append(ExpansionNode(
                    text=_resolve_defines_in_text(line, index), is_leaf=True))

    last_end = 0
    for call_name, call_args, start, end in calls:
        _add_leaf_lines(body[last_end:start])

        child_macro = index.get(call_name)
        if child_macro:
            node.children.append(expand_macro(index, call_name, call_args, depth + 1, max_depth))
        else:
            node.children.append(ExpansionNode(
                text=f"{call_name}({', '.join(call_args)})",
                is_leaf=True,
            ))
        last_end = end

    _add_leaf_lines(body[last_end:])

    return node


def format_tree(node: ExpansionNode, prefix: str = "", is_last: bool = True, is_root: bool = True) -> str:
    """Render an ExpansionNode tree with box-drawing characters."""
    lines = []

    if is_root:
        lines.append(colored(node.text, Color.BOLD, Color.CYAN))
    else:
        connector = "└── " if is_last else "├── "
        if node.is_leaf:
            lines.append(prefix + connector + node.text)
        else:
            lines.append(prefix + connector + colored(node.text, Color.BOLD, Color.YELLOW))

    child_prefix = prefix + ("    " if is_last else "│   ")
    for i, child in enumerate(node.children):
        is_child_last = (i == len(node.children) - 1)
        lines.append(format_tree(child, child_prefix if not is_root else "", is_child_last, is_root=False))

    return "\n".join(lines)


_AV_RULE = re.compile(
    r'^(allow|dontaudit|auditallow|neverallow)\s+(\S+)\s+(\S+:\S+)\s+\{([^}]+)\}\s*;$'
)


def collect_leaf_rules(node: ExpansionNode) -> list[str]:
    """Walk the expansion tree, deduplicate, and merge access vector rules.

    Rules with the same (type, source, target:class) have their permission
    sets unioned.  Non-AV rules (type_transition, etc.) pass through as-is.
    """
    seen: dict[str, None] = {}
    def _walk(n: ExpansionNode):
        if n.is_leaf:
            seen.setdefault(n.text, None)
        for child in n.children:
            _walk(child)
    _walk(node)

    merged_perms: dict[str, dict[str, None]] = {}
    merged_order: dict[str, int] = {}
    other: list[tuple[int, str]] = []

    for pos, rule in enumerate(seen):
        m = _AV_RULE.match(rule)
        if m:
            rule_type, source, target_class, perms_str = m.groups()
            key = f"{rule_type} {source} {target_class}"
            if key not in merged_perms:
                merged_perms[key] = {}
                merged_order[key] = pos
            for p in perms_str.split():
                merged_perms[key].setdefault(p, None)
        else:
            other.append((pos, rule))

    result: list[tuple[int, str]] = list(other)
    for key, perms in merged_perms.items():
        result.append((merged_order[key], f"{key} {{ {' '.join(perms)} }};"))
    result.sort(key=lambda x: x[0])
    return [text for _, text in result]


# --- Commands ---

def cmd_lookup(
    index: dict[str, MacroDef],
    name: str,
    expand: bool = False,
    rules: bool = False,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> int:
    """Look up a macro by exact name and print its definition.

    If name contains parentheses, parse as a call and substitute arguments.
    If --expand is set, recursively expand nested macros with tree output.
    If --rules is set, output flat deduplicated policy rules (copy-paste ready).
    """
    call = parse_call(name)
    if call:
        macro_name, args = call
    else:
        macro_name, args = name, []

    macro = index.get(macro_name)
    if not macro:
        print(f"semacro: macro '{macro_name}' not found", file=sys.stderr)
        near = [n for n in index if macro_name.lower() in n.lower() and n != macro_name]
        if near:
            print(f"  Did you mean: {', '.join(sorted(near)[:5])}", file=sys.stderr)
        else:
            print(f"  Try: semacro find \"{macro_name}\"", file=sys.stderr)
        return 1

    if (rules or expand) and not args:
        print(
            f"semacro: warning: no arguments provided — output will contain raw $N references.\n"
            f"  Try: semacro lookup {'--rules' if rules else '--expand'} \"{macro_name}(type1, type2, ...)\"",
            file=sys.stderr,
        )

    if rules:
        tree = expand_macro(index, macro_name, args, max_depth=max_depth)
        for rule in collect_leaf_rules(tree):
            print(rule)
        return 0

    if expand:
        tree = expand_macro(index, macro_name, args, max_depth=max_depth)
        print(format_tree(tree))
        return 0

    header = colored(f"{macro.kind}", Color.DIM) + " " + colored(macro.name, Color.BOLD, Color.CYAN)
    source = colored(f"# {macro.source_file}:{macro.line_number}", Color.DIM)
    print(f"{header}  {source}")

    if args:
        body = substitute_args(macro.body, args)
        print(f"{macro.kind}(`{macro.name}',`\n{body}\n')")
    else:
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
        print(f"  Patterns are case-insensitive Python regexes. Try a broader pattern.", file=sys.stderr)
        return 1

    for name, macro in matches:
        source = colored(macro.source_file, Color.DIM)
        kind_tag = colored(f"[{macro.kind[0]}]", Color.YELLOW)
        print(f"  {kind_tag} {source}: {colored(name, Color.BOLD)}")

    print(colored(f"\n{len(matches)} result(s)", Color.DIM))
    return 0


_CATEGORY_DIRS = {
    "kernel":      {"kernel"},
    "system":      {"system"},
    "admin":       {"admin"},
    "apps":        {"apps"},
    "roles":       {"roles"},
    "services":    {"services"},
    "contrib":     {"contrib"},
    "distributed": {"distributed"},
    "support":     {"support"},
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


def cmd_callers(index: dict[str, MacroDef], name: str) -> int:
    """Find which macros directly call the given macro (reverse lookup)."""
    if name not in index:
        print(f"semacro: macro '{name}' not found", file=sys.stderr)
        near = [n for n in index if name.lower() in n.lower() and n != name]
        if near:
            print(f"  Did you mean: {', '.join(sorted(near)[:5])}", file=sys.stderr)
        else:
            print(f"  Try: semacro find \"{name}\"", file=sys.stderr)
        return 1

    callers = []
    for macro_name, macro in index.items():
        if macro_name == name:
            continue
        for call_name, _args, _start, _end in find_calls_in_body(macro.body):
            if call_name == name:
                callers.append((macro_name, macro))
                break

    if not callers:
        print(f"semacro: no macros call '{name}'", file=sys.stderr)
        return 0

    callers.sort(key=lambda pair: pair[0])
    for caller_name, macro in callers:
        source = colored(macro.source_file, Color.DIM)
        kind_tag = colored(f"[{macro.kind[0]}]", Color.YELLOW)
        print(f"  {kind_tag} {source}: {colored(caller_name, Color.BOLD)}")

    print(colored(f"\n{len(callers)} caller(s)", Color.DIM))
    return 0


_HIGHEST_ARG = re.compile(r'\$(\d+)')


def _macro_arity(macro: MacroDef) -> int:
    """Estimate the number of positional arguments a macro expects."""
    return max((int(m.group(1)) for m in _HIGHEST_ARG.finditer(macro.body)), default=0)


def _build_transition_trials(
    source: str, parent: str, new_type: str, arity: int,
) -> list[list[str]]:
    """Build trial argument lists for type_transition search.

    Different macros put the new_type in different $N positions, and the
    parent type may be hardcoded.  We try several arrangements so at
    least one is likely to produce the correct type_transition rule.
    """
    _CLASS_GUESSES = ["file", "dir", "sock_file", "lnk_file"]
    trials: list[list[str]] = []

    def _pad(args: list[str]) -> list[str]:
        return args + [""] * max(0, arity - len(args))

    if arity <= 1:
        trials.append(_pad([source]))
    elif arity == 2:
        trials.append(_pad([source, new_type]))
        trials.append(_pad([source, parent]))
    elif arity == 3:
        for cls in _CLASS_GUESSES:
            trials.append(_pad([source, new_type, cls]))
        trials.append(_pad([source, parent, new_type]))
    else:
        for cls in _CLASS_GUESSES:
            trials.append(_pad([source, new_type, cls]))
            trials.append(_pad([source, parent, new_type, cls]))
        trials.append(_pad([source, new_type]))
        trials.append(_pad([source, parent, new_type]))

    return trials


_TT_RULE = re.compile(
    r'^type_transition\s+(\S+)\s+(\S+):(\S+)\s+(\S+)(?:\s+"([^"]*)")?\s*;$'
)


def cmd_which(
    index: dict[str, MacroDef],
    source: str,
    target: str,
    third: str,
    transition: bool = False,
    obj_class: str | None = None,
    trans_name: str | None = None,
) -> int:
    """Find macros that would grant the requested access.

    AV mode (default): find macros producing allow rules for source -> target
    with the given permission(s).
    Transition mode: find macros producing type_transition rules creating
    the new_type under parent_type.
    """
    if transition:
        new_type = third
    else:
        requested_perms = set(third.split())

    candidates: list[tuple[str, MacroDef]] = []
    search_terms = {target}
    if transition:
        search_terms.add(third)
    for macro_name, macro in index.items():
        if macro.kind == "define" and "$" not in macro.body:
            continue
        if any(term in macro.body or term in macro_name for term in search_terms):
            candidates.append((macro_name, macro))

    matches: list[tuple[str, str, MacroDef]] = []

    for macro_name, macro in candidates:
        arity = _macro_arity(macro)

        if transition:
            trial_sets = _build_transition_trials(source, target, third, arity)
        else:
            trial_args = [source]
            if arity >= 2:
                trial_args.append(target)
            if arity >= 3:
                trial_args.append(third)
            for i in range(len(trial_args), arity):
                trial_args.append("")
            trial_sets = [trial_args]

        rules: list[str] = []
        winning_args: list[str] = []
        for trial_args in trial_sets:
            try:
                tree = expand_macro(index, macro_name, trial_args, max_depth=5)
            except Exception:
                continue
            rules = collect_leaf_rules(tree)
            if rules:
                winning_args = trial_args
                break
        if not rules:
            continue

        for rule in rules:
            if transition:
                m = _TT_RULE.match(rule)
                if not m:
                    continue
                r_src, r_parent, r_class, r_new, r_name = m.groups()
                if r_src != source or r_parent != target or r_new != new_type:
                    continue
                if obj_class and r_class != obj_class:
                    continue
                if trans_name and r_name != trans_name:
                    continue
                call_sig = f"{macro_name}({', '.join(a for a in winning_args if a)})"
                matches.append((macro_name, call_sig, macro))
                break
            else:
                av = _AV_RULE.match(rule)
                if not av:
                    continue
                _rtype, r_src, r_target_class, r_perms_str = av.groups()
                if r_src != source:
                    continue
                t_class = r_target_class.split(":")
                r_target = t_class[0]
                r_class = t_class[1] if len(t_class) > 1 else None
                if r_target != target:
                    continue
                if obj_class and r_class != obj_class:
                    continue
                r_perms = set(r_perms_str.split())
                if requested_perms.issubset(r_perms):
                    call_sig = f"{macro_name}({', '.join(a for a in winning_args if a)})"
                    matches.append((macro_name, call_sig, macro))
                    break

    if not matches:
        if transition:
            print(f"semacro: no macros found that create type_transition "
                  f"{source} {target} -> {third}", file=sys.stderr)
        else:
            print(f"semacro: no macros found granting {source} {third} on {target}",
                  file=sys.stderr)
        return 1

    seen_names: set[str] = set()
    for macro_name, call_sig, macro in sorted(matches, key=lambda x: x[0]):
        if macro_name in seen_names:
            continue
        seen_names.add(macro_name)
        source_info = colored(f"{macro.source_file}:{macro.line_number}", Color.DIM)
        print(f"  {colored(call_sig, Color.BOLD, Color.CYAN)}  {source_info}")

    print(colored(f"\n{len(seen_names)} result(s)", Color.DIM))
    return 0


_POLICY_MODULE = re.compile(r'^\s*policy_module\s*\(', re.MULTILINE)
_COMMENT_LINE = re.compile(r'^\s*#')
_BLANK_LINE = re.compile(r'^\s*$')
_RULE_STATEMENT = re.compile(
    r'^\s*(allow|dontaudit|auditallow|neverallow|type_transition|type_change|'
    r'type_member|role_transition|range_transition)\s'
)
_TYPE_DECL = re.compile(r'^\s*(type|attribute|typeattribute|typealias|bool|role)\s')


def cmd_expand_file(
    index: dict[str, MacroDef],
    filepath: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
    tree_mode: bool = False,
) -> int:
    """Expand all macro calls in a .te file to final policy rules."""
    if filepath == "-":
        content = sys.stdin.read()
    else:
        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"semacro: cannot read '{filepath}': {e}", file=sys.stderr)
            return 1

    all_rules: list[str] = []
    all_trees: list[ExpansionNode] = []

    for line in content.splitlines():
        if _COMMENT_LINE.match(line) or _BLANK_LINE.match(line):
            continue
        if _POLICY_MODULE.match(line):
            continue
        stripped = line.strip()
        if stripped.startswith("gen_require") or stripped.startswith("require"):
            continue
        if _TYPE_DECL.match(line):
            continue

        if _RULE_STATEMENT.match(line):
            resolved = _resolve_defines_in_text(stripped, index)
            if not resolved.endswith(";"):
                resolved += ";"
            all_rules.append(resolved)
            continue

        calls = find_calls_in_body(stripped)
        if calls:
            for call_name, call_args, _start, _end in calls:
                macro = index.get(call_name)
                if macro:
                    tree = expand_macro(index, call_name, call_args,
                                        max_depth=max_depth)
                    if tree_mode:
                        all_trees.append(tree)
                    else:
                        all_rules.extend(collect_leaf_rules(tree))

    if tree_mode:
        for tree in all_trees:
            print(format_tree(tree))
            print()
        return 0

    merged = _merge_rules(all_rules)
    for rule in merged:
        print(rule)
    return 0


def _merge_rules(rules: list[str]) -> list[str]:
    """Deduplicate and merge a flat list of policy rule strings."""
    seen: dict[str, None] = {}
    for r in rules:
        seen.setdefault(r, None)

    merged_perms: dict[str, dict[str, None]] = {}
    merged_order: dict[str, int] = {}
    other: list[tuple[int, str]] = []

    for pos, rule in enumerate(seen):
        m = _AV_RULE.match(rule)
        if m:
            rule_type, source, target_class, perms_str = m.groups()
            key = f"{rule_type} {source} {target_class}"
            if key not in merged_perms:
                merged_perms[key] = {}
                merged_order[key] = pos
            for p in perms_str.split():
                merged_perms[key].setdefault(p, None)
        else:
            other.append((pos, rule))

    result: list[tuple[int, str]] = list(other)
    for key, perms in merged_perms.items():
        result.append((merged_order[key], f"{key} {{ {' '.join(perms)} }};"))
    result.sort(key=lambda x: x[0])
    return [text for _, text in result]


# --- CLI ---

def _read_arg(value: str | None, command: str) -> str | None:
    """Resolve a positional argument: use the value if given, read one line
    from stdin if it's piped and value is None or '-', or error out."""
    if value is not None and value != "-":
        return value
    if not sys.stdin.isatty():
        line = sys.stdin.readline().strip()
        if line:
            return line
    print(f"semacro {command}: missing required argument (provide it or pipe via stdin)", file=sys.stderr)
    return None


def main() -> int:
    global _use_color

    parser = argparse.ArgumentParser(
        prog="semacro",
        description="Explore and expand SELinux policy macros, interfaces, and templates.",
        epilog="Examples:\n"
               "  semacro lookup files_pid_filetrans                          Show raw definition\n"
               "  semacro lookup -e \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\"  Expand tree\n"
               "  semacro lookup -r \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\"  Flat rules\n"
               "  semacro find \"pid_filetrans\"                                Search by pattern\n"
               "  semacro list --category kernel                              List kernel macros\n"
               "  semacro callers filetrans_pattern                           Reverse lookup\n"
               "  semacro which ntpd_t httpd_log_t read                       Find granting macro\n"
               "  semacro expand myapp.te                                     Expand a .te file\n"
               "\n"
               "Policy path resolution (highest priority first):\n"
               "  1. --include-path flag\n"
               "  2. SEMACRO_INCLUDE_PATH environment variable\n"
               "  3. /usr/share/selinux/devel/include (requires selinux-policy-devel)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"%(prog)s {__version__}",
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
    p_lookup = sub.add_parser(
        "lookup",
        help="Show or expand a macro definition",
        description="Show a macro definition, optionally with argument substitution and recursive expansion.",
        epilog="Examples:\n"
               "  semacro lookup files_pid_filetrans\n"
               "      Show raw definition with $1, $2, etc.\n\n"
               "  semacro lookup \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\"\n"
               "      Show definition with arguments substituted\n\n"
               "  semacro lookup -e \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\"\n"
               "      Recursively expand nested macros into a tree of policy rules.\n"
               "      Permission-set defines (search_dir_perms, etc.) are resolved inline.\n\n"
               "  semacro lookup -r \"apache_read_log(mysqld_t)\"\n"
               "      Flat deduplicated policy rules, ready to paste into a .te file.\n\n"
               "  semacro lookup -e -d 1 \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\"\n"
               "      Expand only one level deep\n\n"
               "  echo \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\" | semacro lookup -r\n"
               "      Read macro call from stdin (useful in scripts)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_lookup.add_argument("name", nargs="?", default=None,
                          help="Macro name or call — e.g. files_pid_filetrans or \"files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)\". "
                               "Use - to read from stdin.")
    mode = p_lookup.add_mutually_exclusive_group()
    mode.add_argument("-e", "--expand", action="store_true", help="Recursively expand nested macros into a tree of final policy rules")
    mode.add_argument("-r", "--rules", action="store_true", help="Output flat deduplicated policy rules (copy-paste ready for .te files)")
    p_lookup.add_argument("-d", "--depth", type=int, default=DEFAULT_MAX_DEPTH,
                          help=f"Max expansion depth (default: {DEFAULT_MAX_DEPTH})")

    # find
    p_find = sub.add_parser("find", help="Search for macros matching a regex pattern")
    p_find.add_argument("pattern", nargs="?", default=None,
                        help="Regex pattern to match against macro names. Use - to read from stdin.")

    # list
    p_list = sub.add_parser("list", help="List available macros")
    p_list.add_argument(
        "--category", "-c",
        choices=["kernel", "system", "admin", "apps", "roles", "services", "contrib", "distributed", "support", "all"],
        default="all",
        help="Filter by policy category (default: all)",
    )

    # callers
    p_callers = sub.add_parser(
        "callers",
        help="Find which macros call a given macro (reverse lookup)",
        description="Scan the policy index and report every macro that directly calls the given macro.",
        epilog="Examples:\n"
               "  semacro callers filetrans_pattern\n"
               "      Find all macros that call filetrans_pattern\n\n"
               "  semacro callers manage_files_pattern\n"
               "      See who uses manage_files_pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_callers.add_argument("name", nargs="?", default=None,
                           help="Macro name to find callers for. Use - to read from stdin.")

    # which
    p_which = sub.add_parser(
        "which",
        help="Find macros that grant a specific access",
        description="Search for macros that would produce allow rules or type_transitions "
                    "matching the given access parameters.",
        epilog="Examples:\n"
               "  semacro which ntpd_t httpd_log_t read\n"
               "      Find macros granting ntpd_t read access to httpd_log_t\n\n"
               "  semacro which ntpd_t httpd_log_t \"read write\" --class file\n"
               "      Require both perms on file class\n\n"
               "  semacro which -T ntpd_t var_run_t ntpd_var_run_t\n"
               "      Find macros creating type_transition to ntpd_var_run_t",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_which.add_argument("source", help="Source domain type (e.g. ntpd_t)")
    p_which.add_argument("target", help="Target type (e.g. httpd_log_t) or parent type for transitions")
    p_which.add_argument("third", help="Permission(s) for AV rules, or new type for transitions. "
                         "Quote multiple perms: \"read write\"")
    p_which.add_argument("-T", "--transition", action="store_true",
                         help="Search for type_transition rules instead of allow rules")
    p_which.add_argument("-C", "--class", dest="obj_class", metavar="CLASS",
                         help="Filter by object class (e.g. file, dir, sock_file)")
    p_which.add_argument("-N", "--name", dest="trans_name", metavar="FILENAME",
                         help="Filter by named transition filename (only with -T)")

    # expand
    p_expand = sub.add_parser(
        "expand",
        help="Expand all macros in a .te policy file",
        description="Read a .te file, expand every macro call, and output the full set "
                    "of final policy rules.",
        epilog="Examples:\n"
               "  semacro expand myapp.te\n"
               "      Output flat merged rules for the module\n\n"
               "  semacro expand -t myapp.te\n"
               "      Output expansion trees for each macro call\n\n"
               "  cat myapp.te | semacro expand -\n"
               "      Read from stdin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_expand.add_argument("filepath", help="Path to .te file (use - for stdin)")
    p_expand.add_argument("-d", "--depth", type=int, default=DEFAULT_MAX_DEPTH,
                          help=f"Max expansion depth (default: {DEFAULT_MAX_DEPTH})")
    p_expand.add_argument("-t", "--tree", action="store_true",
                          help="Output expansion trees instead of flat rules")

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
        name = _read_arg(args.name, "lookup")
        if name is None:
            return 1
        if args.depth < 1:
            print("semacro: --depth must be at least 1", file=sys.stderr)
            return 1
        return cmd_lookup(index, name, expand=args.expand, rules=args.rules, max_depth=args.depth)
    elif args.command == "find":
        pattern = _read_arg(args.pattern, "find")
        if pattern is None:
            return 1
        return cmd_find(index, pattern)
    elif args.command == "list":
        return cmd_list(index, args.category)
    elif args.command == "callers":
        name = _read_arg(args.name, "callers")
        if name is None:
            return 1
        return cmd_callers(index, name)
    elif args.command == "which":
        if args.trans_name and not args.transition:
            print("semacro: --name only applies with --transition", file=sys.stderr)
            return 1
        return cmd_which(index, args.source, args.target, args.third,
                         transition=args.transition, obj_class=args.obj_class,
                         trans_name=args.trans_name)
    elif args.command == "expand":
        if args.depth < 1:
            print("semacro: --depth must be at least 1", file=sys.stderr)
            return 1
        return cmd_expand_file(index, args.filepath, max_depth=args.depth,
                               tree_mode=args.tree)

    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    try:
        sys.exit(main())
    except BrokenPipeError:
        os._exit(0)
