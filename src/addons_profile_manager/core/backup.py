"""Backup manager for WoW addon configurations with integrity validation."""

import asyncio
import hashlib
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Set, Tuple

from ..config.settings import AddonProfile, BackupConfig, ConflictResolution
from ..utils.exceptions import (
    BackupValidationError,
    InsufficientSpaceError,
    PermissionDeniedError,
)


class FileIntegrity:
    """File integrity information for validation."""
    
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.size: Optional[int] = None
        self.md5_hash: Optional[str] = None
        self.sha256_hash: Optional[str] = None
        self.modified_time: Optional[float] = None
    
    def calculate(self) -> None:
        """Calculate file integrity metrics."""
        try:
            stat = self.file_path.stat()
            self.size = stat.st_size
            self.modified_time = stat.st_mtime
            
            # Calculate hashes
            self.md5_hash = self._calculate_hash(hashlib.md5())
            self.sha256_hash = self._calculate_hash(hashlib.sha256())
        
        except (PermissionError, FileNotFoundError):
            pass
    
    def _calculate_hash(self, hash_algorithm) -> str:
        """Calculate hash for the file."""
        try:
            with open(self.file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_algorithm.update(chunk)
            return hash_algorithm.hexdigest()
        except (PermissionError, FileNotFoundError):
            return ""
    
    def matches(self, other: 'FileIntegrity') -> bool:
        """Check if this integrity matches another."""
        return (
            self.size == other.size and
            self.md5_hash == other.md5_hash and
            self.sha256_hash == other.sha256_hash
        )


class BackupResult:
    """Result of a backup operation."""
    
    def __init__(self) -> None:
        self.success: bool = False
        self.copied_files: List[Path] = []
        self.skipped_files: List[Path] = []
        self.failed_files: List[Tuple[Path, str]] = []
        self.total_size: int = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.validation_errors: List[BackupValidationError] = []
    
    @property
    def duration(self) -> Optional[float]:
        """Get backup duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def add_copied_file(self, file_path: Path, size: int) -> None:
        """Add a successfully copied file."""
        self.copied_files.append(file_path)
        self.total_size += size
    
    def add_failed_file(self, file_path: Path, error: str) -> None:
        """Add a failed file."""
        self.failed_files.append((file_path, error))
    
    def add_validation_error(self, error: BackupValidationError) -> None:
        """Add a validation error."""
        self.validation_errors.append(error)


class BackupManager:
    """Manages backup operations for WoW addon configurations."""
    
    def __init__(self, config: BackupConfig, conflicts: ConflictResolution) -> None:
        """Initialize backup manager."""
        self.config = config
        self.conflicts = conflicts
        self._active_backups: Set[str] = set()
    
    @asynccontextmanager
    async def backup_session(self, profile: AddonProfile) -> AsyncGenerator[None, None]:
        """Context manager for backup session."""
        session_id = f"{profile.name}_{datetime.now().isoformat()}"
        
        if session_id in self._active_backups:
            raise RuntimeError(f"Backup session {session_id} already active")
        
        self._active_backups.add(session_id)
        try:
            yield
        finally:
            self._active_backups.discard(session_id)
    
    async def create_backup(self, profile: AddonProfile, addon_files: Dict[str, List[Path]]) -> BackupResult:
        """Create a backup of addon configurations."""
        result = BackupResult()
        result.start_time = datetime.now()
        
        async with self.backup_session(profile):
            try:
                # Validate requirements
                await self._validate_backup_requirements(profile, addon_files)
                
                # Create backup directory
                backup_path = self.config.get_backup_path(profile.name)
                backup_path.mkdir(parents=True, exist_ok=True)
                
                # Copy files
                await self._copy_addon_files(profile, addon_files, backup_path, result)
                
                # Validate integrity if requested
                if self.config.validate_integrity:
                    await self._validate_backup_integrity(profile, addon_files, backup_path, result)
                
                # Create metadata if requested
                if self.config.backup_metadata:
                    await self._create_backup_metadata(profile, addon_files, backup_path, result)
                
                result.success = len(result.failed_files) == 0 and len(result.validation_errors) == 0
                
            except Exception as e:
                result.add_failed_file(Path("backup_operation"), str(e))
                result.success = False
            finally:
                result.end_time = datetime.now()
        
        return result
    
    async def _validate_backup_requirements(self, profile: AddonProfile, addon_files: Dict[str, List[Path]]) -> None:
        """Validate backup requirements before starting."""
        # Check disk space
        total_size = sum(
            sum(file.stat().st_size for file in files if file.exists())
            for files in addon_files.values()
        )
        
        backup_path = self.config.get_backup_path(profile.name)
        available_space = shutil.disk_usage(backup_path.parent).free
        
        if available_space < total_size:
            raise InsufficientSpaceError(total_size, available_space, backup_path.parent)
        
        # Check permissions
        if not backup_path.parent.exists():
            try:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                raise PermissionDeniedError(backup_path.parent, "create directory") from e
    
    async def _copy_addon_files(
        self, 
        profile: AddonProfile, 
        addon_files: Dict[str, List[Path]], 
        backup_path: Path, 
        result: BackupResult
    ) -> None:
        """Copy addon files to backup location."""
        for addon_name, files in addon_files.items():
            addon_backup_path = backup_path / addon_name
            addon_backup_path.mkdir(parents=True, exist_ok=True)
            
            for source_file in files:
                if not source_file.exists():
                    result.add_failed_file(source_file, "Source file not found")
                    continue
                
                dest_file = addon_backup_path / source_file.name
                
                # Handle conflicts
                if dest_file.exists():
                    action = await self._resolve_conflict(source_file, dest_file)
                    if action == "skip":
                        result.skipped_files.append(source_file)
                        continue
                    elif action == "backup":
                        await self._create_file_backup(dest_file)
                    elif action == "cancel":
                        break
                
                # Copy file
                try:
                    await self._copy_file_with_progress(source_file, dest_file)
                    file_size = source_file.stat().st_size
                    result.add_copied_file(source_file, file_size)
                except Exception as e:
                    result.add_failed_file(source_file, str(e))
    
    async def _copy_file_with_progress(self, source: Path, dest: Path) -> None:
        """Copy file with progress reporting for large files."""
        chunk_size = 1024 * 1024  # 1MB chunks
        
        try:
            with source.open('rb') as src_f, dest.open('wb') as dst_f:
                while chunk := src_f.read(chunk_size):
                    dst_f.write(chunk)
                    # TODO: Add progress callback here
        except PermissionError as e:
            raise PermissionDeniedError(dest, "write file") from e
    
    async def _resolve_conflict(self, source: Path, dest: Path) -> str:
        """Resolve file conflict based on configuration."""
        if self.conflicts.strategy == "overwrite":
            return "overwrite"
        elif self.conflicts.strategy == "skip":
            return "skip"
        elif self.conflicts.strategy == "backup":
            return "backup"
        elif self.conflicts.strategy == "prompt":
            # TODO: Implement user prompt
            return "skip"  # Default for now
        else:
            return "skip"
    
    async def _create_file_backup(self, file_path: Path) -> None:
        """Create backup of existing file."""
        backup_path = file_path.with_suffix(file_path.suffix + self.conflicts.backup_suffix)
        
        try:
            shutil.copy2(file_path, backup_path)
        except PermissionError as e:
            raise PermissionDeniedError(backup_path, "create backup") from e
    
    async def _validate_backup_integrity(
        self, 
        profile: AddonProfile, 
        addon_files: Dict[str, List[Path]], 
        backup_path: Path, 
        result: BackupResult
    ) -> None:
        """Validate integrity of backed up files."""
        for addon_name, files in addon_files.items():
            addon_backup_path = backup_path / addon_name
            
            for source_file in files:
                dest_file = addon_backup_path / source_file.name
                
                if not dest_file.exists():
                    error = BackupValidationError(
                        source_file, 
                        dest_file, 
                        "Destination file not found"
                    )
                    result.add_validation_error(error)
                    continue
                
                # Calculate and compare integrity
                source_integrity = FileIntegrity(source_file)
                dest_integrity = FileIntegrity(dest_file)
                
                source_integrity.calculate()
                dest_integrity.calculate()
                
                if not source_integrity.matches(dest_integrity):
                    error = BackupValidationError(
                        source_file,
                        dest_file,
                        "Integrity check failed"
                    )
                    result.add_validation_error(error)
    
    async def _create_backup_metadata(
        self, 
        profile: AddonProfile, 
        addon_files: Dict[str, List[Path]], 
        backup_path: Path, 
        result: BackupResult
    ) -> None:
        """Create backup metadata file."""
        import json
        
        metadata = {
            "profile_name": profile.name,
            "account_name": profile.account_name,
            "wow_installation": str(profile.wow_installation.path) if profile.wow_installation else None,
            "wow_version": profile.wow_installation.version.value if profile.wow_installation else None,
            "created_at": datetime.now().isoformat(),
            "addons": {},
            "total_files": sum(len(files) for files in addon_files.values()),
            "total_size": result.total_size,
        }
        
        for addon_name, files in addon_files.items():
            metadata["addons"][addon_name] = {
                "files": [f.name for f in files],
                "count": len(files),
            }
        
        metadata_file = backup_path / "backup_metadata.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except PermissionError as e:
            raise PermissionDeniedError(metadata_file, "write metadata") from e
    
    async def restore_backup(self, backup_path: Path, target_installation: Path) -> BackupResult:
        """Restore addon configurations from backup."""
        # TODO: Implement restore functionality
        result = BackupResult()
        result.success = False
        return result
    
    def get_backup_info(self, backup_path: Path) -> Optional[Dict]:
        """Get information about a backup."""
        metadata_file = backup_path / "backup_metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            return None
    
    def list_backups(self, backup_dir: Path) -> List[Dict]:
        """List all available backups in a directory."""
        backups = []
        
        if not backup_dir.exists():
            return backups
        
        for item in backup_dir.iterdir():
            if item.is_dir():
                backup_info = self.get_backup_info(item)
                if backup_info:
                    backups.append({
                        "path": item,
                        "info": backup_info
                    })
        
        return sorted(backups, key=lambda x: x["info"].get("created_at", ""), reverse=True)