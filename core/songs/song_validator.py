import os
import json

class SongValidator:
    @staticmethod
    def is_valid_song_folder(folder_path):
        """
        Checks if a folder contains both Audio.ogg and Meta.json.
        """
        if not os.path.isdir(folder_path):
            return False
            
        meta_path = os.path.join(folder_path, "Meta.json")
        audio_path = os.path.join(folder_path, "Audio.ogg")
        
        if not os.path.isfile(meta_path) or not os.path.isfile(audio_path):
            return False
            
        return SongValidator.is_valid_meta(meta_path)

    @staticmethod
    def is_valid_meta(meta_path):
        """
        Checks if Meta.json is valid JSON.
        """
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    @staticmethod
    def is_supported_audio(file_path):
        """
        Checks if the audio format is supported for conversion/import.
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.mp3', '.wav', '.ogg']
        
    @staticmethod
    def validate_metadata_fields(data):
        """
        Validates metadata values based on requirements:
        - tempo > 0
        - offsets >= 0
        - songName not empty
        """
        errors = []
        if not data.get("songName"):
            errors.append("Song name cannot be empty.")
        
        try:
            tempo = float(data.get("tempo", 0))
            if tempo <= 0:
                errors.append("Tempo must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Tempo must be a number.")
            
        for field in ["beatOffset", "startSongOffset", "endSongOffset"]:
            try:
                val = float(data.get(field, 0))
                if val < 0:
                    errors.append(f"{field} must be 0 or greater.")
            except (ValueError, TypeError):
                errors.append(f"{field} must be a number.")
                
        return len(errors) == 0, errors
