"""Custom exceptions for WoW Addon Profile Manager."""

from pathlib import Path
from typing import Optional


class AddonManagerError(Exception):
    """Base exception for addon manager operations."""
    
    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path
    
    def __str__(self) -> str:
        if self.path:
            return f"{self.message} (Path: {self.path})"
        return self.message


class WoWInstallationNotFoundError(AddonManagerError):
    """Raised when no WoW installation is found."""
    
    def __init__(self, message: str = "No World of Warcraft installation found") -> None:
        super().__init__(message)


class SavedVariablesNotFoundError(AddonManagerError):
    """Raised when SavedVariables directory is not found."""
    
    def __init__(self, path: Path) -> None:
        message = f"SavedVariables directory not found at {path}"
        super().__init__(message, path)


class InsufficientSpaceError(AddonManagerError):
    """Raised when not enough disk space for backup operation."""
    
    def __init__(self, required_bytes: int, available_bytes: int, path: Path) -> None:
        required_mb = required_bytes / (1024 * 1024)
        available_mb = available_bytes / (1024 * 1024)
        message = (
            f"Insufficient disk space. Required: {required_mb:.1f}MB, "
            f"Available: {available_mb:.1f}MB"
        )
        super().__init__(message, path)
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes


class PermissionDeniedError(AddonManagerError):
    """Raised when lacking file permissions."""
    
    def __init__(self, path: Path, operation: str = "access") -> None:
        message = f"Permission denied for {operation} on {path}"
        super().__init__(message, path)
        self.operation = operation


class AddonNotFoundError(AddonManagerError):
    """Raised when specified addon is not found."""
    
    def __init__(self, addon_name: str, path: Optional[Path] = None) -> None:
        message = f"Addon '{addon_name}' not found"
        super().__init__(message, path)
        self.addon_name = addon_name


class CorruptedSavedVariablesError(AddonManagerError):
    """Raised when SavedVariables files appear corrupted."""
    
    def __init__(self, path: Path, reason: str = "Unknown corruption") -> None:
        message = f"Corrupted SavedVariables file: {reason}"
        super().__init__(message, path)
        self.reason = reason


class ConcurrentAccessError(AddonManagerError):
    """Raised when another instance is already running."""
    
    def __init__(self, lock_file: Path) -> None:
        message = "Another instance of addon manager is already running"
        super().__init__(message, lock_file)
        self.lock_file = lock_file


class BackupValidationError(AddonManagerError):
    """Raised when backup integrity validation fails."""
    
    def __init__(self, source_file: Path, dest_file: Path, reason: str) -> None:
        message = f"Backup validation failed for {source_file.name}: {reason}"
        super().__init__(message, dest_file)
        self.source_file = source_file
        self.dest_file = dest_file
        self.reason = reason


class ConfigurationError(AddonManagerError):
    """Raised when there's a configuration error."""
    
    def __init__(self, message: str, config_key: Optional[str] = None) -> None:
        super().__init__(message)
        self.config_key = config_key