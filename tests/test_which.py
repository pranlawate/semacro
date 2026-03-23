"""Tests for the which subcommand."""
import pytest
import semacro as sm


def test_which_real_index_av_rule(real_index, capsys):
    ret = sm.cmd_which(real_index, "httpd_t", "httpd_log_t", "read")
    captured = capsys.readouterr()
    # Should find a macro or not, depending on policy


def test_which_real_index_transition(real_index, capsys):
    ret = sm.cmd_which(real_index, "init_t", "var_run_t", "httpd_var_run_t",
                       transition=True)
    captured = capsys.readouterr()


def test_which_with_class(real_index, capsys):
    ret = sm.cmd_which(real_index, "httpd_t", "httpd_log_t", "read",
                       obj_class="file")
    captured = capsys.readouterr()


def test_which_no_match(synthetic_index, capsys):
    ret = sm.cmd_which(synthetic_index, "zzz_t", "yyy_t", "zzz_perm")
    assert ret == 1


def test_which_returns_int(synthetic_index):
    ret = sm.cmd_which(synthetic_index, "httpd_t", "httpd_conf_t", "read")
    assert isinstance(ret, int)
