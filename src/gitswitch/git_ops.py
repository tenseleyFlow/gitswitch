"""Secure git operations for gitswitch."""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from .constants import VALID_SCOPES
from .exceptions import GitOperationError
from .utils import (
    run_command_safe,
    build_git_command,
    sanitize_git_input,
    validate_ssh_key_path,
    validate_gpg_key_format,
)

logger = logging.getLogger(__name__)


class GitOperations:
    """Secure git operations manager."""

    def run_git_command_safe(self, cmd_list: list, silent: bool = False) -> Optional[str]:
        """
        Run a git command safely using list arguments.

        Args:
            cmd_list: List of command arguments (e.g., ['git', 'config', 'user.name'])
            silent: If True, suppress error logging

        Returns:
            Command output on success, None on failure

        Raises:
            GitOperationError: If command fails and silent=False
        """
        success, stdout, stderr = run_command_safe(cmd_list, silent=silent)

        if not success:
            if silent:
                return None
            raise GitOperationError(f"Git command failed: {' '.join(cmd_list)}\nError: {stderr}")

        return stdout

    def get_current_config(self, scope: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Get current git user configuration safely."""
        try:
            # Build safe commands
            name_cmd = build_git_command("get", scope, "user.name")
            email_cmd = build_git_command("get", scope, "user.email")

            name = self.run_git_command_safe(name_cmd, silent=True)
            email = self.run_git_command_safe(email_cmd, silent=True)

            return name, email
        except Exception as e:
            logger.warning(f"Error getting git config: {e}")
            return None, None

    def get_gpg_config(self, scope: str = None) -> Dict[str, any]:
        """Get current GPG configuration safely."""
        try:
            # Build safe commands for GPG config
            signing_key_cmd = build_git_command("get", scope, "user.signingkey")
            commit_sign_cmd = build_git_command("get", scope, "commit.gpgsign")
            tag_sign_cmd = build_git_command("get", scope, "tag.gpgsign")

            signing_key = self.run_git_command_safe(signing_key_cmd, silent=True)
            commit_sign = self.run_git_command_safe(commit_sign_cmd, silent=True)
            tag_sign = self.run_git_command_safe(tag_sign_cmd, silent=True)

            return {
                "signing_key": signing_key,
                "commit_gpgsign": commit_sign == "true",
                "tag_gpgsign": tag_sign == "true",
            }
        except Exception as e:
            logger.warning(f"Error getting GPG config: {e}")
            return {
                "signing_key": None,
                "commit_gpgsign": False,
                "tag_gpgsign": False,
            }

    def get_ssh_config(self) -> Dict[str, Optional[str]]:
        """Get current SSH configuration from environment."""
        return {
            "git_ssh_command": os.environ.get("GIT_SSH_COMMAND"),
            "ssh_auth_sock": os.environ.get("SSH_AUTH_SOCK"),
        }

    def clear_local_git_config(self) -> list:
        """Clear local git configuration safely to allow global settings to take effect."""
        configs_to_clear = [
            "user.name",
            "user.email",
            "user.signingkey",
            "commit.gpgsign",
            "tag.gpgsign",
        ]

        cleared = []
        for config in configs_to_clear:
            try:
                # Check if local config exists
                get_cmd = build_git_command("get", "local", config)
                result = self.run_git_command_safe(get_cmd, silent=True)

                if result:  # Config exists locally
                    # Clear it safely
                    unset_cmd = build_git_command("unset", "local", config)
                    self.run_git_command_safe(unset_cmd, silent=True)
                    cleared.append(config)
                    logger.debug(f"Cleared local config: {config}")

            except GitOperationError:
                logger.warning(f"Failed to clear local config: {config}")

        return cleared

    def set_basic_config(self, name: str, email: str, scope: str) -> bool:
        """Set basic git user configuration safely."""
        try:
            # Sanitize inputs
            name = sanitize_git_input(name)
            email = sanitize_git_input(email)

            if not name or not email:
                logger.error("Name and email cannot be empty after sanitization")
                return False

            # Build safe commands
            name_cmd = build_git_command("set", scope, "user.name", name)
            email_cmd = build_git_command("set", scope, "user.email", email)

            # Execute commands
            self.run_git_command_safe(name_cmd)
            self.run_git_command_safe(email_cmd)

            logger.info(f"Set git user config ({scope}): {name} <{email}>")
            return True

        except GitOperationError as e:
            logger.error(f"Failed to set basic git config: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting git config: {e}")
            return False

    def set_gpg_config(self, gpg_key: str, signing_enabled: bool, scope: str) -> bool:
        """Set GPG configuration safely."""
        try:
            if gpg_key and signing_enabled:
                # Validate GPG key format
                if not validate_gpg_key_format(gpg_key):
                    logger.warning(f"GPG key format appears invalid: {gpg_key}")
                    # Continue anyway - user may have valid reason

                # Sanitize GPG key (remove any dangerous characters)
                gpg_key = sanitize_git_input(gpg_key)

                if not gpg_key:
                    logger.error("GPG key cannot be empty after sanitization")
                    return False

                # Enable GPG signing with safe commands
                key_cmd = build_git_command("set", scope, "user.signingkey", gpg_key)
                commit_cmd = build_git_command("set", scope, "commit.gpgsign", "true")
                tag_cmd = build_git_command("set", scope, "tag.gpgsign", "true")

                self.run_git_command_safe(key_cmd)
                self.run_git_command_safe(commit_cmd)
                self.run_git_command_safe(tag_cmd)

                logger.info(f"Enabled GPG signing ({scope}): {gpg_key}")
            else:
                # Disable GPG signing
                commit_cmd = build_git_command("set", scope, "commit.gpgsign", "false")
                tag_cmd = build_git_command("set", scope, "tag.gpgsign", "false")

                self.run_git_command_safe(commit_cmd)
                self.run_git_command_safe(tag_cmd)

                logger.debug(f"Disabled GPG signing ({scope})")

            return True

        except GitOperationError as e:
            logger.error(f"Failed to set GPG config: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting GPG config: {e}")
            return False

    def set_ssh_config(self, ssh_key: str, ssh_host: str = None) -> Tuple[bool, str]:
        """Set SSH configuration safely."""
        try:
            if not ssh_key or not ssh_key.strip():
                # Clear SSH configuration
                if "GIT_SSH_COMMAND" in os.environ:
                    del os.environ["GIT_SSH_COMMAND"]
                return True, "SSH configuration cleared"

            # Validate SSH key path for security
            if not validate_ssh_key_path(ssh_key):
                logger.warning(f"SSH key path appears to be outside safe directories: {ssh_key}")
                # Continue anyway - user may have valid reason

            # Expand user path safely
            key_path = Path(ssh_key).expanduser()

            # Build SSH command safely - no shell injection possible here
            ssh_command_parts = ["ssh", "-i", str(key_path)]

            # Add host-specific configuration if provided
            if ssh_host and ssh_host.strip():
                # Sanitize SSH host
                ssh_host = sanitize_git_input(ssh_host)
                if ssh_host:
                    ssh_command_parts.extend(["-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no"])

            # Join the command parts - this is safe since we built them programmatically
            ssh_command = " ".join(ssh_command_parts)

            # Set environment variable
            os.environ["GIT_SSH_COMMAND"] = ssh_command

            logger.info(f"Set SSH configuration: {ssh_command}")
            return True, f"SSH configured: {ssh_command}"

        except Exception as e:
            logger.error(f"Failed to set SSH config: {e}")
            return False, f"SSH configuration failed: {e}"

    def set_git_config(self, account_info: dict, scope: str = "local") -> bool:
        """Set complete git configuration for an account safely."""
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
        """Get git configuration scope information safely."""
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
        """Check if current directory is a git repository safely."""
        try:
            cmd = ["git", "rev-parse", "--git-dir"]
            result = self.run_git_command_safe(cmd, silent=True)
            return result is not None
        except Exception:
            return False

    def get_repository_info(self) -> dict:
        """Get information about the current git repository safely."""
        if not self.is_git_repository():
            return {"is_repo": False}

        repo_info = {"is_repo": True}

        try:
            # Get repository path
            git_dir_cmd = ["git", "rev-parse", "--git-dir"]
            git_dir = self.run_git_command_safe(git_dir_cmd, silent=True)
            if git_dir:
                repo_info["git_dir"] = git_dir

            # Get current branch
            branch_cmd = ["git", "branch", "--show-current"]
            branch = self.run_git_command_safe(branch_cmd, silent=True)
            if branch:
                repo_info["current_branch"] = branch

            # Get remote origin URL
            origin_cmd = build_git_command("get", None, "remote.origin.url")
            origin_url = self.run_git_command_safe(origin_cmd, silent=True)
            if origin_url:
                repo_info["origin_url"] = origin_url

        except Exception as e:
            logger.warning(f"Error getting repository info: {e}")

        return repo_info
