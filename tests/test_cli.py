"""Tests for CLI argument handling and integration."""
import subprocess
import sys

import pytest
import semacro as sm


def _run_semacro(*args):
    """Run semacro as subprocess."""
    script = str(next(p for p in [
        __import__('pathlib').Path(__file__).parent.parent / "semacro.py",
    ] if p.exists()))
    return subprocess.run(
        [sys.executable, script] + list(args),
        capture_output=True, text=True, timeout=30
    )


def test_version():
    result = _run_semacro("--version")
    assert result.returncode == 0
    assert "semacro" in result.stdout.lower() or "0." in result.stdout


def test_help():
    result = _run_semacro("--help")
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "semacro" in result.stdout.lower()


def test_no_args():
    result = _run_semacro()
    assert result.returncode != 0 or "usage" in result.stdout.lower() or "usage" in result.stderr.lower()


def test_lookup_help():
    result = _run_semacro("lookup", "--help")
    assert result.returncode == 0
    assert "lookup" in result.stdout.lower() or "expand" in result.stdout.lower()


def test_find_help():
    result = _run_semacro("find", "--help")
    assert result.returncode == 0


def test_list_help():
    result = _run_semacro("list", "--help")
    assert result.returncode == 0


def test_which_help():
    result = _run_semacro("which", "--help")
    assert result.returncode == 0


def test_init_help():
    result = _run_semacro("init", "--help")
    assert result.returncode == 0


def test_unknown_subcommand():
    result = _run_semacro("nonexistent_command")
    assert result.returncode != 0


def test_main_unknown_argument_for_subcommand(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["semacro", "lookup", "foo", "--bogus"])
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 2
    assert "unrecognized arguments" in captured.err
    assert "semacro lookup -h" in captured.err


def test_main_errors_when_include_path_missing(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["semacro", "list"])
    monkeypatch.setattr(sm, "detect_include_path", lambda: None)
    monkeypatch.delenv("SEMACRO_INCLUDE_PATH", raising=False)
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "cannot find SELinux policy include directory" in captured.err


def test_main_errors_when_include_path_not_directory(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["semacro", "--include-path", "/tmp/not-a-real-dir", "list"],
    )
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "include path '/tmp/not-a-real-dir' does not exist" in captured.err


def test_main_errors_when_index_empty(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["semacro", "list"])
    monkeypatch.setattr(sm, "detect_include_path", lambda: "/tmp")
    monkeypatch.setattr(sm.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(sm, "load_or_build_index", lambda p: {})
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "no macros found under '/tmp'" in captured.err


def test_main_rejects_name_without_transition(monkeypatch, capsys, synthetic_index):
    monkeypatch.setattr(
        sys,
        "argv",
        ["semacro", "which", "myapp_t", "myapp_conf_t", "read", "--name", "foo"],
    )
    monkeypatch.setattr(sm, "detect_include_path", lambda: "/tmp")
    monkeypatch.setattr(sm.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(sm, "load_or_build_index", lambda p: synthetic_index)
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "--name only applies with --transition" in captured.err


@pytest.mark.parametrize("argv", [
    ["semacro", "lookup", "--depth", "0", "myapp_read_config"],
    ["semacro", "telookup", "--depth", "0", "tests/fixtures/myapp.te"],
    ["semacro", "deps", "--depth", "0", "myapp_admin"],
])
def test_main_rejects_non_positive_depth(argv, monkeypatch, capsys, synthetic_index):
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(sm, "detect_include_path", lambda: "/tmp")
    monkeypatch.setattr(sm.os.path, "isdir", lambda p: True)
    monkeypatch.setattr(sm, "load_or_build_index", lambda p: synthetic_index)
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "--depth must be at least 1" in captured.err
