import sys
import os
from core.utils import resource_path, get_ffmpeg_paths

# Global state for lazy initialization
_PYDUB_CONFIGURED = False

def _configure_pydub():
    global _PYDUB_CONFIGURED
    if _PYDUB_CONFIGURED:
        return
    
    try:
        from pydub import AudioSegment
        ffmpeg_path, ffprobe_path = get_ffmpeg_paths()
        AudioSegment.converter = os.path.abspath(ffmpeg_path)
        AudioSegment.ffprobe = os.path.abspath(ffprobe_path)
        _PYDUB_CONFIGURED = True
    except ImportError:
        pass

class AudioConverter:
    @staticmethod
    def is_ready():
        """Checks if dependencies (pydub and bundled ffmpeg) are available."""
        _configure_pydub()
        if not _PYDUB_CONFIGURED:
            return False, "pydub library not found. Please install it via pip."
        
        ffmpeg_path, _ = get_ffmpeg_paths()
        if not os.path.exists(ffmpeg_path):
            return False, f"Bundled FFmpeg not found at: {ffmpeg_path}"
            
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
            _configure_pydub()
            from pydub import AudioSegment
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
