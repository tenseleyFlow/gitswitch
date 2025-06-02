"""Health check"""

import logging
from .constants import SEPARATOR_LONG, SEPARATOR_MEDIUM

logger = logging.getLogger(__name__)


def run_health_check(config_manager, account_manager, git_ops, validation_service) -> bool:
    """Run comprehensive health check with all checks inline."""
    print("🏥 Gitswitch Doctor - Health Check")
    print(SEPARATOR_LONG)

    all_healthy = True

    # === SYSTEM REQUIREMENTS CHECK ===
    print("🔍 Checking System Requirements...")
    print(SEPARATOR_MEDIUM)
    try:
        system_info = validation_service.get_system_info()

        for tool, info in system_info.items():
            if info["status"] == "available":
                print(f"✅ {tool}: {info['version']}")
            else:
                print(f"❌ {tool}: Not found")
                all_healthy = False

    except Exception as e:
        print(f"❌ Error checking system requirements: {e}")
        all_healthy = False

    # === CONFIGURATION CHECK ===
    print("\n📁 Checking Configuration File...")
    print(SEPARATOR_MEDIUM)
    try:
        config_path = config_manager.get_config_path()

        if not config_manager.config_exists():
            print(f"❌ Config file does not exist: {config_path}")
            all_healthy = False
        else:
            print(f"✅ Config file exists: {config_path}")

            # Load and validate config
            config = config_manager.load_config()
            is_valid, errors, warnings = validation_service.validate_config(config)

            if is_valid:
                print("✅ Config file is valid TOML")
                accounts_count = len(config.get("accounts", {}))
                print(f"✅ Found {accounts_count} account(s)")
            else:
                print("❌ Config file has validation errors:")
                for error in errors:
                    print(f"   • {error}")
                all_healthy = False

            # Show warnings
            if warnings:
                print("⚠️  Config warnings:")
                for warning in warnings:
                    print(f"   • {warning}")

    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        all_healthy = False

    # === ACCOUNTS CHECK ===
    print("\n👤 Checking Accounts...")
    print(SEPARATOR_MEDIUM)
    try:
        accounts = account_manager.get_accounts()

        if not accounts:
            print("⚠️  No accounts configured")
        else:
            for account_num, account_data in accounts.items():
                print(f"\n👤 Account #{account_num}: {account_data.get('description', 'No description')}")
                print(SEPARATOR_LONG)

                # Validate account
                is_valid, errors, warnings = validation_service.validate_account(account_data)

                if is_valid:
                    # Show basic info
                    for field in ["name", "email", "preferred_scope"]:
                        value = account_data.get(field, "local" if field == "preferred_scope" else "")
                        print(f"✅ {field.replace('_', ' ').title()}: {value}")

                    # GPG status
                    gpg_key = account_data.get("gpg_key", "").strip()
                    signing_enabled = account_data.get("signing_enabled", False)

                    if gpg_key:
                        key_info = validation_service.get_gpg_key_info(gpg_key)
                        print(f"✅ GPG Key: {gpg_key} - {key_info}")
                        if not signing_enabled:
                            print("⚠️  GPG key provided but signing is disabled")
                    elif signing_enabled:
                        print("❌ GPG signing enabled but no key provided")
                    else:
                        print("ℹ️  GPG: Not configured")

                    # SSH status
                    ssh_key = account_data.get("ssh_key", "").strip()
                    ssh_host = account_data.get("ssh_host", "").strip()

                    if ssh_key:
                        key_info = validation_service.get_ssh_key_info(ssh_key)
                        print(f"✅ SSH Key: {ssh_key} - {key_info}")
                        if ssh_host:
                            print(f"ℹ️  SSH Host: {ssh_host}")
                    else:
                        print("ℹ️  SSH: Not configured")

                    print("\n🎉 Account looks healthy!")
                else:
                    print("❌ Issues found:")
                    for error in errors:
                        print(f"   • {error}")
                    all_healthy = False

                if warnings:
                    print("\n⚠️  Warnings:")
                    for warning in warnings:
                        print(f"   • {warning}")

    except Exception as e:
        print(f"❌ Error checking accounts: {e}")
        all_healthy = False

    # === GIT FUNCTIONALITY CHECK ===
    print("\n🔧 Testing Git Functionality...")
    print(SEPARATOR_MEDIUM)
    try:
        repo_info = git_ops.get_repository_info()

        if repo_info.get("is_repo"):
            print(f"✅ In git repository: {repo_info.get('git_dir', 'unknown')}")

            if "current_branch" in repo_info:
                print(f"✅ Current branch: {repo_info['current_branch']}")

            if "origin_url" in repo_info:
                print(f"✅ Origin URL: {repo_info['origin_url']}")

            # Test current git config
            name, email = git_ops.get_current_config()

            if name:
                print(f"✅ Current git name: {name}")
            else:
                print("⚠️  No git user.name set")

            if email:
                print(f"✅ Current git email: {email}")
            else:
                print("⚠️  No git user.email set")
        else:
            print("ℹ️  Not in a git repository (this is okay)")

    except Exception as e:
        print(f"❌ Error testing git functionality: {e}")
        all_healthy = False

    # === FINAL SUMMARY ===
    print("\n" + SEPARATOR_LONG)
    if all_healthy:
        print("🎉 All checks passed! Gitswitch is healthy!")
        logger.info("Health check completed successfully")
    else:
        print("⚠️  Some issues found. Please review the output above.")
        print("💡 Run 'gitswitch config' to edit your configuration")
        logger.warning("Health check found issues")

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
