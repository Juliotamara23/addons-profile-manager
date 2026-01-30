"""Configuration dataclasses and settings for WoW Addon Profile Manager."""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class WoWVersion(Enum):
    """World of Warcraft client versions."""
    RETAIL = "retail"
    CLASSIC = "classic"
    CLASSIC_TBC = "classic_era"
    CLASSIC_WOTLK = "classic_wrath"
    PTR = "ptr"
    BETA = "beta"


@dataclass
class WoWInstallation:
    """Represents a World of Warcraft installation."""
    path: Path
    version: WoWVersion
    client_version: Optional[str] = None
    
    @property
    def wtf_path(self) -> Path:
        """Get the WTF directory path."""
        return self.path / "WTF"
    
    @property
    def account_path(self) -> Path:
        """Get the Account directory path."""
        return self.wtf_path / "Account"
    
    def get_saved_variables_path(self, account_name: str) -> Path:
        """Get SavedVariables path for a specific account."""
        return self.account_path / account_name / "SavedVariables"


@dataclass
class AddonProfile:
    """Represents an addon configuration profile."""
    name: str
    addons: List[str] = field(default_factory=list)
    wow_installation: Optional[WoWInstallation] = None
    account_name: Optional[str] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    
    def get_saved_variables_path(self) -> Optional[Path]:
        """Get the SavedVariables path for this profile."""
        if self.wow_installation and self.account_name:
            return self.wow_installation.get_saved_variables_path(self.account_name)
        return None


@dataclass
class BackupConfig:
    """Configuration for backup operations."""
    destination_path: Path
    create_timestamp_folder: bool = True
    compress_backup: bool = False
    validate_integrity: bool = True
    overwrite_existing: bool = False
    backup_metadata: bool = True
    
    def get_backup_path(self, profile_name: str) -> Path:
        """Get the full backup path for a profile.
        
        Creates path structure: destination_path/Backup/profile_name[_timestamp]
        """
        # Ensure Backup subfolder is created
        backup_base = self.destination_path / "Backup"
        
        if self.create_timestamp_folder:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return backup_base / f"{profile_name}_{timestamp}"
        return backup_base / profile_name


@dataclass
class ConflictResolution:
    """Configuration for handling file conflicts."""
    strategy: str = "prompt"  # "prompt", "overwrite", "skip", "backup"
    backup_existing: bool = True
    backup_suffix: str = ".backup"
    
    def should_prompt(self) -> bool:
        """Check if user should be prompted for conflicts."""
        return self.strategy == "prompt"


@dataclass
class ScanConfig:
    """Configuration for scanning WoW installations."""
    scan_paths: List[Path] = field(default_factory=list)
    include_beta: bool = False
    include_ptr: bool = False
    max_depth: int = 3
    follow_symlinks: bool = False
    
    def __post_init__(self) -> None:
        """Initialize default scan paths."""
        if not self.scan_paths:
            self.scan_paths = self._get_default_scan_paths()
    
    def _get_default_scan_paths(self) -> List[Path]:
        """Get default WoW installation scan paths."""
        paths = []
        
        # Windows default paths
        if os.name == "nt":
            program_files = [Path("C:/Program Files"), Path("C:/Program Files (x86)")]
            for pf in program_files:
                if pf.exists():
                    paths.extend(pf.glob("World of Warcraft*"))
        
        # macOS default paths
        elif os.name == "posix" and Path("/Applications").exists():
            apps = Path("/Applications")
            paths.extend(apps.glob("World of Warcraft*"))
        
        # Linux default paths (wine/proton)
        elif os.name == "posix":
            home = Path.home()
            steam_paths = [
                home / ".steam/steam/steamapps/common",
                home / ".local/share/Steam/steamapps/common",
            ]
            for steam_path in steam_paths:
                if steam_path.exists():
                    paths.extend(steam_path.glob("World of Warcraft*"))
        
        return [p for p in paths if p.is_dir()]


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    colored_output: bool = True


@dataclass
class Config:
    """Main configuration class for WoW Addon Profile Manager."""
    
    # Core settings
    data_dir: Path = field(default_factory=lambda: Path.home() / ".addons_profile_manager")
    temp_dir: Path = field(default_factory=lambda: Path.home() / ".addons_profile_manager" / "temp")
    
    # Component configurations
    scan: ScanConfig = field(default_factory=ScanConfig)
    backup: BackupConfig = field(default_factory=lambda: BackupConfig(destination_path=Path.home() / "AddonBackups"))
    conflicts: ConflictResolution = field(default_factory=ConflictResolution)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Runtime settings
    debug_mode: bool = False
    verbose_mode: bool = False
    quiet_mode: bool = False
    
    def __post_init__(self) -> None:
        """Initialize configuration after creation."""
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.backup.destination_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging if file path specified
        if self.logging.file_path:
            self.logging.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return self.data_dir / "config.toml"
    
    def get_lock_file_path(self) -> Path:
        """Get the path to the lock file for concurrent access."""
        return self.data_dir / "app.lock"
    
    def load_from_file(self, path: Optional[Path] = None) -> None:
        """Load configuration from TOML file."""
        # TODO: Implement TOML loading
        pass
    
    def save_to_file(self, path: Optional[Path] = None) -> None:
        """Save configuration to TOML file."""
        # TODO: Implement TOML saving
        pass