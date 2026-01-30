"""Interactive CLI interface for WoW Addon Profile Manager."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
from colorama import Fore, Style, init
from tqdm import tqdm

from .config.settings import AddonProfile, Config, WoWInstallation
from .config.constants import Colors, Messages
from .core.backup import BackupManager
from .core.scanner import WoWScanner
from .utils.exceptions import AddonManagerError


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
        self.selected_installation: Optional[WoWInstallation] = None
        self.selected_account: Optional[str] = None
        self.selected_addons: List[str] = []
        self.available_addons: List[str] = []

    def display_welcome(self) -> None:
        """Display welcome message with ASCII banner."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        WoW Addon Profile Manager                             ║
║        Gestiona tus perfiles de addons fácilmente            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")
        self.output.info(Messages.VERSION_INFO.format(version="0.1.0"))
        print(f"{Fore.WHITE}Respalda y restaura configuraciones de addons de World of Warcraft{Style.RESET_ALL}")
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

    async def scan_installations(self) -> List[WoWInstallation]:
        """Scan for WoW installations."""
        self.output.info(Messages.SCANNING_INSTALLATIONS)

        try:
            installations = self.scanner.scan_installations()

            if not installations:
                self.output.error(Messages.NO_INSTALLATIONS_FOUND)
                
                # Offer manual path option
                choice = input(Messages.MANUAL_PATH_PROMPT + " ").strip().lower()
                if choice in ['y', 'yes']:
                    manual_installation = await self._add_manual_installation()
                    if manual_installation:
                        installations = [manual_installation]
                    else:
                        self.output.error("No valid WoW installation found at specified path.")
                        return []
                else:
                    return []

            self.output.success(
                Messages.FOUND_INSTALLATIONS.format(count=len(installations))
            )
            return installations

        except AddonManagerError as e:
            self.output.error(f"Failed to scan installations: {e}")
            return []

    def display_installations(self, installations: List[WoWInstallation]) -> Optional[WoWInstallation]:
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

    async def select_account(self, installation: WoWInstallation) -> Optional[str]:
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

    async def scan_addons(self, installation: WoWInstallation, account_name: str) -> List[str]:
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
            self.output.info(
                "Space to toggle, Enter to confirm, 'a' for all, 'n' for none"
            )
            print()

            for i, addon in enumerate(available_addons):
                status = "✓" if addon in selected else " "
                color = Fore.GREEN if addon in selected else Fore.WHITE
                print(f"{color}[{status}] {i + 1:2d}. {addon}{Style.RESET_ALL}")

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

    async def _add_manual_installation(self) -> Optional[WoWInstallation]:
        """Add a manually specified WoW installation."""
        self.output.info(Messages.MANUAL_PATH_INSTRUCTIONS)
        print(f"{Fore.YELLOW}{Messages.MANUAL_PATH_EXAMPLE}{Style.RESET_ALL}")
        print()
        
        while True:
            try:
                path_input = input(f"{Fore.CYAN}WoW installation path: {Style.RESET_ALL}").strip()
                if not path_input:
                    return None
                
                # Remove quotes if user pasted path with quotes
                path_input = path_input.strip('"').strip("'")
                
                path = Path(path_input)
                if not path.exists():
                    self.output.error(f"Path does not exist: {path}")
                    continue
                
                installation = self.scanner.add_manual_installation(path)
                if installation:
                    version_str = installation.version.value.title()
                    self.output.success(f"Found WoW installation: {version_str}")
                    return installation
                else:
                    self.output.error("No valid WoW installation found at the specified path.")
                    self.output.info("The path should contain WTF/Account folders or be a direct SavedVariables path.")
                    
                    retry = input("Try another path? (y/n): ").strip().lower()
                    if retry not in ['y', 'yes']:
                        return None
                    
            except KeyboardInterrupt:
                return None
            except Exception as e:
                self.output.error(f"Error processing path: {e}")
                return None

    def select_destination(self) -> Optional[Path]:
        """Select backup destination directory."""
        self.output.header("=== Backup Destination ===")

        default_path = self.config.backup.destination_path
        print(f"Default destination: {default_path}")
        print(f"{Fore.YELLOW}Example: C:\\Backups\\WoW_Addons (you can copy-paste paths directly){Style.RESET_ALL}")
        print()

        user_input = input(
            Messages.SELECT_DESTINATION + " (Enter for default): "
        ).strip()

        if not user_input:
            return default_path

        try:
            # Remove quotes if user pasted path with quotes
            user_input = user_input.strip('"').strip("'")
            dest_path = Path(user_input)
            dest_path.mkdir(parents=True, exist_ok=True)
            return dest_path
        except Exception as e:
            self.output.error(f"Invalid destination path: {e}")
            return self.select_destination()

    async def create_backup(self) -> bool:
        """Create backup with current selections."""
        if (
            not self.selected_installation
            or not self.selected_account
            or not self.selected_addons
        ):
            self.output.error("Please complete all selections first.")
            return False

        try:
            # Get addon files
            addon_files = self.scanner.get_addon_files(
                self.selected_installation, self.selected_account
            )

            # Filter selected addons
            selected_files = {
                addon: files
                for addon, files in addon_files.items()
                if addon in self.selected_addons
            }

            # Create profile
            profile = AddonProfile(
                name=f"backup_{self.selected_account}_{len(self.selected_addons)}_addons",
                addons=self.selected_addons,
                wow_installation=self.selected_installation,
                account_name=self.selected_account,
            )

            self.output.info(Messages.STARTING_BACKUP)

            # Create backup with progress bar
            with tqdm(total=len(selected_files), desc="Backing up addons") as pbar:
                # TODO: Implement progress callback
                result = await self.backup_manager.create_backup(
                    profile, selected_files
                )
                pbar.update(len(selected_files))

            if result.success:
                self.output.success(Messages.BACKUP_COMPLETE)
                return True
            else:
                # Collect and display specific errors
                error_msgs = []
                for file_path, error in result.failed_files:
                    error_msgs.append(f"Failed to process {file_path}: {error}")
                
                for val_error in result.validation_errors:
                    error_msgs.append(str(val_error))
                
                if error_msgs:
                    self.output.error("Backup encountered errors:")
                    for idx, msg in enumerate(error_msgs):
                        if idx < 5:  # Limit display to 5 errors
                            self.output.error(f"  - {msg}")
                        else:
                            remaining = len(error_msgs) - 5
                            self.output.error(f"  ...and {remaining} more errors.")
                            break
                    self.output.error(Messages.BACKUP_FAILED.format(error="See detailed errors above"))
                else:
                    self.output.error(Messages.BACKUP_FAILED.format(error="Unknown error (no failure details recorded)"))
                
                return False

        except AddonManagerError as e:
            self.output.error(Messages.BACKUP_FAILED.format(error=str(e)))
            return False

    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        import os

        os.system("cls" if os.name == "nt" else "clear")


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode")
@click.option("--config", "-c", type=click.Path(), help="Path to configuration file")
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
        """Interactive flow with guided steps."""
        menu.display_welcome()
        
        # Step 1: Get WoW installation (initial menu with 2 options)
        menu.output.header("\n=== Selecciona cómo encontrar tu instalación de WoW ===")
        print(f"{Fore.CYAN}1.{Style.RESET_ALL} Buscar automáticamente (escanea rutas comunes)")
        print(f"{Fore.CYAN}2.{Style.RESET_ALL} Especificar ruta manualmente")
        print(f"{Fore.CYAN}3.{Style.RESET_ALL} Salir")
        print()
        
        try:
            initial_choice = int(input("Selecciona una opción: "))
        except (ValueError, KeyboardInterrupt):
            menu.output.warning("Operación cancelada.")
            return
        
        if initial_choice == 3:
            menu.output.success("¡Hasta luego!")
            return
        elif initial_choice == 1:
            # Auto-scan
            installations = await menu.scan_installations()
            if installations:
                menu.selected_installation = menu.display_installations(installations)
            else:
                menu.output.error("No se encontraron instalaciones.")
                return
        elif initial_choice == 2:
            # Manual path
            manual_installation = await menu._add_manual_installation()
            if manual_installation:
                menu.selected_installation = manual_installation
            else:
                menu.output.error("No se pudo agregar instalación manual.")
                return
        else:
            menu.output.error("Opción inválida.")
            return
        
        if not menu.selected_installation:
            menu.output.warning("No se seleccionó instalación. Saliendo...")
            return
        
        # Step 2: Select account
        menu.output.header("\n=== Selecciona una cuenta ===")
        menu.selected_account = await menu.select_account(menu.selected_installation)
        
        if not menu.selected_account:
            menu.output.warning("No se seleccionó cuenta. Saliendo...")
            return
        
        # Step 3: Scan and select addons
        menu.output.header("\n=== Escaneando addons ===")
        menu.available_addons = await menu.scan_addons(
            menu.selected_installation, menu.selected_account
        )
        
        if not menu.available_addons:
            menu.output.error("No se encontraron addons.")
            return
        
        menu.output.success(f"Encontrados {len(menu.available_addons)} addons")
        print()
        
        # Ask if user wants to select specific addons or backup all
        print(f"{Fore.CYAN}¿Qué deseas hacer?{Style.RESET_ALL}")
        print("1. Seleccionar addons específicos")
        print("2. Respaldar todos los addons")
        print()
        
        try:
            addon_choice = int(input("Selecciona una opción: "))
        except (ValueError, KeyboardInterrupt):
            menu.output.warning("Operación cancelada.")
            return
        
        if addon_choice == 1:
            menu.selected_addons = menu.select_addons(menu.available_addons)
        elif addon_choice == 2:
            menu.selected_addons = menu.available_addons.copy()
            menu.output.success(f"Seleccionados todos los {len(menu.selected_addons)} addons")
        else:
            menu.output.error("Opción inválida.")
            return
        
        if not menu.selected_addons:
            menu.output.warning("No se seleccionaron addons. Saliendo...")
            return
        
        # Step 4: Choose backup destination
        menu.output.header("\n=== Destino del Backup ===")
        dest = menu.select_destination()
        if dest:
            menu.config.backup.destination_path = dest
            menu.output.success(f"Destino configurado: {dest}\\Backup\\")
        else:
            menu.output.warning("No se configuró destino. Saliendo...")
            return
        
        # Step 5: Confirm and start backup
        print()
        menu.output.header("=== Resumen del Backup ===")
        print(f"  Instalación: {menu.selected_installation.path}")
        print(f"  Cuenta: {menu.selected_account}")
        print(f"  Addons: {len(menu.selected_addons)} seleccionados")
        print(f"  Destino: {menu.config.backup.destination_path}\\Backup\\")
        print()
        
        confirm = input(f"{Fore.YELLOW}¿Iniciar backup? (s/n): {Style.RESET_ALL}").strip().lower()
        
        if confirm in ['s', 'si', 'y', 'yes']:
            success = await menu.create_backup()
            if success:
                menu.output.success("\n¡Proceso completado!")
            else:
                menu.output.warning("\nEl proceso finalizó con advertencias o errores.")
        else:
            menu.output.warning("Backup cancelado.")

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
