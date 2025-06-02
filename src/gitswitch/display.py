"""Display functions for gitswitch."""

import logging
from typing import Dict, Optional

from .constants import SEPARATOR_LONG, SEPARATOR_MEDIUM, SEPARATOR_SHORT, DEFAULT_SCOPE

logger = logging.getLogger(__name__)


def format_account_display(account_num: int, account: dict) -> str:
    """Format account for display consistently."""
    gpg_key = account.get("gpg_key", "")
    signing_enabled = account.get("signing_enabled", False)
    ssh_key = account.get("ssh_key", "")
    ssh_host = account.get("ssh_host", "")
    preferred_scope = account.get("preferred_scope", "local")

    lines = [
        f"{account_num}. {account['description']} (scope: {preferred_scope})",
        f"   Name: {account['name']}",
        f"   Email: {account['email']}",
    ]

    # GPG info
    if gpg_key and signing_enabled:
        lines.append(f"   GPG: ✅ {gpg_key} (signing enabled)")
    elif gpg_key and not signing_enabled:
        lines.append(f"   GPG: ⚠️  {gpg_key} (signing disabled)")
    else:
        lines.append("   GPG: ❌ No signing")

    # SSH info
    if ssh_key:
        host_text = f" → {ssh_host}" if ssh_host else ""
        lines.append(f"   SSH: ✅ {ssh_key}{host_text}")
    else:
        lines.append("   SSH: ❌ Not configured")

    return "\n".join(lines)


