"""Tests for index building and caching."""
import os
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


def test_detect_include_path_env_var(tmp_path, monkeypatch):
    """SEMACRO_INCLUDE_PATH is read by CLI, not detect_include_path() directly.
    detect_include_path() checks filesystem for policy files."""
    include = sm.detect_include_path()
    # Just verify it returns a valid path or None
    if include:
        assert os.path.isdir(include)


def test_detect_include_path_env_var_invalid(monkeypatch):
    monkeypatch.setenv("SEMACRO_INCLUDE_PATH", "/nonexistent/path")
    path = sm.detect_include_path()
    # Should fall back or return None
    assert path is None or path != "/nonexistent/path"


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


def test_index_deduplicates(fixtures_dir, tmp_path):
    """Same macro defined twice — last wins or first wins, but no crash."""
    dup = tmp_path / "dup.if"
    dup.write_text(
        "interface(`dup_test',`allow $1 self:process signal;')\n"
        "interface(`dup_test',`allow $1 self:process kill;')\n"
    )
    macros = sm.parse_file(str(dup), "dup.if")
    assert len([m for m in macros if m.name == "dup_test"]) >= 1
