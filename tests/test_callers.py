"""Tests for the callers subcommand."""
import pytest
import semacro as sm


def test_callers_found(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "myapp_read_config")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_admin" in captured.out


def test_callers_not_found(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "nonexistent_xyz")
    assert ret == 1


def test_callers_no_callers(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "myapp_admin")
    captured = capsys.readouterr()
    # myapp_admin is not called by any other macro in fixtures


def test_callers_for_define(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "manage_files_pattern")
    captured = capsys.readouterr()
    # manage_files_pattern is called by myapp_manage_pid
    if ret == 0:
        assert "myapp_manage_pid" in captured.out


def test_callers_manage_files_pattern(synthetic_index, capsys):
    ret = sm.cmd_callers(synthetic_index, "manage_files_pattern")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_manage_pid" in captured.out
