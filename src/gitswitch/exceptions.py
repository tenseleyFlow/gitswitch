"""Custom exceptions for gitswitch."""


class GitSwitchError(Exception):
    """Base exception for gitswitch errors."""

    pass


class ConfigurationError(GitSwitchError):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class ValidationError(GitSwitchError):
    """Raised when validation fails."""

    pass


class AccountNotFoundError(GitSwitchError):
    """Raised when requested account cannot be found."""

    pass


class GitOperationError(GitSwitchError):
    """Raised when git operations fail."""

    pass


class KeyValidationError(ValidationError):
    """Raised when GPG or SSH key validation fails."""

    pass
