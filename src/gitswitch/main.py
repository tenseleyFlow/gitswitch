"""Main CLI entry point for gitswitch."""

import argparse
import sys

from .config import load_accounts, get_account_preferred_scope
from .git_ops import set_git_config
from .display import show_accounts, show_current_config, show_config_location, show_scope_status
from .accounts import add_account, remove_account, list_accounts, edit_account, find_account


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
        choice = input(f"Enter account number or search term ({choice_range}) or 'q' to quit: ").strip()

        if choice.lower() == 'q':
            print("👋 buhbye!")
            return

        # Try to find account (by number or search)
        account_info = find_account(choice, accounts)
        if account_info:
            account_num, account = account_info
            # Use scope override if provided, otherwise use account's preferred scope
            scope = scope_override or get_account_preferred_scope(account)
            set_git_config(account, scope)
        # If find_account returns None, it already printed error messages

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def switch_to_account(identifier, scope_override=None):
    """Directly switch to a specific account by number or search term"""
    accounts = load_accounts()
    
    account_info = find_account(identifier, accounts)
    if not account_info:
        return  # error already printed by find_account
    
    account_num, account = account_info
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
  gitswitch work               # Switch to account matching "work"
  gitswitch add                # Add a new account
  gitswitch edit 2             # Edit account #2
  gitswitch edit work          # Edit account matching "work"
  gitswitch remove             # Remove an account
  gitswitch list               # List all accounts
  gitswitch status             # Show current git configuration scope
  gitswitch --global work      # Switch to "work" account globally
  gitswitch --local personal   # Switch to "personal" account locally
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
        help='Command to execute, account number/name to switch to'
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
            # Handle specific commands first
            if args.command == 'add':
                add_account()
            elif args.command == 'edit':
                edit_account()
            elif args.command == 'remove':
                remove_account()
            elif args.command == 'list':
                list_accounts()
                show_config_location()
            elif args.command == 'status':
                show_scope_status()
            else:
                # Try to switch to account (by number or search term)
                switch_to_account(args.command, scope_override)
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
