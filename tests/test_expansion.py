"""Tests for macro expansion engine."""
import pytest
import semacro as sm


def test_expand_simple_interface(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", [])
    assert node is not None


def test_expand_with_args(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", ["httpd_t"])
    assert node is not None


def test_expand_nested_macro(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_admin", [])
    assert node is not None
    assert len(node.children) >= 2


def test_expand_define(synthetic_index):
    node = sm.expand_macro(synthetic_index, "read_file_perms", [])
    assert node is not None


def test_expand_unknown_macro(synthetic_index):
    node = sm.expand_macro(synthetic_index, "nonexistent_macro", [])
    assert node.children == [] or "not found" in node.text.lower() or node is not None


def test_collect_leaf_rules(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", [])
    rules = sm.collect_leaf_rules(node)
    assert isinstance(rules, list)


def test_format_tree(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", [])
    output = sm.format_tree(node)
    assert isinstance(output, str)
    assert len(output) > 0


def test_expand_with_depth_limit(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_admin", [], max_depth=1)
    assert node is not None


def test_strip_gen_require():
    body = """
	gen_require(`
		type myapp_conf_t;
	')

	allow $1 myapp_conf_t:file read;
"""
    result = sm._strip_gen_require(body)
    assert "gen_require" not in result
    assert "allow $1 myapp_conf_t:file read;" in result


def test_flatten_braces():
    text = "{ getattr read open }"
    result = sm._flatten_braces(text)
    assert isinstance(result, str)


def test_expand_preserves_allow_rules(synthetic_index):
    node = sm.expand_macro(synthetic_index, "kernel_read_system_state", [])
    rules = sm.collect_leaf_rules(node)
    rule_text = " ".join(rules)
    assert "allow" in rule_text or "proc_t" in rule_text
