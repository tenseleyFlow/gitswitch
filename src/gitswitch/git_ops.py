"""Git operations for gitswitch."""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from .constants import VALID_SCOPES
from .exceptions import GitOperationError
from .utils import run_command_safe

logger = logging.getLogger(__name__)


class GitOperations:
    """Git operations manager."""

    def run_git_command(self, command: str, scope: str = None, silent: bool = False) -> Optional[str]:
        """Run a git command with proper scope handling."""
        # Add scope flag if specified
        if scope in VALID_SCOPES:
            command = command.replace("git config", f"git config --{scope}")

        success, stdout, stderr = run_command_safe(command, silent=silent)

        if not success:
            if silent:
                return None
            raise GitOperationError(f"Git command failed: {command}\nError: {stderr}")

        return stdout

    def get_current_config(self, scope: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Get current git user configuration."""
        scope_flag = f"--{scope}" if scope in VALID_SCOPES else ""

        name = self.run_git_command(f"git config {scope_flag} user.name".strip(), silent=True)
        email = self.run_git_command(f"git config {scope_flag} user.email".strip(), silent=True)

        return name, email

    def get_gpg_config(self, scope: str = None) -> Dict[str, any]:
        """Get current GPG configuration."""
        scope_flag = f"--{scope}" if scope in VALID_SCOPES else ""

        signing_key = self.run_git_command(f"git config {scope_flag} user.signingkey".strip(), silent=True)
        commit_sign = self.run_git_command(f"git config {scope_flag} commit.gpgsign".strip(), silent=True)
        tag_sign = self.run_git_command(f"git config {scope_flag} tag.gpgsign".strip(), silent=True)

        return {
            "signing_key": signing_key,
            "commit_gpgsign": commit_sign == "true",
            "tag_gpgsign": tag_sign == "true",
        }

    def get_ssh_config(self) -> Dict[str, Optional[str]]:
        """Get current SSH configuration."""
        return {
            "git_ssh_command": os.environ.get("GIT_SSH_COMMAND"),
            "ssh_auth_sock": os.environ.get("SSH_AUTH_SOCK"),
        }

    def clear_local_git_config(self) -> list:
        """Clear local git configuration to allow global settings to take effect."""
        configs_to_clear = [
            "user.name",
            "user.email",
            "user.signingkey",
            "commit.gpgsign",
            "tag.gpgsign",
        ]

        cleared = []
        for config in configs_to_clear:
            # Check if local config exists
            result = self.run_git_command(f"git config --local {config}", silent=True)
            if result:  # Config exists locally
                try:
                    self.run_git_command(f"git config --local --unset {config}")
                    cleared.append(config)
                    logger.debug(f"Cleared local config: {config}")
                except GitOperationError:
                    logger.warning(f"Failed to clear local config: {config}")

        return cleared

    def set_basic_config(self, name: str, email: str, scope: str) -> bool:
        """Set basic git user configuration."""
        try:
            self.run_git_command(f'git config --{scope} user.name "{name}"')
            self.run_git_command(f'git config --{scope} user.email "{email}"')
            logger.info(f"Set git user config ({scope}): {name} <{email}>")
            return True
        except GitOperationError as e:
            logger.error(f"Failed to set basic git config: {e}")
            return False

    def set_gpg_config(self, gpg_key: str, signing_enabled: bool, scope: str) -> bool:
        """Set GPG configuration."""
        try:
            if gpg_key and signing_enabled:
                # Enable GPG signing
                self.run_git_command(f'git config --{scope} user.signingkey "{gpg_key}"')
                self.run_git_command(f"git config --{scope} commit.gpgsign true")
                self.run_git_command(f"git config --{scope} tag.gpgsign true")
                logger.info(f"Enabled GPG signing ({scope}): {gpg_key}")
            else:
                # Disable GPG signing
                self.run_git_command(f"git config --{scope} commit.gpgsign false")
                self.run_git_command(f"git config --{scope} tag.gpgsign false")
                logger.debug(f"Disabled GPG signing ({scope})")

            return True

        except GitOperationError as e:
            logger.error(f"Failed to set GPG config: {e}")
            return False

    def set_ssh_config(self, ssh_key: str, ssh_host: str = None) -> Tuple[bool, str]:
        """Set SSH configuration."""
        if not ssh_key or not ssh_key.strip():
            # Clear SSH configuration
            if "GIT_SSH_COMMAND" in os.environ:
                del os.environ["GIT_SSH_COMMAND"]
            return True, "SSH configuration cleared"

        # Expand user path
        key_path = Path(ssh_key).expanduser()

        # Build SSH command
        ssh_command = f"ssh -i {key_path}"

        # Add host-specific configuration if provided
        if ssh_host and ssh_host.strip():
            ssh_command += " -o 'UserKnownHostsFile=/dev/null' -o 'StrictHostKeyChecking=no'"

        # Set environment variable
        os.environ["GIT_SSH_COMMAND"] = ssh_command

        logger.info(f"Set SSH configuration: {ssh_command}")
        return True, f"SSH configured: {ssh_command}"

    def set_git_config(self, account_info: dict, scope: str = "local") -> bool:
        """Set complete git configuration for an account."""
        if scope not in VALID_SCOPES:
            logger.error(f"Invalid scope: {scope}")
            return False

        success = True

        # If setting global scope, clear local configs first
        if scope == "global":
            cleared_configs = self.clear_local_git_config()
            if cleared_configs:
                logger.info(f"Cleared local git config: {', '.join(cleared_configs)}")

        # Set basic user config
        if not self.set_basic_config(account_info["name"], account_info["email"], scope):
            success = False

        # Set GPG configuration
        gpg_key = account_info.get("gpg_key", "").strip()
        signing_enabled = account_info.get("signing_enabled", False)

        if not self.set_gpg_config(gpg_key, signing_enabled, scope):
            success = False

        # Set SSH configuration
        ssh_key = account_info.get("ssh_key", "").strip()
        ssh_host = account_info.get("ssh_host", "").strip()

        ssh_success, ssh_message = self.set_ssh_config(ssh_key, ssh_host)
        if not ssh_success:
            logger.warning(f"SSH configuration failed: {ssh_message}")
            # Don't fail the entire operation for SSH issues

        if success:
            logger.info(f"Successfully configured git for: {account_info['description']} ({scope})")

        return success

    def get_git_scope_info(self) -> dict:
        """Get git configuration scope information."""
        return {
            "global": {
                "name": self.get_current_config("global")[0],
                "email": self.get_current_config("global")[1],
                "gpg": self.get_gpg_config("global"),
            },
            "local": {
                "name": self.get_current_config("local")[0],
                "email": self.get_current_config("local")[1],
                "gpg": self.get_gpg_config("local"),
            },
            "ssh": self.get_ssh_config(),
        }

    def is_git_repository(self) -> bool:
        """Check if current directory is a git repository."""
        result = self.run_git_command("git rev-parse --git-dir", silent=True)
        return result is not None

    def get_repository_info(self) -> dict:
        """Get information about the current git repository."""
        if not self.is_git_repository():
            return {"is_repo": False}

        repo_info = {"is_repo": True}

        # Get repository path
        git_dir = self.run_git_command("git rev-parse --git-dir", silent=True)
        if git_dir:
            repo_info["git_dir"] = git_dir

        # Get current branch
        branch = self.run_git_command("git branch --show-current", silent=True)
        if branch:
            repo_info["current_branch"] = branch

        # Get remote origin URL
        origin_url = self.run_git_command("git config --get remote.origin.url", silent=True)
        if origin_url:
            repo_info["origin_url"] = origin_url

        return repo_info
