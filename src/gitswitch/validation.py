"""Simple validation for gitswitch."""

from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

from .constants import VALID_SCOPES, REQUIRED_ACCOUNT_FIELDS, DEFAULT_SCOPE
from .utils import validate_email, run_command_safe

logger = logging.getLogger(__name__)


class ValidationService:
    """Simple validation service - returns tuples instead of complex objects."""

    def validate_account(self, account_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate account data. Returns (is_valid, errors, warnings)."""
        errors = []
        warnings = []

        # Check required fields
        for field in REQUIRED_ACCOUNT_FIELDS:
            if not account_data.get(field, "").strip():
                errors.append(f"Missing required field: {field}")

        # Validate email
        email = account_data.get("email", "").strip()
        if email and not validate_email(email):
            errors.append(f"Invalid email format: {email}")

        # Validate scope
        scope = account_data.get("preferred_scope", DEFAULT_SCOPE)
        if scope not in VALID_SCOPES:
            errors.append(f"Invalid scope '{scope}'. Must be one of: {', '.join(VALID_SCOPES)}")

        # Validate GPG
        gpg_key = account_data.get("gpg_key", "").strip()
        signing_enabled = account_data.get("signing_enabled", False)

        if signing_enabled and not gpg_key:
            errors.append("GPG signing enabled but no key provided")
        elif gpg_key:
            if not self._check_gpg_key(gpg_key):
                errors.append(f"GPG key {gpg_key} not found or invalid")
            elif not signing_enabled:
                warnings.append("GPG key provided but signing is disabled")

        # Validate SSH
        ssh_key = account_data.get("ssh_key", "").strip()
        if ssh_key and not self._check_ssh_key(ssh_key):
            errors.append(f"SSH key file not found or invalid: {ssh_key}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration. Returns (is_valid, errors, warnings)."""
        errors = []
        warnings = []

        if not isinstance(config_data, dict):
            return False, ["Config must be a dictionary/object"], []

        # Check settings
        settings = config_data.get("settings", {})
        if settings:
            default_scope = settings.get("default_scope")
            if default_scope and default_scope not in VALID_SCOPES:
                errors.append(f"Invalid default scope '{default_scope}'")

        # Check accounts
        accounts = config_data.get("accounts", {})
        if not accounts:
            warnings.append("No accounts defined")
        else:
            for account_key, account in accounts.items():
                if not isinstance(account, dict):
                    errors.append(f"Account {account_key} must be a dictionary")
                    continue

                is_valid, acc_errors, acc_warnings = self.validate_account(account)
                # Prefix with account key
                errors.extend([f"Account {account_key}: {err}" for err in acc_errors])
                warnings.extend([f"Account {account_key}: {warn}" for warn in acc_warnings])

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def validate_system_requirements(self) -> Tuple[bool, List[str], List[str]]:
        """Validate system requirements. Returns (is_valid, errors, warnings)."""
        errors = []
        warnings = []

        required_tools = [
            ("git", "git --version"),
            ("gpg", "gpg --version"),
            ("ssh", "ssh -V"),
            ("ssh-keygen", "ssh-keygen -V"),
        ]

        for tool, check_cmd in required_tools:
            success, _, _ = run_command_safe(check_cmd, silent=True)
            if not success:
                errors.append(f"Required tool not found: {tool}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def get_system_info(self) -> Dict[str, Dict[str, str]]:
        """Get system tool information."""
        info = {}
        required_tools = [
            ("git", "git --version"),
            ("gpg", "gpg --version"),
            ("ssh", "ssh -V"),
            ("ssh-keygen", "ssh-keygen -V"),
        ]

        for tool, check_cmd in required_tools:
            success, stdout, stderr = run_command_safe(check_cmd, silent=True)
            if success:
                version = (stdout or stderr or "").split("\n")[0] if (stdout or stderr) else "Unknown"
                info[tool] = {"status": "available", "version": version}
            else:
                info[tool] = {"status": "missing", "version": None}

        return info

    def get_gpg_key_info(self, gpg_key: str) -> str:
        """Get GPG key info for display."""
        try:
            success, stdout, _ = run_command_safe(f"gpg --list-secret-keys --keyid-format=long {gpg_key}", silent=True)
            if success and stdout:
                for line in stdout.split("\n"):
                    if "uid" in line:
                        return line.strip()
            return "GPG key is valid"
        except Exception:
            return "GPG key validation failed"

    def get_ssh_key_info(self, ssh_key: str) -> str:
        """Get SSH key info for display."""
        try:
            key_path = Path(ssh_key).expanduser()
            success, stdout, _ = run_command_safe(f"ssh-keygen -l -f {key_path}", silent=True)
            return stdout.strip() if success and stdout else "SSH key is valid"
        except Exception as e:
            return f"SSH key validation failed: {e}"

    def _check_gpg_key(self, gpg_key: str) -> bool:
        """Check if GPG key exists."""
        success, stdout, _ = run_command_safe(f"gpg --list-secret-keys --keyid-format=long {gpg_key}", silent=True)
        return success and gpg_key in (stdout or "")

    def _check_ssh_key(self, ssh_key: str) -> bool:
        """Check if SSH key file exists and is valid."""
        try:
            key_path = Path(ssh_key).expanduser()
            if not key_path.exists() or not key_path.is_file():
                return False

            success, _, _ = run_command_safe(f"ssh-keygen -l -f {key_path}", silent=True)
            return success
        except Exception:
            return False
