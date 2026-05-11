import os
import zipfile
import json
from pathlib import Path

class SongPacker:
    @staticmethod
    def export_songs(target_zip_path, song_folders):
        """
        Packages multiple song folders into a single portable ZIP archive.
        """
        with zipfile.ZipFile(target_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder_path in song_folders:
                folder_path = Path(folder_path)
                if not folder_path.exists():
                    continue
                
                # Each song folder becomes a top-level directory in the ZIP
                base_name = folder_path.name
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        # Exclude hidden files
                        if file_path.name.startswith('.'):
                            continue
                        
                        # Calculate arcname (relative path inside the ZIP)
                        arcname = os.path.join(base_name, file_path.relative_to(folder_path))
                        zipf.write(file_path, arcname)

    @staticmethod
    def validate_package(zip_path):
        """
        Validates that the ZIP archive contains valid song structures.
        Returns a list of valid song folders found in the ZIP.
        """
        valid_songs = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                # Find unique top-level directories that contain Meta.json and Audio.ogg
                potential_folders = {}
                for name in zipf.namelist():
                    parts = Path(name).parts
                    if not parts:
                        continue
                    
                    root_folder = parts[0]
                    if root_folder not in potential_folders:
                        potential_folders[root_folder] = set()
                    potential_folders[root_folder].add(parts[-1])
                
                for folder, files in potential_folders.items():
                    if "Meta.json" in files and "Audio.ogg" in files:
                        valid_songs.append(folder)
        except Exception:
            return []
            
        return valid_songs
