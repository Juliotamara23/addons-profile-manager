"""Integration tests for the complete WoW Addon Profile Manager workflow."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from src.addons_profile_manager.cli import InteractiveMenu
from src.addons_profile_manager.config.settings import Config, AddonProfile
from src.addons_profile_manager.core.scanner import WoWScanner
from src.addons_profile_manager.core.backup import BackupManager
from src.addons_profile_manager.utils.exceptions import AddonManagerError


class TestIntegrationWorkflow:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_backup_workflow(self, create_mock_installation, temp_dir):
        """Test complete backup workflow from scan to backup."""
        # Create mock installation with accounts and addons
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={
                "TestAccount1": ["DBM-Core", "Bartender4"],
                "TestAccount2": ["WeakAuras", "ElvUI"]
            }
        )
        
        # Setup configuration
        config = Config(data_dir=temp_dir / "data")
        config.scan.scan_paths = [temp_dir]
        config.backup.destination_path = temp_dir / "backups"
        
        # Create components
        scanner = WoWScanner(config)
        backup_manager = BackupManager(config.backup, config.conflicts)
        
        # Step 1: Scan installations
        installations = scanner.scan_installations()
        assert len(installations) >= 1
        
        found_installation = None
        for inst in installations:
            if inst.path.name == installation.path.name:
                found_installation = inst
                break
        
        assert found_installation is not None
        
        # Step 2: Get accounts
        accounts = scanner.get_accounts(found_installation)
        assert len(accounts) >= 2
        assert "TestAccount1" in accounts
        
        # Step 3: Get addon files for account
        addon_files = scanner.get_addon_files(found_installation, "TestAccount1")
        assert len(addon_files) >= 2
        assert "DBM-Core" in addon_files
        assert "Bartender4" in addon_files
        
        # Step 4: Create backup
        profile = AddonProfile(
            name="integration_test",
            addons=list(addon_files.keys()),
            wow_installation=found_installation,
            account_name="TestAccount1"
        )
        
        result = await backup_manager.create_backup(profile, addon_files)
        
        # Step 5: Verify backup result
        assert result.success is True
        assert len(result.copied_files) > 0
        assert len(result.failed_files) == 0
        
        # Step 6: Verify backup files exist
        backup_path = config.backup.get_backup_path("integration_test")
        assert backup_path.exists()
        
        for addon_name in addon_files.keys():
            addon_backup_path = backup_path / addon_name
            assert addon_backup_path.exists()
            
            for source_file in addon_files[addon_name]:
                dest_file = addon_backup_path / source_file.name
                assert dest_file.exists()
        
        # Step 7: Verify metadata
        metadata_file = backup_path / "backup_metadata.json"
        assert metadata_file.exists()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conflict_resolution_workflow(self, create_mock_installation, temp_dir):
        """Test workflow with file conflicts."""
        # Create installation
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={"TestAccount": ["DBM-Core"]}
        )
        
        config = Config(data_dir=temp_dir / "data")
        config.backup.destination_path = temp_dir / "backups"
        config.backup.overwrite_existing = False
        config.conflicts.strategy = "prompt"
        
        scanner = WoWScanner(config)
        backup_manager = BackupManager(config.backup, config.conflicts)
        
        # Scan and get files
        installations = scanner.scan_installations()
        found_installation = installations[0]
        
        addon_files = scanner.get_addon_files(found_installation, "TestAccount")
        
        # Create existing backup files (conflict)
        backup_path = config.backup.get_backup_path("conflict_test")
        backup_path.mkdir(parents=True, exist_ok=True)
        
        existing_file = backup_path / "DBM-Core" / "DBM-Core.lua"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.write_text("existing content")
        
        # Create profile
        profile = AddonProfile(
            name="conflict_test",
            addons=["DBM-Core"],
            wow_installation=found_installation,
            account_name="TestAccount"
        )
        
        # Mock user input for conflict resolution
        with patch.object(backup_manager, '_resolve_conflict', return_value="skip"):
            result = await backup_manager.create_backup(profile, addon_files)
        
        # Files should be skipped, not overwritten
        assert len(result.skipped_files) > 0
        assert existing_file.read_text() == "existing content"  # Unchanged
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_workflow(self, create_mock_installation, temp_dir):
        """Test workflow with various error conditions."""
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={"TestAccount": ["DBM-Core"]}
        )
        
        config = Config(data_dir=temp_dir / "data")
        config.backup.destination_path = temp_dir / "backups"
        
        scanner = WoWScanner(config)
        backup_manager = BackupManager(config.backup, config.conflicts)
        
        installations = scanner.scan_installations()
        found_installation = installations[0]
        
        # Test permission error during backup
        addon_files = scanner.get_addon_files(found_installation, "TestAccount")
        
        profile = AddonProfile(
            name="error_test",
            addons=["DBM-Core"],
            wow_installation=found_installation,
            account_name="TestAccount"
        )
        
        # Mock permission error
        with patch.object(backup_manager, '_copy_file_with_progress') as mock_copy:
            mock_copy.side_effect = PermissionError("Access denied")
            
            result = await backup_manager.create_backup(profile, addon_files)
            
            assert result.success is False
            assert len(result.failed_files) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_large_scale_backup_workflow(self, create_mock_installation, temp_dir):
        """Test workflow with many addons (performance test)."""
        # Create installation with many addons
        addon_names = [f"Addon{i:02d}" for i in range(50)]  # 50 addons
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={"TestAccount": addon_names}
        )
        
        config = Config(data_dir=temp_dir / "data")
        config.backup.destination_path = temp_dir / "backups"
        config.backup.validate_integrity = True  # Enable for performance test
        
        scanner = WoWScanner(config)
        backup_manager = BackupManager(config.backup, config.conflicts)
        
        # Start timer
        import time
        start_time = time.time()
        
        # Scan and backup
        installations = scanner.scan_installations()
        found_installation = installations[0]
        
        addon_files = scanner.get_addon_files(found_installation, "TestAccount")
        assert len(addon_files) == 50
        
        profile = AddonProfile(
            name="large_scale_test",
            addons=list(addon_files.keys()),
            wow_installation=found_installation,
            account_name="TestAccount"
        )
        
        result = await backup_manager.create_backup(profile, addon_files)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify results
        assert result.success is True
        assert len(result.copied_files) == 50
        
        # Performance should be reasonable (less than 10 seconds for 50 small files)
        assert duration < 10.0
        
        print(f"Large scale backup completed in {duration:.2f} seconds")
    
    @pytest.mark.integration
    def test_cli_menu_integration(self, create_mock_installation, temp_dir, monkeypatch):
        """Test CLI menu integration with mocked user input."""
        # Create mock installation
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={"TestAccount": ["DBM-Core", "Bartender4"]}
        )
        
        config = Config(data_dir=temp_dir / "data")
        config.scan.scan_paths = [temp_dir]
        
        menu = InteractiveMenu(config)
        
        # Mock user input sequence
        user_inputs = [
            "1",  # Scan installations
            "1",  # Select first installation
            "2",  # List addons (skip account selection for simplicity)
            "6"   # Exit
        ]
        
        input_iter = iter(user_inputs)
        monkeypatch.setattr('builtins.input', lambda prompt="": next(input_iter))
        
        # Mock async operations
        async def mock_scan_installations():
            return [installation]
        
        async def mock_select_account(installation):
            return "TestAccount"
        
        async def mock_scan_addons(installation, account_name):
            return ["DBM-Core", "Bartender4"]
        
        monkeypatch.setattr(menu.scanner, 'scan_installations', mock_scan_installations)
        monkeypatch.setattr(menu, 'select_account', mock_select_account)
        monkeypatch.setattr(menu, 'scan_addons', mock_scan_addons)
        
        # Run menu (should not crash)
        async def run_menu():
            menu.display_welcome()
            choice = menu.display_main_menu()
            assert choice == 1
            
            # Mock the rest of the workflow
            installations = await menu.scan_installations()
            assert len(installations) == 1
            
            selected = menu.display_installations(installations)
            assert selected is not None
        
        asyncio.run(run_menu())
    
    @pytest.mark.integration
    def test_configuration_integration(self, temp_dir):
        """Test configuration system integration."""
        # Test configuration loading and saving
        config = Config(data_dir=temp_dir / "data")
        
        # Modify configuration
        config.backup.destination_path = temp_dir / "custom_backups"
        config.backup.validate_integrity = False
        config.debug_mode = True
        
        # Test config paths
        assert config.get_config_file_path().exists() is False  # Not created yet
        assert config.get_lock_file_path().parent.exists()  # Data dir created
        
        # Test default scan paths
        assert len(config.scan.scan_paths) >= 0
        
        # Test backup config
        backup_path = config.backup.get_backup_path("test_profile")
        assert "test_profile" in str(backup_path)


class TestErrorRecovery:
    """Test error recovery and edge cases."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_partial_backup_recovery(self, create_mock_installation, temp_dir):
        """Test recovery from partial backup failures."""
        installation = create_mock_installation(
            "World of Warcraft",
            accounts={"TestAccount": ["Addon1", "Addon2", "Addon3"]}
        )
        
        config = Config(data_dir=temp_dir / "data")
        config.backup.destination_path = temp_dir / "backups"
        
        scanner = WoWScanner(config)
        backup_manager = BackupManager(config.backup, config.conflicts)
        
        installations = scanner.scan_installations()
        found_installation = installations[0]
        addon_files = scanner.get_addon_files(found_installation, "TestAccount")
        
        profile = AddonProfile(
            name="recovery_test",
            addons=list(addon_files.keys()),
            wow_installation=found_installation,
            account_name="TestAccount"
        )
        
        # Mock partial failure - second file fails
        call_count = 0
        original_copy = backup_manager._copy_file_with_progress
        
        async def mock_copy_with_failure(source, dest):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise PermissionError("Simulated failure")
            await original_copy(source, dest)
        
        with patch.object(backup_manager, '_copy_file_with_progress', mock_copy_with_failure):
            result = await backup_manager.create_backup(profile, addon_files)
        
        # Should have partial success and failure
        assert result.success is False  # Overall failure due to errors
        assert len(result.copied_files) > 0  # Some files copied
        assert len(result.failed_files) > 0   # Some files failed
        assert call_count == 3  # All files attempted