"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock

from src.addons_profile_manager.config.settings import (
    Config,
    WoWInstallation,
    WoWVersion,
    AddonProfile,
    BackupConfig,
    ScanConfig,
)
from src.addons_profile_manager.core.scanner import WoWScanner
from src.addons_profile_manager.core.backup import BackupManager
from src.addons_profile_manager.utils.exceptions import AddonManagerError


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_config(temp_dir):
    """Create mock configuration for testing."""
    return Config(
        data_dir=temp_dir / "data",
        temp_dir=temp_dir / "temp",
        backup=BackupConfig(
            destination_path=temp_dir / "backups",
            create_timestamp_folder=False,
            validate_integrity=True,
        ),
        scan=ScanConfig(
            scan_paths=[temp_dir / "wow_installations"],
            max_depth=2,
        ),
    )


@pytest.fixture
def mock_wow_installation(temp_dir):
    """Create mock WoW installation."""
    wow_path = temp_dir / "World of Warcraft"
    wow_path.mkdir(parents=True)
    
    # Create basic WoW structure
    (wow_path / "WTF").mkdir()
    (wow_path / "WTF" / "Account").mkdir()
    
    # Create mock executable
    (wow_path / "Wow.exe").touch()
    
    return WoWInstallation(
        path=wow_path,
        version=WoWVersion.RETAIL,
        client_version="9.0.0.12345"
    )


@pytest.fixture
def mock_account(mock_wow_installation):
    """Create mock account with SavedVariables."""
    account_name = "TESTACCOUNT"
    account_path = mock_wow_installation.account_path / account_name
    account_path.mkdir(parents=True)
    
    # Create SavedVariables directory
    saved_vars = account_path / "SavedVariables"
    saved_vars.mkdir()
    
    # Create mock addon files
    addon_files = {
        "DBM-Core.lua": "DBM_SavedOptions = {}\n",
        "Bartender4.lua": "Bartender4DB = {}\n",
        "WeakAuras.lua": "WeakAurasSaved = {}\n",
    }
    
    for filename, content in addon_files.items():
        (saved_vars / filename).write_text(content)
    
    return account_name


@pytest.fixture
def mock_addon_profile(mock_wow_installation, mock_account):
    """Create mock addon profile."""
    return AddonProfile(
        name="test_profile",
        addons=["DBM-Core", "Bartender4", "WeakAuras"],
        wow_installation=mock_wow_installation,
        account_name=mock_account,
    )


@pytest.fixture
def mock_scanner(mock_config):
    """Create mock WoW scanner."""
    return WoWScanner(mock_config)


@pytest.fixture
def mock_backup_manager(mock_config):
    """Create mock backup manager."""
    return BackupManager(mock_config.backup, mock_config.conflicts)


@pytest.fixture
def sample_addon_files(temp_dir):
    """Create sample addon files for testing."""
    addon_files = {
        "DBM-Core": [
            temp_dir / "DBM-Core.lua",
            temp_dir / "DBM-StatusBarTimers.lua",
        ],
        "Bartender4": [
            temp_dir / "Bartender4.lua",
        ],
        "WeakAuras": [
            temp_dir / "WeakAuras.lua",
            temp_dir / "WeakAurasOptions.lua",
        ],
    }
    
    # Create files with content
    for addon, files in addon_files.items():
        for file_path in files:
            file_path.write_text(f"-- {addon} saved variables\n")


class MockWoWInstallation:
    """Mock WoW installation for testing."""
    
    def __init__(self, path: Path, version: WoWVersion = WoWVersion.RETAIL):
        self.path = path
        self.version = version
        self.client_version = "9.0.0.12345"
        
        # Create directory structure
        self.wtf_path = path / "WTF"
        self.account_path = self.wtf_path / "Account"
        
        self.wtf_path.mkdir(parents=True, exist_ok=True)
        self.account_path.mkdir(parents=True, exist_ok=True)
        
        # Create executable
        (path / "Wow.exe").touch()
    
    def get_saved_variables_path(self, account_name: str) -> Path:
        """Get SavedVariables path for account."""
        return self.account_path / account_name / "SavedVariables"
    
    def add_account(self, account_name: str, addon_names: List[str] = None) -> None:
        """Add account with addon files."""
        addon_names = addon_names or ["TestAddon"]
        
        account_path = self.account_path / account_name
        saved_vars = account_path / "SavedVariables"
        
        saved_vars.mkdir(parents=True, exist_ok=True)
        
        for addon_name in addon_names:
            (saved_vars / f"{addon_name}.lua").write_text(f"-- {addon_name} data\n")


@pytest.fixture
def create_mock_installation(temp_dir):
    """Factory to create mock installations."""
    def _create_installation(
        name: str = "World of Warcraft",
        version: WoWVersion = WoWVersion.RETAIL,
        accounts: Dict[str, List[str]] = None
    ) -> MockWoWInstallation:
        path = temp_dir / name
        installation = MockWoWInstallation(path, version)
        
        if accounts:
            for account_name, addons in accounts.items():
                installation.add_account(account_name, addons)
        
        return installation
    
    return _create_installation


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    class MockFileOps:
        def __init__(self):
            self.copied_files = []
            self.failed_files = []
        
        async def copy_file_async(self, source: Path, dest: Path, **kwargs):
            if source.name == "fail_copy.lua":
                self.failed_files.append(source)
                raise PermissionError("Mock permission error")
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(source.read_text())
            self.copied_files.append((source, dest))
        
        def calculate_file_hash(self, file_path: Path, algorithm: str = "md5"):
            return f"mock_{algorithm}_hash"
        
        def get_file_size(self, file_path: Path):
            return 1024  # Mock size
        
        def check_disk_space(self, path: Path, required_bytes: int):
            return True  # Always enough space
    
    return MockFileOps()


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    # Disable colorama for cleaner test output
    monkeypatch.setenv("NO_COLOR", "1")
    
    # Mock any environment-dependent functionality
    monkeypatch.setattr("src.addons_profile_manager.utils.logger.init", lambda: None)


# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "windows_only: marks tests that only run on Windows"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for platform-specific tests."""
    # Skip Windows-only tests on other platforms
    import sys
    if sys.platform != "win32":
        skip_windows = pytest.mark.skip(reason="Windows-only test")
        for item in items:
            if "windows_only" in item.keywords:
                item.add_marker(skip_windows)