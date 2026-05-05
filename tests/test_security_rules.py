"""
Tests for security rules added from SECURITY_RULES_REVIEW.md.
"""

from pathlib import Path

from phpoptimizer.config import Config
from phpoptimizer.simple_analyzer import SimpleAnalyzer


def analyze_security_rules(php_code: str):
    config = Config()
    analyzer = SimpleAnalyzer(config)
    result = analyzer.analyze_content(php_code, Path("security_review_fixture.php"))
    return result["issues"]


def issues_for(php_code: str, rule_name: str):
    return [issue for issue in analyze_security_rules(php_code) if issue["rule_name"] == rule_name]


def test_command_injection_detects_tainted_variable():
    php_code = """<?php
$cmd = $_GET['cmd'];
system($cmd);
?>"""

    assert issues_for(php_code, "security.command_injection")


def test_command_injection_ignores_escaped_argument():
    php_code = """<?php
$cmd = escapeshellarg($_GET['cmd']);
system($cmd);
?>"""

    assert not issues_for(php_code, "security.command_injection")


def test_insecure_deserialization_detects_user_input():
    php_code = """<?php
$payload = $_COOKIE['session'];
$data = unserialize($payload);
?>"""

    assert issues_for(php_code, "security.insecure_deserialization")


def test_insecure_deserialization_ignores_disabled_classes():
    php_code = """<?php
$payload = $_COOKIE['session'];
$data = unserialize($payload, ['allowed_classes' => false]);
?>"""

    assert not issues_for(php_code, "security.insecure_deserialization")


def test_path_traversal_detects_user_controlled_path():
    php_code = """<?php
$page = $_GET['page'];
include($page . '.php');
?>"""

    assert issues_for(php_code, "security.path_traversal")


def test_path_traversal_ignores_basename_sanitized_path():
    php_code = """<?php
$page = basename($_GET['page']);
include($page . '.php');
?>"""

    assert not issues_for(php_code, "security.path_traversal")


def test_ssrf_detects_user_controlled_url():
    php_code = """<?php
$url = $_GET['url'];
$body = file_get_contents($url);
?>"""

    assert issues_for(php_code, "security.ssrf")


def test_ssrf_ignores_fixed_url():
    php_code = """<?php
$body = file_get_contents('https://example.com/status');
?>"""

    assert not issues_for(php_code, "security.ssrf")


def test_csrf_missing_protection_detects_post_form_without_token():
    php_code = """<?php ?>
<form method="post" action="/delete-account">
    <button type="submit">Delete</button>
</form>
"""

    assert issues_for(php_code, "security.csrf_missing_protection")


def test_csrf_missing_protection_ignores_post_form_with_token():
    php_code = """<?php ?>
<form method="post" action="/profile">
    <input type="hidden" name="csrf_token" value="<?= $token ?>">
    <button type="submit">Save</button>
</form>
"""

    assert not issues_for(php_code, "security.csrf_missing_protection")


def test_review_security_rules_are_declared_in_config():
    config = Config()
    for rule_name in [
        "security.command_injection",
        "security.insecure_deserialization",
        "security.path_traversal",
        "security.ssrf",
        "security.csrf_missing_protection",
    ]:
        assert config.should_apply_rule(rule_name)
