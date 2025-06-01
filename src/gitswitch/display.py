"""Display and UI functions for gitswitch."""

from .config import get_config_path, get_default_scope
from .git_ops import get_current_config, get_git_scope_info, get_gpg_config


def show_accounts(accounts):
    """Display available accounts"""
    print("\n📋 Available Git Accounts 📋")
    print("=" * 50)
    for num, account in sorted(accounts.items()):
        preferred_scope = account.get('preferred_scope', get_default_scope())
        gpg_key = account.get('gpg_key', '')
        signing_enabled = account.get('signing_enabled', False)

        # Main account info
        print(f"{num}. {account['description']} (scope: {preferred_scope})")
        print(f"   Name: {account['name']}")
        print(f"   Email: {account['email']}")

        # GPG info
        if gpg_key and signing_enabled:
            print(f"   GPG: ✅ {gpg_key} (signing enabled)")
        elif gpg_key and not signing_enabled:
            print(f"   GPG: ⚠️  {gpg_key} (signing disabled)")
        else:
            print("   GPG: ❌ No signing")
        print()


def show_current_config():
    """Display current git configuration"""
    name, email = get_current_config()
    gpg_config = get_gpg_config()

    if name and email:
        print(f"\n🔍 Current Git Configuration 🔍")
        print(f"   Name: {name}")
        print(f"   Email: {email}")

        # Show GPG status
        if gpg_config["signing_key"]:
            sign_status = "✅ Enabled" if gpg_config["commit_gpgsign"] else "⚠️  Key set but signing disabled"
            print(f"   GPG Key: {gpg_config['signing_key']}")
            print(f"   GPG Signing: {sign_status}")
        else:
            print("   GPG Signing: ❌ Disabled")
    else:
        print("\n⚠️  No git configuration found or error reading config")


def show_scope_status():
    """Show detailed scope information"""
    print("\n🎯 Git Configuration Scope Status 🎯")
    print("=" * 50)

    scope_info = get_git_scope_info()
    default_scope = get_default_scope()

    print(f"Default scope: {default_scope}")
    print()

    # Show global config
    global_config = scope_info["global"]
    if global_config["name"] and global_config["email"]:
        print("🌍 Global Configuration:")
        print(f"   Name: {global_config['name']}")
        print(f"   Email: {global_config['email']}")

        gpg = global_config["gpg"]
        if gpg["signing_key"]:
            sign_status = "✅ Enabled" if gpg["commit_gpgsign"] else "⚠️  Disabled"
            print(f"   GPG Key: {gpg['signing_key']}")
            print(f"   GPG Signing: {sign_status}")
        else:
            print("   GPG Signing: ❌ Not configured")
    else:
        print("🌍 Global Configuration: Not set")

    print()

    # Show local config
    local_config = scope_info["local"]
    if local_config["name"] and local_config["email"]:
        print("📁 Local Configuration (current repo):")
        print(f"   Name: {local_config['name']}")
        print(f"   Email: {local_config['email']}")

        gpg = local_config["gpg"]
        if gpg["signing_key"]:
            sign_status = "✅ Enabled" if gpg["commit_gpgsign"] else "⚠️  Disabled"
            print(f"   GPG Key: {gpg['signing_key']}")
            print(f"   GPG Signing: {sign_status}")
        else:
            print("   GPG Signing: ❌ Not configured")
    else:
        print("📁 Local Configuration: Not set (using global)")


def show_config_location():
    """Show where the config file is located"""
    config_path = get_config_path()
    print(f"\n⚙️  Config file location: {config_path}")
