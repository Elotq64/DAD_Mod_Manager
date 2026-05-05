import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QGroupBox, 
                             QListWidget, QListWidgetItem, QStatusBar, 
                             QFileDialog, QMessageBox, QInputDialog, QStackedWidget, QSizeGrip)
from PySide6.QtCore import Qt, QRect
from ui.style import NeonStyle
from ui.widgets import ModItemWidget, CustomTitleBar, HeaderSection, AddModDialog, ModListHeader
from ui.songs.songs_page import SongsPage
from core.i18n import TEXTS

class MainWindow(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.lang = self.core.config.get("language", "es")
        self.setWindowTitle("DEAD AS DISCO - MOD MANAGER")
        self.setMinimumSize(1000, 850)
        self.resize(1000, 850)
        
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_Hover)
        
        # Apply Global Stylesheet
        self.setStyleSheet(NeonStyle.QSS)
        
        self.setup_ui()
        self.refresh_all()
        
    def setup_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainContainer")
        self.setCentralWidget(self.central_widget)
        
        # Root Layout: Horizontal (Sidebar | Content)
        self.root_layout = QHBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        
        # --- SIDEBAR (LEFT) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(f"""
            QWidget#Sidebar {{
                background-color: #0a0a0a;
                border-right: 1px solid {NeonStyle.ACCENT}33;
            }}
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)
        
        # Sidebar Branding
        brand_layout = QVBoxLayout()
        self.brand_title = QLabel("MOD MANAGER")
        self.brand_title.setStyleSheet(f"color: {NeonStyle.ACCENT}; font-weight: bold; font-size: 14pt; letter-spacing: 2px;")
        self.brand_sub = QLabel("V5.0 // STABLE")
        self.brand_sub.setStyleSheet(f"color: {NeonStyle.ACCENT_PURPLE}; font-size: 8pt; font-weight: bold; letter-spacing: 1px;")
        brand_layout.addWidget(self.brand_title)
        brand_layout.addWidget(self.brand_sub)
        sidebar_layout.addLayout(brand_layout)
        
        sidebar_layout.addSpacing(30)
        
        # Navigation Section
        self.nav_label = QLabel("CATEGORIES")
        self.nav_label.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; font-size: 8pt; font-weight: bold;")
        sidebar_layout.addWidget(self.nav_label)
        
        self.mods_tab_btn = QPushButton("MODS")
        self.mods_tab_btn.setCheckable(True)
        self.mods_tab_btn.setChecked(True)
        self.mods_tab_btn.setMinimumHeight(45)
        self.mods_tab_btn.clicked.connect(lambda: self.switch_page(0))
        sidebar_layout.addWidget(self.mods_tab_btn)
        
        self.songs_tab_btn = QPushButton("SONGS")
        self.songs_tab_btn.setCheckable(True)
        self.songs_tab_btn.setMinimumHeight(45)
        self.songs_tab_btn.clicked.connect(lambda: self.switch_page(1))
        sidebar_layout.addWidget(self.songs_tab_btn)
        
        sidebar_layout.addSpacing(30)
        
        # Contextual Actions Section
        self.actions_label = QLabel("ACTIONS")
        self.actions_label.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; font-size: 8pt; font-weight: bold;")
        sidebar_layout.addWidget(self.actions_label)
        
        self.actions_stack = QStackedWidget()
        
        # Actions: Mods
        self.mod_actions_widget = QWidget()
        mod_actions_layout = QVBoxLayout(self.mod_actions_widget)
        mod_actions_layout.setContentsMargins(0, 0, 0, 0)
        mod_actions_layout.setSpacing(10)
        
        self.apply_btn = QPushButton("APLICAR CAMBIOS")
        self.apply_btn.setMinimumHeight(40)
        self.apply_btn.clicked.connect(self.on_apply)
        mod_actions_layout.addWidget(self.apply_btn)
        
        self.refresh_btn = QPushButton("ACTUALIZAR")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.clicked.connect(self.refresh_all)
        mod_actions_layout.addWidget(self.refresh_btn)
        
        self.add_mod_btn = QPushButton("AÑADIR MOD")
        self.add_mod_btn.setMinimumHeight(40)
        self.add_mod_btn.clicked.connect(self.on_add_mod)
        mod_actions_layout.addWidget(self.add_mod_btn)
        
        self.actions_stack.addWidget(self.mod_actions_widget)
        
        # Actions: Songs
        self.song_actions_widget = QWidget()
        song_actions_layout = QVBoxLayout(self.song_actions_widget)
        song_actions_layout.setContentsMargins(0, 0, 0, 0)
        song_actions_layout.setSpacing(10)
        
        self.song_refresh_btn = QPushButton("REFRESH")
        self.song_refresh_btn.setMinimumHeight(40)
        self.song_refresh_btn.clicked.connect(lambda: self.songs_page.refresh_songs())
        song_actions_layout.addWidget(self.song_refresh_btn)
        
        self.import_song_btn = QPushButton("IMPORT SONG")
        self.import_song_btn.setMinimumHeight(40)
        self.import_song_btn.clicked.connect(lambda: self.songs_page.on_import())
        song_actions_layout.addWidget(self.import_song_btn)
        
        self.actions_stack.addWidget(self.song_actions_widget)
        sidebar_layout.addWidget(self.actions_stack)
        
        sidebar_layout.addStretch()
        
        # Global Launch Button
        self.play_btn = QPushButton("LANZAR JUEGO")
        self.play_btn.setObjectName("AccentButton")
        self.play_btn.setMinimumHeight(55)
        self.play_btn.clicked.connect(self.on_play)
        sidebar_layout.addWidget(self.play_btn)
        
        self.root_layout.addWidget(self.sidebar)
        
        # --- MAIN CONTENT (RIGHT) ---
        self.content_container = QWidget()
        main_vbox = QVBoxLayout(self.content_container)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.lang_clicked.connect(self.toggle_language)
        main_vbox.addWidget(self.title_bar)
        
        # Header & Config Section
        self.header_section = HeaderSection()
        header_content_layout = QVBoxLayout(self.header_section)
        header_content_layout.setContentsMargins(40, 30, 40, 30)
        header_content_layout.setSpacing(20)
        
        self.header_title = QLabel("DEAD AS DISCO")
        self.header_title.setObjectName("HeaderTitle")
        header_content_layout.addWidget(self.header_title)
        
        # Configuration Group
        self.config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout(self.config_group)
        
        # EXE Path
        exe_layout = QHBoxLayout()
        self.exe_lbl = QLabel("Ejecutable:")
        self.exe_edit = QLineEdit(self.core.config.get("exe_path", ""))
        self.exe_edit.setReadOnly(True)
        self.exe_btn = QPushButton("...")
        self.exe_btn.setFixedSize(40, 36)
        self.exe_btn.clicked.connect(self.on_select_exe)
        exe_layout.addWidget(self.exe_lbl)
        exe_layout.addWidget(self.exe_edit)
        exe_layout.addWidget(self.exe_btn)
        config_layout.addLayout(exe_layout)
        
        # Storage Path
        storage_layout = QHBoxLayout()
        self.storage_lbl = QLabel("Almacenamiento:")
        self.storage_edit = QLineEdit(self.core.config.get("mods_storage_path", ""))
        self.storage_edit.setReadOnly(True)
        self.storage_btn = QPushButton("...")
        self.storage_btn.setFixedSize(40, 36)
        self.storage_btn.clicked.connect(self.on_select_storage)
        storage_layout.addWidget(self.storage_lbl)
        storage_layout.addWidget(self.storage_edit)
        storage_layout.addWidget(self.storage_btn)
        config_layout.addLayout(storage_layout)
        
        header_content_layout.addWidget(self.config_group)
        main_vbox.addWidget(self.header_section)
        
        # Stacked Widget for Lists
        self.stacked_widget = QStackedWidget()
        
        # Page 0: Mods
        self.mods_content = QWidget()
        mods_layout = QVBoxLayout(self.mods_content)
        mods_layout.setContentsMargins(40, 20, 40, 20)
        
        self.list_group = QGroupBox("Mods Disponibles")
        self.list_group.setObjectName("ModsGroup") 
        list_layout = QVBoxLayout(self.list_group)
        self.mod_list_widget = QListWidget()
        self.mod_list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.mod_header = ModListHeader(self.lang)
        list_layout.addWidget(self.mod_header)
        list_layout.addWidget(self.mod_list_widget)
        mods_layout.addWidget(self.list_group)
        
        # Page 1: Songs
        self.songs_page = SongsPage()
        self.songs_page.launch_requested.connect(self.on_play)
        
        self.stacked_widget.addWidget(self.mods_content)
        self.stacked_widget.addWidget(self.songs_page)
        main_vbox.addWidget(self.stacked_widget, 1)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(True)
        main_vbox.addWidget(self.status_bar)
        
        # Manual Size Grip at the bottom right corner of the root window
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        
        self.root_layout.addWidget(self.content_container, 1)
        self.retranslate_ui()

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.actions_stack.setCurrentIndex(index)
        self.mods_tab_btn.setChecked(index == 0)
        self.songs_tab_btn.setChecked(index == 1)
        
        # Refresh the page being shown
        if index == 0:
            self.refresh_all()
        else:
            self.songs_page.refresh_songs()

    def toggle_language(self):
        self.lang = "en" if self.lang == "es" else "es"
        self.core.config["language"] = self.lang
        self.core.save_config()
        self.retranslate_ui()
        self.refresh_all()

    def retranslate_ui(self):
        t = TEXTS[self.lang]
        self.setWindowTitle(t["title"])
        self.title_bar.title_label.setText(f" {t['title']}")
        self.title_bar.lang_btn.setText(t["lang_btn"])
        
        self.brand_title.setText(t["title_short"] if "title_short" in t else "MOD MANAGER")
        self.brand_sub.setText(t["header_sub"])
        
        self.nav_label.setText(t["nav_categories"])
        self.actions_label.setText(t["nav_actions"])
        self.mods_tab_btn.setText(t["nav_mods"])
        self.songs_tab_btn.setText(t["nav_songs"])
        self.import_song_btn.setText(t["import_song_btn"])
        self.song_refresh_btn.setText(t["refresh_btn"])
        
        self.header_title.setText("DEAD AS DISCO")
        
        self.config_group.setTitle(t["config_group"])
        self.exe_lbl.setText(t["exe_lbl"])
        self.storage_lbl.setText(t["storage_lbl"])
        self.list_group.setTitle(t["mods_group"])
        
        self.apply_btn.setText(t["apply_btn"])
        self.refresh_btn.setText(t["refresh_btn"])
        self.add_mod_btn.setText(t["add_mod_btn"])
        self.play_btn.setText(t["play_btn"])
        
        self.mod_header.retranslate(self.lang)
        
        self.set_status(t["status_ready"])
    
    def set_status(self, msg):
        self.status_bar.showMessage(f"● {msg}")

    def on_select_exe(self):
        t = TEXTS[self.lang]
        path, _ = QFileDialog.getOpenFileName(self, "Selecciona Pagoda.exe", "", "Ejecutable (Pagoda.exe);;Todos (*.exe)")
        if path:
            valid = self.core.set_exe_path(path)
            self.exe_edit.setText(path)
            if not valid:
                QMessageBox.critical(self, "Error", t["msg_error_path"])
            else:
                self.check_migration()
            self.refresh_all()

    def on_select_storage(self):
        path = QFileDialog.getExistingDirectory(self, "Selecciona carpeta de almacenamiento")
        if path:
            self.core.set_storage_path(path)
            self.storage_edit.setText(path)
            self.check_migration()
            self.refresh_all()

    def check_migration(self):
        t = TEXTS[self.lang]
        groups = self.core.check_for_migration()
        if groups:
            if not self.core.config.get("mods_storage_path"): return
            res = QMessageBox.question(self, "Migración", t["msg_migration"], 
                                     QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                try:
                    count, warnings = self.core.migrate_mods(groups)
                    QMessageBox.information(self, "Éxito", f"Migrados {count} mods.")
                    self.refresh_all()
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    def refresh_all(self):
        self.mod_list_widget.clear()
        available_mods = self.core.get_available_mods()
        active_mods = self.core.config.get("active_mods", [])
        
        for mod_data in available_mods:
            folder_name = mod_data["folder_name"]
            is_active = folder_name in active_mods
            item = QListWidgetItem(self.mod_list_widget)
            item_widget = ModItemWidget(mod_data, is_active, self.lang)
            
            # Connect signals
            item_widget.rename_requested.connect(lambda f=folder_name: self.on_rename_mod(f))
            
            # Ensure item height is sufficient
            item.setSizeHint(item_widget.sizeHint())
            self.mod_list_widget.addItem(item)
            self.mod_list_widget.setItemWidget(item, item_widget)
            
        appid = self.core.config.get("steam_appid")
        if appid:
            self.set_status(TEXTS[self.lang]["steam_detected"].format(appid))
        else:
            self.set_status(TEXTS[self.lang]["status_ready"])

    def on_rename_mod(self, old_name):
        t = TEXTS[self.lang]
        new_name, ok = QInputDialog.getText(self, t["msg_rename_title"], t["msg_rename_lbl"].format(old_name), text=old_name)
        if ok and new_name and new_name != old_name:
            if self.core.rename_mod(old_name, new_name):
                self.refresh_all()
            else:
                QMessageBox.warning(self, "Error", "No se pudo renombrar el mod.")

    def on_apply(self):
        t = TEXTS[self.lang]
        selected_mods = []
        for i in range(self.mod_list_widget.count()):
            item = self.mod_list_widget.item(i)
            widget = self.mod_list_widget.itemWidget(item)
            
            folder_name = widget.get_name()
            current_type = widget.type_combo.currentData()
            
            # Update type in metadata
            self.core.update_mod_metadata(folder_name, "type", current_type)
            
            if widget.switch.isChecked():
                selected_mods.append(folder_name)
        
        # Conflict Check
        type_counts = {"character": 0, "map": 0}
        
        # Collect types of selected mods
        available_mods = {m["folder_name"]: m["type"] for m in self.core.get_available_mods()}
        for mod_folder in selected_mods:
            m_type = available_mods.get(mod_folder, "other")
            if m_type in type_counts:
                type_counts[m_type] += 1
        
        # Check for multiple active of same critical type
        conflicts = [t for t, count in type_counts.items() if count > 1]
        if conflicts:
            conflict_names = [t["type_" + c] for c in conflicts] # Get translated names
            msg = t["msg_conflict_warn"].format(", ".join(conflict_names))
            res = QMessageBox.warning(self, t["msg_conflict_title"], msg, 
                                     QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.No:
                return

        try:
            self.set_status(t["status_sync"])
            self.core.sync_mods(selected_mods)
            self.refresh_all()
            self.set_status(t["status_success"])
            QMessageBox.information(self, "OK", t["status_success"])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.set_status(t["status_error"])

    def on_add_mod(self):
        t = TEXTS[self.lang]
        file_path, _ = QFileDialog.getOpenFileName(
            self, t["add_mod_title"], "", "Archives (*.zip *.rar)"
        )
        if not file_path:
            return

        default_name = os.path.splitext(os.path.basename(file_path))[0]
        dialog = AddModDialog(default_name, self.lang, self)
        if dialog.exec():
            mod_name, mod_type = dialog.get_data()
            if not mod_name:
                return
            
            try:
                self.set_status(t["status_sync"]) 
                self.core.install_mod(file_path, mod_name, mod_type)
                self.refresh_all()
                self.set_status(t["status_success"])
            except Exception as e:
                error_msg = str(e)
                if "rarfile" in error_msg:
                    error_msg = t["error_rar_library"]
                elif "No valid files" in error_msg:
                    error_msg = t["error_no_valid_files"]
                elif "Mod already exists" in error_msg:
                    error_msg = t["error_already_exists"]
                
                QMessageBox.critical(self, "Error", error_msg)
                self.set_status(t["status_error"])

    def on_play(self):
        appid = self.core.config.get("steam_appid")
        exe = self.core.config.get("exe_path")
        try:
            if appid:
                self.set_status(f"Iniciando vía Steam ({appid})...")
                os.startfile(f"steam://run/{appid}")
            elif exe and os.path.exists(exe):
                os.startfile(exe)
            else:
                QMessageBox.warning(self, "Configuración incompleta", "Por favor, configura el ejecutable del juego.")
        except Exception as e:
            self.set_status(f"Error al lanzar: {e}")
