"""Account management functions for gitswitch."""

import sys
from .config import load_config, save_config, load_accounts
from .display import show_accounts
from .git_ops import validate_gpg_key


def get_next_account_number(accounts):
    """Get the next available account number"""
    if not accounts:
        return 1
    return max(accounts.keys()) + 1


def search_accounts(query, accounts):
    """Search for accounts by description, name, or email"""
    if not query:
        return []

    query = query.lower().strip()
    matches = []

    for account_num, account in accounts.items():
        # Search in description, name, and email
        searchable_text = [
            account.get('description', ''),
            account.get('name', ''),
            account.get('email', '')
        ]

        # Check if query matches any field (case-insensitive, partial match)
        for text in searchable_text:
            if query in text.lower():
                matches.append((account_num, account))
                break  # Don't add the same account multiple times

    return matches


def find_account(identifier, accounts):
    """Find account by number or search term. Returns (account_num, account) or None"""
    # Try to parse as number first
    try:
        account_num = int(identifier)
        if account_num in accounts:
            return account_num, accounts[account_num]
        else:
            return None
    except ValueError:
        pass

    # Search by text
    matches = search_accounts(identifier, accounts)

    if len(matches) == 0:
        print(f"❌ No accounts found matching '{identifier}'")
        print("\nAvailable accounts:")
        show_accounts(accounts)
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        # Multiple matches - let user choose
        print(f"🔍 Multiple accounts found matching '{identifier}':")
        print()
        for i, (account_num, account) in enumerate(matches, 1):
            print(f"{i}. #{account_num}: {account['description']}")
            print(f"   {account['name']} <{account['email']}>")
        print()

        try:
            choice = input(f"Select account (1-{len(matches)}) or 'q' to cancel: ").strip()
            if choice.lower() == 'q':
                return None

            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(matches):
                return matches[choice_idx]
            else:
                print("❌ Invalid selection")
                return None
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Cancelled")
            return None


def prompt_for_gpg_config(current_key=None, current_enabled=False):
    """Prompt user for GPG configuration with current values as defaults"""
    print("\n🔐 GPG Signing Configuration:")

    # Show current values
    if current_key:
        print(f"   Current GPG key: {current_key}")
        print(f"   Current signing: {'✅ Enabled' if current_enabled else '❌ Disabled'}")
    else:
        print("   Current GPG: ❌ Not configured")

    # Ask if they want GPG signing
    enable_prompt = f"Enable GPG signing? ({'Y/n' if current_enabled else 'y/N'}): "
    enable_input = input(enable_prompt).strip()

    # Determine if enabling based on current state and input
    if current_enabled:
        enable_signing = enable_input.lower() not in ['n', 'no', 'false']
    else:
        enable_signing = enable_input.lower() in ['y', 'yes', 'true']

    if not enable_signing:
        return None, False

    # Get GPG key
    print("\nTo find your GPG key ID, run: gpg --list-secret-keys --keyid-format=long")
    key_prompt = f"GPG key ID [{current_key or 'none'}]: "
    gpg_key = input(key_prompt).strip()

    # Use current key if nothing entered
    if not gpg_key and current_key:
        gpg_key = current_key

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


def edit_account():
    """Interactively edit an existing account"""
    print("✏️  Edit Git Account")
    print("=" * 30)

    # Load accounts
    accounts = load_accounts()

    # Get account to edit
    identifier = input("Enter account number or search term: ").strip()
    if not identifier:
        print("❌ No identifier provided")
        return False

    account_info = find_account(identifier, accounts)
    if not account_info:
        return False

    account_num, account = account_info

    print(f"\n📝 Editing Account #{account_num}: {account['description']}")
    print("=" * 50)
    print("Press Enter to keep current value, or type new value:")
    print()

    try:
        # Edit basic fields
        current_name = account.get('name', '')
        new_name = input(f"Name [{current_name}]: ").strip()
        if not new_name:
            new_name = current_name
        elif not new_name:
            print("❌ Name cannot be empty")
            return False

        current_email = account.get('email', '')
        new_email = input(f"Email [{current_email}]: ").strip()
        if not new_email:
            new_email = current_email
        elif "@" not in new_email:
            print("❌ Please enter a valid email address")
            return False

        current_description = account.get('description', '')
        new_description = input(f"Description [{current_description}]: ").strip()
        if not new_description:
            new_description = current_description

        # Edit scope
        current_scope = account.get('preferred_scope', 'local')
        print(f"\nScope options: local (current repo only) or global (all repos)")
        new_scope = input(f"Preferred scope [{current_scope}]: ").strip().lower()
        if not new_scope:
            new_scope = current_scope
        elif new_scope not in ['local', 'global']:
            print(f"❌ Invalid scope '{new_scope}', keeping '{current_scope}'")
            new_scope = current_scope

        # Edit GPG configuration
        current_gpg_key = account.get('gpg_key')
        current_signing = account.get('signing_enabled', False)
        new_gpg_key, new_signing = prompt_for_gpg_config(current_gpg_key, current_signing)

        # Show summary of changes
        print(f"\n📋 Summary of Changes for Account #{account_num}:")
        print("=" * 50)

        changes = []
        if new_name != current_name:
            changes.append(f"Name: '{current_name}' → '{new_name}'")
        if new_email != current_email:
            changes.append(f"Email: '{current_email}' → '{new_email}'")
        if new_description != current_description:
            changes.append(f"Description: '{current_description}' → '{new_description}'")
        if new_scope != current_scope:
            changes.append(f"Scope: '{current_scope}' → '{new_scope}'")
        if new_gpg_key != current_gpg_key:
            changes.append(f"GPG Key: '{current_gpg_key or 'none'}' → '{new_gpg_key or 'none'}'")
        if new_signing != current_signing:
            changes.append(f"GPG Signing: {'✅' if current_signing else '❌'} → {'✅' if new_signing else '❌'}")

        if not changes:
            print("No changes made.")
            return True

        for change in changes:
            print(f"   {change}")

        print()
        confirm = input("Save these changes? (Y/n): ").strip().lower()
        if confirm in ['n', 'no']:
            print("❌ Changes cancelled")
            return False

        # Apply changes
        updated_account = {
            "name": new_name,
            "email": new_email,
            "description": new_description,
            "preferred_scope": new_scope,
            "signing_enabled": new_signing
        }

        if new_gpg_key:
            updated_account["gpg_key"] = new_gpg_key

        # Save to config
        config = load_config()
        config['accounts'][str(account_num)] = updated_account

        if save_config(config):
            print(f"\n✅ Successfully updated account #{account_num}")
            return True
        else:
            print("❌ Failed to save changes")
            return False

    except KeyboardInterrupt:
        print("\n❌ Editing cancelled")
        return False


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
            "preferred_scope": scope,
            "signing_enabled": signing_enabled
        }

        # Add GPG config if provided
        if gpg_key:
            new_account["gpg_key"] = gpg_key

        # Convert back to string keys for TOML
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
        identifier = input("Enter account number or search term to remove (or 'q' to cancel): ").strip()

        if identifier.lower() == 'q':
            print("❌ Removal cancelled")
            return False

        account_info = find_account(identifier, accounts)
        if not account_info:
            return False

        account_num, account = account_info

        # Show account to be removed
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
        print("❌ Invalid input")
        return False
    except KeyboardInterrupt:
        print("\n❌ Removal cancelled")
        return False


def list_accounts():
    """List all accounts"""
    accounts = load_accounts()
    show_accounts(accounts)
