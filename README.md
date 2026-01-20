# WoW Addon Profile Manager

Una herramienta Python moderna para gestionar configuraciones de addons de World of Warcraft, permitiendo crear backups y restaurar perfiles de addons entre diferentes instalaciones.

## 🚀 Características

- **Detección Automática**: Escanea instalaciones de WoW (Retail, Classic, PTR)
- **Backup Inteligente**: Copia configuraciones de addons con validación de integridad
- **CLI Interactiva**: Menú amigable con colores y barras de progreso
- **Manejo de Conflictos**: Resolución inteligente de archivos existentes
- **Testing Completo**: 90%+ cobertura de tests unitarios e integración
- **Type Safety**: Python 3.10+ con type hints completos

## 📋 Requisitos

- Python 3.10 o superior
- World of Warcraft instalado
- Permisos de lectura en carpetas WTF del juego

## 🛠️ Instalación

### Desde Source

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/addons-profile-manager.git
cd addons-profile-manager

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -e .
```

### Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Instalar pre-commit hooks (opcional)
pre-commit install
```

## 🎮 Uso Rápido

### CLI Interactiva

```bash
# Iniciar el modo interactivo
python -m addons_profile_manager

# O usando el comando instalado
addons-profile-manager
```

### Flujo Básico

1. **Escanear instalaciones**: Detecta automáticamente tus instalaciones de WoW
2. **Seleccionar cuenta**: Elige la cuenta con los addons a respaldar
3. **Seleccionar addons**: Marca los addons específicos que quieres backup
4. **Elegir destino**: Selecciona dónde guardar el backup
5. **Iniciar backup**: Proceso con validación de integridad

### Ejemplo de Uso

```bash
$ addons-profile-manager --verbose
WoW Addon Profile Manager - Manage your addon configurations
Version 0.1.0

=== Main Menu ===
1. Scan for WoW installations
2. List available addons
3. Select addons for backup
4. Choose backup destination
5. Start backup process
6. Exit

Select an option: 1
Scanning for WoW installations...
✓ Found 2 WoW installation(s)

=== WoW Installations ===
1. Retail - C:/Program Files/World of Warcraft
2. Classic - C:/Program Files/World of Warcraft Classic

Select WoW installation (0 to cancel): 1
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
addons_profile_manager/
├── src/addons_profile_manager/
│   ├── __init__.py              # Configuración del paquete
│   ├── __main__.py              # Entry point
│   ├── cli.py                   # CLI interactiva
│   ├── config/
│   │   ├── settings.py          # Dataclasses de configuración
│   │   └── constants.py         # Constantes y mensajes
│   ├── core/
│   │   ├── scanner.py           # Detección de instalaciones WoW
│   │   └── backup.py            # Gestión de backups
│   └── utils/
│       ├── exceptions.py        # Excepciones personalizadas
│       ├── file_ops.py          # Utilidades de archivos
│       └── logger.py            # Sistema de logging
├── tests/
│   ├── unit/                    # Tests unitarios
│   ├── integration/             # Tests de integración
│   └── conftest.py              # Configuración de pytest
├── pyproject.toml               # Configuración del proyecto
└── README.md
```

### Componentes Principales

#### **WoWScanner**
- Detecta instalaciones de WoW en múltiples plataformas
- Soporta Retail, Classic, PTR, y Beta
- Escanea cuentas y archivos de configuración

#### **BackupManager**
- Copia archivos de configuración con validación
- Manejo de conflictos configurable
- Metadatos de backup y restore

#### **Config System**
- Configuración basada en dataclasses
- Paths cross-platform
- Validación automática

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=addons_profile_manager --cov-report=html

# Tests unitarios solamente
pytest tests/unit/

# Tests de integración
pytest tests/integration/ -m integration

# Tests rápidos (excluir slow)
pytest -m "not slow"
```

### Tipos de Tests

- **Unit Tests**: Pruebas de componentes individuales
- **Integration Tests**: Flujo completo de trabajo
- **Performance Tests**: Validación de rendimiento con grandes volúmenes

## 🔧 Configuración

### Archivo de Configuración

El sistema usa `~/.addons_profile_manager/config.toml`:

```toml
[data_dir]
default = "~/.addons_profile_manager"

[backup]
destination_path = "~/AddonBackups"
create_timestamp_folder = true
validate_integrity = true
compress_backup = false

[scan]
include_beta = false
include_ptr = false
max_depth = 3
follow_symlinks = false

[conflicts]
strategy = "prompt"  # "prompt", "overwrite", "skip", "backup"
backup_existing = true
backup_suffix = ".backup"
```

### Variables de Entorno

```bash
# Deshabilitar colores en terminal
export NO_COLOR=1

# Directorio de datos personalizado
export ADDON_MANAGER_DATA_DIR="/custom/path"
```

## 📁 Estructura de WoW

El sistema trabaja con la estructura estándar de WoW:

```
World of Warcraft/
├── Wow.exe
└── WTF/
    └── Account/
        ├── ACCOUNT_NAME/
        │   ├── SavedVariables/
        │   │   ├── DBM-Core.lua
        │   │   ├── Bartender4.lua
        │   │   └── ...
        │   └── account-settings.lua
        └── ...
```

## 🚀 Comandos CLI

```bash
# Iniciar modo interactivo
addons-profile-manager

# Modo verbose para debugging
addons-profile-manager --verbose

# Modo debug
addons-profile-manager --debug

# Usar configuración personalizada
addons-profile-manager --config /path/to/config.toml
```

## 🔄 Ejemplos de Uso

### Backup Individual

```python
from addons_profile_manager import WoWScanner, BackupManager, Config

# Inicializar
config = Config()
scanner = WoWScanner(config)
backup_manager = BackupManager(config.backup, config.conflicts)

# Escanear instalaciones
installations = scanner.scan_installations()
installation = installations[0]

# Obtener addons
accounts = scanner.get_accounts(installation)
addon_files = scanner.get_addon_files(installation, accounts[0])

# Crear backup
from addons_profile_manager.config.settings import AddonProfile
profile = AddonProfile(
    name="my_backup",
    addons=list(addon_files.keys()),
    wow_installation=installation,
    account_name=accounts[0]
)

result = await backup_manager.create_backup(profile, addon_files)
print(f"Backup {'successful' if result.success else 'failed'}")
```

### Validación de Backups

```python
# Verificar integridad de backup
backup_info = backup_manager.get_backup_info(backup_path)
if backup_info:
    print(f"Backup from {backup_info['created_at']}")
    print(f"Addons: {list(backup_info['addons'].keys())}")
```

## 🤝 Contribución

1. Fork el repositorio
2. Crear feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Crear Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/
ruff format src/

# Type checking
mypy src/

# Run all tests
pytest
```

## 📝 License

Este proyecto está bajo la MIT License - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- A la comunidad de addon developers de WoW por inspirar esta herramienta
- A los proyectos open-source que hacen posible este software

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/addons-profile-manager/issues)
- **Discord**: [Servidor de Discord](https://discord.gg/invitación)
- **Wiki**: [Documentación completa](https://addons-profile-manager.readthedocs.io)

---

**⚠️ Disclaimer**: Este software no está afiliado con Blizzard Entertainment. World of Warcraft es marca registrada de Blizzard Entertainment, Inc.