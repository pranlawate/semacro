Name:           semacro
Version:        0.2.0
Release:        1%{?dist}
Summary:        Explore and expand SELinux policy macros, interfaces, and templates

License:        MIT
URL:            https://github.com/pranavlawate/semacro
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.9
Requires:       selinux-policy-devel

%description
semacro parses the SELinux reference-policy macro library and provides
quick lookup, search, and recursive expansion of interfaces, templates,
and defines.  It can substitute arguments, recursively expand nested
calls into a tree of final policy rules, and output flat copy-paste-ready
rules for use in .te policy files.

%prep
%autosetup

%install
install -Dm755 semacro.py       %{buildroot}%{_libexecdir}/semacro/semacro.py
install -Dm644 semacro.1        %{buildroot}%{_mandir}/man1/semacro.1

install -Dm644 completions/semacro.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/semacro
install -Dm644 completions/semacro.zsh \
    %{buildroot}%{_datadir}/zsh/site-functions/_semacro

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
* Thu Feb 27 2026 Pranav Lawate <pran.lawate@gmail.com> - 0.2.0-1
- Add --expand and --rules flags for recursive expansion and flat rule output
- Add bash/zsh tab completion
- Add man page
- Add --version flag
- Permission-set defines resolved inline during expansion
- AV rule merging for --rules output

* Mon Feb 24 2026 Pranav Lawate <pran.lawate@gmail.com> - 0.1.0-1
- Initial package: lookup, find, list subcommands
