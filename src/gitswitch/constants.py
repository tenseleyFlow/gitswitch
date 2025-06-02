"""Constants for gitswitch."""

# Display formatting
SEPARATOR_LONG = "=" * 60
SEPARATOR_SHORT = "=" * 30
SEPARATOR_MEDIUM = "=" * 50

# Configuration
DEFAULT_SCOPE = "local"
VALID_SCOPES = ["local", "global"]
REQUIRED_ACCOUNT_FIELDS = ["name", "email", "description"]

# Messages that are reused
MSG_NO_ACCOUNTS = "[WARN] No valid accounts found in configuration file!"
ERR_EMPTY_NAME = "[ERROR] Name cannot be empty"
ERR_INVALID_EMAIL = "[ERROR] Please enter a valid email address"