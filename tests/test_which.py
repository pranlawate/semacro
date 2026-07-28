"""Tests for the which subcommand."""
import semacro as sm


def test_which_synthetic_av_rule_match(synthetic_index, capsys):
    ret = sm.cmd_which(synthetic_index, "myapp_t", "myapp_conf_t", "read")
    captured = capsys.readouterr()
    assert ret == 0
    assert "myapp_read_config(myapp_t)" in captured.out


def test_which_synthetic_transition_match(synthetic_index, capsys):
    ret = sm.cmd_which(
        synthetic_index,
        "myapp_t",
        "var_run_t",
        "myapp_var_run_t",
        transition=True,
    )
    captured = capsys.readouterr()
    assert ret == 0
    assert "files_pid_filetrans(myapp_t, myapp_var_run_t, file)" in captured.out


def test_which_with_class_filter(synthetic_index, capsys):
    ret = sm.cmd_which(
        synthetic_index,
        "myapp_t",
        "myapp_conf_t",
        "read",
        obj_class="file",
    )
    captured = capsys.readouterr()
    assert ret == 0
    assert "myapp_read_config(myapp_t)" in captured.out


def test_which_transition_name_filter_no_match(synthetic_index, capsys):
    ret = sm.cmd_which(
        synthetic_index,
        "myapp_t",
        "var_run_t",
        "myapp_var_run_t",
        transition=True,
        trans_name="pidfile",
    )
    captured = capsys.readouterr()
    assert ret == 1
    assert "no macros found" in captured.err


def test_which_no_match(synthetic_index, capsys):
    ret = sm.cmd_which(synthetic_index, "zzz_t", "yyy_t", "zzz_perm")
    captured = capsys.readouterr()
    assert ret == 1
    assert "no macros found granting" in captured.err
