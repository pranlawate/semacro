"""Tests for the list subcommand."""
import pytest
import semacro as sm


def test_list_all(synthetic_index, capsys):
    ret = sm.cmd_list(synthetic_index, None)
    assert ret == 0
    captured = capsys.readouterr()
    assert len(captured.out.strip().split('\n')) >= 6


def test_list_returns_zero(synthetic_index):
    ret = sm.cmd_list(synthetic_index, None)
    assert ret == 0


def test_list_with_real_index_kernel(real_index, capsys):
    ret = sm.cmd_list(real_index, "kernel")
    assert ret == 0
    captured = capsys.readouterr()
    assert "kernel" in captured.out.lower()


def test_list_with_real_index_all(real_index, capsys):
    ret = sm.cmd_list(real_index, "all")
    assert ret == 0
    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split('\n') if l.strip()]
    assert len(lines) > 100
