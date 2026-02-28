#compdef semacro
# Zsh completion for semacro
# Install to a directory in $fpath, e.g.:
#   cp completions/semacro.zsh ~/.zsh/completions/_semacro

local -a subcommands
subcommands=(
    'lookup:Show or expand a macro definition'
    'find:Search for macros matching a regex pattern'
    'list:List available macros'
    'callers:Find which macros call a given macro'
    'which:Find macros that grant a specific access'
    'telookup:Expand all macros in a .te policy file'
    'deps:Show macro dependency graph in DOT or Mermaid format'
    'init:Generate starter .te/.if/.fc files for a new policy module'
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

_semacro_callers() {
    _arguments \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':macro name'
}

_semacro_which() {
    _arguments \
        '(-T --transition)'{-T,--transition}'[Search for type_transition rules]' \
        '(-C --class)'{-C,--class}'[Filter by object class]:class' \
        '(-N --name)'{-N,--name}'[Filter by named transition filename]:filename' \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':source type' \
        ':target type' \
        ':permission or new type'
}

_semacro_telookup() {
    _arguments \
        {-d,--depth}'[Max expansion depth]:depth' \
        '(-t --tree)'{-t,--tree}'[Output expansion trees instead of flat rules]' \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':te file:_files -g "*.te"'
}

_semacro_deps() {
    _arguments \
        '(-m --mermaid)'{-m,--mermaid}'[Output Mermaid format instead of DOT]' \
        {-d,--depth}'[Max depth to follow calls]:depth' \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':macro name'
}

_semacro_init() {
    _arguments \
        '(-o --output-dir)'{-o,--output-dir}'[Directory to create files in]:directory:_directories' \
        '(-h --help)'{-h,--help}'[Show help]' \
        ':module name'
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
            lookup)  _semacro_lookup ;;
            find)    _semacro_find ;;
            list)    _semacro_list ;;
            callers) _semacro_callers ;;
            which)   _semacro_which ;;
            telookup) _semacro_telookup ;;
            deps)    _semacro_deps ;;
            init)    _semacro_init ;;
        esac
        ;;
esac
