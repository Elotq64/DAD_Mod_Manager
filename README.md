# DEAD AS DISCO - Mod Manager (V3.0)

![Banner](src/assets/banner.jpg)

> **Modern, fast, and stylized mod manager** designed specifically for games using `.pak` files.  
> Migrated from Tkinter to **PySide6** for a premium *Neon Dark* high-tech experience.

---
## Download

You can download the latest version here:
https://github.com/Elotq64/DAD_Mod_Manager/releases

## Quick Start for compiling or installing this tool for yourself

### 1. Prerequisites
- **Python 3.8 or newer**: [Download here](https://www.python.org/downloads/) (Make sure to check **"Add Python to PATH"** during installation).

### 2. Setup
1. **Download the code**: Click the green **"Code"** button above and select **"Download ZIP"**, then extract it.
2. **Open Terminal**:
   - Go inside the folder you extracted
   - Hold `Shift` + Right Click on empty space
   - Click **"Open Terminal"** or **"Open PowerShell here"**
3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Run**:
   ```powershell
   python main.py
   ```

### Export to Executable (.EXE)
We provide pre-configured `.spec` files for a perfect build:

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Build using the optimized config:
   ```powershell
   pyinstaller DAD_Mod_Manager.spec
   ```
3. Your portable `.exe` will be in the `dist/` folder.

---

## Features

- **Neon Dark Aesthetic**: Premium dark interface with Cyan and Purple accents.
- **Multi-language**: Full Support for English & Spanish with dynamic switching.
- **Frameless UI**: Custom title bar for a sleek, modern desktop look.
- **Smart Sync**: Only active mods are deployed to the game folder (keeping it clean).
- **Steam Integration**: Automatic AppID detection and one-click game launch.
- **Auto-Migration**: Automatically moves your existing mods to a safe storage directory.

---

## Development & Building

If you want to contribute or build your own executable:

### Project Structure
```
main.py            # Entry point
core/              # Logic & Utilities
ui/                # PySide6 Windows & Widgets
src/assets/        # Images, Icons & Banners
```

## Important Note

This project is distributed **as-is**.  
Executables generated with PyInstaller may trigger **false positives** in some antivirus software. If you are concerned, we encourage you to run the software from the source code following the instructions above.

---

## License & Terms

This project is licensed under the **MIT License**.  
Developed by **Elotaku64**.

### Usage Terms:
1. **Mandatory Attribution**: Any distribution or modification must credit the original author.
2. **Strictly Non-Commercial**: This software is free. Selling it or charging for access is strictly prohibited.
3. **No Paywalls**: Do not hide these files behind ad-links or paid shorteners.

---

## Support
Created for the modding community. Found a bug? Have a suggestion? Feel free to open an issue or report it in the repository!

---

## Contributing

I'm currently looking for contributors to help improve and expand this project.

If you're interested in contributing — whether it's code, UI/UX improvements, translations, or ideas — you're more than welcome.

### Areas where help is needed:
- UI/UX polish (PySide6)
- Performance improvements
- Mod compatibility systems
- Translations
- Testing & bug reports

### How to contribute:
1. Fork the repository
2. Create a new branch (`feature/your-feature-name`)
3. Make your changes
4. Submit a Pull Request

Even small contributions are appreciated.

---

## Support the Project

If you enjoy this project or find it useful, consider supporting its development:

- ☕ PayPal: https://paypal.me/elotq64

Your support helps keep the project alive and improving.

---