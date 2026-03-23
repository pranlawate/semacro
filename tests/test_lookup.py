"""Tests for the lookup subcommand."""
import pytest
import semacro as sm


def test_lookup_existing_interface(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_read_config" in captured.out


def test_lookup_existing_define(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "read_file_perms")
    assert ret == 0
    captured = capsys.readouterr()
    assert "read_file_perms" in captured.out


def test_lookup_unknown_name(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "nonexistent_macro_xyz")
    assert ret == 1


def test_lookup_with_expand(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config", expand=True)
    assert ret == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_lookup_with_rules(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config", rules=True)
    assert ret == 0
    captured = capsys.readouterr()
    assert "allow" in captured.out


def test_lookup_with_args(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config(httpd_t)", expand=True)
    assert ret == 0
    captured = capsys.readouterr()
    assert "httpd_t" in captured.out


def test_lookup_shows_source_file(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_read_config")
    captured = capsys.readouterr()
    assert "interfaces.if" in captured.out


def test_lookup_nested_expansion(synthetic_index, capsys):
    ret = sm.cmd_lookup(synthetic_index, "myapp_admin", expand=True)
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_read_config" in captured.out or "myapp_manage_pid" in captured.out
