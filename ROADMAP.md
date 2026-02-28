# semacro roadmap

Planned features and future directions. Phases 1-5 are tracked in the [README](README.md).

## Phase 3 — Polish ✅

- [x] Bash/Zsh tab completion for subcommands, flags, and categories
- [x] Man page (`man semacro`)
- [x] RPM spec and packaging (`semacro.spec`)

## Phase 4 — Analysis commands ✅

- [x] `semacro callers <macro>` — reverse lookup (find direct callers)
- [x] `semacro which <source> <target> <perm>` — rule-to-macro search (AV rules and type_transitions)
- [x] `semacro expand <file.te>` — expand all macros in a policy module

## Phase 5 — Visualization and extras ✅

- [x] `semacro deps <macro>` — dependency graph in DOT (Graphviz) and Mermaid format
- [x] `semacro init <name>` — policy skeleton generator (`.te`, `.if`, `.fc`)

## Future

- **Recursive callers** — `semacro callers --recursive <macro>` to find indirect callers
- **Test suite** — pytest-based tests with synthetic macro definitions for CI validation
- **Graphviz rendering** — optional `--render` flag to call `dot` directly and output PNG/SVG
