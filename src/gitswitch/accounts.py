"""Account management functions for gitswitch."""

import sys
from .config import load_config, save_config, load_accounts
from .display import show_accounts
from .git_ops import validate_gpg_key


def get_next_account_number(accounts):
    """Grab the next available account number"""
    if not accounts:
        return 1
    return max(accounts.keys()) + 1


def prompt_for_gpg_config():
    """Prompt user for GPG configuration"""
    print("\n🔐 GPG Signing Configuration (optional):")

    enable_signing = input("Enable GPG signing for this account? (y/N): ").strip().lower()

    if enable_signing != 'y':
        return None, False

    # grab GPG key
    print("\nTo find your GPG key ID, run: gpg --list-secret-keys --keyid-format=long")
    gpg_key = input("Enter GPG key ID (or press Enter to skip): ").strip()

    if not gpg_key:
        return None, False

    # Validate the key
    is_valid, message = validate_gpg_key(gpg_key)
    if not is_valid:
        print(f"⚠️  Warning: {message}")
        use_anyway = input("Use this key anyway? (y/N): ").strip().lower()
        if use_anyway != 'y':
            return None, False
    else:
        print(f"✅ {message}")

    return gpg_key, True


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

        # get scope preference
        print("\nScope options: local (current repo only) or global (all repos)")
        scope = input("Preferred scope (local/global) [local]: ").strip().lower()
        if scope not in ['local', 'global']:
            scope = 'local'

        # Get GPG configuration
        gpg_key, signing_enabled = prompt_for_gpg_config()

        # load existing config
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

        # Get next account number
        account_num = get_next_account_number(accounts)

        # add new account
        new_account = {
            "name": name,
            "email": email,
            "description": description,
            "preferred_scope": scope
        }

        # Add GPG config if provided
        if gpg_key:
            new_account["gpg_key"] = gpg_key
        new_account["signing_enabled"] = signing_enabled

        # convert back to string keys for TOML
        config['accounts'][str(account_num)] = new_account

        # Save config
        if save_config(config):
            print(f"\n✅ Successfully added account #{account_num}:")
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Description: {description}")
            print(f"   Scope: {scope}")
            if gpg_key:
                print(f"   GPG Key: {gpg_key}")
            print(f"   GPG Signing: {'✅ Enabled' if signing_enabled else '❌ Disabled'}")
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
    show_accounts(accounts)

    try:
        choice = input("Enter account number to remove (or 'q' to cancel): ").strip().lower()

        if choice == 'q':
            print("❌ Removal cancelled")
            return False

        account_num = int(choice)

        if account_num not in accounts:
            print(f"❌ Account #{account_num} not found")
            return False

        # Show account to be removed
        account = accounts[account_num]
        print(f"\n⚠️  About to remove account #{account_num}:")
        print(f"   Name: {account['name']}")
        print(f"   Email: {account['email']}")
        print(f"   Description: {account['description']}")

        gpg_key = account.get('gpg_key')
        if gpg_key:
            print(f"   GPG Key: {gpg_key}")

        confirm = input("\nAre you sure? (y/N): ").strip().lower()

        if confirm != 'y':
            print("❌ Removal cancelled")
            return False

        # Load full config and remove account
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


def list_accounts():
    """List all accounts"""
    accounts = load_accounts()
    show_accounts(accounts)
