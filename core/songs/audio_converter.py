import sys
import os
from core.utils import resource_path

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Resolve FFmpeg paths relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if getattr(sys, 'frozen', False):
    # Bundled path (PyInstaller)
    FFMPEG_DIR = os.path.join(sys._MEIPASS, "ffmpeg")
else:
    # Development path
    FFMPEG_DIR = os.path.join(BASE_DIR, "src", "assets")

FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(FFMPEG_DIR, "ffprobe.exe")

# Add the FFmpeg directory to the system PATH to help pydub/subprocess
if os.path.exists(FFMPEG_DIR):
    os.environ["PATH"] += os.pathsep + os.path.abspath(FFMPEG_DIR)

# Configure pydub
if PYDUB_AVAILABLE:
    # Ensure paths are absolute and normalized
    AudioSegment.converter = os.path.abspath(FFMPEG_PATH)
    AudioSegment.ffprobe = os.path.abspath(FFPROBE_PATH)

class AudioConverter:
    @staticmethod
    def is_ready():
        """Checks if dependencies (pydub and bundled ffmpeg) are available."""
        if not PYDUB_AVAILABLE:
            return False, "pydub library not found. Please install it via pip."
        
        # Check for bundled ffmpeg
        if not os.path.exists(FFMPEG_PATH):
            return False, f"Bundled FFmpeg not found at: {FFMPEG_PATH}"
            
        return True, ""

    @staticmethod
    def convert_to_ogg(input_path, output_path):
        """
        Converts .mp3 or .wav to .ogg (Audio.ogg).
        Returns (success, message).
        """
        ready, msg = AudioConverter.is_ready()
        if not ready:
            return False, msg

        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Load the audio file
            # pydub supports many formats if ffmpeg is present
            audio = AudioSegment.from_file(input_path)
            
            # Export as ogg with the libvorbis codec
            audio.export(output_path, format="ogg", codec="libvorbis")
            
            if os.path.exists(output_path):
                return True, "Conversion successful."
            else:
                return False, "Export failed: output file not created."
                
        except Exception as e:
            return False, f"Conversion error: {str(e)}"
