# 🎮 WoW Addon Profile Manager

Una herramienta Python moderna para gestionar configuraciones de addons de World of Warcraft, permitiendo crear backups y restaurar perfiles de addons entre diferentes instalaciones.

---

## ✨ Características Principales

| Característica | Descripción |
|----------------|-------------|
| 🔍 **Detección Flexible** | Escanea instalaciones de WoW (Retail, Classic, PTR) o acepta rutas manuales |
| 💾 **Backup Inteligente** | Copia `.lua` y `.lua.bak` con validación de integridad |
| 🖥️ **CLI Guiada** | Menú paso a paso en español con colores y progreso |
| ⚙️ **Rutas Flexibles** | Acepta rutas completas, versión específica o SavedVariables directos |
| 🧪 **Testing Completo** | 90%+ cobertura de tests unitarios e integración |

---

## 📋 Requisitos

- Python 3.10+
- World of Warcraft instalado
- Permisos de lectura en carpetas WTF

---

## 🚀 Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/addons-profile-manager.git
cd addons-profile-manager

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instalar
pip install -e .
```

---

## 🎮 Uso Rápido

```bash
python -m src.addons_profile_manager
```

### Flujo del Menú

```
╔══════════════════════════════════════════════════════════════╗
║        WoW Addon Profile Manager                             ║
║        Gestiona tus perfiles de addons fácilmente            ║
╚══════════════════════════════════════════════════════════════╝

=== Selecciona cómo encontrar tu instalación de WoW ===
1. Buscar automáticamente (escanea rutas comunes)
2. Especificar ruta manualmente
3. Salir
```

### Formatos de Ruta Soportados

| Tipo | Ejemplo |
|------|---------|
| Instalación completa | `C:\Program Files\World of Warcraft` |
| Versión específica | `D:\Games\World of Warcraft\_retail_` |
| SavedVariables directo | `E:\WoW\_retail_\WTF\Account\12345#1\SavedVariables` |

---

## 🏗️ Arquitectura

```
src/addons_profile_manager/
├── cli.py              # CLI interactiva guiada
├── config/
│   ├── settings.py     # Dataclasses de configuración
│   └── constants.py    # Mensajes y constantes
├── core/
│   ├── scanner.py      # Detección flexible de instalaciones
│   └── backup.py       # Gestión de backups con validación
└── utils/
    ├── exceptions.py   # Excepciones personalizadas
    └── file_ops.py     # Utilidades de archivos
```

### Componentes Clave

- **WoWScanner**: Detecta instalaciones por estructura de carpetas (no requiere .exe)
- **BackupManager**: Copia archivos con validación y manejo de errores detallado
- **CLI Guiada**: Flujo paso a paso sin loops confusos

---

## 🧪 Testing

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=addons_profile_manager --cov-report=html

# Solo unitarios
pytest tests/unit/
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
NO_COLOR=1                              # Deshabilitar colores
ADDON_MANAGER_DATA_DIR="/custom/path"   # Directorio personalizado
```

### Estructura de WoW Esperada

```
World of Warcraft/
├── _retail_/           # o _classic_, _ptr_
│   └── WTF/
│       └── Account/
│           └── ACCOUNT_ID/
│               └── SavedVariables/
│                   ├── AddonName.lua
│                   └── AddonName.lua.bak
```

---

## 🤝 Contribución

```bash
# Desarrollo
pip install -e ".[dev]"

# Linting
ruff check src/
ruff format src/

# Type checking
mypy src/
```

---

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE)

---

**⚠️ Disclaimer**: No afiliado con Blizzard Entertainment. World of Warcraft es marca registrada de Blizzard Entertainment, Inc.