# semacro

A command-line tool for exploring and expanding SELinux policy macros, interfaces, and templates.

SELinux policies use M4 macros extensively. Understanding what a macro actually does requires manually chaining `seshowif` and `seshowdef` calls, tracking `$1/$2/$3` substitutions by hand, and recursing through nested macros. `semacro` automates this entire process.

## Usage

```
semacro lookup <name>                          # Show definition (searches interfaces + defines)
semacro find <regex>                           # Search for interfaces/defines matching a pattern
semacro list [--category kernel|system|all]    # List all available interfaces/templates
```

## Examples

### Unified lookup (no need to know if it's an interface or define)

```
$ semacro lookup files_pid_filetrans
interface files_pid_filetrans  # modules/kernel/files.if:9312
interface(`files_pid_filetrans',`
	gen_require(`
		type var_t, var_run_t;
	')

	allow $1 var_t:dir search_dir_perms;
	filetrans_pattern($1, var_run_t, $2, $3, $4)
')
```

```
$ semacro lookup search_dir_perms
define search_dir_perms  # support/obj_perm_sets.spt:137
define(`search_dir_perms',`
{ getattr search open }
')
```

### Find macros by pattern

```
$ semacro find pid_filetrans
  [i] modules/kernel/files.if: files_pid_filetrans
  [i] modules/kernel/files.if: files_pid_filetrans_lock_dir
  [i] modules/system/init.if: init_named_pid_filetrans
  [i] modules/system/init.if: init_pid_filetrans
  ...

15 result(s)
```

```
$ semacro find "rw_.*_perms"
  [d] support/obj_perm_sets.spt: rw_dir_perms
  [d] support/obj_perm_sets.spt: rw_file_perms
  [d] support/obj_perm_sets.spt: rw_sock_file_perms
  ...

24 result(s)
```

### List available interfaces

```
$ semacro list --category kernel | head -5
     1  [i] corecmd_bin_alias  modules/kernel/corecommands.if
     2  [i] corecmd_bin_domtrans  modules/kernel/corecommands.if
     3  [i] corecmd_bin_entry_type  modules/kernel/corecommands.if
     4  [i] corecmd_bin_filetrans  modules/kernel/corecommands.if
     5  [i] corecmd_bin_filetrans_to  modules/kernel/corecommands.if
```

Kind tags: `[i]` interface, `[t]` template, `[d]` define.

## Installation

Requires Python 3.9+ and access to SELinux policy source files.

### Quick start

```bash
git clone https://github.com/pranlawate/semacro.git
cd semacro

# Install wrapper to ~/bin (non-interactive)
make install-wrapper-user

# Or choose between ~/bin and /usr/local/bin (interactive)
make install
```

### Configuring the policy path

semacro needs access to the SELinux policy `.if` and `.spt` files. It checks these sources in order:

1. `--include-path` flag (highest priority)
2. `SEMACRO_INCLUDE_PATH` environment variable
3. `/usr/share/selinux/devel/include` (default, requires `selinux-policy-devel`)

**Option A:** Install the policy development headers (provides the default path):

```bash
sudo dnf install selinux-policy-devel
```

**Option B:** Point to a policy source tree (add to `~/.bashrc` for persistence):

```bash
export SEMACRO_INCLUDE_PATH="/path/to/selinux-policy/policy"
```

**Option C:** Pass explicitly per command:

```bash
semacro --include-path /path/to/policy lookup files_pid_filetrans
```

## How it works

SELinux policy macros come in two forms:

| Type | Defined with | Found in | Example |
|------|-------------|----------|---------|
| Interface/Template | `interface()` / `template()` | `.if` files under the include path | `files_pid_filetrans()`, `logging_send_syslog_msg()` |
| M4 Define | `define()` | `.spt` files under `support/` | `rw_dir_perms`, `filetrans_pattern` |

`semacro` parses these files directly (no build toolchain required) and searches both locations automatically.

## Motivation

The existing tools in the SELinux ecosystem have gaps for interactive macro exploration:

| Tool | What it does | What it doesn't do |
|------|---|---|
| `seshowif`/`seshowdef` | Show raw definition | No arg substitution, no recursion, no unified search |
| [`macro-expander`](https://github.com/fedora-selinux/macro-expander) | Expand to final allow rules via M4 | No tree output, no lookup/search, needs build toolchain |
| `sepolicy interface` | List interfaces, show descriptions | No macro body, no defines, no expansion |

`semacro` fills the gap: **show the definition, search the catalog, and (planned) expand step-by-step with a tree view** — all without requiring the policy build toolchain.

## Project structure

```
semacro/
├── README.md
├── semacro.py          # Main CLI (parser, index, commands)
├── Makefile            # Install/uninstall wrapper
└── CONTRIBUTING.md     # Contributor guidelines
```

## Development roadmap

### Phase 1 — Core commands ✅
- [x] Project setup
- [x] `semacro lookup` — unified search across interfaces + defines
- [x] `semacro find` — unified regex search across both
- [x] `semacro list` — list all interfaces/templates with category filter
- [x] Auto-detect policy include path + `SEMACRO_INCLUDE_PATH` env var
- [x] Color output (auto-disabled when piped)
- [x] Error handling, input validation, incomplete install warnings

### Phase 2 — Recursive expansion
- [ ] Parse macro call syntax into name + arguments
- [ ] `$1`, `$2`, `$3` argument substitution
- [ ] Recursive expansion of nested macros
- [ ] Tree-formatted output
- [ ] `--expand` flag
- [ ] Depth limit to prevent infinite recursion

### Phase 3 — Polish
- [ ] `--raw` flag (show unexpanded alongside expanded)
- [ ] `--flat` flag (plain allow rules, no tree, copy-paste ready)
- [ ] Bash/Zsh tab completion
- [ ] Man page

## License

MIT — see [LICENSE](LICENSE) for details.

## References

- [fedora-selinux/macro-expander](https://github.com/fedora-selinux/macro-expander) — M4-based macro expansion tool
- [selinux-funcs-el9.txt](https://gist.githubusercontent.com/jamesfreeman959/40d41810beccc4ded23dc049d6ed570d/raw/5da8c9b2aae21e38777d0d2c0e4ac615cc2a2455/selinux-funcs-el9.txt) — the bash helper functions that inspired this tool
- [SELinux reference policy](https://github.com/SELinuxProject/refpolicy) — upstream policy source

## Acknowledgments

- Sven Vermeulen — original SELinux shell functions
- James Freeman — `selinux-funcs-el9.txt` adaptation for EL9/Fedora
- SELinux reference policy developers
