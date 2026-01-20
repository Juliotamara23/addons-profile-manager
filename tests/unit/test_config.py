"""Unit tests for configuration settings."""

import pytest
from pathlib import Path
from dataclasses import asdict

from src.addons_profile_manager.config.settings import (
    Config,
    WoWInstallation,
    WoWVersion,
    AddonProfile,
    BackupConfig,
    ConflictResolution,
    ScanConfig,
    LoggingConfig,
)


class TestWoWVersion:
    """Test cases for WoWVersion enum."""
    
    def test_version_values(self):
        """Test WoW version enum values."""
        assert WoWVersion.RETAIL.value == "retail"
        assert WoWVersion.CLASSIC.value == "classic"
        assert WoWVersion.CLASSIC_TBC.value == "classic_era"
        assert WoWVersion.CLASSIC_WOTLK.value == "classic_wrath"
        assert WoWVersion.PTR.value == "ptr"
        assert WoWVersion.BETA.value == "beta"


class TestWoWInstallation:
    """Test cases for WoWInstallation dataclass."""
    
    def test_installation_initialization(self, temp_dir):
        """Test WoWInstallation initialization."""
        path = temp_dir / "World of Warcraft"
        installation = WoWInstallation(
            path=path,
            version=WoWVersion.RETAIL,
            client_version="9.0.0.12345"
        )
        
        assert installation.path == path
        assert installation.version == WoWVersion.RETAIL
        assert installation.client_version == "9.0.0.12345"
    
    def test_wtf_path_property(self, temp_dir):
        """Test WTF path property."""
        path = temp_dir / "World of Warcraft"
        installation = WoWInstallation(path=path, version=WoWVersion.RETAIL)
        
        expected_wtf = path / "WTF"
        assert installation.wtf_path == expected_wtf
    
    def test_account_path_property(self, temp_dir):
        """Test account path property."""
        path = temp_dir / "World of Warcraft"
        installation = WoWInstallation(path=path, version=WoWVersion.RETAIL)
        
        expected_account = path / "WTF" / "Account"
        assert installation.account_path == expected_account
    
    def test_get_saved_variables_path(self, temp_dir):
        """Test getting SavedVariables path."""
        path = temp_dir / "World of Warcraft"
        installation = WoWInstallation(path=path, version=WoWVersion.RETAIL)
        
        account_name = "TESTACCOUNT"
        expected_path = path / "WTF" / "Account" / account_name / "SavedVariables"
        
        actual_path = installation.get_saved_variables_path(account_name)
        assert actual_path == expected_path


class TestAddonProfile:
    """Test cases for AddonProfile dataclass."""
    
    def test_profile_initialization(self, temp_dir):
        """Test AddonProfile initialization."""
        installation = WoWInstallation(
            path=temp_dir / "WoW",
            version=WoWVersion.RETAIL
        )
        
        profile = AddonProfile(
            name="test_profile",
            addons=["DBM-Core", "Bartender4"],
            wow_installation=installation,
            account_name="TestAccount",
            description="Test profile"
        )
        
        assert profile.name == "test_profile"
        assert len(profile.addons) == 2
        assert "DBM-Core" in profile.addons
        assert profile.wow_installation == installation
        assert profile.account_name == "TestAccount"
        assert profile.description == "Test profile"
    
    def test_get_saved_variables_path_valid(self, temp_dir):
        """Test getting SavedVariables path with valid installation."""
        installation = WoWInstallation(
            path=temp_dir / "WoW",
            version=WoWVersion.RETAIL
        )
        
        profile = AddonProfile(
            name="test_profile",
            wow_installation=installation,
            account_name="TestAccount"
        )
        
        expected_path = temp_dir / "WoW" / "WTF" / "Account" / "TestAccount" / "SavedVariables"
        actual_path = profile.get_saved_variables_path()
        
        assert actual_path == expected_path
    
    def test_get_saved_variables_path_missing_installation(self):
        """Test getting SavedVariables path without installation."""
        profile = AddonProfile(name="test_profile")
        
        result = profile.get_saved_variables_path()
        assert result is None
    
    def test_get_saved_variables_path_missing_account(self, temp_dir):
        """Test getting SavedVariables path without account name."""
        installation = WoWInstallation(
            path=temp_dir / "WoW",
            version=WoWVersion.RETAIL
        )
        
        profile = AddonProfile(
            name="test_profile",
            wow_installation=installation
        )
        
        result = profile.get_saved_variables_path()
        assert result is None


class TestBackupConfig:
    """Test cases for BackupConfig dataclass."""
    
    def test_backup_config_initialization(self, temp_dir):
        """Test BackupConfig initialization."""
        dest_path = temp_dir / "backups"
        config = BackupConfig(
            destination_path=dest_path,
            create_timestamp_folder=False,
            compress_backup=True,
            validate_integrity=False,
            overwrite_existing=True,
            backup_metadata=False
        )
        
        assert config.destination_path == dest_path
        assert config.create_timestamp_folder is False
        assert config.compress_backup is True
        assert config.validate_integrity is False
        assert config.overwrite_existing is True
        assert config.backup_metadata is False
    
    def test_get_backup_path_with_timestamp(self, temp_dir):
        """Test getting backup path with timestamp folder."""
        dest_path = temp_dir / "backups"
        config = BackupConfig(
            destination_path=dest_path,
            create_timestamp_folder=True
        )
        
        profile_name = "test_profile"
        backup_path = config.get_backup_path(profile_name)
        
        # Should include timestamp
        assert backup_path.parent == dest_path
        assert profile_name in backup_path.name
        assert len(backup_path.name) > len(profile_name)  # Timestamp added
    
    def test_get_backup_path_without_timestamp(self, temp_dir):
        """Test getting backup path without timestamp folder."""
        dest_path = temp_dir / "backups"
        config = BackupConfig(
            destination_path=dest_path,
            create_timestamp_folder=False
        )
        
        profile_name = "test_profile"
        backup_path = config.get_backup_path(profile_name)
        
        expected_path = dest_path / profile_name
        assert backup_path == expected_path


