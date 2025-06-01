"""Display and UI functions for gitswitch."""

from .config import get_config_path
from .git_ops import get_current_config


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
