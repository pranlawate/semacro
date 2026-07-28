"""Tests for utility functions."""
import pytest
import semacro as sm


def test_parse_call_with_args():
    result = sm.parse_call("myapp_read_config(httpd_t)")
    assert result is not None
    name, args = result
    assert name == "myapp_read_config"
    assert args == ["httpd_t"]


def test_parse_call_multiple_args():
    result = sm.parse_call("domtrans_pattern(init_t, myapp_exec_t, myapp_t)")
    assert result is not None
    name, args = result
    assert name == "domtrans_pattern"
    assert len(args) == 3


def test_parse_call_no_args():
    result = sm.parse_call("read_file_perms")
    assert result is None


def test_parse_call_none():
    with pytest.raises(AttributeError):
        sm.parse_call(None)


def test_parse_call_empty():
    result = sm.parse_call("")
    assert result is None


def test_substitute_args_single():
    body = "allow $1 myapp_conf_t:file read;"
    result = sm.substitute_args(body, ["httpd_t"])
    assert "allow httpd_t myapp_conf_t:file read;" in result


def test_substitute_args_multiple():
    body = "allow $1 $2:process transition;\ntype_transition $1 $2:process $3;"
    result = sm.substitute_args(body, ["init_t", "myapp_exec_t", "myapp_t"])
    assert "allow init_t myapp_exec_t:process transition;" in result
    assert "type_transition init_t myapp_exec_t:process myapp_t;" in result


def test_substitute_args_unused():
    body = "allow $1 self:capability kill;"
    result = sm.substitute_args(body, ["myapp_t", "extra_arg"])
    assert "allow myapp_t self:capability kill;" in result


def test_find_calls_in_body():
    body = "myapp_read_config($1)\nmyapp_manage_pid($1)\n"
    calls = sm.find_calls_in_body(body)
    names = [c[0] for c in calls]
    assert "myapp_read_config" in names
    assert "myapp_manage_pid" in names
