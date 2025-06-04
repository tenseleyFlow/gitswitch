"""Simple interactive functions for gitswitch."""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

from .constants import *
from .exceptions import AccountNotFoundError
from .utils import safe_input, validate_email
from .colors import format_status, format_header, format_accent

logger = logging.getLogger(__name__)


def collect_account_info(validation_service, current: Optional[Dict] = None) -> Dict:
    """Collect all account information in one function."""
    account_data = {}

    # === BASIC INFO ===
    # Name
    if current:
        name = safe_input(f"Name [{current.get('name', '')}]: ")
        account_data["name"] = name if name else current.get("name", "")
    else:
        name = safe_input("Enter name: ")
        if not name:
            print(format_status(ERR_EMPTY_NAME))
            return {}
        account_data["name"] = name

    # Email
    if current:
        email = safe_input(f"Email [{current.get('email', '')}]: ")
        email = email if email else current.get("email", "")
    else:
        email = safe_input("Enter email: ")

    if not validate_email(email):
        print(format_status(ERR_INVALID_EMAIL))
        if current:
            account_data["email"] = current.get("email", "")
        else:
            return {}
    else:
        account_data["email"] = email

    # Description
    if current:
        desc = safe_input(f"Description [{current.get('description', '')}]: ")
        account_data["description"] = desc if desc else current.get("description", "")
    else:
        desc = safe_input("Enter description: ")
        account_data["description"] = desc if desc else f"{account_data['name']} ({account_data['email']})"

    # Scope
    print(f"\n{format_header('Scope options')}: local (current repo only) or global (all repos)")
    if current:
        current_scope = current.get("preferred_scope", DEFAULT_SCOPE)
        scope = safe_input(f"Preferred scope [{format_accent(current_scope)}]: ").lower()
        if scope and scope not in VALID_SCOPES:
            print(format_status(f"[ERROR] Invalid scope '{scope}', keeping '{current_scope}'"))
            scope = current_scope
        account_data["preferred_scope"] = scope if scope else current_scope
    else:
        scope = safe_input("Preferred scope (local/global) [local]: ").lower()
        account_data["preferred_scope"] = scope if scope in VALID_SCOPES else DEFAULT_SCOPE

    # === GPG CONFIG ===
    print(f"\n── {format_header('GPG Signing Configuration')} (optional) ──")

    if current:
        current_key = current.get("gpg_key", "")
        current_signing = current.get("signing_enabled", False)
        if current_key:
            status = format_status("[ENABLED]") if current_signing else format_status("[DISABLED]")
            print(f"   Current: {current_key} ({status})")
        enable_signing = ask_yes_no("Enable GPG signing?", default=current_signing)
    else:
        enable_signing = ask_yes_no("Enable GPG signing?", default=False)

    if enable_signing:
        if not current:
            print(f"\n{format_accent('To find your GPG key ID, run')}: gpg --list-secret-keys --keyid-format=long")

        key_prompt = "GPG key ID: " if not current else f"GPG key ID [{current.get('gpg_key', 'none')}]: "
        gpg_key = safe_input(key_prompt).strip()

        if current and not gpg_key:
            gpg_key = current.get("gpg_key", "")

        if gpg_key:
            # Quick validation using correct method name
            if validation_service._check_gpg_key_safe(gpg_key):
                account_data["gpg_key"] = gpg_key
                account_data["signing_enabled"] = True
                key_info = validation_service.get_gpg_key_info(gpg_key)
                print(format_status(f"[OK] {key_info}"))
            else:
                print(format_status(f"[WARN] Warning: GPG key not found"))
                if ask_yes_no("Use this key anyway?", default=False):
                    account_data["gpg_key"] = gpg_key
                    account_data["signing_enabled"] = True
                else:
                    account_data["signing_enabled"] = False
        else:
            account_data["signing_enabled"] = False
    else:
        account_data["gpg_key"] = ""
        account_data["signing_enabled"] = False

    # === SSH CONFIG ===
    print(f"\n── {format_header('SSH Configuration')} (optional) ──")

    if current:
        current_key = current.get("ssh_key", "")
        if current_key:
            print(f"   Current: {current_key}")
        configure = ask_yes_no("Configure SSH key?", default=bool(current_key))
    else:
        configure = ask_yes_no("Configure SSH key for this account?", default=False)

    if configure:
        if not current:
            print(f"\n{format_accent('SSH key should be the path to your private key file')}")
            print(f"{format_accent('Example')}: ~/.ssh/id_rsa_personal")

        key_prompt = "SSH key path: " if not current else f"SSH key path [{current.get('ssh_key', 'none')}]: "
        ssh_key = safe_input(key_prompt).strip()

        if current and not ssh_key:
            ssh_key = current.get("ssh_key", "")

        if ssh_key:
            # Quick validation using correct method name
            if validation_service._check_ssh_key_safe(ssh_key):
                account_data["ssh_key"] = ssh_key
                key_info = validation_service.get_ssh_key_info(ssh_key)
                print(format_status(f"[OK] {key_info}"))
            else:
                print(format_status(f"[WARN] Warning: SSH key file not found or invalid"))
                if ask_yes_no("Use this key anyway?", default=False):
                    account_data["ssh_key"] = ssh_key
                else:
                    account_data["ssh_key"] = ""
                    account_data["ssh_host"] = ""
                    return account_data

            # SSH host
            if not current:
                print(f"\n{format_accent('Optional')}: Custom SSH host (for multiple GitHub accounts)")
                print(f"{format_accent('Example')}: github.com-work (requires ~/.ssh/config setup)")

            host_prompt = (
                "SSH host [default]: " if not current else f"SSH host [{current.get('ssh_host', 'default')}]: "
            )
            ssh_host = safe_input(host_prompt).strip()

            if current and not ssh_host:
                ssh_host = current.get("ssh_host", "")

            account_data["ssh_host"] = ssh_host
        else:
            account_data["ssh_key"] = ""
            account_data["ssh_host"] = ""
    else:
        account_data["ssh_key"] = ""
        account_data["ssh_host"] = ""

    return account_data


