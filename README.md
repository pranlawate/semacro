# semacro

A command-line tool for exploring and expanding SELinux policy macros, interfaces, and templates.

SELinux policies use M4 macros extensively. Understanding what a macro actually does means digging through `.if` and `.spt` files, tracking `$1/$2/$3` substitutions by hand, and recursing through nested macro calls to reach the final allow/type_transition rules. `semacro` automates this entire process.

## Usage

```
semacro lookup <name>                          # Show definition (searches interfaces + defines)
semacro lookup <name> --expand                 # Recursively expand to final policy rules
semacro lookup "name(arg1, arg2)" --expand     # Expand with argument substitution
semacro lookup "name(arg1, arg2)" --rules      # Flat policy rules, copy-paste ready for .te files
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

### Argument substitution

Pass arguments inline to see the macro body with `$1`, `$2`, etc. filled in:

```
$ semacro lookup "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"
interface files_pid_filetrans  # modules/kernel/files.if:9312
interface(`files_pid_filetrans',`
	gen_require(`
		type var_t, var_run_t;
	')

	allow ntpd_t var_t:dir search_dir_perms;
	filetrans_pattern(ntpd_t, var_run_t, ntpd_var_run_t, file, )
')
```

### Recursive expansion

Use `--expand` to recursively expand nested macros into a tree of final policy rules. Define macros (permission sets like `search_dir_perms`) are automatically resolved to their actual values:

```
$ semacro lookup --expand "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"
files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)
├── allow ntpd_t var_t:dir { getattr search open };
└── filetrans_pattern(ntpd_t, var_run_t, ntpd_var_run_t, file, )
    ├── allow ntpd_t var_run_t:dir { open read getattr lock search ioctl add_name remove_name write };
    └── type_transition ntpd_t var_run_t:file ntpd_var_run_t ;
```

Named file transitions (4th argument constrains the filename):

```
$ semacro lookup --expand 'files_pid_filetrans(ntpd_t, ntpd_var_run_t, file, "ntpd.pid")'
files_pid_filetrans(ntpd_t, ntpd_var_run_t, file, "ntpd.pid")
├── allow ntpd_t var_t:dir { getattr search open };
└── filetrans_pattern(ntpd_t, var_run_t, ntpd_var_run_t, file, "ntpd.pid")
    ├── allow ntpd_t var_run_t:dir { open read getattr lock search ioctl add_name remove_name write };
    └── type_transition ntpd_t var_run_t:file ntpd_var_run_t "ntpd.pid";
```

Control expansion depth with `--depth` (default: 10). Macros beyond the limit show `... (max depth reached)`:

```
$ semacro lookup --expand --depth 1 "apache_read_log(mysqld_t)"
apache_read_log(mysqld_t)
├── logging_search_logs(mysqld_t)
│   ├── files_search_var(mysqld_t)
│   │   └── ... (max depth reached)
│   └── allow mysqld_t var_log_t:dir { getattr search open };
├── allow mysqld_t httpd_log_t:dir { getattr search open read lock ioctl };
├── read_files_pattern(mysqld_t, httpd_log_t, httpd_log_t)
│   ├── allow mysqld_t httpd_log_t:dir { getattr search open };
│   └── allow mysqld_t httpd_log_t:file { open getattr read ioctl lock };
└── read_lnk_files_pattern(mysqld_t, httpd_log_t, httpd_log_t)
    ├── allow mysqld_t httpd_log_t:dir { getattr search open };
    └── allow mysqld_t httpd_log_t:lnk_file { getattr read };
```

### Flat output (copy-paste ready)

Use `--rules` to get just the final policy rules — no tree, no color, deduplicated. Ready to paste into a `.te` file:

```
$ semacro lookup --rules "apache_read_log(mysqld_t)"
allow mysqld_t var_t:dir { getattr search open };
allow mysqld_t var_log_t:dir { getattr search open };
allow mysqld_t httpd_log_t:dir { getattr search open read lock ioctl };
allow mysqld_t httpd_log_t:file { open getattr read ioctl lock };
allow mysqld_t httpd_log_t:lnk_file { getattr read };
```

Rules with the same `(source, target:class)` have their permissions merged automatically, just like the policy compiler does. `--rules` and `--expand` are mutually exclusive — use `--expand` to understand the macro structure, `--rules` to get the final output.

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

### Tab completion and man page

```bash
# Install bash/zsh tab completion (requires sudo)
make install-completions

# Install the man page
make install-man
```

After installing completions, open a new shell or run `source /etc/bash_completion.d/semacro` for Bash. Zsh picks up completions from `$fpath` automatically.

### RPM package (Fedora/RHEL/CentOS)

Build and install as an RPM:

```bash
# Create a source tarball
tar czf ~/rpmbuild/SOURCES/semacro-0.2.0.tar.gz --transform='s,^,semacro-0.2.0/,' \
    semacro.py semacro.1 semacro.spec completions/ Makefile \
    README.md CONTRIBUTING.md ROADMAP.md LICENSE

# Build the RPM
rpmbuild -ba semacro.spec

# Install
sudo dnf install ~/rpmbuild/RPMS/noarch/semacro-0.2.0-1.*.noarch.rpm
```

The RPM installs the wrapper to `/usr/bin/semacro`, the man page, and bash/zsh completions.

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

`semacro` fills the gap: **show the definition, search the catalog, and expand step-by-step with a tree view** — all without requiring the policy build toolchain.

## Project structure

```
semacro/
├── semacro.py          # Main CLI (parser, index, commands)
├── semacro.1           # Man page (troff)
├── semacro.spec        # RPM spec file
├── completions/
│   ├── semacro.bash    # Bash tab completion
│   └── semacro.zsh     # Zsh tab completion
├── Makefile            # Install wrapper, completions, man page
├── README.md
├── ROADMAP.md          # Planned features (Phases 4+)
├── CONTRIBUTING.md     # Contributor guidelines
└── LICENSE             # MIT license
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

### Phase 2 — Recursive expansion ✅
- [x] Parse macro call syntax into name + arguments
- [x] `$1`, `$2`, `$3` argument substitution (unset args → empty string, matching M4)
- [x] Recursive expansion of nested macros
- [x] Tree-formatted output with box-drawing characters
- [x] `--expand` / `-e` flag
- [x] `--depth` / `-d` flag to limit recursion depth
- [x] Define resolution — permission sets (`search_dir_perms`, etc.) expanded inline
- [x] Chained define expansion with nested brace flattening

### Phase 3 — Polish ✅
- [x] `--rules` / `-r` flag (flat deduplicated policy rules, copy-paste ready)
- [x] Permission merging — rules with same `(source, target:class)` union their permissions
- [x] Bash/Zsh tab completion
- [x] Man page (`man semacro`)
- [x] RPM packaging (`semacro.spec`)

See [ROADMAP.md](ROADMAP.md) for planned features beyond Phase 3.

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
