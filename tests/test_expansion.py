"""Tests for macro expansion engine."""
import semacro as sm


def test_expand_simple_interface(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", [])
    rules = sm.collect_leaf_rules(node)
    assert "allow $1 myapp_conf_t:file { getattr read open };" in rules


def test_expand_with_args(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", ["httpd_t"])
    rules = sm.collect_leaf_rules(node)
    assert "allow httpd_t myapp_conf_t:file { getattr read open };" in rules


def test_expand_nested_macro(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_admin", [])
    child_names = {c.text.split("(")[0] for c in node.children if not c.is_leaf}
    assert "myapp_read_config" in child_names
    assert "myapp_manage_pid" in child_names


def test_expand_define(synthetic_index):
    node = sm.expand_macro(synthetic_index, "read_file_perms", [])
    assert node.text == "read_file_perms"
    assert len(node.children) == 1
    assert node.children[0].is_leaf is True
    assert node.children[0].text == "{ getattr read open }"


def test_expand_unknown_macro(synthetic_index):
    node = sm.expand_macro(synthetic_index, "nonexistent_macro", [])
    assert node.is_leaf is True
    assert node.children == []
    assert node.text == "nonexistent_macro"


def test_collect_leaf_rules(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", ["myapp_t"])
    rules = sm.collect_leaf_rules(node)
    assert isinstance(rules, list)
    assert "allow myapp_t myapp_conf_t:file { getattr read open };" in rules


def test_format_tree(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_read_config", ["myapp_t"])
    output = sm.format_tree(node)
    assert isinstance(output, str)
    assert "myapp_read_config(myapp_t)" in output
    assert "allow myapp_t myapp_conf_t:file read_file_perms;" in output
    assert "read_file_perms -> { getattr read open }" in output


def test_expand_with_depth_limit(synthetic_index):
    node = sm.expand_macro(synthetic_index, "myapp_admin", [], max_depth=1)
    output = sm.format_tree(node)
    assert "... (max depth reached)" in output


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
    text = "{ getattr { read open } map }"
    result = sm._flatten_braces(text)
    assert result == "{ getattr read open map }"


def test_expand_preserves_allow_rules(synthetic_index):
    node = sm.expand_macro(synthetic_index, "kernel_read_system_state", ["myapp_t"])
    rules = sm.collect_leaf_rules(node)
    assert "allow myapp_t proc_t:file { read open getattr };" in rules
    assert "allow myapp_t proc_t:dir search;" in rules
