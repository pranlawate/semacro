# semacro

A command-line tool for exploring and expanding SELinux policy macros, interfaces, and templates.

SELinux policies use M4 macros extensively. Understanding what a macro actually does requires manually chaining `seshowif` and `seshowdef` calls, tracking `$1/$2/$3` substitutions by hand, and recursing through nested macros. `semacro` automates this entire process.

## Usage

```
semacro lookup <name>                          # Show definition (searches interfaces + defines)
semacro lookup <name>(arg1, arg2, ...)         # Show definition with arguments substituted
semacro lookup <name>(arg1, arg2, ...) --expand # Recursively expand all nested macros
semacro find <regex>                           # Search for interfaces/defines matching a pattern
semacro list [--category kernel|system|all]    # List all available interfaces/templates
```

## Examples

### Unified lookup (no need to know if it's an interface or define)

```
$ semacro lookup files_pid_filetrans
interface(`files_pid_filetrans',`
        gen_require(`
                type var_t, var_run_t;
        ')

        allow $1 var_t:dir search_dir_perms;
        filetrans_pattern($1, var_run_t, $2, $3, $4)
')
```

### Lookup with argument substitution

```
$ semacro lookup "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"
interface(`files_pid_filetrans',`
        gen_require(`
                type var_t, var_run_t;
        ')

        allow ntpd_t var_t:dir search_dir_perms;
        filetrans_pattern(ntpd_t, var_run_t, ntpd_var_run_t, file)
')
```

### Recursive expansion

```
$ semacro lookup "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)" --expand
files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)
├── allow ntpd_t var_t:dir { getattr search open };
└── filetrans_pattern(ntpd_t, var_run_t, ntpd_var_run_t, file)
    ├── allow ntpd_t var_run_t:dir { open read getattr lock search ioctl add_name remove_name write };
    └── type_transition ntpd_t var_run_t:file ntpd_var_run_t;
```

### Find macros by pattern

```
$ semacro find pid_filetrans
kernel/files.if: files_pid_filetrans
support/misc_patterns.spt: filetrans_pattern

$ semacro find "rw_.*_perms"
support/obj_perm_sets.spt: rw_dir_perms
support/obj_perm_sets.spt: rw_file_perms
support/obj_perm_sets.spt: rw_sock_file_perms
```

### List available interfaces

```
$ semacro list --category kernel
   1  kernel_read_system_state (kernel, kernel)
   2  kernel_read_network_state (kernel, kernel)
   ...
```

## Installation

Requires Python 3.9+ and `selinux-policy-devel` installed on the system.

```
# Ensure policy development headers are available
sudo dnf install selinux-policy-devel

# Run directly
python3 semacro.py lookup files_pid_filetrans

# Or install as a command
pip install -e .
```

## How it works

SELinux policy macros come in two forms:

| Type | Defined with | Found in | Example |
|------|-------------|----------|---------|
| Interface/Template | `interface()` / `template()` | `.if` files under `/usr/share/selinux/devel/include/` | `files_pid_filetrans()`, `logging_send_syslog_msg()` |
| M4 Define | `define()` | `.spt` files under `.../include/support/` | `rw_dir_perms`, `filetrans_pattern` |

`semacro lookup` searches both locations automatically. `semacro lookup --expand` recursively resolves nested macros of either type until only raw `allow`/`type_transition` rules and literal permission sets remain.

## Motivation

The existing `selinux-funcs-el9.txt` bash helper (by Sven Vermeulen, modified by James Freeman) provides basic `seshowif`/`seshowdef` functions but requires the user to:

1. Know whether a macro is an interface or a define before looking it up
2. Manually substitute `$1`, `$2`, `$3` arguments by reading the definition
3. Manually chain lookups when macros call other macros (often 3-4 levels deep)
4. Mentally assemble the final expanded policy rules

`semacro` automates all four steps.

## Project structure

```
semacro/
├── README.md
├── semacro.py          # Main CLI entry point
├── requirements.txt    # Dependencies (if any beyond stdlib)
├── tests/              # Test suite
│   └── ...
└── Makefile            # Dev shortcuts (test, lint, install)
```

## Development roadmap

### Phase 1 — Feature parity with bash script
- [x] Project setup
- [ ] `semacro lookup` — unified search across interfaces + defines
- [ ] `semacro find` — unified regex search across both
- [ ] `semacro list` — list all interfaces/templates
- [ ] Auto-detect policy include path
- [ ] Color output
- [ ] Error handling and input validation

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
- [ ] Installable package

## License

TBD

## References

- [selinux-funcs-el9.txt](https://gist.githubusercontent.com/jamesfreeman959/40d41810beccc4ded23dc049d6ed570d/raw/5da8c9b2aae21e38777d0d2c0e4ac615cc2a2455/selinux-funcs-el9.txt) — the bash helper functions that inspired this tool

## Acknowledgments

- Sven Vermeulen — original SELinux shell functions
- James Freeman — `selinux-funcs-el9.txt` adaptation for EL9/Fedora
- SELinux reference policy developers
