"""Main CLI entry point for gitswitch."""

import argparse
import sys

from .config import load_accounts
from .git_ops import set_git_config
from .display import show_accounts, show_current_config, show_config_location
from .accounts import add_account, remove_account, list_accounts


def switch_account():
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
            set_git_config(accounts[choice_num])
        else:
            valid_choices = ", ".join(map(str, account_numbers))
            print(f"❌ Invalid choice: {choice_num}. Please enter one of: {valid_choices}")

    except ValueError:
        print(f"❌ Invalid input. Please enter a number ({choice_range}) or 'q' to quit.")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


def main():
    """Main CLI entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Easy switching between git user configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  gitswitch              # Interactive account switching
  gitswitch add          # Add a new account
  gitswitch remove       # Remove an account
  gitswitch list         # List all accounts
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['add', 'remove', 'list'], 
        help='Command to execute (default: interactive switch)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'add':
            add_account()
        elif args.command == 'remove':
            remove_account()
        elif args.command == 'list':
            list_accounts()
            show_config_location()
        else:
            # Default interactive switching
            switch_account()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


def cli():
    """Entry point for the CLI command"""
    main()


if __name__ == "__main__":
    cli()
