"""Constants and messages for WoW Addon Profile Manager."""

from enum import Enum


class Colors(Enum):
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD_BLACK = "\033[1;30m"
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"


class Messages:
    """User-facing messages."""
    
    # Welcome and help
    WELCOME = "WoW Addon Profile Manager - Manage your addon configurations"
    VERSION_INFO = "Version {version}"
    HELP_TEXT = "Use --help for usage information"
    
    # Scanning messages
    SCANNING_INSTALLATIONS = "Scanning for WoW installations..."
    FOUND_INSTALLATIONS = "Found {count} WoW installation(s)"
    NO_INSTALLATIONS_FOUND = "No WoW installations found. Please check your installation paths."
    MANUAL_PATH_PROMPT = "Would you like to specify the WoW installation path manually? (y/n)"
    MANUAL_PATH_INSTRUCTIONS = "Please enter the path to your World of Warcraft installation:"
    MANUAL_PATH_EXAMPLE = """Example paths (you can use any of these formats):
  - Full installation: C:\\Program Files (x86)\\World of Warcraft
  - Version specific: D:\\Games\\World of Warcraft\\_retail_
  - Direct SavedVariables: E:\\WoW\\_retail_\\WTF\\Account\\12345678#1\\SavedVariables"""
    SCANNING_ACCOUNTS = "Scanning accounts in {path}"
    FOUND_ACCOUNTS = "Found {count} account(s)"
    SCANNING_ADDONS = "Scanning addon configurations..."
    
    # Selection messages
    SELECT_INSTALLATION = "Select WoW installation:"
    SELECT_ACCOUNT = "Select account:"
    SELECT_ADDONS = "Select addons to backup (space to toggle, enter to confirm):"
    SELECT_DESTINATION = "Select backup destination:"
    
    # Backup messages
    STARTING_BACKUP = "Starting backup process..."
    BACKUP_COMPLETE = "Backup completed successfully!"
    BACKUP_FAILED = "Backup failed: {error}"
    VALIDATING_INTEGRITY = "Validating backup integrity..."
    INTEGRITY_CHECK_PASSED = "Integrity check passed"
    INTEGRITY_CHECK_FAILED = "Integrity check failed: {error}"
    
    # Conflict messages
    FILE_EXISTS = "File already exists: {file}"
    CONFLICT_STRATEGY_PROMPT = "File exists. What would you like to do? [(O)verwrite/(S)kip/(B)ackup/(C)ancel]"
    OVERWRITING_FILE = "Overwriting: {file}"
    SKIPPING_FILE = "Skipping: {file}"
    CREATING_BACKUP = "Creating backup: {file}"
    
    # Error messages
    ERROR_PREFIX = "ERROR:"
    WARNING_PREFIX = "WARNING:"
    INFO_PREFIX = "INFO:"
    SUCCESS_PREFIX = "SUCCESS:"
    
    # Progress messages
    COPYING_FILE = "Copying {file} ({current}/{total})"
    PROGRESS_BAR = "[{bar}] {percentage:.1f}% ({current}/{total})"
    
    # Menu options
    MAIN_MENU_OPTIONS = [
        "Scan for WoW installations",
        "List available addons",
        "Select addons for backup",
        "Choose backup destination",
        "Start backup process",
        "Exit"
    ]
    
    # Validation messages
    VALIDATING_FILE = "Validating {file}"
    FILE_VALID = "File valid: {file}"
    FILE_INVALID = "File invalid: {file} - {reason}"
    CHECKSUM_MISMATCH = "Checksum mismatch: expected {expected}, got {actual}"
    SIZE_MISMATCH = "Size mismatch: expected {expected}, got {actual}"


class FilePatterns:
    """File patterns for WoW addon detection."""
    
    SAVED_VARIABLES_PATTERN = "*.lua"
    ADDON_CONFIG_PATTERN = "*.lua"
    ACCOUNT_FOLDER_PATTERN = "*"
    WTF_FOLDER = "WTF"
    ACCOUNT_FOLDER = "Account"
    SAVED_VARIABLES_FOLDER = "SavedVariables"
    
    # Common WoW addon files to look for
    COMMON_ADDON_FILES = [
        "Bindings.lua",
        "ChatCache.lua", 
        "GlyphCache.lua",
        "Macros.lua",
        "Panel.lua",
        "Preferences.lua",
        "SavedVariables.lua",
    ]


class Paths:
    """Default paths and directories."""
    
    # Windows paths
    WINDOWS_PROGRAM_FILES = ["C:/Program Files", "C:/Program Files (x86)", "D:/Expecialtik/"]
    WINDOWS_WOW_DEFAULT = "World of Warcraft"
    
    # macOS paths
    MACOS_APPLICATIONS = "/Applications"
    MACOS_WOW_DEFAULT = "World of Warcraft"
    
    # Linux paths (Wine/Proton)
    LINUX_STAM_PATHS = [
        "~/.steam/steam/steamapps/common",
        "~/.local/share/Steam/steamapps/common",
    ]
    
    # Config and data paths
    USER_CONFIG_DIR = "~/.addons_profile_manager"
    USER_CACHE_DIR = "~/.addons_profile_manager/cache"
    LOCK_FILE = "app.lock"
    CONFIG_FILE = "config.toml"
    
    # WoW directory structure
    WTF_DIR = "WTF"
    ACCOUNT_DIR = "Account"
    SAVED_VARIABLES_DIR = "SavedVariables"