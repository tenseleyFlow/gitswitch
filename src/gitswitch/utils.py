"""Fix for utils.py - correcting GPG key validation"""

import logging
import subprocess
import shlex
import re
from typing import Optional, Tuple, List, Union

logger = logging.getLogger(__name__)


def sanitize_git_input(value: str) -> str:
    """
    Sanitize user input for git configuration values.

    Removes dangerous shell metacharacters while preserving valid characters
    for names, emails, and descriptions.
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")

    # Remove shell metacharacters that could be dangerous
    dangerous_chars = ["`", "$", "$(", "${", ";", "&", "|", "<", ">", "\n", "\r", "\t"]
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Remove leading/trailing whitespace and collapse internal whitespace
    sanitized = " ".join(sanitized.split())

    return sanitized


def validate_git_config_key(key: str) -> bool:
    """
    Validate that a git config key is safe and properly formatted.

    Git config keys should match the pattern: section[.subsection].option
    No consecutive dots allowed.
    """
    if not isinstance(key, str) or not key:
        return False

    # Git config key pattern: letters, numbers, dots, hyphens
    # But no consecutive dots
    pattern = r"^[a-zA-Z][a-zA-Z0-9.-]*[a-zA-Z0-9]$"
    
    # Check basic pattern first
    if not re.match(pattern, key):
        return False
    
    # Check for consecutive dots (invalid)
    if ".." in key:
        return False
    
    # Check length
    if len(key) > 255:
        return False
        
    return True


def validate_gpg_key_format(gpg_key: str) -> bool:
    """
    Validate GPG key ID format.

    Accepts:
    - 8 character short form (e.g., 'ABCD1234' or 'abcd1234')
    - 16 character long form (e.g., 'ABCD1234EFGH5678')
    - 40 character full fingerprint
    """
    if not isinstance(gpg_key, str):
        return False

    gpg_key = gpg_key.strip()  # Don't convert to uppercase for validation

    # Valid GPG key patterns - accept both upper and lowercase
    patterns = [
        r"^[A-Fa-f0-9]{8}$",      # Short form (8 chars)
        r"^[A-Fa-f0-9]{16}$",     # Long form (16 chars)
        r"^[A-Fa-f0-9]{40}$"      # Full fingerprint (40 chars)
    ]

    return any(re.match(pattern, gpg_key) for pattern in patterns)


def run_command_safe(
    command: Union[str, List[str]], silent: bool = False, allow_shell: bool = False
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Run a command safely with proper error handling and security measures.

    Args:
        command: Command as string (will be split safely) or list of arguments
        silent: If True, suppress error logging
        allow_shell: If True, allows shell=True (use with extreme caution)

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)

    Security Notes:
        - Defaults to shell=False for safety
        - If command is a string, it's split using shlex.split()
        - Never use allow_shell=True with user input
    """
    try:
        # Convert string commands to list for safety
        if isinstance(command, str):
            if allow_shell:
                # Only use shell=True when explicitly requested and with sanitized input
                cmd_args = command
                use_shell = True
            else:
                # Safely split string into list to avoid shell injection
                cmd_args = shlex.split(command)
                use_shell = False
        else:
            # Command is already a list - safe to use
            cmd_args = command
            use_shell = False

        # Log the command being executed (for debugging)
        if not silent:
            logger.debug(f"Executing command: {cmd_args}")

        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
            shell=use_shell,
            timeout=30,  # Prevent hanging commands
        )

        success = result.returncode == 0
        stdout = result.stdout.strip() if result.stdout else None
        stderr = result.stderr.strip() if result.stderr else None

        if not silent and not success:
            logger.error(f"Command failed with exit code {result.returncode}: {cmd_args}")
            if stderr:
                logger.error(f"Error output: {stderr}")

        return success, stdout, stderr

    except subprocess.TimeoutExpired:
        if not silent:
            logger.error(f"Command timed out: {command}")
        return False, None, "Command timed out"
    except FileNotFoundError:
        if not silent:
            logger.error(f"Command not found: {command}")
        return False, None, "Command not found"
    except Exception as e:
        if not silent:
            logger.error(f"Exception running command '{command}': {e}")
        return False, None, str(e)


