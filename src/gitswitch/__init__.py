"""Git Account Switcher - Easy switching between git user configurations."""

__version__ = "2.1.0"

# Core functionality
from .main import cli, GitSwitchCLI
from .doctor import run_health_check

# Basic logging setup
from .error_handling import setup_logging, get_logger, LoggerMixin

# Validation system (simplified - returns tuples now)
from .validation import ValidationService

# Core management classes
from .config import ConfigManager
from .accounts import AccountManager
from .git_ops import GitOperations
from .display import DisplayManager

# Interactive functions (simplified - fewer functions now)
from .interactive import (
    add_account_interactive,
    edit_account_interactive,
    remove_account_interactive,
    edit_config_file_interactive,
    collect_account_info,
    ask_yes_no,
)

# Utilities
from .utils import normalize_account_key, validate_email

# Exceptions
from .exceptions import (
    GitSwitchError,
    ConfigurationError,
    ValidationError,
    AccountNotFoundError,
    GitOperationError,
    KeyValidationError,
)

# Constants
from .constants import DEFAULT_SCOPE, VALID_SCOPES, REQUIRED_ACCOUNT_FIELDS

__all__ = [
    # Core functionality
    "cli",
    "GitSwitchCLI",
    "run_health_check",
    # Basic logging
    "setup_logging",
    "get_logger",
    "LoggerMixin",
    # Validation system (simplified)
    "ValidationService",
    # Management classes
    "ConfigManager",
    "AccountManager",
    "GitOperations",
    "DisplayManager",
    # Interactive functions
    "add_account_interactive",
    "edit_account_interactive",
    "remove_account_interactive",
    "edit_config_file_interactive",
    "collect_account_info",
    "ask_yes_no",
    # Utilities
    "normalize_account_key",
    "validate_email",
    # Exceptions
    "GitSwitchError",
    "ConfigurationError",
    "ValidationError",
    "AccountNotFoundError",
    "GitOperationError",
    "KeyValidationError",
    # Constants
    "DEFAULT_SCOPE",
    "VALID_SCOPES",
    "REQUIRED_ACCOUNT_FIELDS",
]
