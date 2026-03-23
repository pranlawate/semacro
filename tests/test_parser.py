"""Tests for M4 file parsing."""
import pytest
from conftest import FIXTURES_DIR
import semacro as sm


def test_parse_interfaces_file():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    assert len(macros) >= 6


def test_parse_defines_file():
    macros = sm.parse_file(str(FIXTURES_DIR / "defines.spt"), "defines.spt")
    assert len(macros) >= 6


def test_interface_has_name():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    names = {m.name for m in macros}
    assert "myapp_read_config" in names
    assert "myapp_domtrans" in names
    assert "myapp_manage_pid" in names
    assert "myapp_admin" in names


def test_define_has_name():
    macros = sm.parse_file(str(FIXTURES_DIR / "defines.spt"), "defines.spt")
    names = {m.name for m in macros}
    assert "read_file_perms" in names
    assert "manage_files_pattern" in names
    assert "domtrans_pattern" in names


def test_interface_body_contains_allow():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    by_name = {m.name: m for m in macros}
    assert "allow $1 myapp_conf_t:file" in by_name["myapp_read_config"].body


def test_interface_body_contains_gen_require():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    by_name = {m.name: m for m in macros}
    assert "gen_require" in by_name["myapp_read_config"].body


def test_define_body_contains_permissions():
    macros = sm.parse_file(str(FIXTURES_DIR / "defines.spt"), "defines.spt")
    by_name = {m.name: m for m in macros}
    assert "getattr read open" in by_name["read_file_perms"].body


def test_parse_stores_rel_path():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    assert macros[0].source_file == "interfaces.if"


def test_parse_empty_file(tmp_path):
    empty = tmp_path / "empty.if"
    empty.write_text("")
    macros = sm.parse_file(str(empty), "empty.if")
    assert macros == []


def test_parse_file_with_comments_only(tmp_path):
    f = tmp_path / "comments.if"
    f.write_text("## Just a comment\n## Another comment\n")
    macros = sm.parse_file(str(f), "comments.if")
    assert macros == []


def test_macro_has_line_number():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    for m in macros:
        assert m.line_number > 0


def test_interface_with_dollar_args():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    by_name = {m.name: m for m in macros}
    assert "$1" in by_name["myapp_read_config"].body


def test_nested_interface_calls_in_body():
    macros = sm.parse_file(str(FIXTURES_DIR / "interfaces.if"), "interfaces.if")
    by_name = {m.name: m for m in macros}
    body = by_name["myapp_admin"].body
    assert "myapp_read_config($1)" in body
    assert "myapp_manage_pid($1)" in body