def build_git_command(operation: str, scope: str, key: str, value: str = None) -> List[str]:
    """
    Safely build git config commands using list arguments.

    Args:
        operation: 'get', 'set', 'unset'
        scope: 'local', 'global', or None
        key: Git config key (will be validated)
        value: Value to set (only for 'set' operation)

    Returns:
        List of command arguments safe for subprocess

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    if operation not in ["get", "set", "unset"]:
        raise ValueError(f"Invalid operation: {operation}")

    if scope and scope not in ["local", "global"]:
        raise ValueError(f"Invalid scope: {scope}")

    if not validate_git_config_key(key):
        raise ValueError(f"Invalid git config key: {key}")

    if operation == "set" and value is None:
        raise ValueError("Value required for 'set' operation")

    if value is not None:
        value = sanitize_git_input(value)

    # Build command as list (safe from injection)
    cmd = ["git", "config"]

    # Add scope flag
    if scope:
        cmd.append(f"--{scope}")

    # Add operation-specific arguments
    if operation == "get":
        cmd.append(key)
    elif operation == "set":
        cmd.extend([key, value])
    elif operation == "unset":
        cmd.extend(["--unset", key])

    return cmd


def normalize_account_key(key) -> int:
    """Convert account key to integer, handling string keys from TOML."""
    try:
        return int(key)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid account key: {key} (must be a number)")


def validate_email(email: str) -> bool:
    """
    Basic email validation with improved security.

    Uses a simple but effective pattern that prevents injection
    while accepting most valid email formats.
    """
    if not isinstance(email, str) or not email:
        return False

    email = email.strip()

    # Basic email pattern - conservative but safe
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Additional checks
    if not re.match(pattern, email):
        return False

    # Length check
    if len(email) > 254:  # RFC 5321 limit
        return False

    # Check for dangerous characters that shouldn't be in emails
    dangerous_chars = ["<", ">", '"', "\\", "`", "$", ";", "&", "|"]
    if any(char in email for char in dangerous_chars):
        return False

    return True


def safe_input(prompt: str, default: str = None) -> str:
    """
    Safe input with default value handling and basic sanitization.

    Args:
        prompt: Prompt to display to user
        default: Default value if user enters nothing

    Returns:
        User input, sanitized and stripped

    Raises:
        KeyboardInterrupt: If user cancels input
    """
    try:
        value = input(prompt).strip()
        result = value if value else (default or "")

        # Basic sanitization - remove null bytes and control characters
        result = "".join(char for char in result if ord(char) >= 32 or char in "\t\n")

        return result
    except (KeyboardInterrupt, EOFError):
        from .colors import format_status
        print(format_status("\n[CANCELLED] Input cancelled"))
        raise KeyboardInterrupt()


def validate_ssh_key_path(ssh_key_path: str) -> bool:
    """
    Validate that SSH key path is in a safe location.

    Only allows keys in:
    - User's .ssh directory
    - /etc/ssh directory (system keys)
    - Current directory's .ssh subdirectory (but not parent traversal)
    """
    if not isinstance(ssh_key_path, str) or not ssh_key_path:
        return False

    from pathlib import Path

    try:
        # Expand user path and resolve to absolute path
        key_path = Path(ssh_key_path).expanduser().resolve()

        # Check for path traversal attempts
        if ".." in ssh_key_path or ssh_key_path.startswith("/"):
            # Only allow absolute paths to known safe directories
            pass

        # Define safe directories
        user_ssh_dir = Path.home().resolve() / ".ssh"
        system_ssh_dir = Path("/etc/ssh").resolve()
        current_ssh_dir = Path.cwd().resolve() / ".ssh"

        # Check if path is within safe directories
        try:
            # Check if it's in user's .ssh directory
            key_path.relative_to(user_ssh_dir)
            return True
        except ValueError:
            pass

        try:
            # Check if it's in system ssh directory
            key_path.relative_to(system_ssh_dir)
            return True
        except ValueError:
            pass

        try:
            # Check if it's in current directory's .ssh (no parent traversal)
            relative_path = key_path.relative_to(current_ssh_dir)
            # Ensure no parent directory access
            if ".." not in str(relative_path):
                return True
        except ValueError:
            pass

        return False

    except (OSError, RuntimeError):
        # Path resolution failed
        return False