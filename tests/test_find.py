"""Tests for the find subcommand."""
import pytest
import semacro as sm


def test_find_by_name(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, "myapp")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_read_config" in captured.out


def test_find_regex(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, ".*pid.*")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_manage_pid" in captured.out
    assert "files_pid_filetrans" in captured.out


def test_find_no_match(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, "zzz_nonexistent_zzz")
    assert ret == 1


def test_find_anchor(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, "^myapp_read")
    assert ret == 0
    captured = capsys.readouterr()
    assert "myapp_read_config" in captured.out


def test_find_multiple_matches(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, "myapp_")
    assert ret == 0
    captured = capsys.readouterr()
    assert captured.out.count("myapp_") >= 3


def test_find_by_perms(synthetic_index, capsys):
    ret = sm.cmd_find(synthetic_index, perms="getattr read open")
    assert ret == 0
    captured = capsys.readouterr()
    assert "read_file_perms" in captured.out
