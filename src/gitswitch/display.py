"""Display functions for gitswitch."""

import logging
from typing import Dict, Optional, Tuple

from .constants import SEPARATOR_LONG, SEPARATOR_MEDIUM, SEPARATOR_SHORT, DEFAULT_SCOPE
from .colors import format_status, format_header, format_accent

logger = logging.getLogger(__name__)


def format_account_display(account_num: int, account: dict) -> str:
    """Format account for display consistently."""
    gpg_key = account.get("gpg_key", "")
    signing_enabled = account.get("signing_enabled", False)
    ssh_key = account.get("ssh_key", "")
    ssh_host = account.get("ssh_host", "")
    preferred_scope = account.get("preferred_scope", "local")

    lines = [
        f"{format_accent(str(account_num))}. {account['description']} (scope: {preferred_scope})",
        f"   Name: {account['name']}",
        f"   Email: {account['email']}",
    ]

    # GPG info
    if gpg_key and signing_enabled:
        lines.append(f"   GPG: {format_status('[ENABLED]')} {gpg_key}")
    elif gpg_key and not signing_enabled:
        lines.append(f"   GPG: {format_status('[DISABLED]')} {gpg_key}")
    else:
        lines.append(f"   GPG: {format_status('[NOT CONFIGURED]')}")

    # SSH info
    if ssh_key:
        host_text = f" -> {ssh_host}" if ssh_host else ""
        lines.append(f"   SSH: {format_status('[CONFIGURED]')} {ssh_key}{host_text}")
    else:
        lines.append(f"   SSH: {format_status('[NOT CONFIGURED]')}")

    return "\n".join(lines)


