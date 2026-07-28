"""Additional branch-focused tests for semacro."""
import io
import sys
from pathlib import Path

import pytest
import semacro as sm


def test_find_m4_block_end_unmatched_returns_minus_one():
    text = "interface(`x',`allow $1 self:process signal;"
    start = text.index("`allow") + 1
    assert sm._find_m4_block_end(text, start) == -1


def test_parse_file_handles_read_error(monkeypatch, tmp_path):
    bad = tmp_path / "bad.if"
    bad.write_text("interface(`x',`allow $1 self:process signal;')")

    def _boom(*_args, **_kwargs):
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_text", _boom)
    assert sm.parse_file(str(bad), "bad.if") == []


def test_parse_file_skips_unterminated_macro(tmp_path):
    fpath = tmp_path / "unterminated.if"
    fpath.write_text("interface(`broken',`allow $1 self:process signal;\n")
    assert sm.parse_file(str(fpath), "unterminated.if") == []


def test_substitute_args_preserves_dollar_zero_and_clears_missing():
    out = sm.substitute_args("name=$0 first=$1 second=$2", ["my_t"])
    assert out == "name=$0 first=my_t second="


def test_substitute_args_expands_dollar_star():
    out = sm.substitute_args("args=$*", ["a_t", "b_t"])
    assert out == "args=a_t,b_t"


def test_find_calls_ignores_comment_and_policy_keywords():
    body = "# myapp_admin($1)\nallow a_t b_t:file read;\nmyapp_read_config($1)\n"
    calls = sm.find_calls_in_body(body)
    names = [name for name, _args, _start, _end in calls]
    assert "myapp_read_config" in names
    assert "allow" not in names
    assert "myapp_admin" not in names


def test_cmd_lookup_not_found_prints_suggestion(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read")
    captured = capsys.readouterr()
    assert ret == 1
    assert "Did you mean" in captured.err


def test_cmd_lookup_call_substitutes_args_without_expand(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config(myapp_t)")
    captured = capsys.readouterr()
    assert ret == 0
    assert "allow myapp_t myapp_conf_t:file read_file_perms;" in captured.out


def test_cmd_find_requires_pattern_or_perms(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, pattern=None, perms=None)
    captured = capsys.readouterr()
    assert ret == 1
    assert "need a pattern or --perms" in captured.err


def test_cmd_find_invalid_regex(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, "[")
    captured = capsys.readouterr()
    assert ret == 1
    assert "invalid regex" in captured.err


def test_cmd_find_perms_requires_non_empty(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, perms="   ")
    captured = capsys.readouterr()
    assert ret == 1
    assert "provide at least one permission" in captured.err


def test_cmd_find_perms_no_match(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, perms="execute_nope")
    captured = capsys.readouterr()
    assert ret == 1
    assert "no defines containing all of" in captured.err


def test_cmd_list_returns_error_when_empty_category(synthetic_index, capsys):
    ret = sm.cmd_list(synthetic_index, "kernel")
    captured = capsys.readouterr()
    assert ret == 1
    assert "no macros found for category 'kernel'" in captured.err


def test_cmd_callers_not_found_prints_suggestion(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "myapp_manage")
    captured = capsys.readouterr()
    assert ret == 1
    assert "Did you mean" in captured.err


def test_cmd_telookup_adds_missing_semicolon(synthetic_index, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("allow myapp_t self:capability kill\n"))
    ret = sm.cmd_telookup(synthetic_index, "-")
    captured = capsys.readouterr()
    assert ret == 0
    assert "allow myapp_t self:capability kill;" in captured.out


def test_read_arg_reads_piped_input(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("myapp_read_config\n"))
    assert sm._read_arg("-", "lookup") == "myapp_read_config"


def test_read_arg_errors_when_no_input(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    val = sm._read_arg("-", "lookup")
    captured = capsys.readouterr()
    assert val is None
    assert "missing required argument" in captured.err


def test_main_init_path_returns_cmd_init_value(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["semacro", "init", "myapp"])
    monkeypatch.setattr(sm, "cmd_init", lambda name, output_dir=".": 7)
    assert sm.main() == 7


def test_main_no_command_returns_one(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["semacro"])
    assert sm.main() == 1


def test_main_unknown_global_arg_raises_system_exit(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["semacro", "--bogus"])
    with pytest.raises(SystemExit):
        sm.main()
