# Implementation Plan: semacro Test Suite

**Date:** 2026-03-23
**Goal:** Create comprehensive pytest test suite for semacro (143+ tests),
add `%check` to spec, enable CI validation.

---

## Context

semacro has 8 subcommands, 15+ internal functions, and 1,418 lines of code
but zero tests. avc-parser has 174 tests, sepgen has 165. semacro needs
comparable coverage to complete the tool suite's testing story.

Key design decision: tests use **synthetic macro fixture files** so they
work without `selinux-policy-devel` installed. Only smoke tests need
the real policy path.

## Fixture Design

### Synthetic policy fixtures (`tests/fixtures/`)

Create minimal `.if` and `.spt` files that define enough macros to test
all subcommands without requiring the full SELinux policy tree.

```
tests/
├── conftest.py              # Shared fixtures, index builder, tmp dirs
├── fixtures/
│   ├── interfaces.if        # 5-10 sample interfaces with known structure
│   ├── templates.if         # 2-3 templates for template expansion
│   ├── defines.spt          # 5-10 permission set defines
│   ├── nested.if            # Interfaces that call other interfaces (for deps/expand)
│   └── myapp.te             # Sample .te file for telookup tests
├── test_parser.py
├── test_index.py
├── test_expansion.py
├── test_lookup.py
├── test_find.py
├── test_list.py
├── test_callers.py
├── test_which.py
├── test_telookup.py
├── test_deps.py
├── test_init.py
├── test_cli.py
└── test_utils.py
```

### Fixture content: `interfaces.if`

