import json
import os

class Song:
    def __init__(self, folder_path, metadata):
        self.folder_path = folder_path
        self.song_name = metadata.get("songName", "Unknown Song")
        self.tempo = metadata.get("tempo", 120.0)
        self.performed_by = metadata.get("performedBy", "Unknown Artist")
        self.beat_offset = metadata.get("beatOffset", 0.0)
        self.start_song_offset = metadata.get("startSongOffset", 0.0)
        self.end_song_offset = metadata.get("endSongOffset", 0.0)
        self.unique_id = metadata.get("uniqueId", 0)
        self.seed = metadata.get("seed", 0)
        # Store full metadata to preserve other fields as required
        self.full_metadata = metadata

    @property
    def id(self):
        return os.path.basename(self.folder_path)

    def to_dict(self):
        # Explicit field order and types to match game expectation
        return {
            "version": self.full_metadata.get("version", 1),
            "uniqueId": int(self.unique_id),
            "songName": self.song_name,
            "performedBy": self.performed_by if isinstance(self.performed_by, list) else [self.performed_by] if self.performed_by else [],
            "writtenBy": self.full_metadata.get("writtenBy", []),
            "seed": int(self.seed),
            "tempo": float(self.tempo),
            "customTempoSections": self.full_metadata.get("customTempoSections", []),
            "beatOffset": int(float(self.beat_offset)),
            "startSongOffset": float(self.start_song_offset),
            "endSongOffset": float(self.end_song_offset)
        }

    def save(self):
        meta_path = os.path.join(self.folder_path, "Meta.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            # The game uses tabs for indentation
            json.dump(self.to_dict(), f, indent="\t")

    def reload(self):
        """ Reloads metadata from the Meta.json file """
        meta_path = os.path.join(self.folder_path, "Meta.json")
        if not os.path.exists(meta_path):
            return
            
        metadata = None
        for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
            try:
                with open(meta_path, 'r', encoding=enc) as f:
                    metadata = json.load(f)
                break
            except:
                continue
        
        if metadata:
            self.__init__(self.folder_path, metadata)

    @classmethod
    def from_folder(cls, folder_path):
        meta_path = os.path.join(folder_path, "Meta.json")
        audio_path = os.path.join(folder_path, "Audio.ogg")
        
        if not os.path.exists(meta_path) or not os.path.exists(audio_path):
            return None
            
        metadata = None
        # Try common encodings: utf-8-sig (handles BOM) and utf-16
        for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
            try:
                with open(meta_path, 'r', encoding=enc) as f:
                    metadata = json.load(f)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            except Exception:
                return None
        
        if metadata:
            return cls(folder_path, metadata)
        return None
