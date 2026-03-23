"""Tests for the init subcommand."""
import pytest
import semacro as sm


def test_init_creates_files(tmp_output):
    ret = sm.cmd_init("testmod", output_dir=str(tmp_output))
    assert ret == 0
    assert (tmp_output / "testmod.te").exists()
    assert (tmp_output / "testmod.if").exists()
    assert (tmp_output / "testmod.fc").exists()


def test_init_te_has_policy_module(tmp_output):
    sm.cmd_init("testmod", output_dir=str(tmp_output))
    content = (tmp_output / "testmod.te").read_text()
    assert "policy_module(testmod" in content


def test_init_te_has_types(tmp_output):
    sm.cmd_init("testmod", output_dir=str(tmp_output))
    content = (tmp_output / "testmod.te").read_text()
    assert "testmod_t" in content
    assert "testmod_exec_t" in content


def test_init_fc_has_exec_entry(tmp_output):
    sm.cmd_init("testmod", output_dir=str(tmp_output))
    content = (tmp_output / "testmod.fc").read_text()
    assert "testmod_exec_t" in content


def test_init_if_has_interface(tmp_output):
    sm.cmd_init("testmod", output_dir=str(tmp_output))
    content = (tmp_output / "testmod.if").read_text()
    assert "interface" in content


def test_init_return_code(tmp_output):
    ret = sm.cmd_init("testmod", output_dir=str(tmp_output))
    assert ret == 0
