"""Tests for the telookup subcommand."""
import io

import semacro as sm


def test_telookup_fixture_outputs_expanded_rules(synthetic_index, myapp_te, capsys):
    ret = sm.cmd_telookup(synthetic_index, str(myapp_te))
    captured = capsys.readouterr()
    assert ret == 0
    assert "allow myapp_t myapp_conf_t:file { getattr read open };" in captured.out
    assert "type_transition myapp_t var_run_t:file myapp_var_run_t;" in captured.out


def test_telookup_skips_policy_module_line(synthetic_index, myapp_te, capsys):
    ret = sm.cmd_telookup(synthetic_index, str(myapp_te))
    captured = capsys.readouterr()
    assert ret == 0
    assert "policy_module(" not in captured.out


def test_telookup_tree_mode_outputs_macro_trees(synthetic_index, myapp_te, capsys):
    ret = sm.cmd_telookup(synthetic_index, str(myapp_te), tree_mode=True)
    captured = capsys.readouterr()
    assert ret == 0
    assert "myapp_read_config(myapp_t)" in captured.out
    assert "myapp_manage_pid(myapp_t)" in captured.out


def test_telookup_nonexistent_file_returns_error(synthetic_index, capsys):
    ret = sm.cmd_telookup(synthetic_index, "/tmp/definitely-missing-semacro.te")
    captured = capsys.readouterr()
    assert ret == 1
    assert "cannot read" in captured.err


def test_telookup_reads_from_stdin(synthetic_index, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("myapp_read_config(myapp_t)\n"))
    ret = sm.cmd_telookup(synthetic_index, "-")
    captured = capsys.readouterr()
    assert ret == 0
    assert "allow myapp_t myapp_conf_t:file { getattr read open };" in captured.out


def test_merge_rules_deduplicates_and_unions_permissions():
    merged = sm._merge_rules(
        [
            "allow myapp_t myapp_conf_t:file { read open };",
            "allow myapp_t myapp_conf_t:file { open getattr };",
            "type_transition myapp_t var_run_t:file myapp_var_run_t;",
            "type_transition myapp_t var_run_t:file myapp_var_run_t;",
        ]
    )
    assert "allow myapp_t myapp_conf_t:file { read open getattr };" in merged
    assert merged.count("type_transition myapp_t var_run_t:file myapp_var_run_t;") == 1
