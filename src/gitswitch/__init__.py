"""Git Account Switcher - Easy switching between git user configurations."""

__version__ = "1.1.0"

# Expose main functions for programmatic use
from .config import load_accounts, get_config_path
from .git_ops import get_current_config, set_git_config
from .accounts import add_account, remove_account
from .main import cli

__all__ = [
    "load_accounts",
    "get_config_path", 
    "get_current_config",
    "set_git_config",
    "add_account",
    "remove_account",
    "cli"
]
