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

## Future

- **Recursive callers** — `semacro callers --recursive <macro>` to find indirect callers
- **`semacro diff`** — compare macro definitions across policy versions
- **Graphviz rendering** — optional `--render` flag to call `dot` directly and output PNG/SVG
- **Test suite** — pytest-based tests with synthetic macro definitions for CI validation
- **PyPI packaging** — `pip install semacro` for non-RPM users
