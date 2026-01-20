"""WoW Addon Profile Manager - Manage World of Warcraft addon configurations."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config.settings import Config
from .core.scanner import WoWScanner
from .core.backup import BackupManager
from .utils.exceptions import AddonManagerError

__all__ = [
    "Config",
    "WoWScanner", 
    "BackupManager",
    "AddonManagerError",
]