class DisplayManager:
    """Display manager for gitswitch output."""

    def __init__(self, config_manager, account_manager, git_ops, validation_service):
        """Initialize with managers directly."""
        self.config_manager = config_manager
        self.account_manager = account_manager
        self.git_ops = git_ops
        self.validation_service = validation_service

    def show_accounts(self, accounts: Optional[Dict[int, dict]] = None) -> Tuple[bool, str]:
        """Display available accounts in a formatted way. Returns (success, message)."""
        print(f"\n┌─────────────────────────────────┐")
        print(f"│      {format_header('Available Git Accounts')}     │")
        print(f"└─────────────────────────────────┘")

        # If no accounts provided, fetch them using new tuple method
        if accounts is None:
            success, accounts, message = self.account_manager.get_accounts()
            if not success:
                print(format_status(f"[ERROR] Error loading accounts: {message}"))
                return False, f"Failed to load accounts: {message}"

        if not accounts:
            print("No accounts configured.")
            print("Run 'gitswitch add' to create your first account.")
            return True, "No accounts to display"

        for num in sorted(accounts.keys()):
            account = accounts[num]
            print(format_account_display(num, account))
            print()  # Empty line between accounts

        return True, f"Displayed {len(accounts)} accounts successfully"

    def show_current_config(self) -> Tuple[bool, str]:
        """Display current git configuration. Returns (success, message)."""
        try:
            # Get current config directly
            name, email = self.git_ops.get_current_config()
            gpg_config = self.git_ops.get_gpg_config()
            ssh_config = self.git_ops.get_ssh_config()

            if name and email:
                print(f"\n── {format_header('Current Git Configuration')} ──")
                print(f"   Name: {name}")
                print(f"   Email: {email}")

                # Show GPG status
                if gpg_config["signing_key"]:
                    commit_status = "[ENABLED]" if gpg_config["commit_gpgsign"] else "[DISABLED]"
                    tag_status = "[ENABLED]" if gpg_config["tag_gpgsign"] else "[DISABLED]"
                    print(f"   GPG Key: {gpg_config['signing_key']}")
                    print(f"   GPG Commit Signing: {format_status(commit_status)}")
                    print(f"   GPG Tag Signing: {format_status(tag_status)}")
                else:
                    print(f"   GPG Signing: {format_status('[DISABLED]')}")

                # Show SSH status
                if ssh_config["git_ssh_command"]:
                    print(f"   SSH Command: {ssh_config['git_ssh_command']}")
                else:
                    print(f"   SSH: {format_status('[SYSTEM DEFAULT]')}")

                # Show repository context if available
                repo_info = self.git_ops.get_repository_info()
                if repo_info["is_repo"]:
                    if "current_branch" in repo_info:
                        print(f"   Current Branch: {format_accent(repo_info['current_branch'])}")
                    if "origin_url" in repo_info:
                        print(f"   Repository: {repo_info['origin_url']}")
                
                return True, "Current configuration displayed successfully"
            else:
                print(format_status("\n[WARN] No git configuration found"))
                print("   Run 'gitswitch list' to see available accounts")
                return True, "No git configuration found"

        except Exception as e:
            logger.error(f"Error displaying current config: {e}")
            print(format_status("\n[WARN] Error reading current git configuration"))
            return False, f"Error displaying current config: {e}"

    def _format_config_scope(self, scope_name: str, config: dict) -> str:
        """Format a single configuration scope for display."""
        if not config["name"] or not config["email"]:
            return f"{scope_name}: {format_status('[NOT SET]')}"

        lines = [f"{scope_name}:", f"   Name: {config['name']}", f"   Email: {config['email']}"]

        gpg = config["gpg"]
        if gpg["signing_key"]:
            commit_status = "[ENABLED]" if gpg["commit_gpgsign"] else "[DISABLED]"
            tag_status = "[ENABLED]" if gpg["tag_gpgsign"] else "[DISABLED]"
            lines.extend(
                [
                    f"   GPG Key: {gpg['signing_key']}",
                    f"   GPG Commit Signing: {format_status(commit_status)}",
                    f"   GPG Tag Signing: {format_status(tag_status)}",
                ]
            )
        else:
            lines.append(f"   GPG Signing: {format_status('[NOT CONFIGURED]')}")

        return "\n".join(lines)

    def show_scope_status(self) -> Tuple[bool, str]:
        """Show detailed scope information. Returns (success, message)."""
        try:
            print(f"\n╔══════════════════════════════════════════════════════════╗")
            print(f"║              {format_header('Git Configuration Scope Status')}             ║")
            print(f"╚══════════════════════════════════════════════════════════╝")

            scope_info = self.git_ops.get_git_scope_info()

            # Get default scope using new tuple method
            scope_success, default_scope, scope_message = self.config_manager.get_default_scope()
            if not scope_success:
                logger.warning(f"Could not get default scope: {scope_message}")
                default_scope = DEFAULT_SCOPE

            print(f"Default scope: {format_accent(default_scope)}\n")

            # Show configurations using helper method
            print(f">> {format_header('Global Configuration')}:")
            global_config = scope_info["global"]
            if global_config["name"] and global_config["email"]:
                print(f"   Name: {global_config['name']}")
                print(f"   Email: {global_config['email']}")

                gpg = global_config["gpg"]
                if gpg["signing_key"]:
                    commit_status = "[ENABLED]" if gpg["commit_gpgsign"] else "[DISABLED]"
                    tag_status = "[ENABLED]" if gpg["tag_gpgsign"] else "[DISABLED]"
                    print(f"   GPG Key: {gpg['signing_key']}")
                    print(f"   GPG Commit Signing: {format_status(commit_status)}")
                    print(f"   GPG Tag Signing: {format_status(tag_status)}")
                else:
                    print(f"   GPG Signing: {format_status('[NOT CONFIGURED]')}")
            else:
                print(f"   {format_status('[NOT SET]')}")
            print()

            # Show local config
            print(f">> {format_header('Local Configuration')}:")
            local_config = scope_info["local"]
            if local_config["name"] and local_config["email"]:
                print(f"   Name: {local_config['name']}")
                print(f"   Email: {local_config['email']}")

                gpg = local_config["gpg"]
                if gpg["signing_key"]:
                    commit_status = "[ENABLED]" if gpg["commit_gpgsign"] else "[DISABLED]"
                    tag_status = "[ENABLED]" if gpg["tag_gpgsign"] else "[DISABLED]"
                    print(f"   GPG Key: {gpg['signing_key']}")
                    print(f"   GPG Commit Signing: {format_status(commit_status)}")
                    print(f"   GPG Tag Signing: {format_status(tag_status)}")
                else:
                    print(f"   GPG Signing: {format_status('[NOT CONFIGURED]')}")
            else:
                print(f"   {format_status('[NOT SET - using global]')}")
            print()

            # SSH info
            ssh_config = scope_info["ssh"]
            print(f">> {format_header('SSH Configuration')}:")
            if ssh_config["git_ssh_command"]:
                print(f"   Command: {ssh_config['git_ssh_command']}")
                if ssh_config["ssh_auth_sock"]:
                    print(f"   Auth Socket: {ssh_config['ssh_auth_sock']}")
                print(f"   Status: {format_status('[CUSTOM SSH ACTIVE]')}")
            else:
                print(f"   Status: {format_status('[SYSTEM DEFAULT SSH]')}")
                if ssh_config["ssh_auth_sock"]:
                    print(f"   Auth Socket: {ssh_config['ssh_auth_sock']}")

            # Repository information
            repo_info = self.git_ops.get_repository_info()
            if repo_info["is_repo"]:
                print(f"\n>> {format_header('Repository Information')}:")
                print(f"   Git Directory: {repo_info.get('git_dir', 'unknown')}")
                if "current_branch" in repo_info:
                    print(f"   Current Branch: {format_accent(repo_info['current_branch'])}")
                if "origin_url" in repo_info:
                    print(f"   Origin URL: {repo_info['origin_url']}")
            else:
                print(f"\n>> Repository: {format_status('[NOT IN GIT REPOSITORY]')}")

            return True, "Scope status displayed successfully"

        except Exception as e:
            logger.error(f"Error displaying scope status: {e}")
            print(format_status("[ERROR] Error retrieving scope status"))
            return False, f"Error displaying scope status: {e}"

    def show_config_location(self) -> Tuple[bool, str]:
        """Show where the config file is located. Returns (success, message)."""
        try:
            config_path = self.config_manager.get_config_path()
            print(f"\n── Config file location: {config_path}")

            # Check config status using new tuple method
            if self.config_manager.config_exists():
                success, config, load_message = self.config_manager.load_config()
                if success:
                    accounts_count = len(config.get("accounts", {}))
                    print(f"   Status: {format_status('[OK]')} File exists with {accounts_count} account(s)")
                    return True, f"Config location displayed (found {accounts_count} accounts)"
                else:
                    print(f"   Status: {format_status('[ERROR]')} File exists but has errors: {load_message}")
                    return False, f"Config file has errors: {load_message}"
            else:
                print(f"   Status: {format_status('[NOT FOUND]')} File does not exist")
                print("   Run 'gitswitch add' to create your first account")
                return True, "Config location displayed (no config file found)"

        except Exception as e:
            logger.error(f"Error showing config location: {e}")
            print(format_status("[WARN] Error getting config path"))
            return False, f"Error showing config location: {e}"