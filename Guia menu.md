# 📖 Guía Rápida: Flujo del Menú

## ✅ Notas de uso

- ✅ El menú te guía paso a paso
- ✅ Solo necesitas ingresar números (1, 2, 3)
- ✅ Mensajes claros en español

## 🚀 Menú Inicial

Al iniciar el programa, verás 3 opciones:

```
=== Selecciona cómo encontrar tu instalación de WoW ===
1. Buscar automáticamente (escanea rutas comunes)
2. Especificar ruta manualmente
3. Salir
```

---

## 🔍 Opción 1: Búsqueda Automática

1. Escanea rutas comunes de instalación
2. Muestra lista de instalaciones encontradas
3. Ingresa el **número** de la instalación (ej: `1`)

---

## 📝 Opción 2: Ruta Manual

Permite especificar la ruta exacta. Acepta estos formatos:

| Tipo | Ejemplo |
|------|---------|
| Instalación completa | `C:\Program Files\World of Warcraft` |
| Versión específica | `D:\Games\World of Warcraft\_retail_` |
| SavedVariables directo | `E:\WoW\_retail_\WTF\Account\12345#1\SavedVariables` |

> 💡 **Tip**: Puedes copiar y pegar rutas directamente, incluso con comillas.

---

## 📋 Flujo Completo

| Paso | Acción | Input |
|------|--------|-------|
| 1 | Seleccionar instalación | Número (ej: `1`) |
| 2 | Seleccionar cuenta | Número (ej: `1`) |
| 3 | Seleccionar addons | `1` = específicos, `2` = todos |
| 4 | Destino del backup | Ruta o `Enter` para default |
| 5 | Confirmación | `s` para iniciar, `n` para cancelar |

---

## 💡 Ejemplos de Uso

### Backup Completo (Todos los Addons)

```
Selecciona una opción: 1
Select WoW installation: 1
Select account: 1
¿Qué deseas hacer? 2
Select backup destination: [Enter]
¿Iniciar backup? s
```

### Backup de Addons Específicos

```
Selecciona una opción: 2
WoW installation path: D:\Games\World of Warcraft\_retail_
Select account: 1
¿Qué deseas hacer? 1
[Selecciona addons con números, 'a' para todos, Enter para confirmar]
¿Iniciar backup? s
```

---