```m4
## <summary>Grant read access to myapp config files.</summary>
interface(`myapp_read_config',`
    gen_require(`
        type myapp_conf_t;
    ')
    allow $1 myapp_conf_t:file read_file_perms;
')

## <summary>Transition to myapp domain.</summary>
interface(`myapp_domtrans',`
    gen_require(`
        type myapp_t, myapp_exec_t;
    ')
    domtrans_pattern($1, myapp_exec_t, myapp_t)
')

## <summary>Manage myapp PID files.</summary>
interface(`myapp_manage_pid',`
    gen_require(`
        type myapp_var_run_t;
    ')
    manage_files_pattern($1, myapp_var_run_t, myapp_var_run_t)
    files_pid_filetrans($1, myapp_var_run_t, file)
')

interface(`myapp_admin',`
    gen_require(`
        type myapp_t, myapp_conf_t, myapp_var_run_t;
    ')
    myapp_read_config($1)
    myapp_manage_pid($1)
    admin_pattern($1, myapp_t)
')
```

### Fixture content: `defines.spt`

```m4
define(`read_file_perms',`{ getattr read open }')
define(`manage_files_pattern',`
    allow $1 $3:dir search_dir_perms;
    allow $1 $3:file { create read write unlink };
')
define(`search_dir_perms',`{ getattr search open }')
define(`domtrans_pattern',`
    allow $1 $2:file { read getattr open execute };
    allow $1 $3:process transition;
    type_transition $1 $2:process $3;
')
define(`admin_pattern',`
    allow $1 $2:process { signal_perms };
')
define(`files_pid_filetrans',`
    filetrans_pattern($1, var_run_t, $2, $3)
')
define(`filetrans_pattern',`
    type_transition $1 $2:$4 $3;
')
```

## Test Files

### Task 1: conftest.py — shared fixtures

```python
@pytest.fixture
def synthetic_index(tmp_path):
    """Build index from synthetic fixture files."""

@pytest.fixture
def real_index():
    """Build index from real policy (skip if not installed)."""
```

### Task 2: test_parser.py (~15 tests)
- Parse a valid `.if` file → correct number of MacroDef objects
- Parse interface with gen_require → body extracted correctly
- Parse define → `is_define=True`
- Parse template → correct handling
- Handle malformed M4 (unclosed backtick) → graceful error
- `_find_m4_block_end()` with nested backtick-quote pairs
- Parse file with comments → comments excluded from body
- Parse empty file → empty list
- Parse file with multiple interfaces → all found
- Verify `rel_path` stored correctly
- Verify line numbers stored correctly
- Parse interface with `$1`, `$2`, `$3` args → preserved in body
- Parse interface with no gen_require → still parses
- Handle unicode/special chars in comments
- Parse `.spt` file with defines

### Task 3: test_index.py (~10 tests)
- `build_index()` from fixture directory → all macros indexed
- `detect_include_path()` finds `/usr/share/selinux/devel/include`
- `detect_include_path()` with `SEMACRO_INCLUDE_PATH` env var
- `detect_include_path()` returns None when nothing found
- `load_or_build_index()` creates cache
- `load_or_build_index()` uses cache on second call (faster)
- `_source_fingerprint()` changes when file modified
- Index contains both interfaces and defines
- Index deduplicates same-name macros
- `_has_policy_files()` true/false detection

### Task 4: test_expansion.py (~25 tests)
- `parse_call("name(arg1, arg2)")` → correct name and args
- `parse_call("name")` → name only, empty args
- `parse_call` with nested parens → handles correctly
- `substitute_args()` replaces `$1`, `$2`, `$3`
- `substitute_args()` with unused args → no crash
- `find_calls_in_body()` finds all macro calls
- `find_calls_in_body()` ignores comments
- `expand_macro()` single level → correct output
- `expand_macro()` recursive → nested tree
- `expand_macro()` with define resolution
- `expand_macro()` with `--depth` limit
- `expand_macro()` circular reference → no infinite loop
- `ExpansionNode` tree structure → correct parent/children
- `format_tree()` produces readable output
- `collect_leaf_rules()` extracts allow/type_transition rules
- `_strip_gen_require()` removes gen_require blocks
- `_flatten_braces()` handles nested braces
- `_resolve_defines_in_text()` substitutes permission sets
- Expansion with argument substitution → `$1` replaced
- Expansion preserving indentation
- Empty body expansion → empty result
- Expansion of template (not interface) → works
- Rule merging in `--rules` output → duplicate rules collapsed
- Multiple expansions don't corrupt state
- Expansion of define that references other defines

### Task 5: test_lookup.py (~15 tests)
- `cmd_lookup()` existing interface → found, prints definition
- `cmd_lookup()` existing define → found, prints definition
- `cmd_lookup()` unknown name → error message, return 1
- `cmd_lookup()` with `--expand` → shows expansion tree
- `cmd_lookup()` with `--rules` → flat allow rules
- `cmd_lookup("name(arg1, arg2)")` → argument substitution
- `cmd_lookup("name(arg1)")` with `--expand` → expanded with args
- `cmd_lookup()` with `--depth 1` → limits expansion
- `cmd_lookup()` case sensitivity → exact match
- Lookup interface that calls defines → defines resolved
- Lookup template → works like interface
- Lookup with `--no-color` → no ANSI codes in output
- Lookup from pipe input (`echo name | semacro lookup`)
- Lookup with `--rules` deduplicates identical rules
- Lookup shows source file and line number

### Task 6: test_find.py (~10 tests)
- `cmd_find("myapp")` → matches myapp_* interfaces
- `cmd_find(".*pid.*")` → regex matching
- `cmd_find("nonexistent")` → no results, return 1
- `cmd_find()` with `--perms "read write"` → finds matching defines
- `cmd_find()` with `--perms` no match → empty result
- `cmd_find()` case insensitive regex
- `cmd_find("^files_")` → anchor works
- Find with pipe input
- Find shows category and source path
- Find with special regex chars → properly escaped

### Task 7: test_list.py (~8 tests)
- `cmd_list(None)` → lists all macros
- `cmd_list("kernel")` → only kernel category
- `cmd_list("system")` → only system category
- `cmd_list("contrib")` → only contrib category
- `cmd_list("all")` → same as None
- `cmd_list("invalid")` → error message
- List output format → name + source file
- List count matches index size for category

### Task 8: test_callers.py (~8 tests)
- `cmd_callers("myapp_read_config")` → finds myapp_admin
- `cmd_callers("nonexistent")` → not found error
- `cmd_callers()` for macro with no callers → "no callers found"
- `cmd_callers()` for macro with multiple callers → all listed
- Callers shows source file location
- Callers for a define → finds interfaces using it
- Callers distinguishes direct vs indirect
- `_macro_arity()` correctly counts `$N` args

### Task 9: test_which.py (~12 tests)
- `cmd_which(index, "httpd_t", "httpd_conf_t", "read")` → finds macro
- `cmd_which()` with unknown types → no match
- `cmd_which()` with `--class file` → filters by class
- `cmd_which()` transition mode `-T` → finds type_transition
- `cmd_which()` transition with `--name` → named transition
- `cmd_which()` multiple permissions `"read write"` → finds matching
- Which shows macro name and source file
- Which with exact match vs subset match
- Which for define → works
- `_build_transition_trials()` generates correct patterns
- Which returns 0 on match, 1 on no match
- Which with real index (skip if not installed)

### Task 10: test_telookup.py (~10 tests)
- `cmd_telookup()` with valid .te file → expands all macros
- `cmd_telookup()` with nonexistent file → error
- `cmd_telookup()` with empty .te → no output
- `cmd_telookup()` preserves non-macro lines
- `cmd_telookup()` with `--expand` → recursive expansion
- `cmd_telookup()` with `--depth` → limited expansion
- telookup handles `policy_module()` line → skips it
- telookup handles `gen_require()` blocks → skips them
- telookup with unknown macro → reports warning
- telookup fixture `myapp.te` → known-good output

### Task 11: test_deps.py (~10 tests)
- `cmd_deps("myapp_admin")` → DOT format output
- `cmd_deps()` with `--mermaid` → Mermaid format
- `cmd_deps()` with `--depth 1` → limited depth
- `cmd_deps()` for unknown macro → error
- `cmd_deps()` for leaf macro (no deps) → single node
- DOT output has correct `digraph` structure
- Mermaid output has correct `graph TD` structure
- Deps includes both direct and transitive dependencies
- Deps handles circular references
- Deps for define → shows usage chain

### Task 12: test_init.py (~8 tests)
- `cmd_init("myapp")` → creates myapp.te, myapp.if, myapp.fc
- `cmd_init()` with `--output-dir` → creates in specified dir
- Generated .te has correct `policy_module()` header
- Generated .te has standard daemon declarations
- Generated .if has template interface stubs
- Generated .fc has executable entry
- `cmd_init()` existing files → warns/skips
- `cmd_init()` with invalid name → error

### Task 13: test_cli.py (~12 tests)
- `--version` → prints version string
- `--help` → shows usage
- No arguments → shows help, return 1
- Unknown subcommand → error message
- `--include-path /path` → uses specified path
- `--no-color` → disables ANSI codes
- Each subcommand `--help` → shows subcommand help
- Invalid flag for subcommand → suggests `semacro <cmd> -h`
- `SEMACRO_INCLUDE_PATH` env var → respected
- Pipe input → works for lookup, find
- Exit codes → 0 success, 1 not found, 2 error
- Version matches spec file version

### Task 14: test_utils.py (~10 tests)
- `parse_call("name(a, b)")` → ("name", ["a", "b"])
- `parse_call("name")` → ("name", [])
- `parse_call("name(a, 'b c')")` → handles quoted args
- `parse_call(None)` → None
- `colored("text", Color.RED)` → ANSI wrapped
- `colored()` with `--no-color` → plain text
- `_strip_gen_require()` removes block
- `_strip_gen_require()` no block → unchanged
- `_flatten_braces()` nested → flattened
- `_flatten_braces()` empty → empty

## Execution Order

1. Create fixtures (interfaces.if, defines.spt, myapp.te)
2. conftest.py with synthetic index builder
3. test_parser.py + test_utils.py (core, no deps)
4. test_index.py (builds on parser)
5. test_expansion.py (builds on index + parser)
6. test_lookup.py + test_find.py + test_list.py (commands, build on index)
7. test_callers.py + test_which.py (analysis commands)
8. test_telookup.py + test_deps.py + test_init.py (advanced commands)
9. test_cli.py (integration)
10. Add `%check` to semacro.spec, rebuild RPM

## Validation

- All 143+ tests pass locally
- `rpmbuild -ba semacro.spec` succeeds with `%check`
- Tests work WITHOUT selinux-policy-devel (synthetic fixtures)
- Optional smoke tests work WITH selinux-policy-devel
