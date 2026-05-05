import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon # <--- Debes importar esto
from core.mod_manager import ModManagerCore
from core.utils import resource_path, get_ffmpeg_paths
from ui.main_window import MainWindow

def main():
    # Initialize FFmpeg paths early
    get_ffmpeg_paths()
    
    app = QApplication(sys.argv)
    from ui.style import NeonStyle
    app.setStyleSheet(NeonStyle.QSS)
    
    # Asegúrate de usar la ruta correcta a la carpeta src/assets
    app.setWindowIcon(QIcon(resource_path("src/assets/icon.png")))
    
    core = ModManagerCore()
    window = MainWindow(core)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
