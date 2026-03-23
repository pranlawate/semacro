# semacro: SELinux Macro Explorer — Design Document

**Version:** 1.0
**Date:** 2026-03-23
**Status:** All 6 phases complete. RPM packaged, COPR distributed.
Test suite implementation plan created.

---

## 1. Overview

### Purpose

semacro parses the SELinux reference-policy M4 macro library and provides
quick lookup, search, and recursive expansion of interfaces, templates,
and defines. It replaces the manual process of digging through `.if` and
`.spt` files to understand what a macro actually does.

### Architecture

```
/usr/share/selinux/devel/include/    ← policy source (.if, .spt files)
        │
        ▼
   Index Builder (parse_file)         ← parse M4 blocks into MacroDef
        │
        ▼
   Cached Index (~/.cache/semacro/)   ← 45x faster repeat access
        │
        ▼
   Subcommands                        ← lookup, find, list, callers,
        │                                which, telookup, deps, init
        ▼
   Output (stdout)                    ← colored, tree, DOT, Mermaid
```

### Core data model

```python
class MacroDef:
    name: str           # "files_pid_filetrans"
    body: str           # M4 body with $1, $2, $3 args
    source_file: str    # "modules/kernel/files.if"
    line_number: int    # 9312
    category: str       # "kernel", "system", "contrib"
    is_define: bool     # True for permission-set defines
    is_template: bool   # True for templates
```

## 2. Components

### 2.1 Parser (`parse_file`)

Parses `.if` and `.spt` files using M4 block detection:
- `interface(` ... `)` → interface MacroDef
- `template(` ... `)` → template MacroDef
- `define(` ... `)` → define MacroDef
- Handles nested backtick-quote pairs `` `...' ``
- Extracts `gen_require` blocks separately

### 2.2 Index builder (`build_index`, `load_or_build_index`)

- Walks the policy include path recursively
- Parses all `.if` and `.spt` files
- Builds `dict[str, MacroDef]` keyed by macro name
- Caches to `~/.cache/semacro/` with fingerprint-based invalidation
- ~45x faster on cached repeat access

### 2.3 Expansion engine (`expand_macro`)

Recursive M4 expansion:
1. Start with a macro body
2. `substitute_args()` replaces `$1`, `$2`, `$3` with provided args
3. `find_calls_in_body()` finds nested macro calls
4. Recursively expand each nested call
5. Build `ExpansionNode` tree
6. `collect_leaf_rules()` extracts final allow/type_transition rules

### 2.4 Subcommands

| Command | Function | Purpose |
|---------|----------|---------|
| `lookup` | `cmd_lookup` | Show definition, expand, flatten to rules |
| `find` | `cmd_find` | Search by regex or permission content |
| `list` | `cmd_list` | List all macros by category |
| `callers` | `cmd_callers` | Reverse lookup — who calls this macro |
| `which` | `cmd_which` | Find macro granting specific access |
| `telookup` | `cmd_telookup` | Expand all macros in a .te file |
| `deps` | `cmd_deps` | Dependency graph (DOT or Mermaid) |
| `init` | `cmd_init` | Generate .te/.if/.fc policy skeleton |

## 3. Implementation phases

| Phase | Status | Deliverables |
|-------|--------|-------------|
| Phase 1: Core | Complete | lookup, find, list subcommands |
| Phase 2: Expansion | Complete | --expand, --rules, argument substitution |
| Phase 3: Polish | Complete | Bash/Zsh completion, man page, RPM spec |
| Phase 4: Analysis | Complete | callers, which, telookup |
| Phase 5: Visualization | Complete | deps (DOT/Mermaid), init (skeleton) |
| Phase 6: UX | Complete | Index caching, find --perms, error messages |
| **Testing** | **Planned** | 13 test files, 143+ tests (next session) |

## 4. Integration with sepgen

semacro is used by sepgen's refine command to suggest macros for AVC
denials:

```python
# sepgen calls semacro via subprocess
subprocess.run(['semacro', 'which', source_type, target_type, perms,
                '--class', tclass], capture_output=True)
```

semacro is also used manually during policy development:
```bash
semacro which myapp_t httpd_log_t read --class file
semacro lookup "files_pid_filetrans(myapp_t, myapp_var_run_t, file)" --rules
```

## 5. Distribution

| Channel | Command |
|---------|---------|
| COPR | `dnf copr enable pranlawate/selinux-tools && dnf install semacro` |
| GitHub | `dnf install https://github.com/pranlawate/semacro/releases/...` |
| Source | `git clone && make install` |

## 6. Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| python3 >= 3.9 | Yes | Runtime |
| selinux-policy-devel | Yes | Policy .if/.spt source files |

## 7. Future enhancements

- Recursive callers (`semacro callers --recursive`)
- `semacro diff` — compare macro definitions across policy versions
- Graphviz rendering (`--render` for PNG/SVG output)
- PyPI packaging (`pip install semacro`)
- Test suite (planned: 143+ tests)
