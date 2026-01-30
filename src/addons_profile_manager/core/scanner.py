"""WoW installation scanner for detecting World of Warcraft installations."""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..config.settings import Config, WoWInstallation, WoWVersion
from ..utils.exceptions import (
    PermissionDeniedError,
    SavedVariablesNotFoundError,
    WoWInstallationNotFoundError,
)


class WoWScanner:
    """Scans for and manages World of Warcraft installations."""
    
    def __init__(self, config: Config) -> None:
        """Initialize scanner with configuration."""
        self.config = config
        self._found_installations: List[WoWInstallation] = []
    
    def scan_installations(self) -> List[WoWInstallation]:
        """Scan for WoW installations and return found installations."""
        self._found_installations.clear()
        
        for scan_path in self.config.scan.scan_paths:
            if not scan_path.exists():
                continue
                
            try:
                installations = self._scan_directory(scan_path)
                self._found_installations.extend(installations)
            except PermissionDeniedError as e:
                if self.config.verbose_mode:
                    print(f"Warning: {e}")
                continue
        
        return self._found_installations.copy()
    
    def _scan_directory(self, base_path: Path) -> List[WoWInstallation]:
        """Scan a directory for WoW installations."""
        installations = []
        
        try:
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue
                
                # Check if this looks like a WoW installation
                if self._is_wow_installation(item):
                    version = self._detect_wow_version(item)
                    installation = WoWInstallation(
                        path=item,
                        version=version,
                        client_version=self._get_client_version(item)
                    )
                    installations.append(installation)
                    
                    # Also scan subdirectories if max_depth allows
                    if self.config.scan.max_depth > 1:
                        sub_installations = self._scan_subdirectories(item, depth=2)
                        installations.extend(sub_installations)
        
        except PermissionError as e:
            raise PermissionDeniedError(base_path, "scan directory") from e
        
        return installations
    
    def _scan_subdirectories(self, base_path: Path, depth: int) -> List[WoWInstallation]:
        """Scan subdirectories for WoW installations."""
        if depth > self.config.scan.max_depth:
            return []
        
        installations = []
        
        try:
            for item in base_path.iterdir():
                if not item.is_dir():
                    continue
                
                if self._is_wow_installation(item):
                    version = self._detect_wow_version(item)
                    installation = WoWInstallation(
                        path=item,
                        version=version,
                        client_version=self._get_client_version(item)
                    )
                    installations.append(installation)
                
                # Recurse deeper
                sub_installations = self._scan_subdirectories(item, depth + 1)
                installations.extend(sub_installations)
        
        except PermissionError:
            # Silently ignore permission errors in subdirectories
            pass
        
        return installations
    
    def _validate_folder_structure(self, path: Path) -> bool:
        """Validate WoW folder structure without requiring executables."""
        # Check for WTF/Account structure
        wtf_dir = path / "WTF"
        account_dir = wtf_dir / "Account"
        
        if not wtf_dir.exists() or not wtf_dir.is_dir():
            return False
        
        if not account_dir.exists() or not account_dir.is_dir():
            return False
        
        # Check if at least one account folder with SavedVariables exists
        try:
            for item in account_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    saved_vars = item / "SavedVariables"
                    if saved_vars.exists() and saved_vars.is_dir():
                        return True
        except PermissionError:
            pass
        
        return False
    
    def _is_wow_installation(self, path: Path) -> bool:
        """Check if a path contains a WoW installation."""
        # First try to validate folder structure (more flexible)
        if self._validate_folder_structure(path):
            return True
        
        # Fallback to checking for WoW executable and WTF directory
        wow_exe_names = ["Wow.exe", "WowClassic.exe", "WowT.exe", "Wow-64.exe"]
        wtf_dir = path / "WTF"
        
        has_exe = any((path / exe).exists() for exe in wow_exe_names)
        has_wtf = wtf_dir.exists() and wtf_dir.is_dir()
        
        return has_exe and has_wtf
    
    def _detect_wow_version(self, path: Path) -> WoWVersion:
        """Detect the WoW version of an installation."""
        # Check all parts of the path for version indicators
        path_str = str(path).lower()
        path_parts = [p.lower() for p in path.parts]
        
        # Check for version folders (_retail_, _classic_, etc.)
        for part in path_parts:
            if part == "_retail_":
                return WoWVersion.RETAIL
            elif part == "_classic_era_" or part == "_classic_":
                if "era" in path_str or "vanilla" in path_str:
                    return WoWVersion.CLASSIC_TBC
                elif "wrath" in path_str or "wotlk" in path_str:
                    return WoWVersion.CLASSIC_WOTLK
                else:
                    return WoWVersion.CLASSIC
            elif part == "_ptr_":
                return WoWVersion.PTR
            elif part == "_beta_":
                return WoWVersion.BETA
        
        # Fallback to checking folder name
        path_lower = path.name.lower()
        
        if "classic" in path_lower:
            if "era" in path_lower or "vanilla" in path_lower:
                return WoWVersion.CLASSIC_TBC
            elif "wrath" in path_lower or "wotlk" in path_lower:
                return WoWVersion.CLASSIC_WOTLK
            else:
                return WoWVersion.CLASSIC
        elif "ptr" in path_lower:
            return WoWVersion.PTR
        elif "beta" in path_lower or "alpha" in path_lower:
            return WoWVersion.BETA
        else:
            return WoWVersion.RETAIL
    
    def _get_client_version(self, path: Path) -> Optional[str]:
        """Extract client version from WoW installation."""
        # Try to read from .build.info file
        build_info = path / ".build.info"
        if build_info.exists():
            try:
                with open(build_info, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split('|')
                            if len(parts) >= 2:
                                return parts[1]
            except (PermissionError, UnicodeDecodeError):
                pass
        
        # Fallback: check executable properties
        for exe_name in ["Wow.exe", "WowClassic.exe", "WowT.exe"]:
            exe_path = path / exe_name
            if exe_path.exists():
                try:
                    # Get file modification time as version indicator
                    mtime = exe_path.stat().st_mtime
                    return f"Build-{int(mtime)}"
                except PermissionError:
                    continue
        
        return None
    
    def get_accounts(self, installation: WoWInstallation) -> List[str]:
        """Get list of account names for a WoW installation."""
        account_path = installation.account_path
        
        if not account_path.exists():
            raise SavedVariablesNotFoundError(account_path)
        
        accounts = []
        
        try:
            for item in account_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if this account has SavedVariables
                    saved_vars = item / "SavedVariables"
                    if saved_vars.exists() and saved_vars.is_dir():
                        accounts.append(item.name)
        except PermissionError as e:
            raise PermissionDeniedError(account_path, "list accounts") from e
        
        return sorted(accounts)
    
    def get_addon_files(self, installation: WoWInstallation, account_name: str) -> Dict[str, List[Path]]:
        """Get addon SavedVariables files for an account.
        
        Groups .lua and .lua.bak files under the same addon name.
        """
        saved_vars_path = installation.get_saved_variables_path(account_name)
        
        if not saved_vars_path.exists():
            raise SavedVariablesNotFoundError(saved_vars_path)
        
        addon_files = {}
        
        try:
            # Collect all .lua files (including .lua.bak)
            lua_files = list(saved_vars_path.glob("*.lua"))
            lua_bak_files = list(saved_vars_path.glob("*.lua.bak"))
            
            all_files = lua_files + lua_bak_files
            
            for file_path in all_files:
                # Skip global files that aren't addon-specific
                if self._is_addon_file(file_path):
                    addon_name = self._extract_addon_name(file_path)
                    if addon_name not in addon_files:
                        addon_files[addon_name] = []
                    addon_files[addon_name].append(file_path)
        
        except PermissionError as e:
            raise PermissionDeniedError(saved_vars_path, "scan addon files") from e
        
        return addon_files
    
    def _is_addon_file(self, file_path: Path) -> bool:
        """Check if a file is an addon SavedVariables file."""
        filename = file_path.name.lower()
        
        # Skip non-addon files
        non_addon_files = {
            'bindings.lua',
            'chatcache.lua',
            'glyphcache.lua',
            'macros.lua',
            'panel.lua',
            'preferences.lua',
            'savedvariables.lua',  # Global SavedVariables
        }
        
        return filename not in non_addon_files
    
    def _extract_addon_name(self, file_path: Path) -> str:
        """Extract addon name from SavedVariables file.
        
        Handles both .lua and .lua.bak files, returning clean addon name.
        """
        # Get filename and remove extensions
        name = file_path.name
        
        # Remove .bak extension if present
        if name.endswith('.lua.bak'):
            name = name[:-8]  # Remove .lua.bak
        elif name.endswith('.lua'):
            name = name[:-4]  # Remove .lua
        
        # Handle special cases
        if name.startswith('DBM-'):
            return 'DeadlyBossMods'
        elif name.startswith('ElvUI'):
            return 'ElvUI'
        elif name.startswith('Details'):
            return 'Details'
        
        return name
    
    def validate_installation(self, installation: WoWInstallation) -> bool:
        """Validate that a WoW installation is properly structured."""
        required_dirs = ["WTF", "WTF/Account"]
        
        for dir_path in required_dirs:
            full_path = installation.path / dir_path
            if not full_path.exists() or not full_path.is_dir():
                return False
        
        return True
    
    def get_installation_size(self, installation: WoWInstallation) -> int:
        """Get total size of SavedVariables for an installation."""
        total_size = 0
        
        try:
            for account_name in self.get_accounts(installation):
                saved_vars_path = installation.get_saved_variables_path(account_name)
                if saved_vars_path.exists():
                    for file_path in saved_vars_path.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
        except (PermissionDeniedError, SavedVariablesNotFoundError):
            pass
        
        return total_size
    
    def find_installation_by_path(self, path: Path) -> Optional[WoWInstallation]:
        """Find a specific WoW installation by path."""
        path = path.resolve()
        
        # Check if we already scanned this installation
        for installation in self._found_installations:
            if installation.path.resolve() == path:
                return installation
        
        # Try to scan the specific path
        if self._is_wow_installation(path):
            version = self._detect_wow_version(path)
            installation = WoWInstallation(
                path=path,
                version=version,
                client_version=self._get_client_version(path)
            )
            return installation
        
        return None
    
    def _find_installation_root_from_savedvariables(self, path: Path) -> Optional[Path]:
        """Find WoW installation root from a SavedVariables path by traversing upward."""
        current = path.resolve()
        
        # Traverse up the directory tree
        for _ in range(5):  # Max 5 levels up
            # Check if current directory looks like WoW installation
            if self._validate_folder_structure(current):
                return current
            
            # Check for version folders in path
            if current.name in ["_retail_", "_classic_", "_classic_era_", "_ptr_", "_beta_"]:
                # This is likely a version folder, check parent
                if self._validate_folder_structure(current):
                    return current
            
            # Move up one level
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent
        
        return None
    
    def add_manual_installation(self, path: Path) -> Optional[WoWInstallation]:
        """Add a manually specified WoW installation.
        
        Supports:
        - Full WoW installation path
        - Direct SavedVariables path (will traverse up to find installation)
        - Version-specific paths (_retail_, _classic_, etc.)
        """
        path = path.resolve()
        
        if not path.exists():
            return None
        
        # Try to find installation root if path is SavedVariables or deeper
        installation_path = path
        if "SavedVariables" in str(path):
            root = self._find_installation_root_from_savedvariables(path)
            if root:
                installation_path = root
        
        if not self._is_wow_installation(installation_path):
            return None
        
        # Create installation object
        version = self._detect_wow_version(installation_path)
        installation = WoWInstallation(
            path=installation_path,
            version=version,
            client_version=self._get_client_version(installation_path)
        )
        
        # Add to found installations if not already present
        for existing in self._found_installations:
            if existing.path.resolve() == installation_path:
                return existing
        
        self._found_installations.append(installation)
        return installation