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
            print("🔄 Git Account Switcher 🔄")
            print(SEPARATOR_SHORT)

            # Load accounts once and reuse
            try:
                accounts = self.account_manager.get_accounts()
            except Exception as e:
                print(f"❌ Error loading accounts: {e}")
                return False

            if not accounts:
                print(MSG_NO_ACCOUNTS)
                print("   Run 'gitswitch add' to create your first account")
                return False

            # Show current config and accounts using loaded data
            self.display.show_current_config()
            self.display.show_accounts(accounts)  # Pass accounts to avoid reload
            self.display.show_config_location()

            # Get user choice
            account_numbers = sorted(accounts.keys())
            choice_range = f"1-{max(account_numbers)}" if account_numbers else "no accounts"

            choice = input(f"Enter account number or search term ({choice_range}) or 'q' to quit: ").strip()

            if choice.lower() == "q":
                print("👋 Goodbye!")
                return True

            # Switch to account directly
            return self._switch_to_account(choice, scope_override, accounts)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return True
        except Exception as e:
            logger.exception("Interactive switching failed")
            print(f"❌ Error during account switching: {e}")
            return False

    def _switch_to_account(self, identifier: str, scope_override: Optional[str] = None, accounts: Optional[Dict] = None) -> bool:
        """Switch to a specific account using direct manager calls."""
        try:
            # Use provided accounts or fetch if not provided
            if accounts is None:
                accounts = self.account_manager.get_accounts()
            
            # Get account directly (now using the updated method signature)
            account_num, account_data = self.account_manager.get_account(identifier, accounts)

            # Validate account data
            is_valid, errors, warnings = self.validation_service.validate_account(account_data)
            if not is_valid:
                print(f"❌ Account validation failed: {'; '.join(errors)}")
                return False

            # Determine scope
            scope = scope_override or account_data.get("preferred_scope", "local")

            # Switch using git operations directly
            success = self.git_ops.set_git_config(account_data, scope)
            if not success:
                print("❌ Failed to set git configuration")
                return False

            # Display success
            self._print_switch_success(account_num, account_data, scope)
            return True

        except AccountNotFoundError as e:
            print(f"❌ {e}")

            # Show available accounts to help user (reuse accounts if available)
            if accounts is None:
                try:
                    accounts = self.account_manager.get_accounts()
                except:
                    accounts = {}
            
            if accounts:
                print("\nAvailable accounts:")
                self.display.show_accounts(accounts)

            return False

        except ValidationError as e:
            print(f"❌ {e}")
            return False

        except Exception as e:
            logger.exception("Account switching failed")
            print(f"❌ Error switching to account: {e}")
            return False

    def _print_switch_success(self, account_num: int, account_data: dict, scope: str):
        """Print successful account switch information."""
        print(f"✅ Successfully switched to: {account_data['description']} ({scope})")
        print(f"   Name: {account_data['name']}")
        print(f"   Email: {account_data['email']}")
        print(f"   Scope: {scope}")

        # Show GPG status
        gpg_key = account_data.get("gpg_key", "")
        signing_enabled = account_data.get("signing_enabled", False)
        if gpg_key and signing_enabled:
            print(f"   GPG Key: {gpg_key}")
            print(f"   GPG Signing: ✅ Enabled")
        else:
            print("   GPG Signing: ❌ Disabled")

        # Show SSH status
        ssh_key = account_data.get("ssh_key", "")
        if ssh_key:
            ssh_host = account_data.get("ssh_host", "")
            host_text = f" (host: {ssh_host})" if ssh_host else ""
            print(f"   SSH Key: {ssh_key}{host_text}")
        else:
            print("   SSH: ❌ Not configured")

    def handle_add_command(self) -> bool:
        """Handle the add account command using direct manager calls."""
        try:
            from .interactive import add_account_interactive

            return add_account_interactive(self.account_manager, self.validation_service, self.git_ops)
        except Exception as e:
            logger.exception("Add account command failed")
            print(f"❌ Error adding account: {e}")
            return False

    def handle_edit_command(self, identifier: str = None) -> bool:
        """Handle the edit account command using direct manager calls."""
        try:
            from .interactive import edit_account_interactive

            return edit_account_interactive(self.account_manager, self.validation_service, identifier)
        except Exception as e:
            logger.exception("Edit account command failed")
            print(f"❌ Error editing account: {e}")
            return False

    def handle_remove_command(self, identifier: str = None) -> bool:
        """Handle the remove account command using direct manager calls."""
        try:
            from .interactive import remove_account_interactive

            return remove_account_interactive(self.account_manager, self.display, identifier)
        except Exception as e:
            logger.exception("Remove account command failed")
            print(f"❌ Error removing account: {e}")
            return False

    def handle_list_command(self) -> bool:
        """Handle the list accounts command using direct manager calls."""
        try:
            accounts = self.account_manager.get_accounts()

            if not accounts:
                print(MSG_NO_ACCOUNTS)
                print("   Please run 'gitswitch add' to create your first account")
                return False

            self.display.show_accounts(accounts)
            self.display.show_config_location()
            return True

        except Exception as e:
            logger.exception("List accounts command failed")
            print(f"❌ Error listing accounts: {e}")
            return False

    def handle_status_command(self) -> bool:
        """Handle the status command using direct manager calls."""
        try:
            self.display.show_scope_status()
            return True
        except Exception as e:
            logger.exception("Status command failed")
            print(f"❌ Error showing status: {e}")
            return False

    def handle_config_command(self) -> bool:
        """Handle the config command using direct manager calls."""
        try:
            from .interactive import edit_config_file_interactive

            return edit_config_file_interactive(self.config_manager)
        except Exception as e:
            logger.exception("Config command failed")
            print(f"❌ Error editing config: {e}")
            return False

    def handle_doctor_command(self) -> bool:
        """Handle the doctor command using direct manager calls."""
        try:
            from .doctor import run_health_check

            return run_health_check(self.config_manager, self.account_manager, self.git_ops, self.validation_service)
        except Exception as e:
            logger.exception("Doctor command failed")
            print(f"❌ Error running health check: {e}")
            return False

    def handle_validate_command(self, target: str = None) -> bool:
        """Handle validation command using direct manager calls."""
        try:
            if target == "config":
                config = self.config_manager.load_config()
                is_valid, errors, warnings = self.validation_service.validate_config(config)
            elif target == "system":
                is_valid, errors, warnings = self.validation_service.validate_system_requirements()
            elif target and target.isdigit():
                # Validate specific account
                account_num, account_data = self.account_manager.get_account(target)
                is_valid, errors, warnings = self.validation_service.validate_account(account_data)
            else:
                # Validate everything - streamlined inline version
                print("🔍 Running comprehensive validation...")

                all_valid = True

                # System validation
                print("\n🔧 System Requirements:")
                sys_valid, sys_errors, _ = self.validation_service.validate_system_requirements()
                if sys_valid:
                    print("✅ All required tools found")
                else:
                    print("❌ Missing tools:")
                    for error in sys_errors:
                        print(f"   • {error}")
                    all_valid = False

                # Config validation
                print("\n📁 Configuration:")
                try:
                    config = self.config_manager.load_config()
                    cfg_valid, cfg_errors, _ = self.validation_service.validate_config(config)
                    if cfg_valid:
                        print("✅ Configuration is valid")
                    else:
                        print("❌ Configuration issues:")
                        for error in cfg_errors:
                            print(f"   • {error}")
                        all_valid = False
                except Exception as e:
                    print(f"❌ Could not load configuration: {e}")
                    all_valid = False

                # Account validation
                print("\n👤 Accounts:")
                try:
                    accounts = self.account_manager.get_accounts()
                    if accounts:
                        for num, account in accounts.items():
                            acc_valid, acc_errors, _ = self.validation_service.validate_account(account)
                            status = "✅" if acc_valid else "❌"
                            print(f"   {status} Account #{num}: {account.get('description', 'No description')}")
                            if not acc_valid:
                                for error in acc_errors:
                                    print(f"      • {error}")
                                all_valid = False
                    else:
                        print("   ⚠️  No accounts configured")
                except Exception as e:
                    print(f"   ❌ Error checking accounts: {e}")
                    all_valid = False

                return all_valid

            # Handle single validation results
            if is_valid:
                print("✅ Validation passed")
            else:
                print("❌ Validation failed:")
                for error in errors:
                    print(f"   • {error}")

            if warnings:
                print("⚠️  Warnings:")
                for warning in warnings:
                    print(f"   • {warning}")

            return is_valid

        except Exception as e:
            logger.exception("Validate command failed")
            print(f"❌ Error during validation: {e}")
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
        print("\n👋 Goodbye!")
        success = True
    except GitSwitchError as e:
        logger.warning(f"GitSwitch error: {e}")
        print(f"❌ {e}")
        success = False
    except Exception as e:
        logger.exception("Unexpected error in main")
        if args.debug:
            raise
        print(f"❌ An unexpected error occurred: {e}")
        success = False

    sys.exit(0 if success else 1)


def cli():
    """Entry point for the CLI command."""
    main()


if __name__ == "__main__":
    cli()