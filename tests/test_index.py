"""Tests for index building and caching."""
import os
import pickle
import sys

import pytest
import semacro as sm


def test_synthetic_index_has_interfaces(synthetic_index):
    assert "myapp_read_config" in synthetic_index
    assert "myapp_domtrans" in synthetic_index
    assert "myapp_admin" in synthetic_index


def test_synthetic_index_has_defines(synthetic_index):
    assert "read_file_perms" in synthetic_index
    assert "manage_files_pattern" in synthetic_index
    assert "domtrans_pattern" in synthetic_index


def test_synthetic_index_count(synthetic_index):
    assert len(synthetic_index) >= 12


def test_detect_include_path_default():
    path = sm.detect_include_path()
    if path:
        assert os.path.isdir(path)
        assert "include" in path or "policy" in path


def test_main_uses_include_path_env_var(monkeypatch, capsys, fixtures_dir):
    """SEMACRO_INCLUDE_PATH is used by main() when --include-path is not set."""
    monkeypatch.setenv("SEMACRO_INCLUDE_PATH", str(fixtures_dir))
    monkeypatch.setattr(sm, "detect_include_path", lambda: None)
    monkeypatch.setattr(sys, "argv", ["semacro", "lookup", "myapp_read_config"])
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 0
    assert "myapp_read_config" in captured.out


def test_main_rejects_nonexistent_env_var_path(monkeypatch, capsys):
    """SEMACRO_INCLUDE_PATH pointing to a non-existent directory causes an error."""
    monkeypatch.setenv("SEMACRO_INCLUDE_PATH", "/nonexistent/path")
    monkeypatch.setattr(sm, "detect_include_path", lambda: None)
    monkeypatch.setattr(sys, "argv", ["semacro", "lookup", "myapp_read_config"])
    ret = sm.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "does not exist" in captured.err


def test_build_index_from_fixture_dir(fixtures_dir):
    index = sm.build_index(str(fixtures_dir))
    assert len(index) >= 12
    assert "myapp_read_config" in index


def test_macrodef_has_expected_attrs(synthetic_index):
    macro = synthetic_index["myapp_read_config"]
    assert hasattr(macro, "name")
    assert hasattr(macro, "body")
    assert hasattr(macro, "source_file")
    assert hasattr(macro, "line_number")


def test_index_deduplicates(tmp_path):
    """Same macro defined twice — build_index keeps last definition."""
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "dup.if").write_text(
        "interface(`dup_test',`allow $1 self:process signal;')\n"
        "interface(`dup_test',`allow $1 self:process kill;')\n"
    )
    index = sm.build_index(str(policy_dir))
    assert "dup_test" in index
    assert "kill" in index["dup_test"].body


def test_has_policy_files_true_and_false(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert sm._has_policy_files(str(empty_dir)) is False

    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "one.if").write_text("interface(`x',`allow $1 self:process signal;')\n")
    assert sm._has_policy_files(str(policy_dir)) is True


def test_source_fingerprint_changes_when_file_mtime_changes(tmp_path):
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    source = policy_dir / "one.if"
    source.write_text("interface(`x',`allow $1 self:process signal;')\n")

    fp1 = sm._source_fingerprint(str(policy_dir))
    current = os.path.getmtime(source)
    os.utime(source, (current + 2, current + 2))
    fp2 = sm._source_fingerprint(str(policy_dir))

    assert fp1 != fp2


def test_load_or_build_index_uses_cache(tmp_path, monkeypatch):
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "one.if").write_text("interface(`x',`allow $1 self:process signal;')\n")

    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(sm, "_CACHE_DIR", cache_dir)

    calls = {"count": 0}
    real_build = sm.build_index

    def _wrapped(path):
        calls["count"] += 1
        return real_build(path)

    monkeypatch.setattr(sm, "build_index", _wrapped)

    first = sm.load_or_build_index(str(policy_dir))
    second = sm.load_or_build_index(str(policy_dir))

    assert "x" in first
    assert "x" in second
    assert calls["count"] == 1


def test_load_or_build_index_recovers_from_bad_cache(tmp_path, monkeypatch):
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    (policy_dir / "one.if").write_text("interface(`x',`allow $1 self:process signal;')\n")

    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(sm, "_CACHE_DIR", cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = sm._cache_path(str(policy_dir))
    with open(cache_path, "wb") as f:
        f.write(b"not-a-pickle")

    index = sm.load_or_build_index(str(policy_dir))
    assert "x" in index

    with open(cache_path, "rb") as f:
        saved_fp, saved_index = pickle.load(f)
    assert isinstance(saved_fp, str)
    assert "x" in saved_index
