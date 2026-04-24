import os
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, compatible con desarrollo y PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
