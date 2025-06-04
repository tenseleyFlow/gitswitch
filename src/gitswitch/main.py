"""Gitswitch driver."""

import argparse
import logging
import sys
from typing import Optional, Dict

from .config import ConfigManager
from .accounts import AccountManager
from .git_ops import GitOperations
from .validation import ValidationService
from .display import DisplayManager
from .constants import *
from .exceptions import GitSwitchError, AccountNotFoundError, ValidationError
from .error_handling import setup_logging, get_logger
from .colors import set_color_mode, format_status, format_header

logger = get_logger("main")


class GitSwitchCLI:
    """Simplified CLI application using direct manager calls."""

    def __init__(self):
        # Initialize managers directly
        self.config_manager = ConfigManager()
        self.account_manager = AccountManager(self.config_manager)
        self.git_ops = GitOperations()
        self.validation_service = ValidationService()
        self.display = DisplayManager(self.config_manager, self.account_manager, self.git_ops, self.validation_service)

    def switch_account_interactive(self, scope_override: Optional[str] = None) -> bool:
        """Interactive account switching using direct manager calls."""
        try:
            print("┌────────────────────────────────┐")
            print(f"│   {format_header('Git Account Switcher')}     │")
            print("└────────────────────────────────┘")

            # Load accounts once and reuse
            success, accounts, message = self.account_manager.get_accounts()
            if not success:
                print(format_status(f"[ERROR] Error loading accounts: {message}"))
                return False

            if not accounts:
                print(format_status(MSG_NO_ACCOUNTS))
                print("   Run 'gitswitch add' to create your first account")
                return True  # Empty accounts is not a failure

            # Show current config and accounts using loaded data
            self.display.show_current_config()
            self.display.show_accounts(accounts)  # Pass accounts to avoid reload
            self.display.show_config_location()

            # Get user choice
            account_numbers = sorted(accounts.keys())
            choice_range = f"1-{max(account_numbers)}" if account_numbers else "no accounts"

            choice = input(f"Enter account number or search term ({choice_range}) or 'q' to quit: ").strip()

            if choice.lower() == "q":
                print("Goodbye!")
                return True

            # Switch to account directly
            return self._switch_to_account(choice, scope_override, accounts)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            return True  # Ctrl+C is success
        except Exception as e:
            logger.exception("Interactive switching failed")
            print(format_status(f"[ERROR] Error during account switching: {e}"))
            return False

    def _switch_to_account(
        self, identifier: str, scope_override: Optional[str] = None, accounts: Optional[Dict] = None
    ) -> bool:
        """Switch to a specific account using direct manager calls."""
        try:
            # Use provided accounts or fetch if not provided
            if accounts is None:
                success, accounts, message = self.account_manager.get_accounts()
                if not success:
                    print(format_status(f"[ERROR] Failed to load accounts: {message}"))
                    return False

            # Get account using new tuple-returning method
            success, account_num, account_data, message = self.account_manager.get_account(identifier, accounts)
            if not success:
                print(format_status(f"[ERROR] {message}"))
                
                # Show available accounts to help user
                if accounts:
                    print("\nAvailable accounts:")
                    self.display.show_accounts(accounts)
                return False

            # Validate account data
            is_valid, errors, warnings = self.validation_service.validate_account(account_data)
            if not is_valid:
                print(format_status(f"[ERROR] Account validation failed: {'; '.join(errors)}"))
                return False

            # Determine scope
            if scope_override:
                scope = scope_override
            else:
                scope_success, scope, scope_message = self.account_manager.get_account_preferred_scope(account_data)
                if not scope_success:
                    print(format_status(f"[WARN] {scope_message}"))
                    scope = "local"  # fallback

            # Switch using git operations directly
            success = self.git_ops.set_git_config(account_data, scope)
            if not success:
                print(format_status("[ERROR] Failed to set git configuration"))
                return False

            # Display success
            self._print_switch_success(account_num, account_data, scope)
            return True

        except Exception as e:
            logger.exception("Account switching failed")
            print(format_status(f"[ERROR] Error switching to account: {e}"))
            return False

    def _print_switch_success(self, account_num: int, account_data: dict, scope: str):
        """Print successful account switch information."""
        print(format_status(f"[SUCCESS] Successfully switched to: {account_data['description']} ({scope})"))
        print(f"   Name: {account_data['name']}")
        print(f"   Email: {account_data['email']}")
        print(f"   Scope: {scope}")

        # Show GPG status
        gpg_key = account_data.get("gpg_key", "")
        signing_enabled = account_data.get("signing_enabled", False)
        if gpg_key and signing_enabled:
            print(f"   GPG Key: {gpg_key}")
            print(f"   GPG Signing: {format_status('[ENABLED]')}")
        else:
            print(f"   GPG Signing: {format_status('[DISABLED]')}")

        # Show SSH status
        ssh_key = account_data.get("ssh_key", "")
        if ssh_key:
            ssh_host = account_data.get("ssh_host", "")
            host_text = f" (host: {ssh_host})" if ssh_host else ""
            print(f"   SSH Key: {ssh_key}{host_text}")
        else:
            print(f"   SSH: {format_status('[NOT CONFIGURED]')}")

    def handle_add_command(self) -> bool:
        """Handle the add account command using direct manager calls."""
        try:
            from .interactive import add_account_interactive

            return add_account_interactive(self.account_manager, self.validation_service, self.git_ops)
        except Exception as e:
            logger.exception("Add account command failed")
            print(format_status(f"[ERROR] Error adding account: {e}"))
            return False

    def handle_edit_command(self, identifier: str = None) -> bool:
        """Handle the edit account command using direct manager calls."""
        try:
            from .interactive import edit_account_interactive

            return edit_account_interactive(self.account_manager, self.validation_service, identifier)
        except Exception as e:
            logger.exception("Edit account command failed")
            print(format_status(f"[ERROR] Error editing account: {e}"))
            return False

    def handle_remove_command(self, identifier: str = None) -> bool:
        """Handle the remove account command using direct manager calls."""
        try:
            from .interactive import remove_account_interactive

            return remove_account_interactive(self.account_manager, self.display, identifier)
        except Exception as e:
            logger.exception("Remove account command failed")
            print(format_status(f"[ERROR] Error removing account: {e}"))
            return False

    def handle_list_command(self) -> bool:
        """Handle the list accounts command using direct manager calls."""
        try:
            success, accounts, message = self.account_manager.get_accounts()
            if not success:
                print(format_status(f"[ERROR] Error loading accounts: {message}"))
                return False

            if not accounts:
                print(format_status(MSG_NO_ACCOUNTS))
                print("   Please run 'gitswitch add' to create your first account")
                return True  # Empty list is successful operation

            self.display.show_accounts(accounts)
            self.display.show_config_location()
            return True

        except Exception as e:
            logger.exception("List accounts command failed")
            print(format_status(f"[ERROR] Error listing accounts: {e}"))
            return False

    def handle_status_command(self) -> bool:
        """Handle the status command using direct manager calls."""
        try:
            self.display.show_scope_status()
            return True
        except Exception as e:
            logger.exception("Status command failed")
            print(format_status(f"[ERROR] Error showing status: {e}"))
            return False

    def handle_config_command(self) -> bool:
        """Handle the config command using direct manager calls."""
        try:
            from .interactive import edit_config_file_interactive

            return edit_config_file_interactive(self.config_manager)
        except Exception as e:
            logger.exception("Config command failed")
            print(format_status(f"[ERROR] Error editing config: {e}"))
            return False

    def handle_doctor_command(self) -> bool:
        """Handle the doctor command using direct manager calls."""
        try:
            from .doctor import run_health_check

            return run_health_check(self.config_manager, self.account_manager, self.git_ops, self.validation_service)
        except Exception as e:
            logger.exception("Doctor command failed")
            print(format_status(f"[ERROR] Error running health check: {e}"))
            return False

    def handle_validate_command(self, target: str = None) -> bool:
        """Handle validation command using direct manager calls."""
        try:
            if target == "config":
                success, config, load_message = self.config_manager.load_config()
                if not success:
                    print(format_status(f"[ERROR] Failed to load config: {load_message}"))
                    return False
                is_valid, errors, warnings = self.validation_service.validate_config(config)
            elif target == "system":
                is_valid, errors, warnings = self.validation_service.validate_system_requirements()
            elif target and target.isdigit():
                # Validate specific account
                success, account_num, account_data, get_message = self.account_manager.get_account(target)
                if not success:
                    print(format_status(f"[ERROR] {get_message}"))
                    return False
                is_valid, errors, warnings = self.validation_service.validate_account(account_data)
            else:
                # Validate everything - streamlined inline version
                print(">> Running comprehensive validation...")

                all_valid = True
                all_warnings = []  # Track warnings separately

                # System validation
                print(f"\n── {format_header('System Requirements')} ──")
                sys_valid, sys_errors, sys_warnings = self.validation_service.validate_system_requirements()
                if sys_valid:
                    print(format_status("[OK] All required tools found"))
                else:
                    print(format_status("[FAIL] Missing tools:"))
                    for error in sys_errors:
                        print(f"   • {error}")
                    all_valid = False
                if sys_warnings:
                    all_warnings.extend(sys_warnings)

                # Config validation
                print(f"\n── {format_header('Configuration')} ──")
                config_success, config, config_message = self.config_manager.load_config()
                if config_success:
                    cfg_valid, cfg_errors, cfg_warnings = self.validation_service.validate_config(config)
                    if cfg_valid:
                        print(format_status("[OK] Configuration is valid"))
                        # Show warnings but don't fail
                        if cfg_warnings:
                            print(format_status("[WARN] Configuration warnings:"))
                            for warning in cfg_warnings:
                                print(f"   • {warning}")
                            all_warnings.extend(cfg_warnings)
                    else:
                        print(format_status("[FAIL] Configuration issues:"))
                        for error in cfg_errors:
                            print(f"   • {error}")
                        all_valid = False
                else:
                    print(format_status(f"[FAIL] Could not load configuration: {config_message}"))
                    all_valid = False

                # Account validation
                print(f"\n── {format_header('Accounts')} ──")
                accounts_success, accounts, accounts_message = self.account_manager.get_accounts()
                if accounts_success:
                    if accounts:
                        account_has_errors = False
                        for num, account in accounts.items():
                            acc_valid, acc_errors, acc_warnings = self.validation_service.validate_account(account)
                            status = "[OK]" if acc_valid else "[FAIL]"
                            print(
                                format_status(
                                    f"   {status} Account #{num}: {account.get('description', 'No description')}"
                                )
                            )
                            if not acc_valid:
                                for error in acc_errors:
                                    print(f"      • {error}")
                                account_has_errors = True
                            # Show warnings but don't fail for them
                            elif acc_warnings:
                                print(format_status("      [WARN] Warnings:"))
                                for warning in acc_warnings:
                                    print(f"         • {warning}")
                                all_warnings.extend(acc_warnings)
                        
                        if account_has_errors:
                            all_valid = False
                    else:
                        print(format_status("   [WARN] No accounts configured"))
                        # Don't fail for no accounts
                else:
                    print(format_status(f"   [FAIL] Error checking accounts: {accounts_message}"))
                    all_valid = False

                # Summary
                print(f"\n── {format_header('Summary')} ──")
                if all_valid:
                    print(format_status("[OK] All validations passed"))
                    if all_warnings:
                        print(format_status(f"[WARN] {len(all_warnings)} warning(s) found"))
                else:
                    print(format_status("[FAIL] Validation failed - see errors above"))

                return all_valid

            # Handle single validation results
            if is_valid:
                print(format_status("[OK] Validation passed"))
                # Show warnings but still return success
                if warnings:
                    print(format_status("[WARN] Warnings:"))
                    for warning in warnings:
                        print(f"   • {warning}")
                return True  # Success even with warnings
            else:
                print(format_status("[FAIL] Validation failed:"))
                for error in errors:
                    print(f"   • {error}")
                if warnings:
                    print(format_status("[WARN] Additional warnings:"))
                    for warning in warnings:
                        print(f"   • {warning}")
                return False

        except Exception as e:
            logger.exception("Validate command failed")
            print(format_status(f"[ERROR] Error during validation: {e}"))
            return False


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Easy switching between git user configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitswitch                    # Interactive account switching
  gitswitch 2                  # Switch directly to account #2
  gitswitch work               # Switch to account matching "work"
  gitswitch add                # Add a new account
  gitswitch edit 2             # Edit account #2
  gitswitch remove             # Remove an account
  gitswitch list               # List all accounts
  gitswitch status             # Show current git configuration scope
  gitswitch config             # Edit config file in $EDITOR
  gitswitch doctor             # Run comprehensive health check
  gitswitch validate           # Validate configuration and accounts
        """,
    )

    # Scope arguments
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument("--global", action="store_true", help="Set git configuration globally")
    scope_group.add_argument("--local", action="store_true", help="Set git configuration locally")

    # Color arguments
    color_group = parser.add_mutually_exclusive_group()
    color_group.add_argument("--color", action="store_true", help="Force color output")
    color_group.add_argument("--no-color", action="store_true", help="Disable color output")

    # Debug and logging options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    # Main command argument
    parser.add_argument("command", nargs="?", help="Command to execute, account number/name to switch to")
    parser.add_argument("subcommand", nargs="?", help="Sub-command argument")

    return parser


def main():
    """Main CLI entry point with simplified direct manager usage."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Set up color mode
    if args.color:
        set_color_mode(True)
    elif args.no_color:
        set_color_mode(False)
    # Otherwise use auto-detection

    # Set up logging
    log_level = "DEBUG" if args.debug else ("WARNING" if args.quiet else "INFO")
    setup_logging(level=log_level)

    logger.info("Gitswitch started", extra={"command": args.command})

    # Create CLI instance
    cli = GitSwitchCLI()

    # Determine scope override
    scope_override = None
    if getattr(args, "global"):
        scope_override = "global"
    elif args.local:
        scope_override = "local"

    success = True

    try:
        if args.command:
            command = args.command.lower()

            # Command dispatch
            command_handlers = {
                "add": lambda: cli.handle_add_command(),
                "edit": lambda: cli.handle_edit_command(args.subcommand),
                "remove": lambda: cli.handle_remove_command(args.subcommand),
                "list": lambda: cli.handle_list_command(),
                "status": lambda: cli.handle_status_command(),
                "config": lambda: cli.handle_config_command(),
                "doctor": lambda: cli.handle_doctor_command(),
                "validate": lambda: cli.handle_validate_command(args.subcommand),
            }

            handler = command_handlers.get(command)
            if handler:
                success = handler()
            else:
                # Try to switch to account
                success = cli._switch_to_account(args.command, scope_override)
        else:
            # Default interactive switching
            success = cli.switch_account_interactive(scope_override)

    except KeyboardInterrupt:
        print("\nGoodbye!")
        success = True  # Ctrl+C is always success
    except GitSwitchError as e:
        logger.warning(f"GitSwitch error: {e}")
        print(format_status(f"[ERROR] {e}"))
        success = False
    except Exception as e:
        logger.exception("Unexpected error in main")
        if args.debug:
            raise
        print(format_status(f"[ERROR] An unexpected error occurred: {e}"))
        success = False

    # Consistent 2-tier exit code system
    sys.exit(0 if success else 1)


def cli():
    """Entry point for the CLI command."""
    main()


if __name__ == "__main__":
    cli()