"""Unit tests for backup manager functionality."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.addons_profile_manager.core.backup import (
    BackupManager,
    BackupResult,
    FileIntegrity,
)
from src.addons_profile_manager.config.settings import BackupConfig, ConflictResolution
from src.addons_profile_manager.utils.exceptions import (
    BackupValidationError,
    InsufficientSpaceError,
    PermissionDeniedError,
)


class TestFileIntegrity:
    """Test cases for FileIntegrity class."""
    
    def test_file_integrity_initialization(self, temp_dir):
        """Test FileIntegrity initialization."""
        test_file = temp_dir / "test.lua"
        test_file.write_text("test content")
        
        integrity = FileIntegrity(test_file)
        assert integrity.file_path == test_file
        assert integrity.size is None
        assert integrity.md5_hash is None
        assert integrity.sha256_hash is None
    
    def test_calculate_integrity(self, temp_dir):
        """Test calculating file integrity."""
        test_file = temp_dir / "test.lua"
        content = "test content for hashing"
        test_file.write_text(content)
        
        integrity = FileIntegrity(test_file)
        integrity.calculate()
        
        assert integrity.size == len(content.encode())
        assert integrity.md5_hash is not None
        assert integrity.sha256_hash is not None
        assert integrity.modified_time is not None
    
    def test_calculate_integrity_nonexistent_file(self, temp_dir):
        """Test calculating integrity for non-existent file."""
        nonexistent = temp_dir / "nonexistent.lua"
        integrity = FileIntegrity(nonexistent)
        
        # Should not raise exception
        integrity.calculate()
        
        assert integrity.size is None
        assert integrity.md5_hash == ""
        assert integrity.sha256_hash == ""
    
    def test_integrity_matches(self, temp_dir):
        """Test integrity matching."""
        test_file = temp_dir / "test.lua"
        test_file.write_text("test content")
        
        integrity1 = FileIntegrity(test_file)
        integrity2 = FileIntegrity(test_file)
        
        integrity1.calculate()
        integrity2.calculate()
        
        assert integrity1.matches(integrity2) is True
    
    def test_integrity_not_matches(self, temp_dir):
        """Test integrity not matching."""
        file1 = temp_dir / "test1.lua"
        file2 = temp_dir / "test2.lua"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        integrity1 = FileIntegrity(file1)
        integrity2 = FileIntegrity(file2)
        
        integrity1.calculate()
        integrity2.calculate()
        
        assert integrity1.matches(integrity2) is False


class TestBackupResult:
    """Test cases for BackupResult class."""
    
    def test_backup_result_initialization(self):
        """Test BackupResult initialization."""
        result = BackupResult()
        
        assert result.success is False
        assert result.copied_files == []
        assert result.skipped_files == []
        assert result.failed_files == []
        assert result.total_size == 0
        assert result.start_time is None
        assert result.end_time is None
        assert result.validation_errors == []
    
    def test_add_copied_file(self, temp_dir):
        """Test adding copied file."""
        result = BackupResult()
        test_file = temp_dir / "test.lua"
        size = 1024
        
        result.add_copied_file(test_file, size)
        
        assert len(result.copied_files) == 1
        assert result.copied_files[0] == test_file
        assert result.total_size == size
    
    def test_add_failed_file(self, temp_dir):
        """Test adding failed file."""
        result = BackupResult()
        test_file = temp_dir / "test.lua"
        error = "Permission denied"
        
        result.add_failed_file(test_file, error)
        
        assert len(result.failed_files) == 1
        assert result.failed_files[0] == (test_file, error)
    
    def test_duration_calculation(self, temp_dir):
        """Test duration calculation."""
        result = BackupResult()
        
        # No duration when times not set
        assert result.duration is None
        
        # Set times and calculate duration
        from datetime import datetime, timedelta
        
        result.start_time = datetime.now()
        result.end_time = result.start_time + timedelta(seconds=5)
        
        assert result.duration == 5.0


class TestBackupManager:
    """Test cases for BackupManager class."""
    
    def test_backup_manager_initialization(self, mock_config):
        """Test BackupManager initialization."""
        backup_config = BackupConfig(destination_path=mock_config.data_dir / "backups")
        conflicts = ConflictResolution()
        
        manager = BackupManager(backup_config, conflicts)
        
        assert manager.config == backup_config
        assert manager.conflicts == conflicts
        assert manager._active_backups == set()
    
    @pytest.mark.asyncio
    async def test_backup_session_context_manager(self, mock_backup_manager):
        """Test backup session context manager."""
        from src.addons_profile_manager.config.settings import AddonProfile
        
        profile = AddonProfile(name="test_profile")
        
        async with mock_backup_manager.backup_session(profile):
            session_id = f"{profile.name}_{profile.created_at or 'unknown'}"
            assert session_id in mock_backup_manager._active_backups
        
        # Session should be removed after context
        assert len(mock_backup_manager._active_backups) == 0
    
    @pytest.mark.asyncio
    async def test_create_backup_success(self, mock_backup_manager, mock_addon_profile, sample_addon_files):
        """Test successful backup creation."""
        result = await mock_backup_manager.create_backup(mock_addon_profile, sample_addon_files)
        
        assert result.success is True
        assert len(result.copied_files) > 0
        assert result.start_time is not None
        assert result.end_time is not None
    
    @pytest.mark.asyncio
    async def test_create_backup_insufficient_space(self, mock_backup_manager, mock_addon_profile, sample_addon_files):
        """Test backup creation with insufficient space."""
        # Mock disk space check to return insufficient space
        with patch('shutil.disk_usage') as mock_disk_usage:
            mock_disk_usage.return_value = Mock(free=1024)  # Very small space
            
            with pytest.raises(InsufficientSpaceError):
                await mock_backup_manager.create_backup(mock_addon_profile, sample_addon_files)
    
    @pytest.mark.asyncio
    async def test_create_backup_permission_error(self, mock_backup_manager, mock_addon_profile, sample_addon_files):
        """Test backup creation with permission error."""
        # Mock permission error on directory creation
        with patch.object(Path, 'mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Access denied")
            
            result = await mock_backup_manager.create_backup(mock_addon_profile, sample_addon_files)
            
            assert result.success is False
            assert len(result.failed_files) > 0
    
    @pytest.mark.asyncio
    async def test_copy_file_with_progress(self, mock_backup_manager, temp_dir):
        """Test copying file with progress."""
        source = temp_dir / "source.lua"
        dest = temp_dir / "dest.lua"
        
        source.write_text("test content")
        
        await mock_backup_manager._copy_file_with_progress(source, dest)
        
        assert dest.exists()
        assert dest.read_text() == source.read_text()
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_overwrite(self, mock_backup_manager, temp_dir):
        """Test conflict resolution with overwrite strategy."""
        mock_backup_manager.conflicts.strategy = "overwrite"
        
        source = temp_dir / "source.lua"
        dest = temp_dir / "dest.lua"
        
        source.write_text("new content")
        dest.write_text("old content")
        
        action = await mock_backup_manager._resolve_conflict(source, dest)
        
        assert action == "overwrite"
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_skip(self, mock_backup_manager, temp_dir):
        """Test conflict resolution with skip strategy."""
        mock_backup_manager.conflicts.strategy = "skip"
        
        source = temp_dir / "source.lua"
        dest = temp_dir / "dest.lua"
        
        action = await mock_backup_manager._resolve_conflict(source, dest)
        
        assert action == "skip"
    
    @pytest.mark.asyncio
    async def test_create_file_backup(self, mock_backup_manager, temp_dir):
        """Test creating file backup."""
        original = temp_dir / "original.lua"
        original.write_text("original content")
        
        await mock_backup_manager._create_file_backup(original)
        
        backup_path = original.with_suffix(original.suffix + mock_backup_manager.conflicts.backup_suffix)
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
    
    @pytest.mark.asyncio
    async def test_validate_backup_integrity(self, mock_backup_manager, mock_addon_profile, sample_addon_files, temp_dir):
        """Test backup integrity validation."""
        # Create backup directory and files
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        
        # Copy files to backup location
        for addon, files in sample_addon_files.items():
            addon_backup_path = backup_path / addon
            addon_backup_path.mkdir()
            
            for source_file in files:
                dest_file = addon_backup_path / source_file.name
                dest_file.write_text(source_file.read_text())
        
        result = BackupResult()
        
        await mock_backup_manager._validate_backup_integrity(
            mock_addon_profile, sample_addon_files, backup_path, result
        )
        
        # Should have no validation errors for identical files
        assert len(result.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_backup_integrity_mismatch(self, mock_backup_manager, mock_addon_profile, sample_addon_files, temp_dir):
        """Test backup integrity validation with mismatched files."""
        # Create backup directory with modified files
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        
        for addon, files in sample_addon_files.items():
            addon_backup_path = backup_path / addon
            addon_backup_path.mkdir()
            
            for source_file in files:
                dest_file = addon_backup_path / source_file.name
                dest_file.write_text("modified content")  # Different content
        
        result = BackupResult()
        
        await mock_backup_manager._validate_backup_integrity(
            mock_addon_profile, sample_addon_files, backup_path, result
        )
        
        # Should have validation errors for mismatched files
        assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_create_backup_metadata(self, mock_backup_manager, mock_addon_profile, sample_addon_files, temp_dir):
        """Test creating backup metadata."""
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        
        result = BackupResult()
        result.total_size = 2048
        
        await mock_backup_manager._create_backup_metadata(
            mock_addon_profile, sample_addon_files, backup_path, result
        )
        
        metadata_file = backup_path / "backup_metadata.json"
        assert metadata_file.exists()
        
        # Check metadata content
        import json
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert metadata["profile_name"] == mock_addon_profile.name
        assert "created_at" in metadata
        assert "addons" in metadata
    
    def test_get_backup_info_valid(self, mock_backup_manager, temp_dir):
        """Test getting backup info for valid backup."""
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        
        # Create metadata file
        metadata = {
            "profile_name": "test_profile",
            "created_at": "2023-01-01T00:00:00",
            "addons": {"TestAddon": {"count": 1}}
        }
        
        import json
        with open(backup_path / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        info = mock_backup_manager.get_backup_info(backup_path)
        
        assert info is not None
        assert info["profile_name"] == "test_profile"
        assert info["addons"]["TestAddon"]["count"] == 1
    
    def test_get_backup_info_invalid(self, mock_backup_manager, temp_dir):
        """Test getting backup info for invalid backup."""
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        
        # No metadata file
        info = mock_backup_manager.get_backup_info(backup_path)
        assert info is None
    
    def test_list_backups(self, mock_backup_manager, temp_dir):
        """Test listing backups in directory."""
        # Create multiple backup directories
        for i in range(3):
            backup_path = temp_dir / f"backup_{i}"
            backup_path.mkdir()
            
            # Create metadata
            metadata = {
                "profile_name": f"backup_{i}",
                "created_at": f"2023-01-0{i+1}T00:00:00"
            }
            
            import json
            with open(backup_path / "backup_metadata.json", 'w') as f:
                json.dump(metadata, f)
        
        backups = mock_backup_manager.list_backups(temp_dir)
        
        assert len(backups) == 3
        # Should be sorted by creation date (newest first)
        assert backups[0]["info"]["profile_name"] == "backup_2"
        assert backups[2]["info"]["profile_name"] == "backup_0"
    
    @pytest.mark.asyncio
    async def test_restore_backup_not_implemented(self, mock_backup_manager, temp_dir):
        """Test restore backup functionality (not implemented)."""
        backup_path = temp_dir / "backup"
        target_path = temp_dir / "target"
        
        result = await mock_backup_manager.restore_backup(backup_path, target_path)
        
        assert result.success is False
        assert len(result.failed_files) == 1