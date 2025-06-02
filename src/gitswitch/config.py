"""Configuration management"""

import logging
import sys
from pathlib import Path
from typing import Dict

# Handle TOML parsing for different Python versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    import tomli_w
except ImportError:
    print("❌ tomli_w is required for configuration management")
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

    def create_default_config(self) -> bool:
        """Create a default configuration file."""
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
            return True
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            raise ConfigurationError(f"Could not create default configuration: {e}")

    def load_config(self, force_reload: bool = False) -> Dict:
        """Load configuration from TOML file with caching."""
        if self._config_cache is None or force_reload:
            if not self.config_exists():
                logger.info("Configuration file not found, creating default")
                self.create_default_config()

            try:
                with open(self.config_path, "rb") as f:
                    self._config_cache = tomllib.load(f)
                logger.debug(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                raise ConfigurationError(f"Could not load configuration file: {e}")

        return self._config_cache.copy()

    def save_config(self, config: Dict) -> bool:
        """Save configuration to TOML file."""
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
            return True

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise ConfigurationError(f"Could not save configuration file: {e}")

    def get_default_scope(self) -> str:
        """Get the default scope from configuration."""
        config = self.load_config()
        return config.get("settings", {}).get("default_scope", DEFAULT_SCOPE)

    def backup_config(self) -> Path:
        """Create a backup of the current configuration."""
        if not self.config_exists():
            raise ConfigurationError("No configuration file to backup")

        import time

        timestamp = str(int(time.time()))
        backup_path = self.config_path.with_suffix(f".backup.{timestamp}.toml")

        try:
            backup_path.write_bytes(self.config_path.read_bytes())
            logger.info(f"Created configuration backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise ConfigurationError(f"Could not create backup: {e}")
