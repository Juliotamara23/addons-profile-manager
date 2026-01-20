"""File operation utilities for WoW Addon Profile Manager."""

import asyncio
import hashlib
import shutil
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from ..utils.exceptions import (
    BackupValidationError,
    InsufficientSpaceError,
    PermissionDeniedError,
)


class FileOperations:
    """Utility class for file operations."""
    
    @staticmethod
    async def copy_file_async(source: Path, destination: Path, chunk_size: int = 1024 * 1024) -> None:
        """Copy file asynchronously with progress support."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with source.open('rb') as src_f, destination.open('wb') as dst_f:
                while chunk := src_f.read(chunk_size):
                    dst_f.write(chunk)
                    # TODO: Add progress callback
        except PermissionError as e:
            raise PermissionDeniedError(destination, "write file") from e
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
        """Calculate hash for a file."""
        hash_obj = hashlib.new(algorithm)
        
        try:
            with file_path.open('rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except (PermissionError, FileNotFoundError):
            return ""
    
    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """Get file size in bytes."""
        try:
            return file_path.stat().st_size
        except (PermissionError, FileNotFoundError):
            return 0
    
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        """Get total size of directory."""
        total_size = 0
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except PermissionError:
            pass
        
        return total_size
    
    @staticmethod
    def check_disk_space(path: Path, required_bytes: int) -> bool:
        """Check if enough disk space is available."""
        try:
            available_bytes = shutil.disk_usage(path.parent).free
            return available_bytes >= required_bytes
        except (PermissionError, OSError):
            return False
    
    @staticmethod
    def ensure_directory(directory: Path) -> bool:
        """Ensure directory exists."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            return False
    
    @staticmethod
    def safe_remove(file_path: Path) -> bool:
        """Safely remove file."""
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except PermissionError:
            return False
    
    @staticmethod
    def create_backup_filename(original_path: Path, suffix: str = ".backup") -> Path:
        """Create backup filename that doesn't conflict."""
        backup_path = original_path.with_suffix(original_path.suffix + suffix)
        counter = 1
        
        while backup_path.exists():
            backup_path = original_path.with_suffix(f"{original_path.suffix}{suffix}.{counter}")
            counter += 1
        
        return backup_path


class AsyncFileIterator:
    """Async iterator for file operations."""
    
    def __init__(self, file_paths: List[Path]) -> None:
        self.file_paths = file_paths
        self._index = 0
    
    def __aiter__(self) -> AsyncGenerator[Path, None]:
        return self
    
    async def __anext__(self) -> Path:
        if self._index >= len(self.file_paths):
            raise StopAsyncIteration
        
        file_path = self.file_paths[self._index]
        self._index += 1
        return file_path


class ProgressTracker:
    """Track progress for file operations."""
    
    def __init__(self, total_files: int) -> None:
        self.total_files = total_files
        self.completed_files = 0
        self.total_bytes = 0
        self.completed_bytes = 0
        self.start_time = None
        self.end_time = None
    
    def start(self) -> None:
        """Start tracking."""
        import time
        self.start_time = time.time()
    
    def update(self, file_bytes: int) -> None:
        """Update progress."""
        self.completed_files += 1
        self.completed_bytes += file_bytes
    
    def finish(self) -> None:
        """Finish tracking."""
        import time
        self.end_time = time.time()
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100
    
    @property
    def bytes_progress_percentage(self) -> float:
        """Get bytes progress as percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.completed_bytes / self.total_bytes) * 100
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time:
            end_time = self.end_time or self._get_current_time()
            return end_time - self.start_time
        return None
    
    def _get_current_time(self) -> float:
        """Get current time."""
        import time
        return time.time()
    
    def estimate_remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.completed_files == 0 or not self.elapsed_time:
            return None
        
        rate = self.completed_files / self.elapsed_time
        remaining_files = self.total_files - self.completed_files
        
        if rate > 0:
            return remaining_files / rate
        
        return None