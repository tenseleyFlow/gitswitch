#!/usr/bin/env python3
import subprocess
import sys
import argparse
from pathlib import Path

# Handle TOML parsing for different Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # allback for older Python versions

# For writing TOML files
try:
    import tomli_w
except ImportError:
    print("❌ tomli_w is required for add/remove functionality")
    print("   Install with: pip install tomli_w")
    sys.exit(1)


def get_config_path():
    """Grab the path to the configuration file"""
    config_dir = Path.home() / ".config" / "gitswitch"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "accounts.toml"


def create_default_config(config_path):
    """Create a default configuration file"""
    default_config = """# Git Switcher Account Configuration
# Add your git accounts here

[accounts.1]
name = "You"
email = "your@email.com"
description = "Default Account"

# Add more as follows:
#   [accounts.2]
#   name = "your/user name"
#   email = "account email"
#   description = "Account description"
#
"""

    with open(config_path, 'w') as f:
        f.write(default_config)

    print(f"📝 Created default config file at: {config_path}")
    print("   You can edit this file to customize your accounts!")
    return True


def load_config():
    """Load the full configuration from TOML file"""
    config_path = get_config_path()

    if not config_path.exists():
        print("🔧 No configuration file found.")
        create_default_config(config_path)

    try:
        with open(config_path, 'rb') as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"❌ Error loading configuration file: {e}")
        print(f"   Config file: {config_path}")
        sys.exit(1)


def save_config(config):
    """Save configuration to TOML file"""
    config_path = get_config_path()
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
        return True
    except Exception as e:
        print(f"❌ Error saving configuration file: {e}")
        return False


def load_accounts():
    """Load accounts from TOML configuration file"""
    config = load_config()

    # Convert string keys to integers for backwards compatibility
    accounts = {}
    for key, value in config.get('accounts', {}).items():
        try:
            accounts[int(key)] = value
        except ValueError:
            print(f"⚠️  Skipping invalid account key: {key} (must be a number)")

    if not accounts:
        print("⚠️  No valid accounts found in configuration file!")
        print(f"   Please edit: {get_config_path()}")
        sys.exit(1)

    return accounts


def get_next_account_number(accounts):
    """Grab the next available account number"""
    if not accounts:
        return 1
    return max(accounts.keys()) + 1


def add_account():
    """Interactively add a new account"""
    print("➕ Adding New Git Account")
    print("=" * 30)

    # grab account details
    try:
        name = input("Enter name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return False

        email = input("Enter email: ").strip()
        if not email or "@" not in email:
            print("❌ Please enter a valid email address")
            return False

        description = input("Enter description: ").strip()
        if not description:
            description = f"{name} ({email})"

        config = load_config()
        if 'accounts' not in config:
            config['accounts'] = {}

        # Convert to int keys for processing
        accounts = {}
        for key, value in config['accounts'].items():
            try:
                accounts[int(key)] = value
            except ValueError:
                continue

        account_num = get_next_account_number(accounts)

        new_account = {
            "name": name,
            "email": email,
            "description": description
        }

        # Convert back to string keys for TOML
        config['accounts'][str(account_num)] = new_account

        # Save config
        if save_config(config):
            print(f"✅ Successfully added account #{account_num}:")
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Description: {description}")
            return True
        else:
            print("❌ Failed to save account")
            return False

    except KeyboardInterrupt:
        print("\n❌ Account creation cancelled")
        return False


def remove_account():
    """Interactively remove an account"""
    print("➖ Remove Git Account")
    print("=" * 30)

    # Load and show current accounts
    accounts = load_accounts()
    print("\nCurrent accounts:")
    for num, account in sorted(accounts.items()):
        print(f"{num}. {account['description']}")
        print(f"   Name: {account['name']}")
        print(f"   Email: {account['email']}")
        print()

    try:
        choice = input("Enter account number to remove (or 'q' to cancel): ").strip().lower()

        if choice == 'q':
            print("❌ Removal cancelled")
            return False

        account_num = int(choice)

        if account_num not in accounts:
            print(f"❌ Account #{account_num} not found")
            return False

        # show account to be removed
        account = accounts[account_num]
        print(f"\n⚠️  About to remove account #{account_num}:")
        print(f"   Name: {account['name']}")
        print(f"   Email: {account['email']}")
        print(f"   Description: {account['description']}")

        confirm = input("\nAre you sure? (y/N): ").strip().lower()

        if confirm != 'y':
            print("❌ Removal cancelled")
            return False

        # load full config and remove account
        config = load_config()
        if str(account_num) in config.get('accounts', {}):
            del config['accounts'][str(account_num)]

            if save_config(config):
                print(f"✅ Successfully removed account #{account_num}")
                return True
            else:
                print("❌ Failed to save changes")
                return False
        else:
            print(f"❌ Account #{account_num} not found in config")
            return False

    except ValueError:
        print("❌ Invalid account number")
        return False
    except KeyboardInterrupt:
        print("\n❌ Removal cancelled")
        return False


def run_git_command(command):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(command, shell=True,
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None


def get_current_config():
    """Get current git user configuration"""
    name = run_git_command("git config user.name")
    email = run_git_command("git config user.email")
    return name, email


def set_git_config(account_info):
    """Set git user configuration"""
    name_cmd = f'git config user.name "{account_info["name"]}"'
    email_cmd = f'git config user.email "{account_info["email"]}"'

    if (run_git_command(name_cmd) is not None
        and run_git_command(email_cmd) is not None):
        print(f"✅ Successfully switched to: {account_info['description']}")
        print(f"   Name: {account_info['name']}")
        print(f"   Email: {account_info['email']}")
        return True
    else:
        print("❌ Failed to set git configuration")
        return False


def show_accounts(accounts):
    """Display available accounts"""
    print("\n📋 Available Git Accounts 📋")
    print("=" * 40)
    for num, account in sorted(accounts.items()):
        print(f"{num}. {account['description']}")
        print(f"   Name: {account['name']}")
        print(f"   Email: {account['email']}")
        print()


def show_current_config():
    """Display current git configuration"""
    name, email = get_current_config()
    if name and email:
        print(f"\n🔍 Current Git Configuration 🔍")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
    else:
        print("\n⚠️  No git configuration found or error reading config")


def show_config_location():
    """Show where the config file is located"""
    config_path = get_config_path()
    print(f"\n⚙️  Config file location: {config_path}")


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
Examples:
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
            accounts = load_accounts()
            show_accounts(accounts)
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
