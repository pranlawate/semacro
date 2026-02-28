# Bash completion for semacro
# Source this file or install to /etc/bash_completion.d/semacro
#   source completions/semacro.bash

_semacro() {
    local cur prev words cword
    _init_completion || return

    local subcommands="lookup find list callers which expand deps init"
    local global_opts="--no-color --include-path --version --help"
    local lookup_opts="-e --expand -r --rules -d --depth --help"
    local find_opts="--help"
    local list_opts="-c --category --help"
    local callers_opts="--help"
    local which_opts="-T --transition -C --class -N --name --help"
    local expand_opts="-d --depth -t --tree --help"
    local deps_opts="-m --mermaid -d --depth --help"
    local init_opts="-o --output-dir --help"
    local categories="kernel system admin apps roles services contrib distributed support all"

    # Find which subcommand is active
    local subcmd=""
    local i
    for ((i=1; i < cword; i++)); do
        case "${words[i]}" in
            lookup|find|list|callers|which|expand|deps|init)
                subcmd="${words[i]}"
                break
                ;;
        esac
    done

    # Complete category values after --category or -c
    if [[ "$prev" == "--category" || "$prev" == "-c" ]]; then
        COMPREPLY=($(compgen -W "$categories" -- "$cur"))
        return
    fi

    # Complete path after --include-path
    if [[ "$prev" == "--include-path" ]]; then
        _filedir -d
        return
    fi

    # Complete depth value after --depth or -d
    if [[ "$prev" == "--depth" || "$prev" == "-d" ]]; then
        return
    fi

    # Complete .te files for expand command
    if [[ "$subcmd" == "expand" && "$cur" != -* ]]; then
        _filedir te
        return
    fi

    case "$subcmd" in
        lookup)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$lookup_opts" -- "$cur"))
            fi
            ;;
        find)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$find_opts" -- "$cur"))
            fi
            ;;
        list)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$list_opts" -- "$cur"))
            fi
            ;;
        callers)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$callers_opts" -- "$cur"))
            fi
            ;;
        which)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$which_opts" -- "$cur"))
            fi
            ;;
        expand)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$expand_opts" -- "$cur"))
            fi
            ;;
        deps)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$deps_opts" -- "$cur"))
            fi
            ;;
        init)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$init_opts" -- "$cur"))
            fi
            ;;
        "")
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$global_opts" -- "$cur"))
            else
                COMPREPLY=($(compgen -W "$subcommands" -- "$cur"))
            fi
            ;;
    esac
}

complete -F _semacro semacro
