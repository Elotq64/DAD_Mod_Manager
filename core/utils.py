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

def get_ffmpeg_paths():
    """Returns (ffmpeg_path, ffprobe_path) and adds to system PATH."""
    # BASE_DIR should be the root of the project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if getattr(sys, 'frozen', False):
        # Bundled path (PyInstaller)
        ffmpeg_dir = os.path.join(sys._MEIPASS, "ffmpeg")
    else:
        # Development path
        ffmpeg_dir = os.path.join(base_dir, "src", "assets")
        
    ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe.exe")
    
    if os.path.exists(ffmpeg_dir):
        path_abs = os.path.abspath(ffmpeg_dir)
        if path_abs not in os.environ["PATH"]:
            os.environ["PATH"] = path_abs + os.pathsep + os.environ["PATH"]
            
    return ffmpeg_path, ffprobe_path
