import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon # <--- Debes importar esto
from core.mod_manager import ModManagerCore
from core.utils import resource_path
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Asegúrate de usar la ruta correcta a la carpeta src/assets
    app.setWindowIcon(QIcon(resource_path("src/assets/icon.png")))
    
    core = ModManagerCore()
    window = MainWindow(core)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
