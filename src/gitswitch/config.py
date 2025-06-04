"""Configuration management"""

import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

# Handle TOML parsing for different Python versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    import tomli_w
except ImportError:
    from .colors import format_status
    print(format_status("[ERROR] tomli_w is required for configuration management"))
    print("   Install with: pip install tomli_w")
    sys.exit(1)

from .constants import DEFAULT_SCOPE
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Simplified configuration manager focused on file I/O only."""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config_cache = None

    def _get_default_config_path(self) -> Path:
        """Get the default path to the configuration file."""
        config_dir = Path.home() / ".config" / "gitswitch"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "accounts.toml"

    def _clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache = None

    def get_config_path(self) -> Path:
        """Get the configuration file path."""
        return self.config_path

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_path.exists()

    def create_default_config(self) -> Tuple[bool, str]:
        """Create a default configuration file. Returns (success, message)."""
        default_config = """# Git Switcher Account Configuration

[settings]
default_scope = "local"  # Options: "local", "global"

[accounts.1]
name = "You"
email = "your@email.com"
description = "Default Account"
preferred_scope = "local"     # Optional: override default scope for this account
gpg_key = ""                  # Optional: GPG key ID for signing (e.g., "ABC123DEF456")
signing_enabled = false       # Optional: enable GPG signing for this account
ssh_key = ""                  # Optional: SSH key file path (e.g., "~/.ssh/id_rsa_personal")
ssh_host = ""                 # Optional: Custom SSH host (e.g., "github.com-personal")

# Example with full configuration:
# [accounts.2]
# name = "Your Name"
# email = "work@company.com"
# description = "Work Account"
# preferred_scope = "global"
# gpg_key = "ABC123DEF456"              # Your GPG key ID
# signing_enabled = true                # Enable GPG signing
# ssh_key = "~/.ssh/id_rsa_work"        # SSH key for this account
# ssh_host = "github.com-work"          # Custom SSH host alias
"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(default_config)
            logger.info(f"Created default config file at: {self.config_path}")
            return True, f"Created default configuration at {self.config_path}"
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            return False, f"Could not create default configuration: {e}"

    def load_config(self, force_reload: bool = False) -> Tuple[bool, Dict, str]:
        """Load configuration from TOML file with caching. Returns (success, config_data, message)."""
        if self._config_cache is None or force_reload:
            if not self.config_exists():
                logger.info("Configuration file not found, creating default")
                success, message = self.create_default_config()
                if not success:
                    return False, {}, f"Failed to create default config: {message}"

            try:
                with open(self.config_path, "rb") as f:
                    self._config_cache = tomllib.load(f)
                logger.debug(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return False, {}, f"Could not load configuration file: {e}"

        return True, self._config_cache.copy(), "Configuration loaded successfully"

    def save_config(self, config: Dict) -> Tuple[bool, str]:
        """Save configuration to TOML file. Returns (success, message)."""
        try:
            # Create backup if config exists
            if self.config_exists():
                backup_path = self.config_path.with_suffix(".toml.backup")
                backup_path.write_bytes(self.config_path.read_bytes())
                logger.debug(f"Created backup at {backup_path}")

            # Save new config
            with open(self.config_path, "wb") as f:
                tomli_w.dump(config, f)

            # Clear cache to force reload
            self._clear_cache()

            logger.info(f"Saved configuration to {self.config_path}")
            return True, f"Configuration saved to {self.config_path}"

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False, f"Could not save configuration file: {e}"

    def get_default_scope(self) -> Tuple[bool, str, str]:
        """Get the default scope from configuration. Returns (success, scope, message)."""
        success, config, message = self.load_config()
        if not success:
            return False, DEFAULT_SCOPE, f"Could not load config, using default scope: {message}"
        
        scope = config.get("settings", {}).get("default_scope", DEFAULT_SCOPE)
        return True, scope, f"Default scope: {scope}"

    def backup_config(self) -> Tuple[bool, Path, str]:
        """Create a backup of the current configuration. Returns (success, backup_path, message)."""
        if not self.config_exists():
            return False, None, "No configuration file to backup"

        import time

        timestamp = str(int(time.time()))
        backup_path = self.config_path.with_suffix(f".backup.{timestamp}.toml")

        try:
            backup_path.write_bytes(self.config_path.read_bytes())
            logger.info(f"Created configuration backup at {backup_path}")
            return True, backup_path, f"Backup created at {backup_path}"
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False, None, f"Could not create backup: {e}"

    # Legacy methods for backward compatibility (these raise exceptions as before)
    # These can be removed once all calling code is updated
    
    def load_config_legacy(self, force_reload: bool = False) -> Dict:
        """Legacy method - raises exceptions. Use load_config() instead."""
        success, config, message = self.load_config(force_reload)
        if not success:
            raise ConfigurationError(message)
        return config

    def save_config_legacy(self, config: Dict) -> bool:
        """Legacy method - raises exceptions. Use save_config() instead."""
        success, message = self.save_config(config)
        if not success:
            raise ConfigurationError(message)
        return True

    def get_default_scope_legacy(self) -> str:
        """Legacy method - raises exceptions. Use get_default_scope() instead."""
        success, scope, message = self.get_default_scope()
        if not success:
            raise ConfigurationError(message)
        return scope

    def backup_config_legacy(self) -> Path:
        """Legacy method - raises exceptions. Use backup_config() instead."""
        success, backup_path, message = self.backup_config()
        if not success:
            raise ConfigurationError(message)
        return backup_path