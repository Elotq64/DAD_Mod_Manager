import os
import sys
from core.utils import get_ffmpeg_paths

# Ensure FFmpeg is in PATH for librosa/audioread
get_ffmpeg_paths()

class BpmAnalyzer:
    @staticmethod
    def detect_bpm(audio_path):
        """
        Detects the BPM of an audio file.
        Returns the BPM as a float, or None if detection fails.
        """
        if not os.path.exists(audio_path):
            return None
            
        try:
            import numpy as np
            import librosa
            # Load only the first 60 seconds to speed up analysis
            y, sr = librosa.load(audio_path, duration=60)
            
            # Use onset strength envelope
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Estimate tempo
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            
            # librosa returns an array of tempos, usually we just want the first one
            if isinstance(tempo, np.ndarray):
                if tempo.size > 0:
                    return float(tempo[0])
                return None
            return float(tempo)
        except Exception as e:
            print(f"BPM detection error: {e}")
            return None

    @staticmethod
    def get_waveform_data(audio_path, samples=1000):
        """
        Returns downsampled waveform data for visualization.
        Returns a list of (min, max) values.
        """
        if not os.path.exists(audio_path):
            return []
            
        try:
            import numpy as np
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            
            # Reshape into blocks and find min/max for each block
            block_size = len(y) // samples
            if block_size < 1:
                return [(float(v), float(v)) for v in y]
                
            y_trimmed = y[:samples * block_size]
            blocks = y_trimmed.reshape(samples, block_size)
            
            waveform = []
            for block in blocks:
                waveform.append((float(np.min(block)), float(np.max(block))))
            return waveform
        except Exception as e:
            print(f"Waveform generation error: {e}")
            return []
