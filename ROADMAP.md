# semacro roadmap

Planned features and future directions. Phases 1-3 are tracked in the [README](README.md).

## Phase 3 — Polish ✅

- [x] Bash/Zsh tab completion for subcommands, flags, and categories
- [x] Man page (`man semacro`)
- [x] RPM spec and packaging (`semacro.spec`)

## Phase 4 — Analysis commands

### `semacro callers <macro>` — reverse lookup

Find which macros and `.te` files reference a given macro. Essential for understanding the impact of changing a macro definition.

```
$ semacro callers filetrans_pattern
  files_pid_filetrans          modules/kernel/files.if:9312
  files_tmp_filetrans          modules/kernel/files.if:9445
  logging_log_filetrans        modules/system/logging.if:812
  ...
```

### `semacro which "<domain> <type> <perm>"` — rule-to-macro search

Given a domain, target type, and permission, find which macros would grant that access. Currently, policy authors grep through hundreds of `.if` files by hand.

```
$ semacro which "ntpd_t httpd_log_t read"
  apache_read_log(ntpd_t)
  apache_manage_log(ntpd_t)
```

### `semacro expand <file.te>` — expand a policy module

Parse a `.te` file and expand every macro call, producing the full set of final policy rules for the module.

```
$ semacro expand myapp.te
allow myapp_t var_t:dir { getattr search open };
allow myapp_t myapp_log_t:file { open read write append getattr };
...
```

## Phase 5 — Visualization and extras

- **Dependency graph** — show which macros call which, output in DOT or Mermaid format for visualization
- **Stdin pipe support** — `echo "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)" | semacro lookup -r`
- **Policy skeleton generator** — `semacro init myapp` generates starter `.te` / `.if` / `.fc` files for a new confined daemon
