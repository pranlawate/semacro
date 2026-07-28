# semacro roadmap

Planned features and future directions. Phases 1-5 are tracked in the [README](README.md).

## Phase 3 — Polish ✅

- [x] Bash/Zsh tab completion for subcommands, flags, and categories
- [x] Man page (`man semacro`)
- [x] RPM spec and packaging (`semacro.spec`)

## Phase 4 — Analysis commands ✅

- [x] `semacro callers <macro>` — reverse lookup (find direct callers)
- [x] `semacro which <source> <target> <perm>` — rule-to-macro search (AV rules and type_transitions)
- [x] `semacro telookup <file.te>` — expand all macros in a policy module

## Phase 5 — Visualization and extras ✅

- [x] `semacro deps <macro>` — dependency graph in DOT (Graphviz) and Mermaid format
- [x] `semacro init <name>` — policy skeleton generator (`.te`, `.if`, `.fc`)

## Phase 6 — UX and performance ✅

- [x] `telookup -e/--expand` — expansion trees for `.te` file macros (renamed from `-t/--tree`)
- [x] Improved error messages — unrecognized subcommand flags now suggest `semacro <cmd> -h`
- [x] `find --perms` — reverse permission-set search (find defines by permission content)
- [x] Index caching — parsed index cached to `~/.cache/semacro/`, ~45x faster repeat runs

## Known Issues

Found Jul 28, 2026 while using `lookup -r`/`-e` to combine two macros for a real SELinux policy fix candidate (RHINENG-28982):

- **`_read_arg()` truncates piped multi-line input to one line.** It calls `sys.stdin.readline()` instead of `sys.stdin.read()`, so anything after the first `\n` in piped stdin is silently dropped. Affects `lookup`, `find`, `callers`, and `deps` alike, since all four share this helper.
- **No support for merging multiple macro calls in one invocation.** Even with the read fix above, `cmd_lookup` only ever processes a single macro name/call per run. There's no way to pass a list of macros and get one merged, deduplicated rule set back, you have to invoke `lookup -r` once per macro and merge the output by hand. This is the real feature gap behind the stdin bug: the natural use case (a fix needs two or more interfaces called together) has no first-class support.
- **Nested-paren macro calls aren't parsed correctly.** Both `_BODY_CALL` (`r"\b(\w+)\(([^)]*)\)"`) and `_CALL_PATTERN` (`r"^(\w+)\((.+)\)$"`) assume single-level parens. A body containing `some_interface(other_call(a, b), c)` would parse wrong, since `[^)]*` stops at the first `)`. Not yet hit in practice (the `rhsmcertd.if` interfaces used so far don't nest calls), but latent.
- **`optional_policy`/`tunable_policy` block contents leak into output unconditionally.** These are in `skip_names` so their call span isn't expanded, but their bracketed body text also isn't stripped, it falls through to `_add_leaf_lines` as ordinary surrounding text, which will pick up any `allow ...;` lines inside and print them as if always active. Could misrepresent conditionally-gated rules as unconditional for interfaces that use these constructs.
- **`load_or_build_index()` doesn't recover from a cross-context cache.** Found Jul 28 while validating PR #2 (test-quality PR, unrelated to this bug). Its cache-load `except` only catches `(pickle.UnpicklingError, ValueError, EOFError, OSError)`, not `AttributeError`/`ModuleNotFoundError`. If a cache file was pickled while `semacro.py` ran as `__main__` (direct script invocation) and is then loaded via `import semacro` (e.g. under pytest), unpickling can't resolve the class (`module '__main__' has no attribute 'MacroDef'`) and raises instead of falling back to a rebuild. Low real-world impact since the packaged `semacro` entry point always imports consistently, but worth widening the except clause for robustness.

## Future

- **Recursive callers** — `semacro callers --recursive <macro>` to find indirect callers
- **`semacro diff`** — compare macro definitions across policy versions
- **Graphviz rendering** — optional `--render` flag to call `dot` directly and output PNG/SVG
- **CI test workflow** — test suite itself already exists (128 tests across 11 files, `tests/`), but nothing runs it automatically. Only `.github/workflows/build-rpm.yml` exists; add a pytest workflow that runs on PRs/pushes
- **PyPI packaging** — `pip install semacro` for non-RPM users
- **Add `fedora-44-x86_64` chroot to Copr** — `pranlawate/selinux-tools` currently only targets `fedora-43-x86_64`; F44 has been the latest stable release since Apr 2026. No urgency, F43 users unaffected either way (noted Jul 28 after a Copr outdated-chroot cleanup notice for the now-EOL F42 chroot, unrelated to this)
