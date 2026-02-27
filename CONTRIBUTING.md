# Contributing to semacro

Thanks for your interest in contributing to semacro.

## Getting started

1. Clone the repo and set up the include path:

```bash
git clone https://github.com/pranlawate/semacro.git
cd semacro
export SEMACRO_INCLUDE_PATH="/path/to/selinux-policy/policy"
```

2. Run it directly during development:

```bash
python3 semacro.py lookup files_pid_filetrans
python3 semacro.py find "rw_.*_perms"
```

## Project layout

```
semacro.py       # Everything lives here — parser, index, commands, CLI
Makefile         # Install/uninstall wrapper to ~/bin
README.md        # User-facing documentation
CONTRIBUTING.md  # This file
```

semacro is intentionally a single-file tool with no dependencies beyond the Python 3.9+ standard library. Keep it that way unless there's a strong reason not to.

## Code style

- Follow PEP 8.
- No dependencies outside the standard library.
- Keep functions focused — one function, one job.
- Error messages go to stderr, normal output to stdout.
- Color output must degrade gracefully (respect `--no-color` and pipe detection).

## Making changes

1. Create a branch for your work:

```bash
git checkout -b your-feature
```

2. Test your changes against real policy files:

```bash
# Basic commands
python3 semacro.py lookup files_pid_filetrans
python3 semacro.py find "rw_.*_perms"
python3 semacro.py list --category kernel | head -10
python3 semacro.py list --category support | head -10

# Argument substitution
python3 semacro.py lookup "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"

# Recursive expansion with define resolution
python3 semacro.py lookup --expand "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"
python3 semacro.py lookup --expand "manage_files_pattern(ntpd_t, ntpd_var_run_t, ntpd_var_run_t)"
python3 semacro.py lookup --expand "read_files_pattern(ntpd_t, ntpd_conf_t, ntpd_conf_t)"

# Named file transition (4th arg)
python3 semacro.py lookup --expand 'files_pid_filetrans(ntpd_t, ntpd_var_run_t, file, "ntpd.pid")'

# Depth-limited expansion
python3 semacro.py lookup --expand --depth 1 "files_pid_filetrans(ntpd_t, ntpd_var_run_t, file)"
```

3. Verify edge cases:

```bash
# Nonexistent macro
python3 semacro.py lookup nonexistent_macro

# Bad regex
python3 semacro.py find "[invalid"

# Pipe (no broken pipe errors)
python3 semacro.py list | head -5

# No color when piped
python3 semacro.py find domtrans | cat

# Expansion without args (shows raw $N references)
python3 semacro.py lookup --expand files_pid_filetrans
```

4. Commit with a clear message:

```bash
git commit -m "feat: add argument substitution for lookup"
```

Follow conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`.

## What to work on

Check the **Development roadmap** in the README. Phases 1 and 2 are complete. Phase 3 (polish) is next.

If you're looking for smaller tasks:

- Improve error messages
- Add tests
- Improve `--help` text for subcommands
- Handle edge cases in the M4 parser
- `--raw` flag (show unexpanded alongside expanded)
- `--flat` flag (plain allow rules, no tree, copy-paste ready)

## Reporting bugs

Open an issue with:
- The command you ran
- What you expected
- What happened instead
- Your Python version (`python3 --version`)
- Your OS and SELinux policy version (`rpm -q selinux-policy`)

## Policy file formats

If you're contributing to the parser, here's a quick reference:

**`.if` files** (interfaces and templates):
```m4
interface(`name',`
    body with $1 $2 $3 parameters
')

template(`name',`
    body with $1 $2 $3 parameters
')
```

**`.spt` files** (M4 defines):
```m4
define(`name',`value or body')

define(`name',`
    multiline body
')
```

The backtick (`` ` ``) opens a quote, the single quote (`'`) closes it. They nest: inner `` `...' `` pairs must balance.
