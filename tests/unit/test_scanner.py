"""Unit tests for WoW scanner functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.addons_profile_manager.core.scanner import WoWScanner
from src.addons_profile_manager.config.settings import Config, WoWVersion
from src.addons_profile_manager.utils.exceptions import (
    PermissionDeniedError,
    SavedVariablesNotFoundError,
    WoWInstallationNotFoundError,
)


class TestWoWScanner:
    """Test cases for WoWScanner class."""
    
    def test_scanner_initialization(self, mock_config):
        """Test scanner initialization."""
        scanner = WoWScanner(mock_config)
        assert scanner.config == mock_config
        assert scanner._found_installations == []
    
    def test_scan_installations_empty(self, mock_config, temp_dir):
        """Test scanning when no installations found."""
        scanner = WoWScanner(mock_config)
        
        # Empty scan path
        mock_config.scan.scan_paths = [temp_dir / "nonexistent"]
        
        installations = scanner.scan_installations()
        assert installations == []
    
    def test_scan_installations_success(self, mock_config, create_mock_installation):
        """Test successful scanning of installations."""
        # Create mock installations
        installation1 = create_mock_installation("WoW_Retail", WoWVersion.RETAIL)
        installation2 = create_mock_installation("WoW_Classic", WoWVersion.CLASSIC)
        
        scanner = WoWScanner(mock_config)
        installations = scanner.scan_installations()
        
        assert len(installations) == 2
        assert any(inst.version == WoWVersion.RETAIL for inst in installations)
        assert any(inst.version == WoWVersion.CLASSIC for inst in installations)
    
    def test_is_wow_installation_valid(self, mock_config, create_mock_installation):
        """Test detection of valid WoW installation."""
        installation = create_mock_installation()
        scanner = WoWScanner(mock_config)
        
        assert scanner._is_wow_installation(installation.path) is True
    
    def test_is_wow_installation_invalid(self, mock_config, temp_dir):
        """Test detection of invalid WoW installation."""
        # Create directory without WoW structure
        fake_wow = temp_dir / "FakeWoW"
        fake_wow.mkdir()
        
        scanner = WoWScanner(mock_config)
        assert scanner._is_wow_installation(fake_wow) is False
    
    def test_detect_wow_version_retail(self, mock_config, create_mock_installation):
        """Test detection of retail version."""
        installation = create_mock_installation("World of Warcraft", WoWVersion.RETAIL)
        scanner = WoWScanner(mock_config)
        
        detected_version = scanner._detect_wow_version(installation.path)
        assert detected_version == WoWVersion.RETAIL
    
    def test_detect_wow_version_classic(self, mock_config, create_mock_installation):
        """Test detection of classic version."""
        installation = create_mock_installation("World of Warcraft Classic", WoWVersion.CLASSIC)
        scanner = WoWScanner(mock_config)
        
        detected_version = scanner._detect_wow_version(installation.path)
        assert detected_version == WoWVersion.CLASSIC
    
    def test_detect_wow_version_ptr(self, mock_config, create_mock_installation):
        """Test detection of PTR version."""
        installation = create_mock_installation("World of Warcraft PTR", WoWVersion.PTR)
        scanner = WoWScanner(mock_config)
        
        detected_version = scanner._detect_wow_version(installation.path)
        assert detected_version == WoWVersion.PTR
    
    def test_get_accounts_success(self, mock_config, create_mock_installation):
        """Test getting accounts from installation."""
        installation = create_mock_installation()
        installation.add_account("Account1", ["Addon1"])
        installation.add_account("Account2", ["Addon2"])
        
        scanner = WoWScanner(mock_config)
        accounts = scanner.get_accounts(installation)
        
        assert len(accounts) == 2
        assert "Account1" in accounts
        assert "Account2" in accounts
    
    def test_get_accounts_no_saved_variables(self, mock_config, create_mock_installation):
        """Test getting accounts when no SavedVariables found."""
        installation = create_mock_installation()
        # Don't add any accounts
        
        scanner = WoWScanner(mock_config)
        
        with pytest.raises(SavedVariablesNotFoundError):
            scanner.get_accounts(installation)
    
    def test_get_addon_files_success(self, mock_config, create_mock_installation):
        """Test getting addon files for account."""
        installation = create_mock_installation()
        installation.add_account("TestAccount", ["DBM-Core", "Bartender4"])
        
        scanner = WoWScanner(mock_config)
        addon_files = scanner.get_addon_files(installation, "TestAccount")
        
        assert len(addon_files) == 2
        assert "DBM-Core" in addon_files
        assert "Bartender4" in addon_files
        assert len(addon_files["DBM-Core"]) == 1
        assert len(addon_files["Bartender4"]) == 1
    
    def test_is_addon_file_valid_addon(self, mock_config):
        """Test addon file detection for valid addon."""
        scanner = WoWScanner(mock_config)
        
        addon_file = Path("DBM-Core.lua")
        assert scanner._is_addon_file(addon_file) is True
    
    def test_is_addon_file_non_addon(self, mock_config):
        """Test addon file detection for non-addon file."""
        scanner = WoWScanner(mock_config)
        
        non_addon_files = [
            Path("Bindings.lua"),
            Path("Macros.lua"),
            Path("SavedVariables.lua"),
        ]
        
        for file_path in non_addon_files:
            assert scanner._is_addon_file(file_path) is False
    
    def test_extract_addon_name_standard(self, mock_config):
        """Test addon name extraction for standard addon."""
        scanner = WoWScanner(mock_config)
        
        file_path = Path("MyAddon.lua")
        addon_name = scanner._extract_addon_name(file_path)
        
        assert addon_name == "MyAddon"
    
    def test_extract_addon_name_dbm(self, mock_config):
        """Test addon name extraction for DBM."""
        scanner = WoWScanner(mock_config)
        
        file_path = Path("DBM-BlackrockFoundry.lua")
        addon_name = scanner._extract_addon_name(file_path)
        
        assert addon_name == "DeadlyBossMods"
    
    def test_extract_addon_name_elvui(self, mock_config):
        """Test addon name extraction for ElvUI."""
        scanner = WoWScanner(mock_config)
        
        file_path = Path("ElvUI.lua")
        addon_name = scanner._extract_addon_name(file_path)
        
        assert addon_name == "ElvUI"
    
    def test_validate_installation_valid(self, mock_config, create_mock_installation):
        """Test validation of valid installation."""
        installation = create_mock_installation()
        scanner = WoWScanner(mock_config)
        
        assert scanner.validate_installation(installation) is True
    
    def test_validate_installation_invalid_structure(self, mock_config, temp_dir):
        """Test validation of installation with invalid structure."""
        # Create installation without proper structure
        invalid_path = temp_dir / "InvalidWoW"
        invalid_path.mkdir()
        
        from src.addons_profile_manager.config.settings import WoWInstallation
        installation = WoWInstallation(path=invalid_path, version=WoWVersion.RETAIL)
        
        scanner = WoWScanner(mock_config)
        assert scanner.validate_installation(installation) is False
    
    def test_get_installation_size(self, mock_config, create_mock_installation):
        """Test getting installation size."""
        installation = create_mock_installation()
        installation.add_account("TestAccount", ["Addon1", "Addon2"])
        
        scanner = WoWScanner(mock_config)
        size = scanner.get_installation_size(installation)
        
        assert size > 0
    
    def test_find_installation_by_path_existing(self, mock_config, create_mock_installation):
        """Test finding installation by existing path."""
        installation = create_mock_installation()
        scanner = WoWScanner(mock_config)
        
        # First scan to populate found installations
        scanner.scan_installations()
        
        found = scanner.find_installation_by_path(installation.path)
        assert found is not None
        assert found.path == installation.path
    
    def test_find_installation_by_path_not_found(self, mock_config, temp_dir):
        """Test finding installation by non-existent path."""
        non_existent = temp_dir / "NonExistentWoW"
        scanner = WoWScanner(mock_config)
        
        found = scanner.find_installation_by_path(non_existent)
        assert found is None
    
    def test_permission_error_handling(self, mock_config, create_mock_installation):
        """Test handling of permission errors."""
        installation = create_mock_installation()
        scanner = WoWScanner(mock_config)
        
        # Mock permission error
        with patch.object(installation.account_path, 'iterdir') as mock_iterdir:
            mock_iterdir.side_effect = PermissionError("Access denied")
            
            with pytest.raises(PermissionDeniedError):
                scanner.get_accounts(installation)
    
    @pytest.mark.slow
    def test_scan_large_directory(self, mock_config, temp_dir):
        """Test scanning directory with many subdirectories."""
        # Create many subdirectories to test performance
        for i in range(100):
            sub_dir = temp_dir / f"subdir_{i}"
            sub_dir.mkdir()
        
        scanner = WoWScanner(mock_config)
        mock_config.scan.max_depth = 1  # Limit depth for performance
        
        # Should not crash and should complete in reasonable time
        installations = scanner.scan_installations()
        assert isinstance(installations, list)