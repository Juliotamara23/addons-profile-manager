"""Interactive CLI interface for WoW Addon Profile Manager."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
from colorama import Fore, Style, init
from tqdm import tqdm

from ..config.settings import AddonProfile, Config
from ..config.constants import Colors, Messages
from ..core.backup import BackupManager
from ..core.scanner import WoWScanner
from ..utils.exceptions import AddonManagerError


# Initialize colorama
init(autoreset=True)


class ColoredOutput:
    """Helper class for colored terminal output."""
    
    @staticmethod
    def success(message: str) -> None:
        """Print success message in green."""
        print(f"{Fore.GREEN}{Messages.SUCCESS_PREFIX}: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def error(message: str) -> None:
        """Print error message in red."""
        print(f"{Fore.RED}{Messages.ERROR_PREFIX}: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def warning(message: str) -> None:
        """Print warning message in yellow."""
        print(f"{Fore.YELLOW}{Messages.WARNING_PREFIX}: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def info(message: str) -> None:
        """Print info message in blue."""
        print(f"{Fore.CYAN}{Messages.INFO_PREFIX}: {message}{Style.RESET_ALL}")
    
    @staticmethod
    def header(message: str) -> None:
        """Print header message in bold cyan."""
        print(f"{Fore.CYAN}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    
    @staticmethod
    def highlight(message: str) -> None:
        """Print highlighted message in bold white."""
        print(f"{Fore.WHITE}{Style.BRIGHT}{message}{Style.RESET_ALL}")


class InteractiveMenu:
    """Interactive menu system for CLI operations."""
    
    def __init__(self, config: Config) -> None:
        """Initialize menu with configuration."""
        self.config = config
        self.scanner = WoWScanner(config)
        self.backup_manager = BackupManager(config.backup, config.conflicts)
        self.output = ColoredOutput()
        
        # Runtime state
        self.selected_installation: Optional[object] = None
        self.selected_account: Optional[str] = None
        self.selected_addons: List[str] = []
        self.available_addons: List[str] = []
    
    def display_welcome(self) -> None:
        """Display welcome message."""
        self.output.header(Messages.WELCOME)
        self.output.info(Messages.VERSION_INFO.format(version="0.1.0"))
        print()
    
    def display_main_menu(self) -> int:
        """Display main menu and get user choice."""
        self.output.header("=== Main Menu ===")
        
        for i, option in enumerate(Messages.MAIN_MENU_OPTIONS, 1):
            print(f"{i}. {option}")
        
        print()
        try:
            choice = int(input("Select an option: "))
            if 1 <= choice <= len(Messages.MAIN_MENU_OPTIONS):
                return choice
            else:
                self.output.warning("Invalid choice. Please try again.")
                return self.display_main_menu()
        except (ValueError, KeyboardInterrupt):
            return 6  # Exit
    
    async def scan_installations(self) -> List[object]:
        """Scan for WoW installations."""
        self.output.info(Messages.SCANNING_INSTALLATIONS)
        
        try:
            installations = self.scanner.scan_installations()
            
            if not installations:
                self.output.error(Messages.NO_INSTALLATIONS_FOUND)
                return []
            
            self.output.success(Messages.FOUND_INSTALLATIONS.format(count=len(installations)))
            return installations
            
        except AddonManagerError as e:
            self.output.error(f"Failed to scan installations: {e}")
            return []
    
    def display_installations(self, installations: List[object]) -> Optional[object]:
        """Display found installations and let user select."""
        if not installations:
            return None
        
        self.output.header("=== WoW Installations ===")
        
        for i, installation in enumerate(installations, 1):
            version_str = installation.version.value.title()
            path_str = str(installation.path)
            print(f"{i}. {version_str} - {path_str}")
        
        print()
        try:
            choice = int(input(Messages.SELECT_INSTALLATION + " (0 to cancel): "))
            if choice == 0:
                return None
            elif 1 <= choice <= len(installations):
                return installations[choice - 1]
            else:
                self.output.warning("Invalid choice.")
                return self.display_installations(installations)
        except (ValueError, KeyboardInterrupt):
            return None
    
    async def select_account(self, installation: object) -> Optional[str]:
        """Select account from WoW installation."""
        try:
            accounts = self.scanner.get_accounts(installation)
            
            if not accounts:
                self.output.error("No accounts found with SavedVariables.")
                return None
            
            self.output.header("=== Accounts ===")
            for i, account in enumerate(accounts, 1):
                print(f"{i}. {account}")
            
            print()
            choice = int(input(Messages.SELECT_ACCOUNT + " (0 to cancel): "))
            if choice == 0:
                return None
            elif 1 <= choice <= len(accounts):
                return accounts[choice - 1]
            else:
                self.output.warning("Invalid choice.")
                return await self.select_account(installation)
                
        except AddonManagerError as e:
            self.output.error(f"Failed to get accounts: {e}")
            return None
    
    async def scan_addons(self, installation: object, account_name: str) -> List[str]:
        """Scan for available addons."""
        try:
            addon_files = self.scanner.get_addon_files(installation, account_name)
            addons = list(addon_files.keys())
            
            if not addons:
                self.output.warning("No addon configurations found.")
                return []
            
            self.output.success(f"Found {len(addons)} addon(s)")
            return addons
            
        except AddonManagerError as e:
            self.output.error(f"Failed to scan addons: {e}")
            return []
    
    def select_addons(self, available_addons: List[str]) -> List[str]:
        """Interactive addon selection."""
        if not available_addons:
            return []
        
        self.output.header("=== Select Addons ===")
        self.output.info(Messages.SELECT_ADDONS)
        print()
        
        selected = []
        
        while True:
            # Clear screen and display current selection
            self._clear_screen()
            self.output.header("=== Select Addons ===")
            self.output.info("Space to toggle, Enter to confirm, 'a' for all, 'n' for none")
            print()
            
            for i, addon in enumerate(available_addons):
                status = "✓" if addon in selected else " "
                color = Fore.GREEN if addon in selected else Fore.WHITE
                print(f"{color}[{status}] {i+1:2d}. {addon}{Style.RESET_ALL}")
            
            print()
            print(f"Selected: {len(selected)} of {len(available_addons)} addons")
            
            # Get user input
            try:
                user_input = input("Action: ").strip().lower()
                
                if user_input == "":
                    break  # Confirm selection
                elif user_input == "a":
                    selected = available_addons.copy()
                elif user_input == "n":
                    selected = []
                elif user_input.isdigit():
                    index = int(user_input) - 1
                    if 0 <= index < len(available_addons):
                        addon = available_addons[index]
                        if addon in selected:
                            selected.remove(addon)
                        else:
                            selected.append(addon)
                else:
                    self.output.warning("Invalid input.")
            
            except KeyboardInterrupt:
                return []
        
        return selected
    
    def select_destination(self) -> Optional[Path]:
        """Select backup destination directory."""
        self.output.header("=== Backup Destination ===")
        
        default_path = self.config.backup.destination_path
        print(f"Default destination: {default_path}")
        print()
        
        user_input = input(Messages.SELECT_DESTINATION + " (Enter for default): ").strip()
        
        if not user_input:
            return default_path
        
        try:
            dest_path = Path(user_input)
            dest_path.mkdir(parents=True, exist_ok=True)
            return dest_path
        except Exception as e:
            self.output.error(f"Invalid destination path: {e}")
            return self.select_destination()
    
    async def create_backup(self) -> bool:
        """Create backup with current selections."""
        if not self.selected_installation or not self.selected_account or not self.selected_addons:
            self.output.error("Please complete all selections first.")
            return False
        
        try:
            # Get addon files
            addon_files = self.scanner.get_addon_files(
                self.selected_installation, 
                self.selected_account
            )
            
            # Filter selected addons
            selected_files = {
                addon: files for addon, files in addon_files.items()
                if addon in self.selected_addons
            }
            
            # Create profile
            profile = AddonProfile(
                name=f"backup_{self.selected_account}_{len(self.selected_addons)}_addons",
                addons=self.selected_addons,
                wow_installation=self.selected_installation,
                account_name=self.selected_account
            )
            
            self.output.info(Messages.STARTING_BACKUP)
            
            # Create backup with progress bar
            with tqdm(total=len(selected_files), desc="Backing up addons") as pbar:
                # TODO: Implement progress callback
                result = await self.backup_manager.create_backup(profile, selected_files)
                pbar.update(len(selected_files))
            
            if result.success:
                self.output.success(Messages.BACKUP_COMPLETE)
                if result.validation_errors:
                    self.output.warning(f"Found {len(result.validation_errors)} validation errors")
                return True
            else:
                self.output.error(Messages.BACKUP_FAILED.format(error="Unknown error"))
                return False
        
        except AddonManagerError as e:
            self.output.error(Messages.BACKUP_FAILED.format(error=str(e)))
            return False
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
@click.option('--config', '-c', type=click.Path(), help='Path to configuration file')
def main(verbose: bool, debug: bool, config: Optional[str]) -> int:
    """WoW Addon Profile Manager - Manage your addon configurations."""
    
    # Load configuration
    try:
        app_config = Config()
        app_config.verbose_mode = verbose
        app_config.debug_mode = debug
        
        if config:
            config_path = Path(config)
            if config_path.exists():
                app_config.load_from_file(config_path)
    
    except Exception as e:
        ColoredOutput.error(f"Failed to load configuration: {e}")
        return 1
    
    # Create and run interactive menu
    menu = InteractiveMenu(app_config)
    
    async def run_interactive():
        menu.display_welcome()
        
        while True:
            choice = menu.display_main_menu()
            
            if choice == 1:  # Scan installations
                installations = await menu.scan_installations()
                if installations:
                    menu.selected_installation = menu.display_installations(installations)
            
            elif choice == 2:  # List addons
                if menu.selected_installation and menu.selected_account:
                    menu.available_addons = await menu.scan_addons(
                        menu.selected_installation, 
                        menu.selected_account
                    )
                    if menu.available_addons:
                        menu.output.header("=== Available Addons ===")
                        for addon in menu.available_addons:
                            print(f"  • {addon}")
                else:
                    menu.output.warning("Please select installation and account first.")
            
            elif choice == 3:  # Select addons
                if menu.available_addons:
                    menu.selected_addons = menu.select_addons(menu.available_addons)
                    menu.output.success(f"Selected {len(menu.selected_addons)} addons")
                else:
                    menu.output.warning("No addons available. Please scan first.")
            
            elif choice == 4:  # Choose destination
                dest = menu.select_destination()
                if dest:
                    menu.config.backup.destination_path = dest
                    menu.output.success(f"Destination set to: {dest}")
            
            elif choice == 5:  # Start backup
                if not menu.selected_installation:
                    menu.output.warning("Please select WoW installation first.")
                elif not menu.selected_account:
                    menu.output.warning("Please select account first.")
                elif not menu.selected_addons:
                    menu.output.warning("Please select addons first.")
                else:
                    await menu.create_backup()
            
            elif choice == 6:  # Exit
                menu.output.success("Goodbye!")
                break
    
    try:
        asyncio.run(run_interactive())
        return 0
    except KeyboardInterrupt:
        ColoredOutput.warning("Operation cancelled by user.")
        return 1
    except Exception as e:
        ColoredOutput.error(f"Unexpected error: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())