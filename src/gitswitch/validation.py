"""Secure validation for gitswitch."""

import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

from .constants import VALID_SCOPES, REQUIRED_ACCOUNT_FIELDS, DEFAULT_SCOPE
from .utils import validate_email, run_command_safe, validate_gpg_key_format, validate_ssh_key_path, sanitize_git_input

logger = logging.getLogger(__name__)


class ValidationService:
    """Secure validation service - returns tuples and sanitizes inputs."""

    def validate_account(self, account_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate and sanitize account data. Returns (is_valid, errors, warnings).

        This method also sanitizes inputs to prevent injection attacks.
        """
        errors = []
        warnings = []

        # Check required fields and sanitize them
        for field in REQUIRED_ACCOUNT_FIELDS:
            value = account_data.get(field, "")
            if not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
                continue

            # Sanitize the field
            sanitized_value = sanitize_git_input(value)
            if not sanitized_value.strip():
                errors.append(f"Missing required field: {field}")
            elif sanitized_value != value:
                warnings.append(f"Field '{field}' was sanitized (removed dangerous characters)")
                # Update the account data with sanitized value
                account_data[field] = sanitized_value

        # Validate email format and security
        email = account_data.get("email", "").strip()
        if email:
            if not validate_email(email):
                errors.append(f"Invalid email format: {email}")
            else:
                # Additional email security checks
                if len(email) > 254:
                    errors.append("Email address is too long (max 254 characters)")

                # Check for suspicious patterns that might indicate injection attempts
                suspicious_patterns = ["javascript:", "data:", "vbscript:", "<script", "onclick="]
                if any(pattern in email.lower() for pattern in suspicious_patterns):
                    errors.append("Email contains suspicious content")

        # Validate scope
        scope = account_data.get("preferred_scope", DEFAULT_SCOPE)
        if scope not in VALID_SCOPES:
            errors.append(f"Invalid scope '{scope}'. Must be one of: {', '.join(VALID_SCOPES)}")

        # Validate and secure GPG configuration
        gpg_key = account_data.get("gpg_key", "").strip()
        signing_enabled = account_data.get("signing_enabled", False)

        if gpg_key:
            # Sanitize GPG key
            sanitized_gpg_key = sanitize_git_input(gpg_key)
            if sanitized_gpg_key != gpg_key:
                warnings.append("GPG key was sanitized (removed dangerous characters)")
                account_data["gpg_key"] = sanitized_gpg_key
                gpg_key = sanitized_gpg_key

            # Validate GPG key format
            if not validate_gpg_key_format(gpg_key):
                warnings.append(f"GPG key format may be invalid: {gpg_key}")

            # Check if GPG key actually exists
            if not self._check_gpg_key_safe(gpg_key):
                errors.append(f"GPG key {gpg_key} not found or invalid")

        # Check GPG consistency
        if signing_enabled and not gpg_key:
            errors.append("GPG signing enabled but no key provided")
        elif gpg_key and not signing_enabled:
            warnings.append("GPG key provided but signing is disabled")

        # Validate and secure SSH configuration
        ssh_key = account_data.get("ssh_key", "").strip()
        if ssh_key:
            # Sanitize SSH key path
            sanitized_ssh_key = sanitize_git_input(ssh_key)
            if sanitized_ssh_key != ssh_key:
                warnings.append("SSH key path was sanitized (removed dangerous characters)")
                account_data["ssh_key"] = sanitized_ssh_key
                ssh_key = sanitized_ssh_key

            # Validate SSH key path security
            if not validate_ssh_key_path(ssh_key):
                warnings.append(f"SSH key path appears to be outside safe directories: {ssh_key}")

            # Check if SSH key file exists and is valid
            if not self._check_ssh_key_safe(ssh_key):
                errors.append(f"SSH key file not found or invalid: {ssh_key}")

        # Sanitize SSH host if provided
        ssh_host = account_data.get("ssh_host", "").strip()
        if ssh_host:
            sanitized_ssh_host = sanitize_git_input(ssh_host)
            if sanitized_ssh_host != ssh_host:
                warnings.append("SSH host was sanitized (removed dangerous characters)")
                account_data["ssh_host"] = sanitized_ssh_host

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration structure and content."""
        errors = []
        warnings = []

        if not isinstance(config_data, dict):
            return False, ["Config must be a dictionary/object"], []

        # Check settings section
        settings = config_data.get("settings", {})
        if settings:
            if not isinstance(settings, dict):
                errors.append("Settings section must be a dictionary")
            else:
                default_scope = settings.get("default_scope")
                if default_scope and default_scope not in VALID_SCOPES:
                    errors.append(f"Invalid default scope '{default_scope}'")

        # Check accounts section
        accounts = config_data.get("accounts", {})
        if not accounts:
            warnings.append("No accounts defined")
        else:
            if not isinstance(accounts, dict):
                errors.append("Accounts section must be a dictionary")
            else:
                for account_key, account in accounts.items():
                    if not isinstance(account, dict):
                        errors.append(f"Account {account_key} must be a dictionary")
                        continue

                    # Validate account key format (should be numeric)
                    try:
                        int(account_key)
                    except (ValueError, TypeError):
                        errors.append(f"Account key '{account_key}' must be numeric")

                    # Validate individual account
                    is_valid, acc_errors, acc_warnings = self.validate_account(account)
                    # Prefix with account key for clarity
                    errors.extend([f"Account {account_key}: {err}" for err in acc_errors])
                    warnings.extend([f"Account {account_key}: {warn}" for warn in acc_warnings])

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def validate_system_requirements(self) -> Tuple[bool, List[str], List[str]]:
        """Validate system requirements safely."""
        errors = []
        warnings = []

        required_tools = [
            ("git", ["git", "--version"]),
            ("gpg", ["gpg", "--version"]),
            ("ssh", ["ssh", "-V"]),
            ("ssh-keygen", ["ssh-keygen", "-V"]),
        ]

        for tool, check_cmd in required_tools:
            success, _, _ = run_command_safe(check_cmd, silent=True)
            if not success:
                errors.append(f"Required tool not found: {tool}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def get_system_info(self) -> Dict[str, Dict[str, str]]:
        """Get system tool information safely."""
        info = {}
        required_tools = [
            ("git", ["git", "--version"]),
            ("gpg", ["gpg", "--version"]),
            ("ssh", ["ssh", "-V"]),
            ("ssh-keygen", ["ssh-keygen", "-V"]),
        ]

        for tool, check_cmd in required_tools:
            success, stdout, stderr = run_command_safe(check_cmd, silent=True)
            if success:
                # Get the first line of output and sanitize it
                output = stdout or stderr or ""
                version = sanitize_git_input(output.split("\n")[0]) if output else "Unknown"
                info[tool] = {"status": "available", "version": version}
            else:
                info[tool] = {"status": "missing", "version": None}

        return info

    def get_gpg_key_info(self, gpg_key: str) -> str:
        """Get GPG key info for display safely."""
        try:
            # Sanitize GPG key first
            gpg_key = sanitize_git_input(gpg_key)
            if not gpg_key:
                return "Invalid GPG key"

            # Validate format
            if not validate_gpg_key_format(gpg_key):
                return "GPG key format appears invalid"

            # Build safe command
            cmd = ["gpg", "--list-secret-keys", "--keyid-format=long", gpg_key]
            success, stdout, _ = run_command_safe(cmd, silent=True)

            if success and stdout:
                # Look for uid line and sanitize it
                for line in stdout.split("\n"):
                    if "uid" in line:
                        # Extract just the email/name part, not the full line
                        uid_line = sanitize_git_input(line.strip())
                        # Further sanitize by only keeping printable chars and basic punctuation
                        safe_uid = "".join(c for c in uid_line if c.isprintable() and c not in "<>&|;`$")
                        return f"Valid key: {safe_uid[:100]}"  # Limit length too

            return "GPG key is valid"

        except Exception as e:
            logger.warning(f"Error getting GPG key info: {e}")
            return "GPG key validation failed"

    def get_ssh_key_info(self, ssh_key: str) -> str:
        """Get SSH key info for display safely."""
        try:
            # Sanitize SSH key path
            ssh_key = sanitize_git_input(ssh_key)
            if not ssh_key:
                return "Invalid SSH key path"

            # Validate path security
            if not validate_ssh_key_path(ssh_key):
                return "SSH key path appears unsafe"

            key_path = Path(ssh_key).expanduser()

            # Build safe command
            cmd = ["ssh-keygen", "-l", "-f", str(key_path)]
            success, stdout, _ = run_command_safe(cmd, silent=True)

            if success and stdout:
                # Sanitize output and limit length
                safe_output = sanitize_git_input(stdout.strip())
                return safe_output[:200]  # Limit output length
            else:
                return "SSH key validation failed"

        except Exception as e:
            logger.warning(f"Error getting SSH key info: {e}")
            return f"SSH key validation failed"

    def _check_gpg_key_safe(self, gpg_key: str) -> bool:
        """Check if GPG key exists safely."""
        try:
            # Sanitize and validate first
            gpg_key = sanitize_git_input(gpg_key)
            if not gpg_key or not validate_gpg_key_format(gpg_key):
                return False

            # Build safe command
            cmd = ["gpg", "--list-secret-keys", "--keyid-format=long", gpg_key]
            success, stdout, _ = run_command_safe(cmd, silent=True)

            return success and gpg_key in (stdout or "")

        except Exception as e:
            logger.warning(f"Error checking GPG key: {e}")
            return False

    def _check_ssh_key_safe(self, ssh_key: str) -> bool:
        """Check if SSH key file exists and is valid safely."""
        try:
            # Sanitize and validate path first
            ssh_key = sanitize_git_input(ssh_key)
            if not ssh_key:
                return False

            if not validate_ssh_key_path(ssh_key):
                logger.warning(f"SSH key path validation failed: {ssh_key}")
                # Continue anyway - user may have valid reason

            key_path = Path(ssh_key).expanduser()

            # Check file existence and permissions
            if not key_path.exists() or not key_path.is_file():
                return False

            # Check if it's readable
            if not os.access(key_path, os.R_OK):
                return False

            # Validate the key format using ssh-keygen
            cmd = ["ssh-keygen", "-l", "-f", str(key_path)]
            success, _, _ = run_command_safe(cmd, silent=True)

            return success

        except Exception as e:
            logger.warning(f"Error checking SSH key: {e}")
            return False
