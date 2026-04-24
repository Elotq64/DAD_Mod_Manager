import os
import shutil
import json
import re
import zipfile
try:
    import rarfile
except ImportError:
    rarfile = None
from pathlib import Path
from collections import defaultdict

class ModManagerCore:
    def __init__(self):
        self.base_dir = Path.home() / "Documents" / "ModManager"
        self.config_file = self.base_dir / "config.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
        self.active_mods_path = None
        self._update_paths()

    def load_config(self):
        default_config = {
            "exe_path": "",
            "mods_storage_path": "",
            "active_mods": [],
            "steam_appid": ""
        }
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    default_config.update(data)
            except Exception:
                pass
        return default_config

    def save_config(self):
        with open(self.config_file, "w", encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def _update_paths(self):
        exe_path = self.config.get("exe_path")
        if exe_path and os.path.exists(exe_path):
            p = Path(exe_path)
            game_folder_name = p.stem 
            content_paks = p.parent / game_folder_name / "Content" / "Paks"
            if content_paks.exists():
                self.active_mods_path = content_paks / "~mods"
            else:
                self.active_mods_path = None
        else:
            self.active_mods_path = None

    def detect_steam_appid(self, exe_path):
        p = Path(exe_path)
        game_folder = None
        steamapps_path = None
        for parent in p.parents:
            if parent.name.lower() == "common":
                child_of_common = p
                for c in p.parents:
                    if c.parent == parent:
                        child_of_common = c
                        break
                game_folder = child_of_common.name
                steamapps_path = parent.parent
                break
            if parent.name.lower() == "steamapps":
                steamapps_path = parent
                break
        if not steamapps_path or not steamapps_path.exists():
            return ""
        if not game_folder:
            game_folder = p.parent.name

        for acf in steamapps_path.glob("appmanifest_*.acf"):
            try:
                with open(acf, "r", encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    match = re.search(r'"installdir"\s+"([^"]+)"', content, re.IGNORECASE)
                    if match and match.group(1).lower() == game_folder.lower():
                        appid_match = re.search(r'appmanifest_(\d+)\.acf', acf.name)
                        if appid_match:
                            return appid_match.group(1)
            except Exception:
                continue
        return ""

    def set_exe_path(self, path):
        self.config["exe_path"] = path
        self._update_paths()
        appid = self.detect_steam_appid(path)
        self.config["steam_appid"] = appid
        self.save_config()
        return self.active_mods_path is not None

    def set_storage_path(self, path):
        self.config["mods_storage_path"] = path
        self.save_config()

    def get_available_mods(self):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str or not os.path.exists(storage_path_str):
            return []
        
        storage_path = Path(storage_path_str)
        mods_metadata = []
        
        if storage_path.exists() and storage_path.is_dir():
            for d in storage_path.iterdir():
                if d.is_dir() and not d.name.startswith("_"):
                    # Check if it's a mod folder (contains .pak or mod.json)
                    if list(d.glob("*.pak")) or (d / "mod.json").exists():
                        metadata = self._ensure_mod_json(d)
                        if metadata:
                            # Sync enabled status with config.json active_mods
                            metadata["enabled"] = d.name in self.config.get("active_mods", [])
                            # Add folder name for reference
                            metadata["folder_name"] = d.name
                            mods_metadata.append(metadata)
        
        return sorted(mods_metadata, key=lambda x: x["name"])

    def _ensure_mod_json(self, mod_path):
        json_path = mod_path / "mod.json"
        mod_folder_name = mod_path.name
        
        default_meta = {
            "name": mod_folder_name,
            "type": "other",
            "enabled": False
        }
        
        if json_path.exists():
            try:
                with open(json_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all fields exist
                    for k, v in data.items():
                        default_meta[k] = v
            except Exception:
                pass # Will overwrite with defaults if corrupt
        
        # Save back to ensure it exists and is clean
        self.save_mod_json(mod_folder_name, default_meta)
        return default_meta

    def save_mod_json(self, mod_folder_name, metadata):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str: return
        
        # Clean folder_name from metadata before saving
        save_data = metadata.copy()
        if "folder_name" in save_data: del save_data["folder_name"]
        
        json_path = Path(storage_path_str) / mod_folder_name / "mod.json"
        try:
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump(save_data, f, indent=4)
        except Exception:
            pass

    def update_mod_metadata(self, mod_folder_name, key, value):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str: return
        
        json_path = Path(storage_path_str) / mod_folder_name / "mod.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                data[key] = value
                with open(json_path, "w", encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            except Exception:
                pass

    def rename_mod(self, old_name, new_name):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str: return False
        
        storage_path = Path(storage_path_str)
        old_path = storage_path / old_name
        new_path = storage_path / new_name
        
        if old_path.exists() and not new_path.exists():
            os.rename(old_path, new_path)
            # Update mod.json internal name
            self.update_mod_metadata(new_name, "name", new_name)
            # Update active mods list
            if old_name in self.config["active_mods"]:
                idx = self.config["active_mods"].index(old_name)
                self.config["active_mods"][idx] = new_name
            self.save_config()
            return True
        return False

    def check_for_migration(self):
        if not self.active_mods_path or not self.active_mods_path.exists():
            return None
        extensions = {'.pak', '.ucas', '.utoc'}
        groups = defaultdict(list)
        for f in self.active_mods_path.iterdir():
            if f.is_file() and f.suffix.lower() in extensions:
                groups[f.stem].append(f)
        return groups if groups else None

    def migrate_mods(self, groups):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str:
            raise ValueError("Selecciona primero una carpeta de almacenamiento")
        
        storage_path = Path(storage_path_str)
        migrated_count = 0
        warnings = []
        for mod_name, files in groups.items():
            has_pak = any(f.suffix.lower() == '.pak' for f in files)
            if not has_pak: continue
            target_dir = storage_path / mod_name
            counter = 1
            while target_dir.exists():
                target_dir = storage_path / f"{mod_name}_{counter}"
                counter += 1
            target_dir.mkdir(parents=True)
            for f in files:
                shutil.move(str(f), str(target_dir / f.name))
            migrated_count += 1
        return migrated_count, warnings

    def sync_mods(self, selected_mods):
        if not self.active_mods_path:
            raise ValueError("Ruta del juego no válida.")
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str:
            raise ValueError("Ruta de almacenamiento no válida.")
        storage_path = Path(storage_path_str)
        
        if self.active_mods_path.exists():
            for f in self.active_mods_path.iterdir():
                if f.is_file(): os.remove(f)
                elif f.is_dir(): shutil.rmtree(f)
        else:
            self.active_mods_path.mkdir(parents=True)

        for mod_name in selected_mods:
            mod_dir = storage_path / mod_name
            if mod_dir.exists():
                for f in mod_dir.iterdir():
                    if f.is_file() and f.suffix.lower() in {'.pak', '.ucas', '.utoc'}:
                        shutil.copy2(f, self.active_mods_path / f.name)
        
        self.config["active_mods"] = selected_mods
        self.save_config()

        # Sync 'enabled' status in mod.json for all mods
        for d in storage_path.iterdir():
            if d.is_dir() and (d / "mod.json").exists():
                is_enabled = d.name in selected_mods
                self.update_mod_metadata(d.name, "enabled", is_enabled)

    def install_mod(self, archive_path, mod_name, mod_type):
        storage_path_str = self.config.get("mods_storage_path")
        if not storage_path_str:
            raise ValueError("No storage path configured")
        
        storage_path = Path(storage_path_str)
        target_dir = storage_path / mod_name
        
        if target_dir.exists():
            raise ValueError("Mod already exists")

        # Temp extraction dir
        temp_dir = storage_path / "_temp_extract"
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)

        try:
            # Extract
            if archive_path.lower().endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif archive_path.lower().endswith('.rar'):
                if not rarfile:
                    raise ImportError("rarfile library not installed")
                with rarfile.RarFile(archive_path) as rf:
                    rf.extractall(temp_dir)
            else:
                raise ValueError("Unsupported archive format")

            # Scan for valid files
            valid_ext = {".pak", ".ucas", ".utoc"}
            found_files = []
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    if any(f.lower().endswith(ext) for ext in valid_ext):
                        found_files.append(Path(root) / f)

            if not found_files:
                raise ValueError("No valid files found")

            # Create mod folder and move files
            target_dir.mkdir(parents=True)
            for f in found_files:
                shutil.move(str(f), str(target_dir / f.name))

            # Save metadata
            metadata = {"name": mod_name, "type": mod_type}
            with open(target_dir / "mod.json", "w", encoding='utf-8') as f:
                json.dump(metadata, f, indent=4)

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
