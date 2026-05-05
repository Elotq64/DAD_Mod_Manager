from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QMessageBox, QFileDialog, QSizePolicy, QDialog,
                             QProgressDialog)
from PySide6.QtCore import Qt, Signal, QSize, QUrl, QTimer, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
from core.songs.song_scanner import SongScanner
from core.songs.song_importer import SongImporter
from core.songs.song_editor import SongEditor
from ui.songs.song_edit_dialog import SongMetadataDialog
from ui.songs.beat_mapper import BeatMapperDialog
from ui.style import NeonStyle
from ui.widgets import CustomTitleBar

class ImportWorker(QThread):
    finished = Signal(bool, str) # Success, Error Message

    def __init__(self, importer, file_path, metadata):
        super().__init__()
        self.importer = importer
        self.file_path = file_path
        self.metadata = metadata

    def run(self):
        try:
            success, msg = self.importer.import_from_path(self.file_path, self.metadata)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))

class LoadingDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #111111;
                border: 2px solid {NeonStyle.ACCENT_PURPLE};
                border-radius: 10px;
            }}
        """)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"color: white; font-size: 12pt; font-weight: bold;")
        
        self.sub_label = QLabel("Please wait while we process your audio...")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; font-size: 9pt;")
        
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.sub_label)
        layout.addStretch()

class ImportSongDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None
        self.result_type = None # 'file' or 'folder'
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.container)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title_label.setText(" IMPORT SONG")
        self.title_bar.min_btn.hide()
        self.title_bar.lang_btn.hide()
        main_layout.addWidget(self.title_bar)
        
        content = QVBoxLayout()
        content.setContentsMargins(30, 30, 30, 30)
        content.setSpacing(20)
        
        msg = QLabel("How would you like to import a song?")
        msg.setStyleSheet("font-size: 11pt; font-weight: bold;")
        content.addWidget(msg)
        
        self.btn_file = QPushButton("IMPORT FILE (AUDIO/ZIP)")
        self.btn_file.setObjectName("AccentButton")
        self.btn_file.setMinimumHeight(45)
        self.btn_file.clicked.connect(self.select_file)
        content.addWidget(self.btn_file)
        
        self.btn_folder = QPushButton("IMPORT FOLDER")
        self.btn_folder.setMinimumHeight(45)
        self.btn_folder.clicked.connect(self.select_folder)
        content.addWidget(self.btn_folder)
        
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.clicked.connect(self.reject)
        content.addWidget(self.btn_cancel)
        
        main_layout.addLayout(content)

    def select_file(self):
        self.result_type = 'file'
        self.accept()

    def select_folder(self):
        self.result_type = 'folder'
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.move(self.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

class SongItemWidget(QWidget):
    edit_requested = Signal()
    map_requested = Signal()
    delete_requested = Signal()
    play_requested = Signal()

    def __init__(self, song, parent=None):
        super().__init__(parent)
        self.song = song
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(15)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.name_label = QLabel(self.song.song_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: #ffffff;")
        
        artist_text = f"by {self.song.performed_by}" if self.song.performed_by else "Unknown Artist"
        self.details_label = QLabel(f"{artist_text}  |  {self.song.tempo} BPM")
        self.details_label.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; font-size: 9pt;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.details_label)
        
        layout.addLayout(info_layout, 1)
        
        # Actions
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 36)
        self.play_btn.setToolTip("Preview Song")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.play_requested.emit)
        layout.addWidget(self.play_btn)
        
        self.edit_btn = QPushButton("EDIT")
        self.edit_btn.setFixedSize(80, 36)
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.clicked.connect(self.edit_requested.emit)
        layout.addWidget(self.edit_btn)
        
        self.map_btn = QPushButton("MAP")
        self.map_btn.setObjectName("AccentButton")
        self.map_btn.setFixedSize(80, 36)
        self.map_btn.setCursor(Qt.PointingHandCursor)
        self.map_btn.clicked.connect(self.map_requested.emit)
        layout.addWidget(self.map_btn)
        
        from core.i18n import TEXTS
        from ui.main_window import MainWindow
        lang = "en"
        curr = self.parent()
        while curr:
            if isinstance(curr, MainWindow):
                lang = curr.lang
                break
            curr = curr.parent()
        self.map_btn.setText(TEXTS[lang].get("map_btn", "MAP"))
        
        self.delete_btn = QPushButton("DELETE")
        self.delete_btn.setObjectName("DeleteButton")
        self.delete_btn.setStyleSheet(f"""
            QPushButton:hover {{ 
                background-color: {NeonStyle.DANGER}; 
                border-color: {NeonStyle.DANGER};
                color: white;
            }}
        """)
        self.delete_btn.setFixedSize(80, 36)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.delete_btn)

    def set_playing(self, is_playing):
        if is_playing:
            self.play_btn.setText("■")
            self.play_btn.setToolTip("Stop Preview")
            self.play_btn.setStyleSheet(f"color: {NeonStyle.ACCENT}; border-color: {NeonStyle.ACCENT};")
        else:
            self.play_btn.setText("▶")
            self.play_btn.setToolTip("Preview Song")
            self.play_btn.setStyleSheet("")

    def sizeHint(self):
        return QSize(100, 64)

class SongsPage(QWidget):
    launch_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = SongScanner()
        self.importer = SongImporter(self.scanner.get_base_path())
        
        # Audio Playback
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        self.current_playing_widget = None
        
        self.init_ui()
        self.refresh_songs()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        # Songs List Area
        self.songs_list = QListWidget()
        self.songs_list.setObjectName("SongsList")
        self.songs_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        layout.addWidget(self.songs_list)

    def refresh_songs(self):
        self.player.stop()
        self.songs_list.clear()
        songs = self.scanner.scan()
        
        if not songs:
            item = QListWidgetItem(self.songs_list)
            placeholder = QLabel("No custom songs found. Import some to get started!")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; padding: 40px;")
            item.setSizeHint(QSize(100, 100))
            self.songs_list.addItem(item)
            self.songs_list.setItemWidget(item, placeholder)
            return

        for song in songs:
            item = QListWidgetItem(self.songs_list)
            widget = SongItemWidget(song)
            widget.edit_requested.connect(lambda s=song: self.on_edit_song(s))
            widget.map_requested.connect(lambda s=song: self.on_beat_map(s))
            widget.delete_requested.connect(lambda s=song: self.on_delete_song(s))
            widget.play_requested.connect(lambda s=song, w=widget: self.on_play_song(s, w))
            item.setSizeHint(widget.sizeHint())
            self.songs_list.addItem(item)
            self.songs_list.setItemWidget(item, widget)

    def on_play_song(self, song, widget):
        # If already playing this exact song, just stop it
        if self.current_playing_widget == widget:
            if self.player and self.player.playbackState() == QMediaPlayer.PlayingState:
                self.player.stop()
                return

        audio_path = os.path.join(song.folder_path, "Audio.ogg")
        if not os.path.exists(audio_path):
            QMessageBox.warning(self, "Error", "Audio file not found.")
            return

        # Reset visual state of previous widget
        if self.current_playing_widget:
            self.current_playing_widget.set_playing(False)

        # Completely destroy and recreate the player to prevent state-related crashes
        if self.player:
            try:
                self.player.stop()
                self.player.playbackStateChanged.disconnect()
                self.player.deleteLater()
            except:
                pass
        
        # Create fresh player instance
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        self.current_playing_widget = widget
        self.player.setSource(QUrl.fromLocalFile(audio_path))
        self.player.play()
        widget.set_playing(True)

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            if self.current_playing_widget:
                self.current_playing_widget.set_playing(False)
                self.current_playing_widget = None

    def on_import(self):
        dialog = ImportSongDialog(self)
        if dialog.exec():
            if dialog.result_type == 'file':
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select Song File", "", 
                    "All Supported (*.zip *.mp3 *.wav *.ogg);;ZIP Archives (*.zip);;Audio Files (*.mp3 *.wav *.ogg)"
                )
                if path:
                    # Collect metadata before importing if it's a direct audio file
                    if not path.lower().endswith('.zip'):
                        name_hint = os.path.splitext(os.path.basename(path))[0]
                        meta_dialog = SongMetadataDialog(initial_data={"songName": name_hint}, parent=self)
                        if meta_dialog.exec():
                            custom_meta = meta_dialog.get_metadata()
                            self._start_import_worker(path, custom_meta)
                    else:
                        self._start_import_worker(path)
            else:
                path = QFileDialog.getExistingDirectory(self, "Select Song Folder")
                if path:
                    self._start_import_worker(path)

    def _start_import_worker(self, path, metadata=None):
        from core.i18n import TEXTS
        from ui.main_window import MainWindow
        # Get language from parent window
        lang = "en"
        curr = self.parent()
        while curr:
            if isinstance(curr, MainWindow):
                lang = curr.lang
                break
            curr = curr.parent()
        
        t = TEXTS[lang]
        
        # Show Loading Dialog
        self.loading = LoadingDialog(t["importing_msg"], self)
        self.loading.sub_label.setText(t["wait_msg"])
        
        # Start Background Worker
        self.worker = ImportWorker(self.importer, path, metadata)
        self.worker.finished.connect(self._on_import_finished)
        
        self.loading.show()
        self.worker.start()

    def _on_import_finished(self, success, msg):
        if hasattr(self, 'loading'):
            self.loading.close()
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.refresh_songs()
        else:
            QMessageBox.critical(self, "Import Error", msg)

    def on_edit_song(self, song):
        dialog = SongMetadataDialog(song=song, parent=self)
        if dialog.exec():
            new_data = dialog.get_metadata()
            success, result = SongEditor.update_song_metadata(song, new_data)
            if success:
                self.refresh_songs()
            else:
                QMessageBox.critical(self, "Validation Error", "\n".join(result))

    def on_beat_map(self, song):
        from ui.main_window import MainWindow
        lang = "en"
        curr = self.parent()
        while curr:
            if isinstance(curr, MainWindow):
                lang = curr.lang
                break
            curr = curr.parent()
            
        self.player.stop() # Stop preview if playing
        song.reload() # Reload from JSON to ensure latest data
        dialog = BeatMapperDialog(song, lang=lang, parent=self)
        if dialog.exec():
            self.refresh_songs()

    def on_delete_song(self, song):
        res = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete '{song.song_name}'?\n\nThis will remove the folder from the game's directory.",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            success, msg = SongEditor.delete_song(song)
            if success:
                self.refresh_songs()
            else:
                QMessageBox.critical(self, "Error", msg)

