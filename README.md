# DEAD AS DISCO - Mod Manager (V2.0)

![Banner](src/assets/banner.jpg)

Un gestor de mods moderno, rápido y estilizado diseñado específicamente para juegos que utilizan archivos `.pak`.  
Esta versión 2.0 ha sido migrada de Tkinter a **PySide6**, ofreciendo una interfaz de alta tecnología con estética *Neon Dark*.

---

## Características (Features)

- **Estética Neon Dark**: Interfaz oscura premium con acentos en Cyan y Purple  
- **Multi-idioma**: Soporte completo para Español e Inglés con cambio dinámico  
- **Frameless UI**: Barra de título personalizada para un look moderno  
- **Sincronización Inteligente**: Solo los mods activos se despliegan en la carpeta del juego  
- **Integración con Steam**: Detección automática de AppID y lanzamiento directo  
- **Gestión de Archivos**: Migración automática de mods a almacenamiento seguro  

---

## Requisitos (Requirements)

- **Python 3.8+**
- **PySide6**

---

## Instalación y Uso (Setup & Usage)

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd "DAD mod manager"
```

### 2. Instalar dependencias
```bash
pip install PySide6
```

### 3. Ejecutar la aplicación
```bash
python main.py
```

---

## Exportar a Ejecutable (.EXE)

Para generar una versión portable en Windows:

### 1. Instalar PyInstaller
```bash
pip install pyinstaller
```

### 2. Compilar
```powershell
pyinstaller --noconsole --onefile --name "DAD_Mod_Manager" --add-data "src/assets;src/assets" --icon="src/assets/icon.ico" main.py
```

El ejecutable se generará en:
```
dist/
```

---

## Estructura del Proyecto

```
main.py
core/
  mod_manager.py
  i18n.py
  utils.py
ui/
  main_window.py
  widgets.py
  style.py
src/assets/
```

---

## Aviso Importante

Este proyecto se distribuye **sin garantía**.  
El ejecutable (`.exe`) fue generado con Python + PyInstaller, lo que puede provocar **falsos positivos en antivirus**.

Si tienes dudas sobre su funcionamiento, puedes revisar el código fuente en este repositorio.

---

## Autor

**Elotaku64**

---

## Licencia

Este proyecto está bajo la licencia MIT.  
Eres libre de usar, modificar y distribuir este software con atribución al autor.

## Términos de Uso y Redistribución

Este software se distribuye de forma gratuita para la comunidad. Sin embargo, se establecen las siguientes condiciones:

1.  **Atribución Obligatoria**: Cualquier distribución, modificación o proyecto derivado debe incluir un crédito visible al autor original.
2.  **Sin Venta**: Está estrictamente prohibido vender este software o cobrar por su descarga o uso.
3.  **No Bloquear Descargas**: No se deben ocultar los archivos detrás de acortadores de enlaces que requieran pasos adicionales o pagos.

## Notas

Proyecto creado para la comunidad de modding.  
Si encuentras bugs o tienes sugerencias, puedes reportarlas en el repositorio.
# DAD_Mod_Manager
Mod manager for Dead as Disco