class TestConflictResolution:
    """Test cases for ConflictResolution dataclass."""
    
    def test_conflict_resolution_initialization(self):
        """Test ConflictResolution initialization."""
        resolution = ConflictResolution(
            strategy="skip",
            backup_existing=False,
            backup_suffix=".old"
        )
        
        assert resolution.strategy == "skip"
        assert resolution.backup_existing is False
        assert resolution.backup_suffix == ".old"
    
    def test_should_prompt_true(self):
        """Test should_prompt when strategy is prompt."""
        resolution = ConflictResolution(strategy="prompt")
        assert resolution.should_prompt() is True
    
    def test_should_prompt_false(self):
        """Test should_prompt when strategy is not prompt."""
        strategies = ["overwrite", "skip", "backup"]
        
        for strategy in strategies:
            resolution = ConflictResolution(strategy=strategy)
            assert resolution.should_prompt() is False


class TestScanConfig:
    """Test cases for ScanConfig dataclass."""
    
    def test_scan_config_initialization(self, temp_dir):
        """Test ScanConfig initialization."""
        scan_paths = [temp_dir / "wow1", temp_dir / "wow2"]
        config = ScanConfig(
            scan_paths=scan_paths,
            include_beta=True,
            include_ptr=False,
            max_depth=5,
            follow_symlinks=True
        )
        
        assert config.scan_paths == scan_paths
        assert config.include_beta is True
        assert config.include_ptr is False
        assert config.max_depth == 5
        assert config.follow_symlinks is True
    
    def test_scan_config_default_paths(self, temp_dir):
        """Test ScanConfig with default scan paths."""
        config = ScanConfig()
        
        # Should have some default paths
        assert len(config.scan_paths) >= 0
        assert config.max_depth == 3
        assert config.include_beta is False
        assert config.include_ptr is False
        assert config.follow_symlinks is False


class TestLoggingConfig:
    """Test cases for LoggingConfig dataclass."""
    
    def test_logging_config_initialization(self, temp_dir):
        """Test LoggingConfig initialization."""
        log_file = temp_dir / "app.log"
        config = LoggingConfig(
            level="DEBUG",
            format="%(message)s",
            file_path=log_file,
            max_file_size=5 * 1024 * 1024,
            backup_count=3,
            console_output=False,
            colored_output=False
        )
        
        assert config.level == "DEBUG"
        assert config.format == "%(message)s"
        assert config.file_path == log_file
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_count == 3
        assert config.console_output is False
        assert config.colored_output is False


class TestConfig:
    """Test cases for main Config dataclass."""
    
    def test_config_initialization(self, temp_dir):
        """Test Config initialization."""
        data_dir = temp_dir / "data"
        temp_dir_path = temp_dir / "temp"
        
        config = Config(
            data_dir=data_dir,
            temp_dir=temp_dir_path,
            debug_mode=True,
            verbose_mode=True,
            quiet_mode=False
        )
        
        assert config.data_dir == data_dir
        assert config.temp_dir == temp_dir_path
        assert config.debug_mode is True
        assert config.verbose_mode is True
        assert config.quiet_mode is False
    
    def test_config_post_init(self, temp_dir):
        """Test Config post-initialization directory creation."""
        config = Config(data_dir=temp_dir / "data")
        
        # Directories should be created
        assert config.data_dir.exists()
        assert config.temp_dir.exists()
        assert config.backup.destination_path.exists()
    
    def test_get_config_file_path(self, temp_dir):
        """Test getting config file path."""
        config = Config(data_dir=temp_dir / "data")
        
        expected_path = temp_dir / "data" / "config.toml"
        actual_path = config.get_config_file_path()
        
        assert actual_path == expected_path
    
    def test_get_lock_file_path(self, temp_dir):
        """Test getting lock file path."""
        config = Config(data_dir=temp_dir / "data")
        
        expected_path = temp_dir / "data" / "app.lock"
        actual_path = config.get_lock_file_path()
        
        assert actual_path == expected_path
    
    def test_load_from_file_not_implemented(self, temp_dir):
        """Test loading from file (not implemented)."""
        config = Config(data_dir=temp_dir / "data")
        config_file = temp_dir / "config.toml"
        
        # Should not raise exception
        config.load_from_file(config_file)
    
    def test_save_to_file_not_implemented(self, temp_dir):
        """Test saving to file (not implemented)."""
        config = Config(data_dir=temp_dir / "data")
        config_file = temp_dir / "config.toml"
        
        # Should not raise exception
        config.save_to_file(config_file)
    
    def test_config_default_values(self, temp_dir):
        """Test Config default values."""
        config = Config()
        
        # Check default component configs
        assert isinstance(config.scan, ScanConfig)
        assert isinstance(config.backup, BackupConfig)
        assert isinstance(config.conflicts, ConflictResolution)
        assert isinstance(config.logging, LoggingConfig)
        
        # Check default runtime settings
        assert config.debug_mode is False
        assert config.verbose_mode is False
        assert config.quiet_mode is False