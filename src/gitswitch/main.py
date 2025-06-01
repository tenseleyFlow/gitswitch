"""Main CLI entry point for gitswitch."""

import argparse
import sys

from .config import load_accounts, get_account_preferred_scope
from .git_ops import set_git_config
from .display import show_accounts, show_current_config, show_config_location, show_scope_status
from .accounts import add_account, remove_account, list_accounts


def switch_account(scope_override=None):
    """Interactive account switching (original functionality)"""
    print("🔄 Git Account Switcher 🔄")
    print("=" * 30)

    # Load accounts from TOML config
    accounts = load_accounts()

    # Show current configuration
    show_current_config()

    # show available accounts
    show_accounts(accounts)

    # Show config file location
    show_config_location()

    # grab user choice
    account_numbers = sorted(accounts.keys())
    choice_range = f"1-{max(account_numbers)}" if account_numbers else "no accounts"

    try:
        choice = input(f"Enter account number ({choice_range}) or 'q' to quit: ").strip().lower()

        if choice == 'q':
            print("👋 buhbye!")
            return

        choice_num = int(choice)

        if choice_num in accounts:
            account = accounts[choice_num]
            # Use scope override if provided, otherwise use account's preferred scope
            scope = scope_override or get_account_preferred_scope(account)
            set_git_config(account, scope)
        else:
            valid_choices = ", ".join(map(str, account_numbers))
            print(f"❌ Invalid choice: {choice_num}. Please enter one of: {valid_choices}")

    except ValueError:
        print(f"❌ Invalid input. Please enter a number ({choice_range}) or 'q' to quit.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def switch_to_account(account_num, scope_override=None):
    """Directly switch to a specific account number"""
    accounts = load_accounts()

    if account_num not in accounts:
        print(f"❌ Account #{account_num} not found")
        print("\nAvailable accounts:")
        show_accounts(accounts)
        return

    account = accounts[account_num]
    scope = scope_override or get_account_preferred_scope(account)
    set_git_config(account, scope)


def main():
    """Main CLI entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Easy switching between git user configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gitswitch                    # Interactive account switching
  gitswitch 2                  # Switch directly to account #2
  gitswitch add                # Add a new account
  gitswitch remove             # Remove an account
  gitswitch list               # List all accounts
  gitswitch status             # Show current git configuration scope
  gitswitch --global 1         # Switch to account #1 globally
  gitswitch --local 2          # Switch to account #2 locally
        """
    )

    # Scope arguments
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        '--global', 
        action='store_true', 
        help='Set git configuration globally'
    )
    scope_group.add_argument(
        '--local', 
        action='store_true', 
        help='Set git configuration locally (current repo only)'
    )

    parser.add_argument(
        'command', 
        nargs='?', 
        help='Command to execute or account number to switch to'
    )

    args = parser.parse_args()

    # Determine scope
    scope_override = None
    # args.global is a reserved word, so use getattr
    if getattr(args, 'global'):
        scope_override = "global"
    elif args.local:
        scope_override = "local"

    try:
        if args.command:
            # Check if command is a number (direct account switch)
            try:
                account_num = int(args.command)
                switch_to_account(account_num, scope_override)
                return
            except ValueError:
                # Not a number, treat as a command
                pass

            # Handle string commands
            if args.command == 'add':
                add_account()
            elif args.command == 'remove':
                remove_account()
            elif args.command == 'list':
                list_accounts()
                show_config_location()
            elif args.command == 'status':
                show_scope_status()
            else:
                print(f"❌ Unknown command: {args.command}")
                parser.print_help()
        else:
            # Default interactive switching
            switch_account(scope_override)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


def cli():
    """Entry point for the CLI command"""
    main()


if __name__ == "__main__":
    cli()
