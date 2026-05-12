import os
import sys
from core.utils import get_ffmpeg_paths

# Ensure FFmpeg is in PATH for librosa/audioread
get_ffmpeg_paths()

class BpmAnalyzer:
    @staticmethod
    def analyze_audio(audio_path, progress_callback=None):
        """
        Performs advanced audio analysis to detect BPM, offset, and confidence.
        Returns a dict with: {bpm, offset, confidence, warnings}
        """
        if not os.path.exists(audio_path):
            return None
            
        try:
            import numpy as np
            import librosa
            
            # Load first 180 seconds for a better context
            # Resample to 22050 for standard librosa analysis speed
            y, sr = librosa.load(audio_path, duration=180, sr=22050)
            
            if progress_callback: progress_callback(20)
            
            # 1. Harmonic-Percussive Separation
            # We mostly care about percussive for beat tracking
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            if progress_callback: progress_callback(40)
            
            # 2. Onset Strength
            onset_env = librosa.onset.onset_strength(y=y_percussive, sr=sr)
            
            # 3. Tempo Estimation (Global)
            # We use aggregate=None to get windowed tempo if we wanted, 
            # but beat_track is generally more stable for a starting point
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
            
            if progress_callback: progress_callback(60)
            
            # 4. Offset Estimation
            # Convert beat frames to time
            beat_times = librosa.frames_to_time(beats, sr=sr)
            offset = 0.0
            if len(beat_times) > 0:
                # Find the first beat that has significant onset strength
                # We look at the first few beats
                for i in range(min(5, len(beat_times))):
                    bt = beat_times[i]
                    if bt > 0.05: # Avoid extreme starts
                        offset = bt
                        break
            
            if progress_callback: progress_callback(80)
            
            # 5. Confidence & Stability Analysis
            # Windowed analysis to check for consistency
            hop_length = 512
            # Calculate local tempo across the loaded audio
            # We analyze in 15-second windows
            window_size = 15 * sr // hop_length
            local_tempos = []
            
            # Simple windowed check
            for start in range(0, len(onset_env) - window_size, window_size // 2):
                win = onset_env[start:start+window_size]
                if np.max(win) > 0:
                    t, _ = librosa.beat.beat_track(onset_envelope=win, sr=sr)
                    local_tempos.append(float(t[0]) if isinstance(t, np.ndarray) else float(t))
            
            warnings = []
            confidence = 0.8 # Base confidence
            
            if local_tempos:
                std_dev = np.std(local_tempos)
                if std_dev > 2.0:
                    warnings.append("variable_bpm_detected")
                    confidence -= min(0.4, std_dev / 10.0)
                
                # Check for doubling/halving consensus
                # (Simple heuristic for now)
            
            # Pulse clarity (periodicity strength)
            # librosa.beat.plp can give us a sense of pulse clarity
            pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
            clarity = np.mean(np.max(pulse, axis=0)) if pulse.ndim > 1 else np.mean(pulse)
            # Normalize clarity (heuristically)
            confidence *= (0.5 + min(0.5, clarity * 2))
            
            if progress_callback: progress_callback(100)
            
            return {
                "bpm": round(bpm, 2),
                "offset": round(offset * 1000, 0), # s to ms
                "confidence": round(max(0.1, min(1.0, confidence)) * 100, 0),
                "warnings": warnings
            }
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
            return None

    @staticmethod
    def detect_bpm(audio_path):
        """ Legacy wrapper for backward compatibility """
        res = BpmAnalyzer.analyze_audio(audio_path)
        return res["bpm"] if res else None

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
