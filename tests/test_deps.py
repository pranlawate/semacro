"""Tests for the deps subcommand."""
import semacro as sm


def test_deps_dot_output_contains_edges(synthetic_index, capsys):
    ret = sm.cmd_deps(synthetic_index, "myapp_admin")
    captured = capsys.readouterr()
    assert ret == 0
    assert 'digraph "myapp_admin" {' in captured.out
    assert '"myapp_admin" -> "myapp_read_config";' in captured.out
    assert '"myapp_admin" -> "myapp_manage_pid";' in captured.out


def test_deps_mermaid_output_contains_edges(synthetic_index, capsys):
    ret = sm.cmd_deps(synthetic_index, "myapp_admin", mermaid=True)
    captured = capsys.readouterr()
    assert ret == 0
    assert "graph LR" in captured.out
    assert "myapp_admin --> myapp_read_config" in captured.out


def test_deps_depth_zero_hides_transitive_calls(synthetic_index, capsys):
    ret = sm.cmd_deps(synthetic_index, "myapp_admin", depth=0, mermaid=True)
    captured = capsys.readouterr()
    assert ret == 0
    assert "myapp_admin --> myapp_manage_pid" in captured.out
    assert "myapp_manage_pid --> manage_files_pattern" not in captured.out


def test_deps_unknown_macro_returns_error(synthetic_index, capsys):
    ret = sm.cmd_deps(synthetic_index, "no_such_macro")
    captured = capsys.readouterr()
    assert ret == 1
    assert "macro 'no_such_macro' not found" in captured.err


def test_deps_leaf_macro_returns_zero_with_hint(synthetic_index, capsys):
    ret = sm.cmd_deps(synthetic_index, "read_file_perms")
    captured = capsys.readouterr()
    assert ret == 0
    assert "does not call any other macros" in captured.err
