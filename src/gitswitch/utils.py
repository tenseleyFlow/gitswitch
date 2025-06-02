"""Core utility functions for gitswitch."""

import logging
import subprocess
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def normalize_account_key(key) -> int:
    """Convert account key to integer, handling string keys from TOML."""
    try:
        return int(key)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid account key: {key} (must be a number)")


def run_command_safe(command: str, silent: bool = False) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Run a shell command safely with proper error handling.

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception
        )

        success = result.returncode == 0
        stdout = result.stdout.strip() if result.stdout else None
        stderr = result.stderr.strip() if result.stderr else None

        if not silent and not success:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {stderr}")

        return success, stdout, stderr

    except Exception as e:
        if not silent:
            logger.error(f"Exception running command '{command}': {e}")
        return False, None, str(e)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return bool(email and "@" in email and "." in email.split("@")[1])


def safe_input(prompt: str, default: str = None) -> str:
    """Safe input with default value handling."""
    try:
        value = input(prompt).strip()
        return value if value else (default or "")
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Input cancelled")
        raise KeyboardInterrupt()
