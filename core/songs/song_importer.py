import os
import shutil
import zipfile
import tempfile
import json
import secrets
from pathlib import Path
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

    def check_conflicts(self, zip_path):
        """
        Scans a ZIP package and returns a dictionary of conflicts.
        { 'song_folder_name': 'reason' }
        Reasons: 'folder_exists', 'id_collision', or both.
        """
        conflicts = {}
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # Find unique top-level directories
            root_folders = set(Path(n).parts[0] for n in zipf.namelist())
            
            for folder in root_folders:
                # 1. Folder name collision
                folder_exists = os.path.exists(os.path.join(self.target_dir, folder))
                
                # 2. ID/Seed collision
                meta_content = None
                try:
                    with zipf.open(f"{folder}/Meta.json") as f:
                        raw_data = f.read()
                        # Try encodings just like in song_model.py
                        for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
                            try:
                                meta_content = json.loads(raw_data.decode(enc))
                                break
                            except:
                                continue
                except Exception:
                    continue
                
                id_collision = self._is_duplicate(meta_content)
                
                if folder_exists or id_collision:
                    reason = []
                    if folder_exists: reason.append("folder_exists")
                    if id_collision: reason.append("id_collision")
                    conflicts[folder] = reason
        return conflicts

    def import_from_shared_package(self, zip_path, strategies=None):
        """
        Imports songs from a shared ZIP package.
        strategies: dict mapping folder_name to 'replace', 'new', or 'skip'
        """
        strategies = strategies or {}
        imported_count = 0
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                for entry in os.scandir(temp_dir):
                    if entry.is_dir() and SongValidator.is_valid_song_folder(entry.path):
                        strategy = strategies.get(entry.name, 'new') # Default to new if not specified
                        
                        if strategy == 'replace':
                            self._import_replace(entry.path)
                            imported_count += 1
                        elif strategy == 'new':
                            self._import_as_new(entry.path)
                            imported_count += 1
                        # 'skip' does nothing
                
                return True, f"Imported {imported_count} songs."
            except Exception as e:
                return False, f"Failed to import shared package: {e}"

    def _import_replace(self, source_path):
        folder_name = os.path.basename(source_path)
        dest_path = os.path.join(self.target_dir, folder_name)
        
        # Clean up existing folder first
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        
        shutil.copytree(source_path, dest_path)
        # Re-index
        self._refresh_existing_ids()

    def _import_as_new(self, source_path):
        folder_name = os.path.basename(source_path)
        dest_path = os.path.join(self.target_dir, folder_name)
        
        # 1. Handle folder collision
        counter = 1
        original_dest = dest_path
        while os.path.exists(dest_path):
            dest_path = f"{original_dest}_{counter}"
            counter += 1
        
        os.makedirs(dest_path, exist_ok=True)
        for f in os.listdir(source_path):
            shutil.copy2(os.path.join(source_path, f), os.path.join(dest_path, f))
            
        # 2. Handle ID collision (Regenerate ID and Seed)
        meta_path = os.path.join(dest_path, "Meta.json")
        if os.path.exists(meta_path):
            data = None
            # Try multiple encodings
            for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
                try:
                    with open(meta_path, 'r', encoding=enc) as f:
                        data = json.load(f)
                    break
                except:
                    continue
            
            if data:
                try:
                    # Regenerate to ensure it's "new" for the game
                    data["uniqueId"] = secrets.randbits(32)
                    data["seed"] = secrets.randbits(32)
                    
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent="\t")
                        
                    self.existing_ids.add((data["uniqueId"], data["seed"]))
                except Exception:
                    pass

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
        # 1. Check if it's a valid song folder directly
        if SongValidator.is_valid_song_folder(folder_path):
            return self._copy_song_folder(folder_path)
        
        # 2. Check if it's a folder containing multiple song folders (Legacy behavior)
        imported_count = 0
        found_song_folders = False
        
        for entry in os.scandir(folder_path):
            if entry.is_dir() and SongValidator.is_valid_song_folder(entry.path):
                found_song_folders = True
                success, _ = self._copy_song_folder(entry.path)
                if success:
                    imported_count += 1
        
        if imported_count > 0:
            return True, f"Imported {imported_count} songs from folders."
        
        # 3. Recursive Audio Scavenger: Find all raw audio files
        # This is for when the user selects a folder full of MP3s
        audio_files = []
        for root, _, files in os.walk(folder_path):
            for f in files:
                if SongValidator.is_supported_audio(f):
                    audio_files.append(os.path.join(root, f))
        
        if audio_files:
            for audio_path in audio_files:
                success, _ = self._import_audio_file(audio_path)
                if success:
                    imported_count += 1
            
            if imported_count > 0:
                return True, f"Imported {imported_count} songs from audio files."
            return False, "Found audio files but failed to import them."

        if found_song_folders:
            return False, "Songs already exist or could not be copied."
        return False, "No valid song folders or audio files found in the selected directory."

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
