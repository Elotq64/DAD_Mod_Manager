import os
from .song_model import Song

class SongScanner:
    def __init__(self, base_path=None):
        if base_path is None:
            # Game directory for custom songs
            self.base_path = os.path.expandvars(r"%LOCALAPPDATA%\Pagoda\Saved\ImportedSongs")
        else:
            self.base_path = base_path

    def scan(self):
        """
        Scans the ImportedSongs directory for valid song folders.
        A valid folder must contain Audio.ogg and Meta.json.
        """
        songs = []
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
            except Exception:
                return []

        for entry in os.scandir(self.base_path):
            if entry.is_dir():
                song = Song.from_folder(entry.path)
                if song:
                    songs.append(song)
        
        # Sort by song name
        songs.sort(key=lambda s: s.song_name.lower())
        return songs

    def get_base_path(self):
        return self.base_path
