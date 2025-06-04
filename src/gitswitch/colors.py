# colors.py
"""Color utility for gitswitch output."""

import os
import sys
from typing import Optional

class Colors:
    """ANSI color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Status colors
    SUCCESS = '\033[92m'  # Bright green
    ERROR = '\033[91m'    # Bright red  
    WARNING = '\033[93m'  # Bright yellow
    INFO = '\033[94m'     # Bright blue
    DISABLED = '\033[90m' # Gray
    
    # Special colors
    HEADER = '\033[95m'   # Magenta
    ACCENT = '\033[96m'   # Cyan

class ColorFormatter:
    """Smart color formatting with auto-detection."""
    
    def __init__(self, force_color: Optional[bool] = None):
        self.enabled = self._should_use_color(force_color)
    
    def _should_use_color(self, force: Optional[bool]) -> bool:
        """Auto-detect if colors should be used."""
        if force is not None:
            return force
        
        # Don't use colors if:
        # - NO_COLOR env var is set
        # - Output is redirected  
        # - Not a TTY
        if os.environ.get('NO_COLOR'):
            return False
        
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.enabled:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    # Convenience methods for common patterns
    def success(self, text: str) -> str:
        return self.colorize(text, Colors.SUCCESS)
    
    def error(self, text: str) -> str:
        return self.colorize(text, Colors.ERROR)
    
    def warning(self, text: str) -> str:
        return self.colorize(text, Colors.WARNING)
    
    def info(self, text: str) -> str:
        return self.colorize(text, Colors.INFO)
    
    def disabled(self, text: str) -> str:
        return self.colorize(text, Colors.DISABLED)
    
    def header(self, text: str) -> str:
        return self.colorize(text, Colors.HEADER + Colors.BOLD)
    
    def accent(self, text: str) -> str:
        return self.colorize(text, Colors.ACCENT)

# Global formatter instance
_formatter = ColorFormatter()

def set_color_mode(enabled: Optional[bool]):
    """Set global color mode."""
    global _formatter
    _formatter = ColorFormatter(enabled)

def format_status(text: str) -> str:
    """Format status codes with appropriate colors."""
    # Define status patterns and their colors
    status_map = {
        '[OK]': _formatter.success,
        '[SUCCESS]': _formatter.success,
        '[ENABLED]': _formatter.success,
        '[FAIL]': _formatter.error,
        '[ERROR]': _formatter.error,
        '[WARN]': _formatter.warning,
        '[WARNING]': _formatter.warning,
        '[INFO]': _formatter.info,
        '[DISABLED]': _formatter.disabled,
        '[CANCELLED]': _formatter.disabled,
        '[NOT SET]': _formatter.disabled,
        '[NOT CONFIGURED]': _formatter.disabled,
        '[CUSTOM SSH ACTIVE]': _formatter.success,
        '[SYSTEM DEFAULT SSH]': _formatter.info,
        '[NOT FOUND]': _formatter.warning,
        '[NOT IN GIT REPOSITORY]': _formatter.disabled,
    }
    
    result = text
    for pattern, color_func in status_map.items():
        if pattern in result:
            colored_pattern = color_func(pattern)
            result = result.replace(pattern, colored_pattern)
    
    return result

def format_header(text: str) -> str:
    """Format header text with color."""
    return _formatter.header(text)

def format_accent(text: str) -> str:
    """Format accent text with color."""
    return _formatter.accent(text)
