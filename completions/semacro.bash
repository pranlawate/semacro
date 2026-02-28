# Bash completion for semacro
# Source this file or install to /etc/bash_completion.d/semacro
#   source completions/semacro.bash

_semacro() {
    local cur prev words cword
    _init_completion || return

    local subcommands="lookup find list callers which telookup deps init"
    local global_opts="--no-color --include-path --version --help"
    local lookup_opts="-e --expand -r --rules -d --depth --help"
    local find_opts="--help"
    local list_opts="-c --category --help"
    local callers_opts="--help"
    local which_opts="-T --transition -C --class -N --name --help"
    local telookup_opts="-d --depth -t --tree --help"
    local deps_opts="-m --mermaid -d --depth --help"
    local init_opts="-o --output-dir --help"
    local categories="kernel system admin apps roles services contrib distributed support all"

    # Find which subcommand is active
    local subcmd=""
    local i
    for ((i=1; i < cword; i++)); do
        case "${words[i]}" in
            lookup|find|list|callers|which|telookup|deps|init)
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

    # Complete path after --include-path or --output-dir / -o
    if [[ "$prev" == "--include-path" || "$prev" == "--output-dir" || "$prev" == "-o" ]]; then
        _filedir -d
        return
    fi

    # Complete depth value after --depth or -d
    if [[ "$prev" == "--depth" || "$prev" == "-d" ]]; then
        return
    fi

    # Complete object class after --class / -C
    if [[ "$prev" == "--class" || "$prev" == "-C" ]]; then
        local classes="file dir lnk_file sock_file fifo_file chr_file blk_file process"
        COMPREPLY=($(compgen -W "$classes" -- "$cur"))
        return
    fi

    # Free-form filename after --name / -N
    if [[ "$prev" == "--name" || "$prev" == "-N" ]]; then
        return
    fi

    # Complete .te files for telookup command
    if [[ "$subcmd" == "telookup" && "$cur" != -* ]]; then
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
        telookup)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "$telookup_opts" -- "$cur"))
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
