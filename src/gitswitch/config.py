"""Configuration file management for gitswitch."""

import sys
from pathlib import Path

# Handle TOML parsing for different Python versions
try:
    # Python 3.11+
    import tomllib
except ImportError:
    # Fallback for older Python versions
    import tomli as tomllib

# For writing TOML files
try:
    import tomli_w
except ImportError:
    print("❌ tomli_w is required for add/remove functionality")
    print("   Install with: pip install tomli_w")
    sys.exit(1)


def get_config_path():
    """Get the path to the configuration file"""
    config_dir = Path.home() / ".config" / "gitswitch"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "accounts.toml"


def create_default_config(config_path):
    """Create a default configuration file"""
    default_config = """# Git Switcher Account Configuration

[settings]
default_scope = "local"  # Options: "local", "global"

[accounts.1]
name = "You"
email = "your@email.com"
description = "Default Account"
preferred_scope = "local"     # Optional: override default scope for this account
gpg_key = ""                  # Optional: GPG key ID for signing (e.g., "ABC123DEF456")
signing_enabled = false       # Optional: enable GPG signing for this account

# Example with GPG signing:
# [accounts.2]
# name = "Your Name"
# email = "work@company.com"
# description = "Work Account"
# preferred_scope = "global"
# gpg_key = "ABC123DEF456"    # Your GPG key ID
# signing_enabled = true       # Enable GPG signing

# Add more as follows:
#   [accounts.3]
#   name = "your/user name"
#   email = "account email"
#   description = "Account description"
#   preferred_scope = "local"   # Optional per-account preference
#   gpg_key = "XYZ789GHI012"   # Optional GPG key
#   signing_enabled = true      # Optional GPG signing
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


def get_default_scope():
    """Get the default scope from configuration"""
    config = load_config()
    return config.get('settings', {}).get('default_scope', 'local')


def get_account_preferred_scope(account_info):
    """Get the preferred scope for a specific account"""
    return account_info.get('preferred_scope', get_default_scope())