class DisplayManager:
    """Display manager for gitswitch output."""

    def __init__(self, config_manager, account_manager, git_ops, validation_service):
        """Initialize with managers directly."""
        self.config_manager = config_manager
        self.account_manager = account_manager
        self.git_ops = git_ops
        self.validation_service = validation_service

    def show_accounts(self, accounts: Optional[Dict[int, dict]] = None):
        """Display available accounts in a formatted way."""
        print("\n📋 Available Git Accounts 📋")
        print(SEPARATOR_LONG)

        # If no accounts provided, fetch them directly
        if accounts is None:
            try:
                accounts = self.account_manager.get_accounts()
            except Exception as e:
                print(f"❌ Error loading accounts: {e}")
                return

        if not accounts:
            print("No accounts configured.")
            print("Run 'gitswitch add' to create your first account.")
            return

        for num in sorted(accounts.keys()):
            account = accounts[num]
            print(format_account_display(num, account))
            print()  # Empty line between accounts

    def show_current_config(self):
        """Display current git configuration."""
        try:
            # Get current config directly
            name, email = self.git_ops.get_current_config()
            gpg_config = self.git_ops.get_gpg_config()
            ssh_config = self.git_ops.get_ssh_config()

            if name and email:
                print(f"\n🔍 Current Git Configuration 🔍")
                print(f"   Name: {name}")
                print(f"   Email: {email}")

                # Show GPG status
                if gpg_config["signing_key"]:
                    commit_status = "✅" if gpg_config["commit_gpgsign"] else "⚠️"
                    tag_status = "✅" if gpg_config["tag_gpgsign"] else "⚠️"
                    print(f"   GPG Key: {gpg_config['signing_key']}")
                    print(f"   GPG Commit Signing: {commit_status}")
                    print(f"   GPG Tag Signing: {tag_status}")
                else:
                    print("   GPG Signing: ❌ Disabled")

                # Show SSH status
                if ssh_config["git_ssh_command"]:
                    print(f"   SSH Command: {ssh_config['git_ssh_command']}")
                else:
                    print("   SSH: ❌ Using system default")

                # Show repository context if available
                repo_info = self.git_ops.get_repository_info()
                if repo_info["is_repo"]:
                    if "current_branch" in repo_info:
                        print(f"   Current Branch: {repo_info['current_branch']}")
                    if "origin_url" in repo_info:
                        print(f"   Repository: {repo_info['origin_url']}")
            else:
                print("\n⚠️  No git configuration found")
                print("   Run 'gitswitch list' to see available accounts")

        except Exception as e:
            logger.error(f"Error displaying current config: {e}")
            print("\n⚠️  Error reading current git configuration")

    def show_scope_status(self):
        """Show detailed scope information with inline scope display."""
        try:
            print("\n🎯 Git Configuration Scope Status 🎯")
            print(SEPARATOR_LONG)

            # Get scope info directly
            scope_info = self.git_ops.get_git_scope_info()

            # Get default scope from config
            try:
                default_scope = self.config_manager.get_default_scope()
            except:
                default_scope = DEFAULT_SCOPE

            print(f"Default scope: {default_scope}")
            print()

            # Show global config (inline instead of helper method)
            global_config = scope_info["global"]
            if global_config["name"] and global_config["email"]:
                print("🌍 Global Configuration:")
                print(f"   Name: {global_config['name']}")
                print(f"   Email: {global_config['email']}")

                gpg = global_config["gpg"]
                if gpg["signing_key"]:
                    commit_status = "✅ Enabled" if gpg["commit_gpgsign"] else "⚠️  Disabled"
                    tag_status = "✅ Enabled" if gpg["tag_gpgsign"] else "⚠️  Disabled"
                    print(f"   GPG Key: {gpg['signing_key']}")
                    print(f"   GPG Commit Signing: {commit_status}")
                    print(f"   GPG Tag Signing: {tag_status}")
                else:
                    print("   GPG Signing: ❌ Not configured")
            else:
                print("🌍 Global Configuration: Not set")
            print()

            # Show local config (inline instead of helper method)
            local_config = scope_info["local"]
            if local_config["name"] and local_config["email"]:
                print("📁 Local Configuration:")
                print(f"   Name: {local_config['name']}")
                print(f"   Email: {local_config['email']}")

                gpg = local_config["gpg"]
                if gpg["signing_key"]:
                    commit_status = "✅ Enabled" if gpg["commit_gpgsign"] else "⚠️  Disabled"
                    tag_status = "✅ Enabled" if gpg["tag_gpgsign"] else "⚠️  Disabled"
                    print(f"   GPG Key: {gpg['signing_key']}")
                    print(f"   GPG Commit Signing: {commit_status}")
                    print(f"   GPG Tag Signing: {tag_status}")
                else:
                    print("   GPG Signing: ❌ Not configured")
            else:
                print("📁 Local Configuration: Not set using global")
            print()

            # Show SSH info
            ssh_config = scope_info["ssh"]
            print("🔑 SSH Configuration:")
            if ssh_config["git_ssh_command"]:
                print(f"   Command: {ssh_config['git_ssh_command']}")
                if ssh_config["ssh_auth_sock"]:
                    print(f"   Auth Socket: {ssh_config['ssh_auth_sock']}")
                print("   Status: ✅ Custom SSH configuration active")
            else:
                print("   Status: ❌ Using system default SSH")
                if ssh_config["ssh_auth_sock"]:
                    print(f"   Auth Socket: {ssh_config['ssh_auth_sock']}")

            # Show repository information
            repo_info = self.git_ops.get_repository_info()
            if repo_info["is_repo"]:
                print(f"\n📂 Repository Information:")
                print(f"   Git Directory: {repo_info.get('git_dir', 'unknown')}")
                if "current_branch" in repo_info:
                    print(f"   Current Branch: {repo_info['current_branch']}")
                if "origin_url" in repo_info:
                    print(f"   Origin URL: {repo_info['origin_url']}")
            else:
                print(f"\n📂 Repository: Not in a git repository")

        except Exception as e:
            logger.error(f"Error displaying scope status: {e}")
            print("❌ Error retrieving scope status")

    def show_config_location(self):
        """Show where the config file is located."""
        try:
            config_path = self.config_manager.get_config_path()
            print(f"\n⚙️  Config file location: {config_path}")

            # Check config status
            if self.config_manager.config_exists():
                try:
                    config = self.config_manager.load_config()
                    accounts_count = len(config.get("accounts", {}))
                    print(f"   Status: ✅ File exists with {accounts_count} account(s)")
                except:
                    print("   Status: ❌ File exists but has errors")
            else:
                print("   Status: ❌ File does not exist")
                print("   Run 'gitswitch add' to create your first account")

        except Exception as e:
            logger.error(f"Error showing config location: {e}")
            print("⚠️  Error getting config path")
