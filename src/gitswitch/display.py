"""Display and UI functions for gitswitch."""

from .config import get_config_path, get_default_scope
from .git_ops import get_current_config, get_git_scope_info


def show_accounts(accounts):
    """Display available accounts"""
    print("\n📋 Available Git Accounts 📋")
    print("=" * 40)
    for num, account in sorted(accounts.items()):
        preferred_scope = account.get('preferred_scope', get_default_scope())
        print(f"{num}. {account['description']} (scope: {preferred_scope})")
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


def show_scope_status():
    """Show detailed scope information"""
    print("\n🎯 Git Configuration Scope Status 🎯")
    print("=" * 45)

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
    else:
        print("🌍 Global Configuration: Not set")

    print()

    # show local config
    local_config = scope_info["local"]
    if local_config["name"] and local_config["email"]:
        print("📁 Local Configuration (current repo):")
        print(f"   Name: {local_config['name']}")
        print(f"   Email: {local_config['email']}")
    else:
        print("📁 Local Configuration: Not set (using global)")


def show_config_location():
    """Show where the config file is located"""
    config_path = get_config_path()
    print(f"\n⚙️  Config file location: {config_path}")
