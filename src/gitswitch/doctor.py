"""Health check"""

import logging
from .constants import SEPARATOR_LONG, SEPARATOR_MEDIUM

logger = logging.getLogger(__name__)


def run_health_check(config_manager, account_manager, git_ops, validation_service) -> bool:
    """Run comprehensive health check using validation service methods."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                Gitswitch Health Check                    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    all_healthy = True

    # === SYSTEM REQUIREMENTS CHECK ===
    print(">> Checking System Requirements...")
    print(SEPARATOR_MEDIUM)

    is_valid, errors, warnings = validation_service.validate_system_requirements()
    if is_valid:
        # Show tool versions
        system_info = validation_service.get_system_info()
        for tool, info in system_info.items():
            print(f"[OK] {tool}: {info['version']}")
    else:
        print("[FAIL] Missing tools:")
        for error in errors:
            print(f"   • {error}")
        all_healthy = False

    # === CONFIGURATION CHECK ===
    print("\n>> Checking Configuration File...")
    print(SEPARATOR_MEDIUM)

    try:
        config_path = config_manager.get_config_path()
        print(f"[OK] Config file location: {config_path}")

        if config_manager.config_exists():
            config = config_manager.load_config()
            is_valid, errors, warnings = validation_service.validate_config(config)

            if is_valid:
                accounts_count = len(config.get("accounts", {}))
                print(f"[OK] Configuration is valid with {accounts_count} account(s)")
            else:
                print("[FAIL] Configuration validation errors:")
                for error in errors:
                    print(f"   • {error}")
                all_healthy = False

            if warnings:
                print("[WARN] Configuration warnings:")
                for warning in warnings:
                    print(f"   • {warning}")
        else:
            print("[FAIL] Config file does not exist")
            all_healthy = False

    except Exception as e:
        print(f"[ERROR] Error checking configuration: {e}")
        all_healthy = False

    # === ACCOUNTS CHECK ===
    print("\n>> Checking Accounts...")
    print(SEPARATOR_MEDIUM)

    try:
        accounts = account_manager.get_accounts()
        if not accounts:
            print("[WARN] No accounts configured")
        else:
            for account_num, account_data in accounts.items():
                print(f"\n-- Account #{account_num}: {account_data.get('description', 'No description')} --")

                is_valid, errors, warnings = validation_service.validate_account(account_data)

                if is_valid:
                    print("[OK] Account validation passed")

                    # Show GPG status using validation service
                    gpg_key = account_data.get("gpg_key", "").strip()
                    if gpg_key:
                        gpg_info = validation_service.get_gpg_key_info(gpg_key)
                        print(f"[OK] GPG: {gpg_info}")

                    # Show SSH status using validation service
                    ssh_key = account_data.get("ssh_key", "").strip()
                    if ssh_key:
                        ssh_info = validation_service.get_ssh_key_info(ssh_key)
                        print(f"[OK] SSH: {ssh_info}")
                else:
                    print("[FAIL] Account validation failed:")
                    for error in errors:
                        print(f"   • {error}")
                    all_healthy = False

                if warnings:
                    print("[WARN] Account warnings:")
                    for warning in warnings:
                        print(f"   • {warning}")

    except Exception as e:
        print(f"[ERROR] Error checking accounts: {e}")
        all_healthy = False

    # === GIT FUNCTIONALITY CHECK ===
    print("\n>> Testing Git Functionality...")
    print(SEPARATOR_MEDIUM)

    try:
        repo_info = git_ops.get_repository_info()
        if repo_info.get("is_repo"):
            print(f"[OK] Git repository detected")
            for key, value in repo_info.items():
                if key != "is_repo" and value:
                    print(f"   {key.replace('_', ' ').title()}: {value}")
        else:
            print("[INFO] Not in a git repository (this is okay)")

        # Check current configuration
        name, email = git_ops.get_current_config()
        if name and email:
            print(f"[OK] Current git config: {name} <{email}>")
        else:
            print("[WARN] No git user configuration set")

    except Exception as e:
        print(f"[ERROR] Error testing git functionality: {e}")
        all_healthy = False

    # === FINAL SUMMARY ===
    print("\n" + SEPARATOR_LONG)
    if all_healthy:
        print("[SUCCESS] All checks passed! Gitswitch is healthy!")
    else:
        print("[WARN] Some issues found. Please review the output above.")
        print(">> Run 'gitswitch config' to edit your configuration")

    return all_healthy


# Legacy function for compatibility
def run_doctor():
    """Legacy function - use run_health_check instead."""
    from .config import ConfigManager
    from .accounts import AccountManager
    from .git_ops import GitOperations
    from .validation import ValidationService

    config_manager = ConfigManager()
    account_manager = AccountManager(config_manager)
    git_ops = GitOperations()
    validation_service = ValidationService()

    return run_health_check(config_manager, account_manager, git_ops, validation_service)
