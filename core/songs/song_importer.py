import os
import shutil
import zipfile
import tempfile
import json
import secrets
from .song_validator import SongValidator
from .audio_converter import AudioConverter
from .song_model import Song
class SongImporter:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self._refresh_existing_ids()

    def _refresh_existing_ids(self):
        """Scans existing songs to build a set of (uniqueId, seed) pairs."""
        self.existing_ids = set()
        if not os.path.exists(self.target_dir):
            return
            
        for entry in os.scandir(self.target_dir):
            if entry.is_dir():
                meta_path = os.path.join(entry.path, "Meta.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            uid = data.get("uniqueId")
                            seed = data.get("seed")
                            if uid is not None and seed is not None:
                                self.existing_ids.add((uid, seed))
                    except Exception:
                        pass

    def _is_duplicate(self, meta_data):
        uid = meta_data.get("uniqueId")
        seed = meta_data.get("seed")
        if uid is None or seed is None:
            return False
        return (uid, seed) in self.existing_ids

    def import_from_path(self, path, custom_metadata=None):
        """
        Main entry point for importing. Path can be:
        - A folder
        - A .zip file
        - A single audio file (.mp3, .wav, .ogg)
        """
        if os.path.isdir(path):
            return self._import_folder(path)
        elif path.lower().endswith('.zip'):
            return self._import_zip(path)
        elif SongValidator.is_supported_audio(path):
            return self._import_audio_file(path, custom_metadata)
        return False, "Unsupported file format or path."

    def _import_folder(self, folder_path):
        # Check if it's a valid song folder directly
        if SongValidator.is_valid_song_folder(folder_path):
            return self._copy_song_folder(folder_path)
        
        # Or maybe it's a folder containing multiple song folders?
        imported_count = 0
        found_folders = 0
        for entry in os.scandir(folder_path):
            if entry.is_dir() and SongValidator.is_valid_song_folder(entry.path):
                found_folders += 1
                success, _ = self._copy_song_folder(entry.path)
                if success:
                    imported_count += 1
        
        if imported_count > 0:
            return True, f"Imported {imported_count} songs."
        if found_folders > 0:
            return False, "Songs already exist or could not be copied."
        return False, "No valid song folders found in the selected directory."

    def _import_zip(self, zip_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                return self._import_folder(temp_dir)
            except Exception as e:
                return False, f"Failed to extract zip: {e}"

    def _import_audio_file(self, audio_path, custom_metadata=None):
        song_name = os.path.splitext(os.path.basename(audio_path))[0]
        # Create a safe folder name (alphanumeric and underscores)
        safe_name = "".join([c if c.isalnum() or c == '_' else '_' for c in song_name]).strip('_')
        if not safe_name:
            safe_name = "imported_song"
            
        dest_folder = os.path.join(self.target_dir, safe_name)
        
        # Handle duplicates by adding a suffix
        counter = 1
        original_dest = dest_folder
        while os.path.exists(dest_folder):
            dest_folder = f"{original_dest}_{counter}"
            counter += 1
        
        try:
            os.makedirs(dest_folder, exist_ok=True)
            
            # Convert audio
            target_audio = os.path.join(dest_folder, "Audio.ogg")
            success, msg = AudioConverter.convert_to_ogg(audio_path, target_audio)
            if not success:
                shutil.rmtree(dest_folder)
                return False, f"Audio conversion failed: {msg}"
                
            # Create Meta.json with secure uniqueId and seed
            uid = secrets.randbits(32)
            seed = secrets.randbits(32)
            
            if custom_metadata:
                # Use a dummy Song object to leverage its to_dict formatting logic
                from .song_model import Song
                temp_song = Song(dest_folder, custom_metadata)
                temp_song.unique_id = uid
                temp_song.seed = seed
                final_meta = temp_song.to_dict()
            else:
                final_meta = {
                    "version": 1,
                    "uniqueId": int(uid),
                    "songName": song_name,
                    "performedBy": ["Unknown Artist"],
                    "writtenBy": [],
                    "seed": int(seed),
                    "tempo": 120,
                    "customTempoSections": [],
                    "beatOffset": 0,
                    "startSongOffset": 0,
                    "endSongOffset": 0
                }
            
            meta_path = os.path.join(dest_folder, "Meta.json")
            with open(meta_path, 'w', encoding='utf-8') as f:
                # The game expects tabs for indentation
                json.dump(final_meta, f, indent="\t")
            
            # Update cache for duplicate detection
            self.existing_ids.add((final_meta["uniqueId"], final_meta["seed"]))
                
            return True, f"Imported '{song_name}' successfully."
        except Exception as e:
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            return False, f"Error creating song folder: {e}"

    def _copy_song_folder(self, source_path):
        # Read Meta.json BEFORE copying to detect duplicates
        meta_path = os.path.join(source_path, "Meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                    if self._is_duplicate(meta_data):
                        return False, "Duplicate song skipped"
            except Exception:
                pass

        folder_name = os.path.basename(source_path)
        dest_path = os.path.join(self.target_dir, folder_name)
        
        if os.path.exists(dest_path):
            return False, f"Folder '{folder_name}' already exists."
            
        try:
            shutil.copytree(source_path, dest_path)
            
            # Update cache for duplicate detection
            try:
                uid = meta_data.get("uniqueId")
                seed = meta_data.get("seed")
                if uid is not None and seed is not None:
                    self.existing_ids.add((uid, seed))
            except:
                pass

            return True, f"Imported '{folder_name}'."
        except Exception as e:
            return False, f"Error copying folder: {e}"
