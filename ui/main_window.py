import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QGroupBox, 
                             QListWidget, QListWidgetItem, QStatusBar, 
                             QFileDialog, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt
from ui.style import NeonStyle
from ui.widgets import ModItemWidget, CustomTitleBar, HeaderSection
from core.i18n import TEXTS

class MainWindow(QMainWindow):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.lang = self.core.config.get("language", "es")
        self.setWindowTitle("DEAD AS DISCO - MOD MANAGER")
        self.setMinimumSize(800, 750)
        
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Apply Global Stylesheet
        self.setStyleSheet(NeonStyle.QSS)
        
        self.setup_ui()
        self.refresh_all()
        
    def setup_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainContainer")
        self.setCentralWidget(self.central_widget)
        
        self.main_vbox = QVBoxLayout(self.central_widget)
        self.main_vbox.setContentsMargins(0, 0, 0, 0)
        self.main_vbox.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.lang_clicked.connect(self.toggle_language)
        self.main_vbox.addWidget(self.title_bar)
        
        # Main Content Area
        self.content_widget = QWidget()
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 30) # No side margins here
        self.main_layout.setSpacing(0)
        
        self.main_vbox.addWidget(self.content_widget)
        
        # Header & Config Section (with Background Banner)
        self.header_section = HeaderSection()
        self.header_layout_outer = QVBoxLayout(self.header_section)
        self.header_layout_outer.setContentsMargins(30, 40, 30, 40)
        self.header_layout_outer.setSpacing(25)
        
        # Header Content
        header_layout = QVBoxLayout()
        self.header_title = QLabel("DEAD AS DISCO")
        self.header_title.setObjectName("HeaderTitle")
        
        self.header_sub = QLabel("MOD MANAGER // V2.0")
        self.header_sub.setObjectName("HeaderSub")
        self.header_sub.setStyleSheet(f"color: {NeonStyle.ACCENT_PURPLE}; font-weight: bold;")
        
        header_layout.addWidget(self.header_title)
        header_layout.addWidget(self.header_sub)
        self.header_layout_outer.addLayout(header_layout)
        
        # Configuration Group
        self.config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout(self.config_group)
        
        # EXE Path
        exe_layout = QHBoxLayout()
        exe_layout.setAlignment(Qt.AlignVCenter)
        self.exe_lbl = QLabel("Ejecutable:")
        exe_layout.addWidget(self.exe_lbl)
        self.exe_edit = QLineEdit(self.core.config.get("exe_path", ""))
        self.exe_edit.setReadOnly(True)
        exe_layout.addWidget(self.exe_edit)
        self.exe_btn = QPushButton("...")
        self.exe_btn.setFixedSize(40, 36)
        self.exe_btn.clicked.connect(self.on_select_exe)
        exe_layout.addWidget(self.exe_btn)
        config_layout.addLayout(exe_layout)
        
        # Storage Path
        storage_layout = QHBoxLayout()
        storage_layout.setAlignment(Qt.AlignVCenter)
        self.storage_lbl = QLabel("Almacenamiento:")
        storage_layout.addWidget(self.storage_lbl)
        self.storage_edit = QLineEdit(self.core.config.get("mods_storage_path", ""))
        self.storage_edit.setReadOnly(True)
        storage_layout.addWidget(self.storage_edit)
        self.storage_btn = QPushButton("...")
        self.storage_btn.setFixedSize(40, 36)
        self.storage_btn.clicked.connect(self.on_select_storage)
        storage_layout.addWidget(self.storage_btn)
        config_layout.addLayout(storage_layout)
        
        self.header_layout_outer.addWidget(self.config_group)
        self.main_layout.addWidget(self.header_section)
        
        # Lower Section (Mod List & Actions)
        self.lower_content = QWidget()
        self.lower_layout = QVBoxLayout(self.lower_content)
        self.lower_layout.setContentsMargins(30, 20, 30, 0)
        self.lower_layout.setSpacing(20)
        
        # Mod List Group
        self.list_group = QGroupBox("Mods Disponibles")
        self.list_group.setObjectName("ModsGroup") # Use cyan accent
        list_layout = QVBoxLayout(self.list_group)
        
        self.mod_list_widget = QListWidget()
        self.mod_list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        list_layout.addWidget(self.mod_list_widget)
        
        self.lower_layout.addWidget(self.list_group, 1)
        
        # Action Buttons
        actions_layout = QHBoxLayout()
        actions_layout.setAlignment(Qt.AlignVCenter)
        actions_layout.setContentsMargins(0, 10, 0, 10)
        
        self.apply_btn = QPushButton("APLICAR CAMBIOS")
        self.apply_btn.clicked.connect(self.on_apply)
        actions_layout.addWidget(self.apply_btn)
        
        self.refresh_btn = QPushButton("ACTUALIZAR")
        self.refresh_btn.clicked.connect(self.refresh_all)
        actions_layout.addWidget(self.refresh_btn)
        
        actions_layout.addStretch()
        
        self.play_btn = QPushButton("LANZAR JUEGO")
        self.play_btn.setObjectName("AccentButton")
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setMinimumHeight(45) # Make the main action button stand out more
        actions_layout.addWidget(self.play_btn)
        
        self.lower_layout.addLayout(actions_layout)
        self.main_layout.addWidget(self.lower_content, 1)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.retranslate_ui()

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
        self.header_title.setText("DEAD AS DISCO")
        self.header_sub.setText(t["header_sub"])
        
        self.config_group.setTitle(t["config_group"])
        self.exe_lbl.setText(t["exe_lbl"])
        self.storage_lbl.setText(t["storage_lbl"])
        self.list_group.setTitle(t["mods_group"])
        
        self.apply_btn.setText(t["apply_btn"])
        self.refresh_btn.setText(t["refresh_btn"])
        self.play_btn.setText(t["play_btn"])
        
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
        
        for mod_name in available_mods:
            is_active = mod_name in active_mods
            item = QListWidgetItem(self.mod_list_widget)
            item_widget = ModItemWidget(mod_name, is_active)
            
            # Connect signals
            item_widget.rename_requested.connect(lambda m=mod_name: self.on_rename_mod(m))
            
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
            if widget.switch.isChecked():
                selected_mods.append(widget.get_name())
        
        try:
            self.set_status(t["status_sync"])
            self.core.sync_mods(selected_mods)
            self.refresh_all()
            self.set_status(t["status_success"])
            QMessageBox.information(self, "OK", t["status_success"])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
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