def ask_yes_no(question: str, default: Optional[bool] = None) -> bool:
    """Ask a yes/no question."""
    if default is True:
        prompt = f"{question} (Y/n): "
    elif default is False:
        prompt = f"{question} (y/N): "
    else:
        prompt = f"{question} (y/n): "

    while True:
        try:
            answer = safe_input(prompt).lower().strip()

            if not answer and default is not None:
                return default

            if answer in ["y", "yes", "true", "1"]:
                return True
            elif answer in ["n", "no", "false", "0"]:
                return False
            else:
                print("Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print(format_status("\n[CANCELLED]"))
            # Return the default instead of affecting parent function
            return default if default is not None else False


def display_account_summary(account_data: dict):
    """Display account summary."""
    print(f"   Name: {account_data['name']}")
    print(f"   Email: {account_data['email']}")
    print(f"   Description: {account_data['description']}")
    print(f"   Scope: {format_accent(account_data.get('preferred_scope', DEFAULT_SCOPE))}")

    # GPG info
    gpg_key = account_data.get("gpg_key")
    signing_enabled = account_data.get("signing_enabled", False)
    if gpg_key:
        status = format_status("[ENABLED]") if signing_enabled else format_status("[DISABLED]")
        print(f"   GPG Key: {gpg_key}")
        print(f"   GPG Signing: {status}")
    else:
        print(f"   GPG Signing: {format_status('[DISABLED]')}")

    # SSH info
    ssh_key = account_data.get("ssh_key")
    if ssh_key:
        ssh_host = account_data.get("ssh_host", "")
        host_text = f" (host: {ssh_host})" if ssh_host else ""
        print(f"   SSH Key: {ssh_key}{host_text}")
    else:
        print(f"   SSH: {format_status('[NOT CONFIGURED]')}")


def add_account_interactive(account_manager, validation_service, git_ops) -> bool:
    """Add a new account interactively."""
    print(f"++ {format_header('Adding New Git Account')}")
    print(SEPARATOR_SHORT)

    try:
        # Collect account information
        account_data = collect_account_info(validation_service)
        if not account_data:
            return False

        # Confirm
        print(f"\n-- {format_header('Account Summary')} --")
        print(SEPARATOR_MEDIUM)
        display_account_summary(account_data)

        if not ask_yes_no("Create this account?", default=True):
            print(format_status("[CANCELLED] Account creation cancelled"))
            return True  # User cancellation is success

        # Validate
        is_valid, errors, warnings = validation_service.validate_account(account_data)
        if not is_valid:
            print(format_status(f"[ERROR] Account validation failed: {'; '.join(errors)}"))
            return False

        # Add account using new tuple-returning method
        success, account_num, add_message = account_manager.add_account(account_data)
        if not success:
            print(format_status(f"[ERROR] {add_message}"))
            return False
        
        print(format_status(f"\n[SUCCESS] {add_message}"))
        display_account_summary(account_data)

        # Offer to switch
        if ask_yes_no("Switch to this account now?", default=True):
            scope = account_data.get("preferred_scope", DEFAULT_SCOPE)
            if git_ops.set_git_config(account_data, scope):
                print(f">> Switched to new account ({format_accent(scope)})")
            else:
                print(format_status("[WARN] Account created but failed to switch"))

        return True

    except KeyboardInterrupt:
        print(format_status("\n[CANCELLED] Account creation cancelled"))
        return True  # Ctrl+C is success
    except Exception as e:
        logger.error(f"Account creation failed: {e}")
        print(format_status(f"[ERROR] Error creating account: {e}"))
        return False


def edit_account_interactive(account_manager, validation_service, identifier: Optional[str] = None) -> bool:
    """Edit an existing account interactively."""
    print(f"~~ {format_header('Edit Git Account')}")
    print(SEPARATOR_SHORT)

    try:
        # Get account using new tuple-returning method
        if not identifier:
            identifier = safe_input("Enter account number or search term: ")
            if not identifier:
                print(format_status("[CANCELLED] No identifier provided"))
                return True  # Empty input is user cancellation (success)

        success, account_num, account, get_message = account_manager.get_account(identifier)
        if not success:
            print(format_status(f"[ERROR] {get_message}"))
            return False

        print(f"\n-- {format_header(f'Editing Account #{account_num}')}: {account['description']} --")
        print(SEPARATOR_MEDIUM)
        print("Press Enter to keep current value, or type new value:")
        print()

        # Collect updates
        updated_account = collect_account_info(validation_service, account)
        if not updated_account:
            return True  # User cancellation during input is success

        # Check for changes (simple comparison)
        if updated_account == account:
            print("No changes made.")
            return True

        # Confirm changes
        print(f"\n-- {format_header(f'Updated Account #{account_num}')} --")
        print(SEPARATOR_MEDIUM)
        display_account_summary(updated_account)

        if not ask_yes_no("Save these changes?", default=True):
            print(format_status("[CANCELLED] Changes cancelled"))
            return True  # User cancellation is success

        # Validate
        is_valid, errors, warnings = validation_service.validate_account(updated_account)
        if not is_valid:
            print(format_status(f"[ERROR] Account validation failed: {'; '.join(errors)}"))
            return False

        # Update account using new tuple-returning method
        success, update_message = account_manager.update_account(account_num, updated_account)
        if not success:
            print(format_status(f"[ERROR] {update_message}"))
            return False

        print(format_status(f"\n[SUCCESS] {update_message}"))

        if warnings:
            print(format_status("\n[WARN] Warnings:"))
            for warning in warnings:
                print(f"   • {warning}")

        return True

    except KeyboardInterrupt:
        print(format_status("\n[CANCELLED] Editing cancelled"))
        return True  # Ctrl+C is success
    except Exception as e:
        logger.error(f"Account editing failed: {e}")
        print(format_status(f"[ERROR] Error editing account: {e}"))
        return False


def remove_account_interactive(account_manager, display_manager, identifier: Optional[str] = None) -> bool:
    """Remove an account interactively."""
    print(f"-- {format_header('Remove Git Account')}")
    print(SEPARATOR_SHORT)

    try:
        # Get account to remove
        if not identifier:
            success, accounts, load_message = account_manager.get_accounts()
            if not success:
                print(format_status(f"[ERROR] Error loading accounts: {load_message}"))
                return False
                
            if not accounts:
                print("No accounts to remove.")
                return True  # Nothing to remove is success

            display_manager.show_accounts(accounts)

            identifier = safe_input("Enter account number or search term to remove (or 'q' to cancel): ")
            if not identifier or identifier.lower() == "q":
                print(format_status("[CANCELLED] Removal cancelled"))
                return True  # User cancellation is success

        # Get account info using new tuple-returning method
        success, account_num, account, get_message = account_manager.get_account(identifier)
        if not success:
            print(format_status(f"[ERROR] {get_message}"))
            return False

        # Confirm removal
        print(format_status(f"\n[WARN] About to remove account #{account_num}:"))
        print(SEPARATOR_MEDIUM)
        display_account_summary(account)

        if not ask_yes_no("Are you sure you want to remove this account?", default=False):
            print(format_status("[CANCELLED] Removal cancelled"))
            return True  # User cancellation is success

        # Remove account using new tuple-returning method
        success, remove_message = account_manager.remove_account(account_num)
        if not success:
            print(format_status(f"[ERROR] {remove_message}"))
            return False

        print(format_status(f"[SUCCESS] {remove_message}"))
        return True

    except KeyboardInterrupt:
        print(format_status("\n[CANCELLED] Removal cancelled"))
        return True  # Ctrl+C is success
    except Exception as e:
        logger.error(f"Account removal failed: {e}")
        print(format_status(f"[ERROR] Error removing account: {e}"))
        return False


def edit_config_file_interactive(config_manager) -> bool:
    """Edit config file in editor."""
    print(f"-- {format_header('Interactive Config Editor')}")
    print(SEPARATOR_SHORT)

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "nano"))

    try:
        config_path = config_manager.get_config_path()
    except Exception as e:
        print(format_status(f"[ERROR] Failed to get config path: {e}"))
        return False

    print(f"Opening {format_accent(str(config_path))} in {format_accent(editor)}")
    print(">> Make your changes and save the file")
    print()

    # Create backup
    try:
        if config_manager.config_exists():
            success, backup_path, backup_message = config_manager.backup_config()
            if success:
                print(format_status(f"[INFO] {backup_message}"))
            else:
                print(format_status(f"[WARN] Could not create backup: {backup_message}"))
                if not ask_yes_no("Continue without backup?", default=False):
                    return True  # User cancellation is success
        else:
            print(format_status("[INFO] No existing config to backup"))
    except Exception as e:
        print(format_status(f"[WARN] Could not create backup: {e}"))
        if not ask_yes_no("Continue without backup?", default=False):
            return True  # User cancellation is success

    # Edit with validation
    while True:
        try:
            subprocess.run([editor, str(config_path)], check=True)

            print(f"\n>> {format_header('Validating configuration')}...")

            success, config, load_message = config_manager.load_config(force_reload=True)
            if success:
                print(format_status("[OK] Configuration is valid!"))
                accounts_count = len(config.get("accounts", {}))
                print(format_status(f"[INFO] Configuration summary: {accounts_count} account(s)"))
                return True
            else:
                print(format_status(f"[ERROR] Configuration validation failed: {load_message}"))
                print()

                choice = safe_input("Edit again (e), restore backup (r), or ignore errors (i)? [e]: ").lower()

                if choice == "r":
                    print(format_status("[OK] Configuration restored from backup"))
                    return True
                elif choice == "i":
                    print(format_status("[WARN] Proceeding with errors (configuration may not work properly)"))
                    return True
                # else continue loop

        except subprocess.CalledProcessError:
            print(format_status("[ERROR] Editor exited with error"))
            return False
        except KeyboardInterrupt:
            print(format_status("\n[CANCELLED] Editing cancelled"))
            return True  # Ctrl+C is success
        except Exception as e:
            logger.error(f"Config editing failed: {e}")
            print(format_status(f"[ERROR] Error opening editor: {e}"))
            return False