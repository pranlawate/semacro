#compdef semacro
# Zsh completion for semacro
# Install to a directory in $fpath, e.g.:
#   cp completions/semacro.zsh ~/.zsh/completions/_semacro

local -a subcommands
subcommands=(
    'lookup:Show or expand a macro definition'
    'find:Search for macros matching a regex pattern'
    'list:List available macros'
)

local -a categories
categories=(kernel system admin apps roles services contrib distributed support all)

_semacro_lookup() {
    _arguments \
        '(-e --expand -r --rules)'{-e,--expand}'[Recursively expand nested macros into a tree]' \
        '(-r --rules -e --expand)'{-r,--rules}'[Output flat deduplicated policy rules]' \
        {-d,--depth}'[Max expansion depth]:depth' \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':macro name or call'
}

_semacro_find() {
    _arguments \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':regex pattern'
}

_semacro_list() {
    _arguments \
        '(-c --category)'{-c,--category}'[Filter by category]:category:('"${categories[*]}"')' \
        '(-h --help)'{-h,--help}'[Show help]'
}

_arguments -C \
    '--no-color[Disable colored output]' \
    '--include-path[Path to SELinux policy include directory]:directory:_directories' \
    '(-V --version)'{-V,--version}'[Show version]' \
    '(-h --help)'{-h,--help}'[Show help]' \
    ':command:->command' \
    '*::arg:->args'

case "$state" in
    command)
        _describe -t commands 'semacro command' subcommands
        ;;
    args)
        case "$words[1]" in
            lookup) _semacro_lookup ;;
            find)   _semacro_find ;;
            list)   _semacro_list ;;
        esac
        ;;
esac
