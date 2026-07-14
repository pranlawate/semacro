Name:           semacro
Version:        0.2.0
Release:        2%{?dist}
Summary:        Explore and expand SELinux policy macros, interfaces, and templates

License:        MIT
URL:            https://github.com/pranlawate/semacro
Source0:        https://github.com/pranlawate/semacro/archive/refs/tags/v%{version}-2.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.9
Requires:       selinux-policy-devel
BuildRequires:  python3-pytest
BuildRequires:  selinux-policy-devel

%description
semacro parses the SELinux reference-policy macro library and provides
quick lookup, search, and recursive expansion of interfaces, templates,
and defines.  It can substitute arguments, recursively expand nested
calls into a tree of final policy rules, and output flat copy-paste-ready
rules for use in .te policy files.

%prep
%autosetup -n %{name}-%{version}-2

%build
# Nothing to build (pure Python script) 


%install
install -Dm755 semacro.py       %{buildroot}%{_libexecdir}/semacro/semacro.py
install -Dm644 semacro.1        %{buildroot}%{_mandir}/man1/semacro.1

install -Dm644 completions/semacro.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/semacro
install -Dm644 completions/semacro.zsh \
    %{buildroot}%{_datadir}/zsh/site-functions/_semacro

%check
python3 -m pytest tests/ 


mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/semacro << 'WRAPPER'
#!/bin/bash
exec python3 %{_libexecdir}/semacro/semacro.py "$@"
WRAPPER
chmod 755 %{buildroot}%{_bindir}/semacro

%files
%license LICENSE
%doc README.md CONTRIBUTING.md ROADMAP.md
%{_bindir}/semacro
%{_libexecdir}/semacro/semacro.py
%{_mandir}/man1/semacro.1*
%{_datadir}/bash-completion/completions/semacro
%{_datadir}/zsh/site-functions/_semacro

%changelog
* Mon Mar 23 2026 Pranav Lawate <pran.lawate@gmail.com> - 0.2.0-2
- Add pytest test suite (85 tests) and %%check
- Add semacro deps for dependency graphs in DOT and Mermaid format
- Add semacro init for policy skeleton generation (.te/.if/.fc)
- Add man page, bash/zsh completion scripts
- Add semacro callers for reverse macro lookup
- Add semacro which for rule-to-macro search (AV rules and type_transitions)
- Add semacro telookup for expanding all macros in a .te file
- Add stdin pipe support for lookup, find, deps

* Fri Feb 27 2026 Pranav Lawate <pran.lawate@gmail.com> - 0.2.0-1
- Add --expand and --rules flags for recursive expansion and flat rule output
- Add bash/zsh tab completion
- Add man page
- Add --version flag
- Permission-set defines resolved inline during expansion
- AV rule merging for --rules output

* Tue Feb 24 2026 Pranav Lawate <pran.lawate@gmail.com> - 0.1.0-1
- Initial package: lookup, find, list subcommands
