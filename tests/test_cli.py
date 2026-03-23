"""Tests for CLI argument handling and integration."""
import subprocess
import sys
import pytest


def _run_semacro(*args):
    """Run semacro as subprocess."""
    cmd = [sys.executable, "-c",
           "import sys; sys.path.insert(0,'.'); import semacro; semacro.main()",
           "--"] + list(args)
    # Simpler: just call the script directly
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
