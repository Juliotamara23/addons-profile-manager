"""Quick manual test script to verify scanner changes."""

from pathlib import Path
from src.addons_profile_manager.config.settings import Config, ScanConfig
from src.addons_profile_manager.core.scanner import WoWScanner

def test_scanner():
    # Create test config
    config = Config()
    scanner = WoWScanner(config)
    
    # Test folder structure validation
    print("Testing folder structure validation...")
    test_path = Path("E:/DEV/Proyects")  # Example, won't have WoW structure
    result = scanner._validate_folder_structure(test_path)
    print(f"Validation result for non-WoW path: {result}")
    
    # Test addon name extraction
    print("\nTesting addon name extraction...")
    test_files = [
        Path("DBM-Core.lua"),
        Path("DBM-Core.lua.bak"),
        Path("Bartender4.lua"),
        Path("Bartender4.lua.bak"),
        Path("ElvUI.lua"),
    ]
    
    for test_file in test_files:
        addon_name = scanner._extract_addon_name(test_file)
        print(f"{test_file.name} -> {addon_name}")
    
    print("\nScanner basic functionality test complete!")

if __name__ == "__main__":
    test_scanner()
